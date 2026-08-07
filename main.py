from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from pet.pet_window import PetWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Guga Desktop Pet")
    app.setQuitOnLastWindowClosed(True)
    pet = PetWindow()
    pet.show_at_default_position()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
