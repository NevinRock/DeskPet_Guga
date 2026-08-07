from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from pet.schedule import ScheduleDialog
from pet.settings import PetSettings


class _CalendarHandler(BaseHTTPRequestHandler):
    payload = None

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        type(self).payload = json.loads(self.rfile.read(length))
        body = "人物 ID `guga-test` 暂无日程。".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        pass


class ScheduleDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_calendar_request_and_response(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _CalendarHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            settings = PetSettings(
                calendar_server_url=f"http://127.0.0.1:{server.server_port}",
                calendar_person_id="guga-test",
            )
            dialog = ScheduleDialog(settings, None)
            dialog._send("查看日程")
            loop = QEventLoop()

            def finish_when_ready() -> None:
                if dialog.reply is None:
                    loop.quit()
                else:
                    QTimer.singleShot(20, finish_when_ready)

            QTimer.singleShot(20, finish_when_ready)
            QTimer.singleShot(5000, loop.quit)
            loop.exec()

            self.assertIsNone(dialog.reply)
            self.assertEqual(_CalendarHandler.payload["mode"], "calendar")
            self.assertEqual(_CalendarHandler.payload["calendarPersonId"], "guga-test")
            self.assertIn("暂无日程", dialog.output.toPlainText())
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
