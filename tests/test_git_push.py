from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from pet.git_push import GitPushRunner


class GitPushRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_rejects_embedded_credentials(self) -> None:
        self.assertTrue(GitPushRunner._has_embedded_credentials("https://user:token@example.com/repo.git"))
        self.assertFalse(GitPushRunner._has_embedded_credentials("git@example.com:owner/repo.git"))
        self.assertFalse(GitPushRunner._has_embedded_credentials("origin"))

    def test_commits_and_pushes_to_local_bare_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            remote = root / "remote.git"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Guga Test"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "guga@example.invalid"], check=True)
            (repo / "note.txt").write_text("hello from Guga\n", encoding="utf-8")

            runner = GitPushRunner()
            result: list[tuple[bool, str]] = []
            loop = QEventLoop()
            runner.finished.connect(lambda ok, message: (result.append((ok, message)), loop.quit()))
            self.assertTrue(runner.start(str(repo), str(remote), "test: automatic push"))
            QTimer.singleShot(15000, loop.quit)
            loop.exec()

            self.assertTrue(result, "GitPushRunner timed out")
            self.assertTrue(result[0][0], result[0][1])
            branch = subprocess.run(
                ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertTrue(branch)


if __name__ == "__main__":
    unittest.main()
