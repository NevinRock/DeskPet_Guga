from __future__ import annotations

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from pet.git_push import GitPushDialog
from pet.pet_window import AboutDialog, ActionMenu, PetWindow, SettingsDialog
from pet.schedule import ScheduleDialog


class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_language_menu_stays_english_and_ui_switches(self) -> None:
        with tempfile.TemporaryDirectory() as appdata:
            previous = os.environ.get("APPDATA")
            os.environ["APPDATA"] = appdata
            try:
                window = PetWindow()
                window._set_language("en")
                menu = window._build_system_menu()
                settings_menu = next(action.menu() for action in menu.actions() if action.text() == "Settings")
                self.assertIn("Language", [action.text() for action in settings_menu.actions()])
                action_menu = ActionMenu(lambda _name: None, "en")
                self.assertEqual(action_menu.findChildren(QPushButton)[0].text(), "👋  Wave")
                self.assertEqual(SettingsDialog(210, lambda _size: None, "en", window).windowTitle(), "Guga Settings")
                self.assertEqual(AboutDialog(1, "en", window).findChildren(QPushButton)[0].text(), "OK")
                self.assertEqual(GitPushDialog(window.settings, window, "en").windowTitle(), "Automatic Git Push")

                window._set_language("ja")
                japanese_menu = window._build_system_menu()
                japanese_settings = next(action.menu() for action in japanese_menu.actions() if action.text() == "設定")
                self.assertIn("Language", [action.text() for action in japanese_settings.actions()])
                self.assertEqual(ScheduleDialog(window.settings, window, "ja").windowTitle(), "スケジュール")
                self.assertEqual(window.settings.language, "ja")
                window.close()
            finally:
                if previous is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = previous


if __name__ == "__main__":
    unittest.main()
