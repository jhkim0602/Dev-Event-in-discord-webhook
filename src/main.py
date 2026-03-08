from __future__ import annotations

import argparse
from datetime import datetime
import logging
import sys

from src.config import load_config
from src.discord_webhook import build_discord_payload, post_forum_thread
from src.event_meta_fetcher import fetch_event_meta
from src.gemini_client import generate_summary
from src.identity import dedupe_events
from src.models import EventItem, EventMeta, State, StoredEvent
from src.readme_fetcher import fetch_readme
from src.readme_parser import parse_events
from src.state_store import load_state, save_state
from src.tag_policy import resolve_tags


logger = logging.getLogger(__name__)


def current_month_label(now: datetime) -> str:
    year_short = now.year % 100
    return f"{year_short:02d}년 {now.month:02d}월"


def seed_unposted_events(state: State, events: list[EventItem]) -> None:
    for event in events:
        if event.event_id in state.events:
            continue
        state.events[event.event_id] = StoredEvent(
            event_id=event.event_id,
            canonical_url=event.canonical_url,
            source_title=event.title,
            posted_at=None,
            thread_id=None,
            message_id=None,
            tags=[],
            posted=False,
        )


def select_events_to_post(events: list[EventItem], state: State, now: datetime) -> tuple[list[EventItem], list[EventItem]]:
    if not state.bootstrap_completed:
        current_month = current_month_label(now)
        bootstrap_candidates = [event for event in events if event.month_section == current_month]
        baseline_only = [event for event in events if event.month_section != current_month]
        return bootstrap_candidates, baseline_only
    return [event for event in events if event.event_id not in state.events], []


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Dev-Event README entries into a Discord forum.")
    parser.add_argument("--dry-run", action="store_true", help="Run without posting to Discord or saving state.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    configure_logging()
    config = load_config(dry_run=args.dry_run)
    now = datetime.now(config.timezone)

    readme = fetch_readme(
        config.readme_url,
        timeout_seconds=config.request_timeout_seconds,
        user_agent=config.user_agent,
    )
    events = dedupe_events(parse_events(readme))
    state = load_state(config.state_file)

    to_post, baseline_only = select_events_to_post(events, state, now)
    if not state.bootstrap_completed:
        seed_unposted_events(state, baseline_only)
        state.bootstrap_completed = True
        state.seeded_month = current_month_label(now)
        logger.info("Bootstrap mode enabled for %s; %d events will be seeded without posting", state.seeded_month, len(baseline_only))

    if not to_post:
        logger.info("No new events to post")
        if not args.dry_run:
            save_state(config.state_file, state)
        return 0

    failures = 0
    for event in to_post:
        logger.info("Processing event: %s", event.title)
        try:
            meta = fetch_event_meta(
                event.url,
                timeout_seconds=config.request_timeout_seconds,
                user_agent=config.user_agent,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch event metadata for %s: %s", event.title, exc)
            meta = EventMeta(final_url=event.url)

        summary = generate_summary(
            event,
            meta,
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            timeout_seconds=config.request_timeout_seconds,
        )
        selected_tags = resolve_tags(
            event,
            meta,
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            timeout_seconds=config.request_timeout_seconds,
        )
        tag_ids = [config.discord_tag_map[tag] for tag in selected_tags if tag in config.discord_tag_map]
        if selected_tags and not tag_ids:
            logger.warning("No configured Discord tag IDs matched selected tags for %s: %s", event.title, ", ".join(selected_tags))
        payload = build_discord_payload(
            event,
            summary,
            meta,
            source_readme_page_url=config.source_readme_page_url,
            tag_ids=tag_ids,
            selected_tags=selected_tags,
        )

        if args.dry_run:
            logger.info("Dry run: would post %s with tags %s", event.title, ", ".join(selected_tags) if selected_tags else "-")
            continue

        try:
            response = post_forum_thread(
                config.discord_webhook_url or "",
                payload,
                timeout_seconds=config.request_timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            failures += 1
            logger.error("Failed to post event %s: %s", event.title, exc)
            continue

        state.events[event.event_id] = StoredEvent(
            event_id=event.event_id,
            canonical_url=event.canonical_url,
            source_title=event.title,
            posted_at=now.isoformat(),
            thread_id=response.get("channel_id"),
            message_id=response.get("id"),
            tags=selected_tags,
            posted=True,
        )

    if args.dry_run:
        logger.info("Dry run completed; state file was not modified")
        return 0

    save_state(config.state_file, state)
    if failures:
        logger.error("Completed with %d posting failures", failures)
        return 1
    logger.info("Completed successfully; state saved to %s", config.state_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
