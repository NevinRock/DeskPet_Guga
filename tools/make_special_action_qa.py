from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


SKINS = (
    ("Guga — wiggle", Path("assets/actions/special")),
    ("Phoebe — hat and cake", Path("assets/skins/phoebe/actions/special")),
    ("Guga (Eunuch) — bow", Path("assets/skins/guga-eunuch/actions/special")),
    ("Creator — BUG", Path("assets/skins/author/actions/special")),
)


def checkerboard(size: tuple[int, int], tile: int = 8) -> Image.Image:
    image = Image.new("RGBA", size, "white")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#d8d8d8")
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--fps", type=int, default=3)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    scale = 0.65
    frame_size = (round(192 * scale), round(208 * scale))
    columns = 5
    rows = 3
    title_height = 28
    block_width = columns * frame_size[0]
    block_height = title_height + rows * frame_size[1]
    sheet = Image.new("RGB", (block_width, block_height * len(SKINS)), "#f2f2f2")
    draw = ImageDraw.Draw(sheet)

    for skin_index, (label, relative_dir) in enumerate(SKINS):
        action_dir = Path(__file__).resolve().parents[1] / relative_dir
        frame_paths = sorted(action_dir.glob("*.png"))
        if len(frame_paths) != 15:
            raise SystemExit(f"{relative_dir} has {len(frame_paths)} PNG frames; expected 15")
        top = skin_index * block_height
        draw.text((8, top + 7), label, fill="#202020")
        preview_frames: list[Image.Image] = []
        transparent_preview_frames: list[Image.Image] = []
        for index, frame_path in enumerate(frame_paths):
            frame = Image.open(frame_path).convert("RGBA")
            if frame.size != (192, 208):
                raise SystemExit(f"{frame_path} has size {frame.size}; expected 192x208")
            scaled = frame.resize(frame_size, Image.Resampling.NEAREST)
            panel = checkerboard(frame_size)
            panel.alpha_composite(scaled)
            panel_rgb = panel.convert("RGB")
            x = (index % columns) * frame_size[0]
            y = top + title_height + (index // columns) * frame_size[1]
            sheet.paste(panel_rgb, (x, y))
            ImageDraw.Draw(sheet).text((x + 4, y + 4), f"{index:02d}", fill="#303030")

            gif_panel = checkerboard((192, 208))
            gif_panel.alpha_composite(frame)
            preview_frames.append(gif_panel.convert("RGB"))
            transparent_preview_frames.append(frame)

        preview_frames[0].save(
            args.output_dir / f"special-{relative_dir.parts[-3] if 'skins' in relative_dir.parts else 'guga'}.gif",
            save_all=True,
            append_images=preview_frames[1:],
            duration=round(1000 / args.fps),
            loop=0,
            disposal=2,
        )
        transparent_preview_frames[0].save(
            args.output_dir
            / f"special-{relative_dir.parts[-3] if 'skins' in relative_dir.parts else 'guga'}.webp",
            save_all=True,
            append_images=transparent_preview_frames[1:],
            duration=round(1000 / args.fps),
            loop=0,
            lossless=True,
            method=6,
        )

    sheet.save(args.output_dir / "special-actions-contact-sheet.png")


if __name__ == "__main__":
    main()
