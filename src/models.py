from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class EventItem:
    event_id: str
    month_section: str
    title: str
    url: str
    canonical_url: str
    categories: list[str]
    organizer: str | None
    schedule_label: str | None
    schedule_text: str | None


@dataclass(slots=True)
class EventMeta:
    final_url: str
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None


@dataclass(slots=True)
class AiSummary:
    headline: str
    summary: str
    who_is_it_for: str
    key_points: list[str]
    cta: str
    used_fallback: bool = False


@dataclass(slots=True)
class StoredEvent:
    event_id: str
    canonical_url: str
    source_title: str
    posted_at: str | None
    thread_id: str | None
    message_id: str | None
    tag: str | None
    posted: bool = True

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StoredEvent":
        return cls(
            event_id=payload["event_id"],
            canonical_url=payload["canonical_url"],
            source_title=payload.get("source_title", ""),
            posted_at=payload.get("posted_at"),
            thread_id=payload.get("thread_id"),
            message_id=payload.get("message_id"),
            tag=payload.get("tag"),
            posted=payload.get("posted", True),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class State:
    version: int = 1
    bootstrap_completed: bool = False
    seeded_month: str | None = None
    events: dict[str, StoredEvent] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "State":
        bootstrap = payload.get("bootstrap", {})
        raw_events = payload.get("events", {})
        return cls(
            version=payload.get("version", 1),
            bootstrap_completed=bootstrap.get("completed", False),
            seeded_month=bootstrap.get("seeded_month"),
            events={key: StoredEvent.from_dict(value) for key, value in raw_events.items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "bootstrap": {
                "completed": self.bootstrap_completed,
                "seeded_month": self.seeded_month,
            },
            "events": {key: value.to_dict() for key, value in self.events.items()},
        }
