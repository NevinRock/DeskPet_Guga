from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import QObject, Signal

from .animation_manager import AnimationManager
from .hunger import HungerLevel


class PetState(Enum):
    IDLE = auto()
    HUNGRY = auto()
    TOUCHED = auto()
    ACTION = auto()
    DRAGGING = auto()


class ActionManager(QObject):
    state_changed = Signal(PetState)

    def __init__(self, animation: AnimationManager) -> None:
        super().__init__()
        self.animation = animation
        self.state = PetState.IDLE
        self.hungry = False
        self.hunger_level = HungerLevel.FULL
        self.animation.animation_finished.connect(self._finished)

    def start_idle(self) -> None:
        self.state = PetState.HUNGRY if self.hungry else PetState.IDLE
        self.state_changed.emit(self.state)
        animation = "idle" if self.hunger_level is HungerLevel.FULL else self.hunger_level.value
        self.animation.play(animation)

    def set_hunger_level(self, level: HungerLevel, play: bool = True) -> None:
        self.hunger_level = level
        self.hungry = level is not HungerLevel.FULL
        if play and self.state is not PetState.DRAGGING:
            self.start_idle()

    def set_hungry(self, hungry: bool, play: bool = True) -> None:
        # Compatibility for callers that only distinguish full and hungry.
        self.set_hunger_level(HungerLevel.HUNGRY if hungry else HungerLevel.FULL, play)

    def touch(self) -> None:
        if self.state is PetState.IDLE:
            self.state = PetState.TOUCHED
            self.state_changed.emit(self.state)
            self.animation.play("wave")

    def action(self, name: str) -> None:
        self.state = PetState.ACTION
        self.state_changed.emit(self.state)
        self.animation.play(name)

    def dragging(self, active: bool) -> None:
        self.state = PetState.DRAGGING if active else PetState.IDLE
        self.state_changed.emit(self.state)
        if not active:
            self.start_idle()

    def _finished(self, _: str) -> None:
        if self.state in {PetState.TOUCHED, PetState.ACTION}:
            self.start_idle()
