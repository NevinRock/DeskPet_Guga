from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QPixmap


def app_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


@dataclass(frozen=True)
class Animation:
    name: str
    frames: list[QPixmap]
    fps: int
    loop: bool


class AnimationManager(QObject):
    frame_changed = Signal(QPixmap)
    animation_finished = Signal(str)

    def __init__(self, skin: str = "guga") -> None:
        super().__init__()
        self.root = app_root()
        self.skins = json.loads((self.root / "config" / "skins.json").read_text(encoding="utf-8"))
        self.skin = skin if skin in self.skins else "guga"
        self.animations = self._load_animations()
        self.current: Animation | None = None
        self.index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance)

    def _load_animations(self) -> dict[str, Animation]:
        config = json.loads((self.root / "config" / "actions.json").read_text(encoding="utf-8"))
        asset_prefix = Path(self.skins[self.skin]["assetPrefix"])
        guga_prefix = Path("assets/actions")
        animations: dict[str, Animation] = {}
        for name, spec in config.items():
            frame_paths = [asset_prefix / Path(relative).relative_to(guga_prefix) for relative in spec["frames"]]
            frames = [QPixmap(str(self.root / relative)) for relative in frame_paths]
            if not frames or any(frame.isNull() for frame in frames):
                raise RuntimeError(f"Missing frame for action {name} in skin {self.skin}")
            animations[name] = Animation(name, frames, spec.get("fps", 8), spec.get("loop", False))
        return animations

    def set_skin(self, skin: str) -> None:
        if skin not in self.skins:
            raise ValueError(f"Unknown skin: {skin}")
        if skin == self.skin:
            return
        self.timer.stop()
        self.skin = skin
        self.animations = self._load_animations()
        self.current = None
        self.index = 0

    def play(self, name: str) -> None:
        self.current = self.animations[name]
        self.index = 0
        self.timer.start(max(1, round(1000 / self.current.fps)))
        self.frame_changed.emit(self.current.frames[0])

    def _advance(self) -> None:
        if self.current is None:
            return
        self.index += 1
        if self.index < len(self.current.frames):
            self.frame_changed.emit(self.current.frames[self.index])
            return
        if self.current.loop:
            self.index = 0
            self.frame_changed.emit(self.current.frames[0])
            return
        name = self.current.name
        self.timer.stop()
        self.animation_finished.emit(name)
