from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--cell-width", type=int, default=192)
    parser.add_argument("--cell-height", type=int, default=208)
    args = parser.parse_args()

    strip = Image.open(args.input).convert("RGBA")
    slot_edges = [round(i * strip.width / args.frames) for i in range(args.frames + 1)]
    slots = [strip.crop((slot_edges[i], 0, slot_edges[i + 1], strip.height)) for i in range(args.frames)]
    boxes = [slot.getchannel("A").getbbox() for slot in slots]
    if any(box is None for box in boxes):
        raise SystemExit("A generated frame is empty")

    typed_boxes = [box for box in boxes if box is not None]
    common_top = min(box[1] for box in typed_boxes)
    common_bottom = max(box[3] for box in typed_boxes)
    widest = max(box[2] - box[0] for box in typed_boxes)
    common_height = common_bottom - common_top
    scale = min((args.cell_width - 10) / widest, (args.cell_height - 10) / common_height)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index, (slot, box) in enumerate(zip(slots, typed_boxes)):
        subject = slot.crop(box)
        size = (max(1, round(subject.width * scale)), max(1, round(subject.height * scale)))
        subject = subject.resize(size, Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", (args.cell_width, args.cell_height), (0, 0, 0, 0))
        x = (args.cell_width - subject.width) // 2
        y = 5 + round((box[1] - common_top) * scale)
        frame.alpha_composite(subject, (x, y))
        frame.save(args.output_dir / f"{index:02d}.png")

    print({"frames": args.frames, "scale": scale, "common_y": [common_top, common_bottom]})


if __name__ == "__main__":
    main()
