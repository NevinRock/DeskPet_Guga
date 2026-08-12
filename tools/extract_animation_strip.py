from __future__ import annotations

import argparse
from pathlib import Path
from statistics import median

from PIL import Image


def _frame_boundaries(strip: Image.Image, frame_count: int, threshold: int) -> list[int]:
    """Find the quietest vertical seam around every expected frame boundary.

    Image generators do not place characters on an exact pixel grid. Splitting a
    strip into equal-width cells can therefore cut through one pose and include
    a piece of the next one. The transparent/low-ink valley between poses is a
    much safer seam.
    """
    alpha = strip.getchannel("A")
    pixels = alpha.load()
    column_ink = [
        sum(1 for y in range(strip.height) if pixels[x, y] > threshold)
        for x in range(strip.width)
    ]
    nominal_width = strip.width / frame_count
    boundaries = [0]
    for index in range(1, frame_count):
        target = round(index * nominal_width)
        radius = max(4, round(nominal_width * 0.30))
        left = max(boundaries[-1] + 1, target - radius)
        right = min(strip.width - 1, target + radius)
        lowest = min(column_ink[left : right + 1])
        candidates = [x for x in range(left, right + 1) if column_ink[x] == lowest]
        boundaries.append(min(candidates, key=lambda x: abs(x - target)))
    boundaries.append(strip.width)
    return boundaries


def _visible_box(image: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    mask = image.getchannel("A").point(lambda value: 255 if value > threshold else 0)
    return mask.getbbox()


def _body_anchor_x(
    image: Image.Image, box: tuple[int, int, int, int], threshold: int
) -> float:
    """Use the lower robe as a stable horizontal anchor instead of the full pose.

    Hands, food and props change the full bounding box substantially. Centering
    that box makes the character's body jump in the opposite direction. The
    median centre of the lower-body silhouette stays visually stationary.
    """
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
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--cell-width", type=int, default=192)
    parser.add_argument("--cell-height", type=int, default=208)
    parser.add_argument("--alpha-threshold", type=int, default=24)
    parser.add_argument(
        "--resampling",
        choices=("lanczos", "nearest"),
        default="lanczos",
        help="Use nearest for pixel art and lanczos for rendered/photographic characters.",
    )
    parser.add_argument(
        "--preserve-vertical-motion",
        action="store_true",
        help="Keep source Y offsets (use for jumping); otherwise align every pose to one baseline.",
    )
    args = parser.parse_args()
    resampling = (
        Image.Resampling.NEAREST
        if args.resampling == "nearest"
        else Image.Resampling.LANCZOS
    )

    strip = Image.open(args.input).convert("RGBA")
    slot_edges = _frame_boundaries(strip, args.frames, args.alpha_threshold)
    slots = [strip.crop((slot_edges[i], 0, slot_edges[i + 1], strip.height)) for i in range(args.frames)]
    boxes = [_visible_box(slot, args.alpha_threshold) for slot in slots]
    if any(box is None for box in boxes):
        raise SystemExit("A generated frame is empty")

    typed_boxes = [box for box in boxes if box is not None]
    anchors = [
        _body_anchor_x(slot, box, args.alpha_threshold)
        for slot, box in zip(slots, typed_boxes)
    ]
    common_top = min(box[1] for box in typed_boxes)
    common_bottom = max(box[3] for box in typed_boxes)
    common_height = common_bottom - common_top
    margin = 5
    left_extent = max(anchor - box[0] for anchor, box in zip(anchors, typed_boxes))
    right_extent = max(box[2] - anchor for anchor, box in zip(anchors, typed_boxes))
    scale = min(
        (args.cell_width / 2 - margin) / left_extent,
        (args.cell_width / 2 - margin) / right_extent,
        (args.cell_height - margin * 2) / common_height,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index, (slot, box, anchor) in enumerate(zip(slots, typed_boxes, anchors)):
        subject = slot.crop(box)
        size = (max(1, round(subject.width * scale)), max(1, round(subject.height * scale)))
        subject = subject.resize(size, resampling)
        frame = Image.new("RGBA", (args.cell_width, args.cell_height), (0, 0, 0, 0))
        x = round(args.cell_width / 2 - (anchor - box[0]) * scale)
        if args.preserve_vertical_motion:
            y = margin + round((box[1] - common_top) * scale)
        else:
            y = args.cell_height - margin - subject.height
        frame.alpha_composite(subject, (x, y))
        # The scale calculation reserves a safety margin. Clearing it also
        # removes any antialias residue exactly on a detected strip seam.
        pixels = frame.load()
        for edge_x in range(margin):
            for edge_y in range(args.cell_height):
                pixels[edge_x, edge_y] = (0, 0, 0, 0)
                pixels[args.cell_width - 1 - edge_x, edge_y] = (0, 0, 0, 0)
        for edge_y in range(margin):
            for edge_x in range(args.cell_width):
                pixels[edge_x, edge_y] = (0, 0, 0, 0)
                pixels[edge_x, args.cell_height - 1 - edge_y] = (0, 0, 0, 0)
        frame.save(args.output_dir / f"{index:02d}.png")

    print(
        {
            "frames": args.frames,
            "scale": scale,
            "boundaries": slot_edges,
            "common_y": [common_top, common_bottom],
        }
    )


if __name__ == "__main__":
    main()
