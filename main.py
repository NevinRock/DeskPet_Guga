from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from pet.animation_manager import app_root
from pet.pet_window import PetWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Guga Desktop Pet")
    app.setApplicationDisplayName("Guga Desktop Pet")
    app.setWindowIcon(QIcon(str(app_root() / "assets" / "guga.ico")))
    app.setQuitOnLastWindowClosed(True)
    pet = PetWindow()
    pet.show_at_default_position()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
