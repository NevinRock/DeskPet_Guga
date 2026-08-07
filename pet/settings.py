from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PetSettings:
    x: int | None = None
    y: int | None = None
    size: int = 210
    language: str = "zh_CN"
    adopted_at: str | None = None
    last_fed_at: str | None = None
    git_auto_push_enabled: bool = False
    git_repo_path: str = ""
    git_remote_url: str = ""
    git_push_time: str = "23:00"
    git_commit_message: str = "chore: automatic backup"
    git_last_attempt_date: str | None = None
    git_last_push_at: str | None = None
    git_last_push_status: str = "尚未执行"
    calendar_server_url: str = "https://nevinrock.space"
    calendar_person_id: str = ""


class SettingsStore:
    def __init__(self) -> None:
        root = Path(os.getenv("APPDATA", Path.home())) / "GugaDesktopPet"
        self.path = root / "settings.json"

    def load(self) -> PetSettings:
        try:
            return PetSettings(**json.loads(self.path.read_text(encoding="utf-8")))
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return PetSettings()

    def save(self, settings: PetSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
