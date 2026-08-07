from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from .i18n import tr


class GitPushRunner(QObject):
    finished = Signal(bool, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("GIT_TERMINAL_PROMPT", "0")
        self.process.setProcessEnvironment(environment)
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)
        self.running = False
        self.repo_path = ""
        self.remote_url = ""
        self.commit_message = ""
        self.branch = ""
        self.committed = False
        self.step = ""
        self.stdout = ""
        self.stderr = ""
        self.language = "zh_CN"

    def start(self, repo_path: str, remote_url: str, commit_message: str, language: str = "zh_CN") -> bool:
        self.language = language
        if self.running:
            return False
        repo = Path(repo_path).expanduser()
        if not repo.is_dir() or not (repo / ".git").exists():
            self.finished.emit(False, tr(language, "git_invalid_repo"))
            return False
        if not remote_url.strip():
            self.finished.emit(False, tr(language, "git_remote_required"))
            return False
        if self._has_embedded_credentials(remote_url):
            self.finished.emit(False, tr(language, "git_credentials"))
            return False
        if not commit_message.strip():
            self.finished.emit(False, tr(language, "git_commit_required"))
            return False

        self.running = True
        self.repo_path = str(repo.resolve())
        self.remote_url = remote_url.strip()
        self.commit_message = commit_message.strip()
        self.branch = ""
        self.committed = False
        self._run("add", ["add", "-A"])
        return True

    @staticmethod
    def _has_embedded_credentials(remote_url: str) -> bool:
        if "://" not in remote_url:
            return False
        parsed = urlsplit(remote_url)
        return parsed.username is not None or parsed.password is not None

    def _run(self, step: str, arguments: list[str]) -> None:
        self.step = step
        self.stdout = ""
        self.stderr = ""
        self.process.setWorkingDirectory(self.repo_path)
        self.process.start("git", arguments)

    def _read_stdout(self) -> None:
        self.stdout += bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")

    def _read_stderr(self) -> None:
        self.stderr += bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")

    def _process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if not self.running:
            return
        self._read_stdout()
        self._read_stderr()
        if exit_status is QProcess.ExitStatus.CrashExit:
            self._finish(False, tr(self.language, "git_crashed"))
            return

        if self.step == "add":
            if exit_code != 0:
                self._fail_from_output(tr(self.language, "git_add_failed"))
            else:
                self._run("diff", ["diff", "--cached", "--quiet"])
        elif self.step == "diff":
            if exit_code == 0:
                self._run("branch", ["branch", "--show-current"])
            elif exit_code == 1:
                self._run("commit", ["commit", "-m", self.commit_message])
            else:
                self._fail_from_output(tr(self.language, "git_check_failed"))
        elif self.step == "commit":
            if exit_code != 0:
                self._fail_from_output(tr(self.language, "git_commit_failed"))
            else:
                self.committed = True
                self._run("branch", ["branch", "--show-current"])
        elif self.step == "branch":
            self.branch = self.stdout.strip()
            if exit_code != 0 or not self.branch:
                self._fail_from_output(tr(self.language, "git_branch_failed"))
            else:
                self._run("push", ["push", self.remote_url, f"HEAD:{self.branch}"])
        elif self.step == "push":
            if exit_code != 0:
                self._fail_from_output(tr(self.language, "git_push_failed"))
            else:
                key = "git_pushed" if self.committed else "git_synced"
                self._finish(True, tr(self.language, key, branch=self.branch))

    def _process_error(self, error: QProcess.ProcessError) -> None:
        if self.running and error is QProcess.ProcessError.FailedToStart:
            self._finish(False, tr(self.language, "git_missing"))

    def _fail_from_output(self, prefix: str) -> None:
        detail = (self.stderr or self.stdout).strip().splitlines()
        self._finish(False, f"{prefix}：{detail[-1] if detail else tr(self.language, 'git_unknown')}")

    def _finish(self, success: bool, message: str) -> None:
        self.running = False
        self.finished.emit(success, message)


class GitPushDialog(QDialog):
    def __init__(self, settings, parent: QWidget, language: str = "zh_CN") -> None:
        super().__init__(parent)
        self.language = language
        self.setWindowTitle(tr(language, "git_dialog_title"))
        self.setMinimumWidth(520)
        self.run_immediately = False
        self.setStyleSheet(
            "QDialog { background: white; } QLabel { font-size: 13px; }"
            "QLineEdit, QTimeEdit { padding: 7px; border: 1px solid #d9ceda; border-radius: 7px; }"
            "QPushButton { padding: 7px 13px; border-radius: 8px; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        self.enabled = QCheckBox(tr(language, "git_enable"))
        self.enabled.setChecked(settings.git_auto_push_enabled)
        layout.addWidget(self.enabled)

        form = QFormLayout()
        self.repo_path = QLineEdit(settings.git_repo_path)
        browse = QPushButton(tr(language, "git_choose"))
        browse.clicked.connect(self._browse_repo)
        repo_row = QHBoxLayout()
        repo_row.addWidget(self.repo_path, 1)
        repo_row.addWidget(browse)
        form.addRow(tr(language, "git_repo"), repo_row)

        self.remote_url = QLineEdit(settings.git_remote_url)
        self.remote_url.setPlaceholderText(tr(language, "git_remote_hint"))
        form.addRow(tr(language, "git_remote"), self.remote_url)

        self.push_time = QTimeEdit()
        self.push_time.setDisplayFormat("HH:mm")
        parsed_time = QTime.fromString(settings.git_push_time, "HH:mm")
        self.push_time.setTime(parsed_time if parsed_time.isValid() else QTime(23, 0))
        form.addRow(tr(language, "git_time"), self.push_time)

        self.commit_message = QLineEdit(settings.git_commit_message)
        self.commit_message.setPlaceholderText(tr(language, "git_commit_hint"))
        form.addRow(tr(language, "git_commit"), self.commit_message)
        layout.addLayout(form)

        note = QLabel(tr(language, "git_security"))
        note.setWordWrap(True)
        note.setStyleSheet("color: #7a6d7c; padding: 6px 0;")
        layout.addWidget(note)

        status = settings.git_last_push_status or tr(language, "git_never")
        last_run = settings.git_last_push_at or "—"
        self.status_label = QLabel(tr(language, "git_last", status=status, time=last_run))
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("background: #f7f1f8; padding: 9px; border-radius: 8px; color: #584d59;")
        layout.addWidget(self.status_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr(language, "save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr(language, "cancel"))
        run_now = QPushButton(tr(language, "git_run_now"))
        buttons.addButton(run_now, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        run_now.clicked.connect(self._accept_and_run)
        layout.addWidget(buttons)

    def _browse_repo(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, tr(self.language, "git_select_repo"), self.repo_path.text())
        if selected:
            self.repo_path.setText(selected)

    def _accept_and_run(self) -> None:
        self.run_immediately = True
        self.accept()

    def accept(self) -> None:
        if self.enabled.isChecked() or self.run_immediately:
            repo = Path(self.repo_path.text().strip()).expanduser()
            if not repo.is_dir() or not (repo / ".git").exists():
                QMessageBox.warning(self, tr(self.language, "git_incomplete"), tr(self.language, "git_bad_repo"))
                return
            if not self.remote_url.text().strip():
                QMessageBox.warning(self, tr(self.language, "git_incomplete"), tr(self.language, "git_missing_remote"))
                return
            if GitPushRunner._has_embedded_credentials(self.remote_url.text().strip()):
                QMessageBox.warning(self, tr(self.language, "git_unsafe"), tr(self.language, "git_unsafe_detail"))
                return
            if not self.commit_message.text().strip():
                QMessageBox.warning(self, tr(self.language, "git_incomplete"), tr(self.language, "git_missing_commit"))
                return
        super().accept()
