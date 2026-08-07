from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PetSettings:
    x: int | None = None
    y: int | None = None
    size: int = 210


class SettingsStore:
    def __init__(self) -> None:
        root = Path(os.getenv("APPDATA", Path.home())) / "GugaDesktopPet"
        self.path = root / "settings.json"

    def load(self) -> PetSettings:
        try:
            return PetSettings(**json.loads(self.path.read_text(encoding="utf-8")))
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return PetSettings()

    def save(self, settings: PetSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
