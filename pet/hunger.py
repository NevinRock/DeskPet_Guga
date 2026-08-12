from __future__ import annotations

from datetime import timedelta
from enum import Enum


class HungerLevel(str, Enum):
    FULL = "full"
    HUNGRY = "hungry"
    STARVING = "starving"
    TOMBSTONE = "tombstone"


HUNGRY_AFTER = timedelta(minutes=30)
STARVING_AFTER = timedelta(hours=3)
TOMBSTONE_AFTER = timedelta(hours=6)


def hunger_level_for_elapsed(elapsed: timedelta) -> HungerLevel:
    """Return the visible hunger state for the time since the last meal."""
    if elapsed >= TOMBSTONE_AFTER:
        return HungerLevel.TOMBSTONE
    if elapsed >= STARVING_AFTER:
        return HungerLevel.STARVING
    if elapsed >= HUNGRY_AFTER:
        return HungerLevel.HUNGRY
    return HungerLevel.FULL
