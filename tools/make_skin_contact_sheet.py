from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def checkerboard(size: tuple[int, int], tile: int = 8) -> Image.Image:
    image = Image.new("RGBA", size, "white")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#d9d9d9")
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skin_actions", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=float, default=0.75)
    args = parser.parse_args()

    action_dirs = sorted(path for path in args.skin_actions.iterdir() if path.is_dir())
    frame_width = round(192 * args.scale)
    frame_height = round(208 * args.scale)
    label_width = 120
    row_height = frame_height + 18
    max_frames = max(len(list(path.glob("*.png"))) for path in action_dirs)
    sheet = Image.new(
        "RGBA",
        (label_width + frame_width * max_frames, row_height * len(action_dirs)),
        "#f3f3f3",
    )
    draw = ImageDraw.Draw(sheet)
    for row, action_dir in enumerate(action_dirs):
        top = row * row_height
        draw.text((6, top + 6), action_dir.name, fill="black")
        for column, frame_path in enumerate(sorted(action_dir.glob("*.png"))):
            frame = Image.open(frame_path).convert("RGBA")
            frame = frame.resize((frame_width, frame_height), Image.Resampling.NEAREST)
            panel = checkerboard(frame.size)
            panel.alpha_composite(frame)
            sheet.alpha_composite(panel, (label_width + column * frame_width, top))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(args.output, quality=92)


if __name__ == "__main__":
    main()
