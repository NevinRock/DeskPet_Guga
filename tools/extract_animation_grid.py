from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median

from PIL import Image


def visible_box(image: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    mask = image.getchannel("A").point(lambda value: 255 if value > threshold else 0)
    return mask.getbbox()


def body_anchor_x(
    image: Image.Image, box: tuple[int, int, int, int], threshold: int
) -> float:
    """Estimate the stable lower-body centre while ignoring raised hands and props."""
    alpha = image.getchannel("A")
    pixels = alpha.load()
    top = box[1] + round((box[3] - box[1]) * 0.56)
    bottom = box[1] + round((box[3] - box[1]) * 0.90)
    centres: list[float] = []
    for y in range(top, max(top + 1, bottom)):
        visible = [x for x in range(box[0], box[2]) if pixels[x, y] > threshold]
        if visible:
            centres.append((visible[0] + visible[-1] + 1) / 2)
    return median(centres) if centres else (box[0] + box[2]) / 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--columns", type=int, default=5)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--cell-width", type=int, default=192)
    parser.add_argument("--cell-height", type=int, default=208)
    parser.add_argument("--alpha-threshold", type=int, default=24)
    parser.add_argument("--margin", type=int, default=5)
    parser.add_argument("--resampling", choices=("lanczos", "nearest"), default="lanczos")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if args.columns < 1 or args.rows < 1:
        raise SystemExit("columns and rows must be positive")

    source = Image.open(args.input).convert("RGBA")
    slots: list[Image.Image] = []
    source_boxes: list[tuple[int, int, int, int]] = []
    source_edge_hits: list[bool] = []
    for row in range(args.rows):
        top = round(row * source.height / args.rows)
        bottom = round((row + 1) * source.height / args.rows)
        for column in range(args.columns):
            left = round(column * source.width / args.columns)
            right = round((column + 1) * source.width / args.columns)
            slot = source.crop((left, top, right, bottom))
            box = visible_box(slot, args.alpha_threshold)
            if box is None:
                raise SystemExit(f"Generated grid cell {len(slots)} is empty")
            slots.append(slot)
            source_boxes.append(box)
            source_edge_hits.append(
                box[0] <= 1
                or box[1] <= 1
                or box[2] >= slot.width - 1
                or box[3] >= slot.height - 1
            )

    anchors = [
        body_anchor_x(slot, box, args.alpha_threshold)
        for slot, box in zip(slots, source_boxes)
    ]
    max_width = max(box[2] - box[0] for box in source_boxes)
    max_height = max(box[3] - box[1] for box in source_boxes)
    scale = min(
        (args.cell_width - args.margin * 2) / max_width,
        (args.cell_height - args.margin * 2) / max_height,
    )
    if scale <= 0:
        raise SystemExit("Unable to calculate a positive shared scale")

    resampling = (
        Image.Resampling.NEAREST
        if args.resampling == "nearest"
        else Image.Resampling.LANCZOS
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_frames: list[dict[str, object]] = []
    for index, (slot, box, anchor, source_edge_hit) in enumerate(
        zip(slots, source_boxes, anchors, source_edge_hits)
    ):
        subject = slot.crop(box)
        size = (
            max(1, round(subject.width * scale)),
            max(1, round(subject.height * scale)),
        )
        subject = subject.resize(size, resampling)
        frame = Image.new("RGBA", (args.cell_width, args.cell_height), (0, 0, 0, 0))
        x = round(args.cell_width / 2 - (anchor - box[0]) * scale)
        x = max(args.margin, min(x, args.cell_width - args.margin - subject.width))
        y = args.cell_height - args.margin - subject.height
        frame.alpha_composite(subject, (x, y))

        pixels = frame.load()
        for edge_x in range(args.margin):
            for edge_y in range(args.cell_height):
                pixels[edge_x, edge_y] = (0, 0, 0, 0)
                pixels[args.cell_width - 1 - edge_x, edge_y] = (0, 0, 0, 0)
        for edge_y in range(args.margin):
            for edge_x in range(args.cell_width):
                pixels[edge_x, edge_y] = (0, 0, 0, 0)
                pixels[edge_x, args.cell_height - 1 - edge_y] = (0, 0, 0, 0)

        output_path = args.output_dir / f"{index:02d}.png"
        frame.save(output_path)
        output_box = visible_box(frame, args.alpha_threshold)
        if output_box is None:
            raise SystemExit(f"Extracted frame {index} is empty")
        report_frames.append(
            {
                "frame": index,
                "source_box": list(box),
                "source_edge_hit": source_edge_hit,
                "output_box": list(output_box),
                "baseline": output_box[3],
                "edge_clear": (
                    output_box[0] >= args.margin
                    and output_box[1] >= args.margin
                    and output_box[2] <= args.cell_width - args.margin
                    and output_box[3] <= args.cell_height - args.margin
                ),
            }
        )

    report = {
        "ok": all(frame["edge_clear"] for frame in report_frames),
        "input": str(args.input),
        "grid": [args.columns, args.rows],
        "frames": len(report_frames),
        "shared_scale": scale,
        "output_size": [args.cell_width, args.cell_height],
        "output_baseline_range": [
            min(int(frame["baseline"]) for frame in report_frames),
            max(int(frame["baseline"]) for frame in report_frames),
        ],
        "details": report_frames,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit("Grid extraction QA failed; inspect the JSON report")


if __name__ == "__main__":
    main()
