from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from pet.care import format_care_duration
from pet.pet_window import PetWindow


class CareDurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_duration_uses_minutes_then_two_largest_units(self) -> None:
        self.assertEqual(format_care_duration("zh_CN", timedelta()), "0分钟")
        self.assertEqual(format_care_duration("zh_CN", timedelta(minutes=59)), "59分钟")
        self.assertEqual(format_care_duration("zh_CN", timedelta(hours=1)), "1小时0分钟")
        self.assertEqual(
            format_care_duration("zh_CN", timedelta(hours=23, minutes=59)),
            "23小时59分钟",
        )
        self.assertEqual(format_care_duration("zh_CN", timedelta(days=1)), "1天0小时")
        self.assertEqual(
            format_care_duration("zh_CN", timedelta(days=12, hours=7, minutes=55)),
            "12天7小时",
        )
        self.assertEqual(format_care_duration("en", timedelta(hours=2, minutes=3)), "2 hr 3 min")
        self.assertEqual(format_care_duration("ja", timedelta(days=2, hours=4)), "2日4時間")

    def test_legacy_time_is_kept_for_guga_and_new_skins_start_separately(self) -> None:
        with tempfile.TemporaryDirectory() as appdata:
            previous = os.environ.get("APPDATA")
            os.environ["APPDATA"] = appdata
            try:
                legacy = datetime.now(timezone.utc) - timedelta(days=3, hours=2)
                settings_dir = Path(appdata) / "GugaDesktopPet"
                settings_dir.mkdir(parents=True)
                (settings_dir / "settings.json").write_text(
                    json.dumps({"skin": "phoebe", "adopted_at": legacy.isoformat()}),
                    encoding="utf-8",
                )

                window = PetWindow()
                self.assertEqual(
                    window._parse_timestamp(window.settings.adopted_at_by_skin["guga"]),
                    legacy,
                )
                self.assertIn("phoebe", window.settings.adopted_at_by_skin)
                self.assertNotIn("author", window.settings.adopted_at_by_skin)

                window._set_skin("author")
                self.assertIn("author", window.settings.adopted_at_by_skin)
                author_started = window.settings.adopted_at_by_skin["author"]
                window._set_skin("guga")
                window._set_skin("author")
                self.assertEqual(window.settings.adopted_at_by_skin["author"], author_started)
                window.close()
            finally:
                if previous is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = previous


if __name__ == "__main__":
    unittest.main()
