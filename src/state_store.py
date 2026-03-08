from __future__ import annotations

import json
from pathlib import Path

from src.models import State


def load_state(path: Path) -> State:
    if not path.exists():
        return State()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return State.from_dict(payload)


def save_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
