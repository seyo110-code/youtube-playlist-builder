from __future__ import annotations

from typing import Any

import typer

from .config import ConfigError, load_config
from .discovery import merge_dedupe
from .playlist_sync import add_video_to_playlist, fetch_existing_video_ids
from .ranking import apply_quality_filters, apply_relative_view_filter, select_candidates
from .report import now_iso, write_report
from .youtube_client import (
    authenticate,
    build_client,
    fetch_channel_recent_videos,
    fetch_keyword_videos,
    hydrate_video_stats,
)

app = typer.Typer(help="YouTube playlist builder")


def _topic_threshold(topic: Any, defaults: Any) -> float:
    return topic.relative_view_threshold or defaults.relative_view_threshold


def _topic_max_add(topic: Any, defaults: Any) -> int:
    return topic.max_add_per_topic or defaults.max_add_per_topic


def _topic_min_duration(topic: Any, defaults: Any) -> int:
    if topic.min_duration_seconds is None:
        return defaults.min_duration_seconds
    return topic.min_duration_seconds


def _topic_min_view_count(topic: Any, defaults: Any) -> int:
    if topic.min_view_count is None:
        return defaults.min_view_count
    return topic.min_view_count


@app.command("auth")
def auth(client_secret_file: str, token_file: str) -> None:
    authenticate(client_secret_file=client_secret_file, token_file=token_file)
    typer.echo(f"Authentication complete. Token saved to {token_file}")


@app.command("validate-config")
def validate_config(config: str = typer.Option(..., "--config")) -> None:
    cfg = load_config(config)
    typer.echo(f"Config valid: {len(cfg.topics)} topic(s)")


@app.command("run")
def run(
    config: str = typer.Option(..., "--config"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    report_file: str | None = typer.Option("run-report.json", "--report-file"),
) -> None:
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        typer.echo(f"Config error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    creds = authenticate(
        client_secret_file=str(cfg.oauth.client_secret_file),
        token_file=str(cfg.oauth.token_file),
    )
    youtube = build_client(creds)

    run_report: dict[str, Any] = {"run_at": now_iso(), "topics": []}

    for topic in cfg.topics:
        max_add = _topic_max_add(topic, cfg.defaults)
        threshold = _topic_threshold(topic, cfg.defaults)
        min_duration = _topic_min_duration(topic, cfg.defaults)
        min_view_count = _topic_min_view_count(topic, cfg.defaults)

        fresh_candidates: list[dict[str, Any]] = []
        archive_candidates: list[dict[str, Any]] = []

        for channel_id in topic.channels:
            fresh_candidates.extend(
                fetch_channel_recent_videos(youtube, channel_id, topic.search_days_fresh)
            )
            archive_candidates.extend(
                fetch_channel_recent_videos(youtube, channel_id, topic.search_days_archive)
            )

        for keyword in topic.keywords:
            fresh_candidates.extend(fetch_keyword_videos(youtube, keyword, topic.search_days_fresh))
            archive_candidates.extend(fetch_keyword_videos(youtube, keyword, topic.search_days_archive))

        fresh_candidates = hydrate_video_stats(youtube, merge_dedupe(fresh_candidates))
        archive_candidates = hydrate_video_stats(youtube, merge_dedupe(archive_candidates))

        fresh_filtered = apply_relative_view_filter(fresh_candidates, threshold)
        archive_filtered = apply_relative_view_filter(archive_candidates, threshold)
        fresh_filtered = apply_quality_filters(fresh_filtered, min_duration, min_view_count)
        archive_filtered = apply_quality_filters(archive_filtered, min_duration, min_view_count)

        selection = select_candidates(
            fresh_pool=fresh_filtered,
            archive_pool=archive_filtered,
            max_add=max_add,
            mix_fresh_ratio=topic.mix_fresh_ratio,
        )

        selected = selection["selected"]
        existing_ids = fetch_existing_video_ids(youtube, topic.playlist_id)

        added = 0
        skipped_duplicates = 0
        failures: list[str] = []

        for item in selected:
            video_id = item.get("video_id")
            if not video_id:
                continue
            if video_id in existing_ids:
                skipped_duplicates += 1
                continue

            if dry_run:
                typer.echo(f"[DRY-RUN] would add {video_id} to {topic.name}")
                added += 1
                continue

            try:
                add_video_to_playlist(youtube, topic.playlist_id, video_id)
                existing_ids.add(video_id)
                added += 1
            except Exception as exc:  # pragma: no cover - API surface failures
                failures.append(f"{video_id}: {exc}")

        topic_report = {
            "name": topic.name,
            "playlist_id": topic.playlist_id,
            "fresh_candidates": len(fresh_candidates),
            "archive_candidates": len(archive_candidates),
            "selected": len(selected),
            "added": added,
            "skipped_duplicates": skipped_duplicates,
            "min_duration_seconds": min_duration,
            "min_view_count": min_view_count,
            "failures": failures,
        }
        run_report["topics"].append(topic_report)

        typer.echo(
            f"[{topic.name}] selected={len(selected)} added={added} "
            f"skipped_duplicates={skipped_duplicates} failures={len(failures)}"
        )

    write_report(run_report, report_file)
    typer.echo("Run complete")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
