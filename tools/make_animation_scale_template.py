from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def visible_box(image: Image.Image, threshold: int) -> tuple[int, int, int, int]:
    mask = image.getchannel("A").point(lambda value: 255 if value > threshold else 0)
    box = mask.getbbox()
    if box is None:
        raise SystemExit("Reference image has no visible pixels")
    return box


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--columns", type=int, default=5)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--width", type=int, default=1536)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--body-height", type=int, default=230)
    parser.add_argument("--bottom-padding", type=int, default=16)
    parser.add_argument("--key-color", default="#00ff00")
    parser.add_argument("--alpha-threshold", type=int, default=24)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    reference = Image.open(args.reference).convert("RGBA")
    box = visible_box(reference, args.alpha_threshold)
    visible_height = box[3] - box[1]
    scale = args.body_height / visible_height
    resized = reference.resize(
        (round(reference.width * scale), round(reference.height * scale)),
        Image.Resampling.LANCZOS,
    )
    resized_box = visible_box(resized, args.alpha_threshold)
    canvas = Image.new("RGB", (args.width, args.height), args.key_color)
    placements: list[dict[str, int]] = []

    for row in range(args.rows):
        cell_top = round(row * args.height / args.rows)
        cell_bottom = round((row + 1) * args.height / args.rows)
        for column in range(args.columns):
            cell_left = round(column * args.width / args.columns)
            cell_right = round((column + 1) * args.width / args.columns)
            target_center_x = (cell_left + cell_right) // 2
            target_baseline = cell_bottom - args.bottom_padding
            x = round(target_center_x - (resized_box[0] + resized_box[2]) / 2)
            y = target_baseline - resized_box[3]
            canvas.paste(resized.convert("RGB"), (x, y), resized.getchannel("A"))
            placements.append(
                {
                    "frame": row * args.columns + column,
                    "body_left": x + resized_box[0],
                    "body_top": y + resized_box[1],
                    "body_right": x + resized_box[2],
                    "body_baseline": y + resized_box[3],
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    report = {
        "ok": True,
        "reference": str(args.reference),
        "output": str(args.output),
        "canvas": [args.width, args.height],
        "grid": [args.columns, args.rows],
        "target_body_height": args.body_height,
        "scale": scale,
        "placements": placements,
    }
    if args.report:
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
