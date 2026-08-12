from __future__ import annotations

from datetime import timedelta
import unittest

from pet.hunger import HungerLevel, hunger_level_for_elapsed


class HungerLevelTests(unittest.TestCase):
    def test_hunger_thresholds_are_exact(self) -> None:
        self.assertEqual(hunger_level_for_elapsed(timedelta(minutes=29, seconds=59)), HungerLevel.FULL)
        self.assertEqual(hunger_level_for_elapsed(timedelta(minutes=30)), HungerLevel.HUNGRY)
        self.assertEqual(hunger_level_for_elapsed(timedelta(hours=2, minutes=59, seconds=59)), HungerLevel.HUNGRY)
        self.assertEqual(hunger_level_for_elapsed(timedelta(hours=3)), HungerLevel.STARVING)
        self.assertEqual(hunger_level_for_elapsed(timedelta(hours=5, minutes=59, seconds=59)), HungerLevel.STARVING)
        self.assertEqual(hunger_level_for_elapsed(timedelta(hours=6)), HungerLevel.TOMBSTONE)


if __name__ == "__main__":
    unittest.main()
