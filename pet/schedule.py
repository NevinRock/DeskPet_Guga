from __future__ import annotations

import html
import json
from datetime import datetime

from PySide6.QtCore import QByteArray, QTimeZone, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .i18n import tr


class ScheduleDialog(QDialog):
    def __init__(self, settings, parent: QWidget, language: str = "zh_CN") -> None:
        super().__init__(parent)
        self.language = language
        self.setWindowTitle(tr(language, "schedule_title"))
        self.resize(620, 590)
        self.network = QNetworkAccessManager(self)
        self.reply: QNetworkReply | None = None
        self.setStyleSheet(
            "QDialog { background: white; } QLabel { font-size: 13px; }"
            "QLineEdit, QPlainTextEdit, QTextBrowser { border: 1px solid #d9ceda; border-radius: 8px; padding: 7px; }"
            "QPushButton { padding: 7px 13px; border-radius: 8px; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        form = QFormLayout()
        self.server_url = QLineEdit(settings.calendar_server_url)
        self.server_url.setPlaceholderText("https://nevinrock.space")
        self.person_id = QLineEdit(settings.calendar_person_id)
        self.person_id.setPlaceholderText(tr(language, "schedule_person_hint"))
        form.addRow(tr(language, "schedule_server"), self.server_url)
        form.addRow(tr(language, "schedule_person"), self.person_id)
        layout.addLayout(form)

        security_note = QLabel(tr(language, "schedule_security"))
        security_note.setWordWrap(True)
        security_note.setStyleSheet("color: #a1495d; background: #fff3f5; padding: 8px; border-radius: 8px;")
        layout.addWidget(security_note)

        toolbar = QHBoxLayout()
        self.refresh_button = QPushButton(tr(language, "schedule_refresh"))
        self.subscription_button = QPushButton(tr(language, "schedule_subscription"))
        self.refresh_button.clicked.connect(lambda: self._send(tr(self.language, "schedule_list_command")))
        self.subscription_button.clicked.connect(self._select_calendar)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.subscription_button)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.output = QTextBrowser()
        self.output.setPlaceholderText(tr(language, "schedule_output_hint"))
        layout.addWidget(self.output, 1)

        hint = QLabel(tr(language, "schedule_help"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #706472;")
        layout.addWidget(hint)

        self.command = QPlainTextEdit()
        self.command.setPlaceholderText(tr(language, "schedule_command_hint"))
        self.command.setMaximumHeight(86)
        layout.addWidget(self.command)

        send_row = QHBoxLayout()
        self.status_label = QLabel(tr(language, "schedule_ready"))
        self.status_label.setStyleSheet("color: #756a77;")
        self.send_button = QPushButton(tr(language, "schedule_send"))
        self.send_button.clicked.connect(self._send_command)
        send_row.addWidget(self.status_label, 1)
        send_row.addWidget(self.send_button)
        layout.addLayout(send_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr(language, "save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr(language, "cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def build_payload(message: str, person_id: str | None) -> dict:
        now = datetime.now().astimezone()
        zone_bytes = bytes(QTimeZone.systemTimeZoneId())
        time_zone = zone_bytes.decode("utf-8", errors="replace") or "Asia/Shanghai"
        return {
            "message": message,
            "mode": "calendar",
            "currentTime": {
                "iso": now.isoformat(),
                "solar": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timeZone": time_zone,
            },
            "calendarPersonId": person_id,
        }

    def _validated_connection(self) -> tuple[str, str] | None:
        server = self.server_url.text().strip().rstrip("/")
        person_id = self.person_id.text().strip()
        url = QUrl(server)
        if not url.isValid() or url.scheme() not in {"http", "https"} or not url.host():
            QMessageBox.warning(self, tr(self.language, "schedule_bad_server_title"), tr(self.language, "schedule_bad_server"))
            return None
        if url.userInfo():
            QMessageBox.warning(self, tr(self.language, "schedule_unsafe_server"), tr(self.language, "schedule_unsafe_server_detail"))
            return None
        if not person_id:
            QMessageBox.warning(self, tr(self.language, "schedule_missing_id_title"), tr(self.language, "schedule_missing_id"))
            return None
        return server, person_id

    def _select_calendar(self) -> None:
        connection = self._validated_connection()
        if connection:
            _, person_id = connection
            self._send(person_id, select_person=True)

    def _send_command(self) -> None:
        message = self.command.toPlainText().strip()
        if not message:
            QMessageBox.information(self, tr(self.language, "schedule_empty_title"), tr(self.language, "schedule_empty"))
            return
        self._send(message)

    def _send(self, message: str, select_person: bool = False) -> None:
        if self.reply is not None:
            QMessageBox.information(self, tr(self.language, "schedule_wait_title"), tr(self.language, "schedule_wait"))
            return
        connection = self._validated_connection()
        if not connection:
            return
        server, person_id = connection
        endpoint = QUrl(f"{server}/api/chat/stream")
        payload = self.build_payload(message, None if select_person else person_id)
        request = QNetworkRequest(endpoint)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        self._append_message(tr(self.language, "schedule_you"), message)
        self.status_label.setText(tr(self.language, "schedule_connecting"))
        self._set_request_buttons(False)
        self.reply = self.network.post(
            request,
            QByteArray(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
        )
        self.reply.finished.connect(self._request_finished)

    def _request_finished(self) -> None:
        reply = self.reply
        self.reply = None
        self._set_request_buttons(True)
        if reply is None:
            return
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        body = bytes(reply.readAll()).decode("utf-8", errors="replace").strip()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            detail = body or reply.errorString()
            self.status_label.setText(tr(self.language, "schedule_failed", status=status or "—"))
            self._append_message(tr(self.language, "schedule_error"), detail)
        else:
            self.status_label.setText(tr(self.language, "schedule_updated"))
            self._append_message(tr(self.language, "schedule_agent"), body or tr(self.language, "schedule_empty_response"))
            self.command.clear()
        reply.deleteLater()

    def _append_message(self, role: str, message: str) -> None:
        safe_role = html.escape(role)
        safe_message = html.escape(message).replace("\n", "<br>")
        self.output.append(f"<b>{safe_role}</b><br>{safe_message}<br>")

    def _set_request_buttons(self, enabled: bool) -> None:
        self.refresh_button.setEnabled(enabled)
        self.subscription_button.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

    def accept(self) -> None:
        if not self._validated_connection():
            return
        super().accept()

    def reject(self) -> None:
        if self.reply is not None:
            self.reply.abort()
        super().reject()
