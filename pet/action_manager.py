from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import QObject, Signal

from .animation_manager import AnimationManager


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
        self.animation.animation_finished.connect(self._finished)

    def start_idle(self) -> None:
        self.state = PetState.HUNGRY if self.hungry else PetState.IDLE
        self.state_changed.emit(self.state)
        self.animation.play("hungry" if self.hungry else "idle")

    def set_hungry(self, hungry: bool, play: bool = True) -> None:
        self.hungry = hungry
        if play and self.state is not PetState.DRAGGING:
            self.start_idle()

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
