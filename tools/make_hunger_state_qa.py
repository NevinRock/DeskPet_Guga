from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SKINS = {
    "Guga": ROOT / "assets" / "actions",
    "Phoebe": ROOT / "assets" / "skins" / "phoebe" / "actions",
    "Author": ROOT / "assets" / "skins" / "author" / "actions",
    "Guga Eunuch": ROOT / "assets" / "skins" / "guga-eunuch" / "actions",
}
ACTIONS = ("starving", "tombstone")
CELL = (192, 208)


def checkerboard(size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGBA", size, "#d8d8d8")
    draw = ImageDraw.Draw(canvas)
    step = 12
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2:
                draw.rectangle((x, y, x + step - 1, y + step - 1), fill="#f4f4f4")
    return canvas


def main() -> None:
    out = ROOT / "qa" / "hunger-states"
    out.mkdir(parents=True, exist_ok=True)
    width, height = 8 * CELL[0], len(SKINS) * len(ACTIONS) * (CELL[1] + 28)
    sheet = Image.new("RGBA", (width, height), "#ffffff")
    draw = ImageDraw.Draw(sheet)
    row = 0
    for skin_name, prefix in SKINS.items():
        for action in ACTIONS:
            y = row * (CELL[1] + 28)
            draw.text((4, y + 4), f"{skin_name} — {action}", fill="#222222")
            for index, path in enumerate(sorted((prefix / action).glob("*.png"))):
                frame = Image.open(path).convert("RGBA")
                tile = checkerboard(CELL)
                tile.alpha_composite(frame)
                sheet.alpha_composite(tile, (index * CELL[0], y + 28))
            row += 1
    sheet.convert("RGB").save(out / "hunger-states-contact-sheet.png")
    print(out / "hunger-states-contact-sheet.png")


if __name__ == "__main__":
    main()
