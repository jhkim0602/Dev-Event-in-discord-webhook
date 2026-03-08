from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_README_URL = "https://raw.githubusercontent.com/brave-people/Dev-Event/master/README.md"
DEFAULT_SOURCE_README_PAGE_URL = "https://github.com/brave-people/Dev-Event/blob/master/README.md"


@dataclass(slots=True)
class Config:
    readme_url: str
    source_readme_page_url: str
    discord_webhook_url: str | None
    discord_tag_id_open: str | None
    discord_tag_id_closed: str | None
    gemini_api_key: str | None
    gemini_model: str
    state_file: Path
    request_timeout_seconds: int
    timezone_name: str
    user_agent: str
    dry_run: bool

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name)

    def validate(self) -> None:
        if self.dry_run:
            return
        missing: list[str] = []
        if not self.discord_webhook_url:
            missing.append("DISCORD_WEBHOOK_URL")
        if not self.discord_tag_id_open:
            missing.append("DISCORD_TAG_ID_OPEN")
        if not self.discord_tag_id_closed:
            missing.append("DISCORD_TAG_ID_CLOSED")
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {joined}")


def load_config(*, dry_run: bool = False) -> Config:
    state_dir = Path(os.getenv("STATE_DIR", ".state"))
    state_dir.mkdir(parents=True, exist_ok=True)
    config = Config(
        readme_url=os.getenv("README_URL", DEFAULT_README_URL),
        source_readme_page_url=os.getenv("SOURCE_README_PAGE_URL", DEFAULT_SOURCE_README_PAGE_URL),
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
        discord_tag_id_open=os.getenv("DISCORD_TAG_ID_OPEN"),
        discord_tag_id_closed=os.getenv("DISCORD_TAG_ID_CLOSED"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        state_file=state_dir / "state.json",
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
        timezone_name=os.getenv("TIMEZONE_NAME", "Asia/Seoul"),
        user_agent=os.getenv(
            "USER_AGENT",
            "dev-event-discord-sync/1.0 (+https://github.com/brave-people/Dev-Event)",
        ),
        dry_run=dry_run,
    )
    config.validate()
    return config
