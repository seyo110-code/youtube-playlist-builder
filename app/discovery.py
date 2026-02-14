from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def days_ago_iso(days: int) -> str:
    return (utc_now() - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def parse_youtube_datetime(value: str | None) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_iso8601_duration_seconds(duration: str | None) -> int:
    if not duration or not duration.startswith("P"):
        return 0

    # Examples: PT4M13S, PT59S, PT1H2M
    match = re.fullmatch(
        r"P(?:\d+Y)?(?:\d+M)?(?:\d+D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?",
        duration,
    )
    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def extract_video(item: dict[str, Any], source: str) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    raw_id = item.get("id")

    if isinstance(raw_id, dict):
        video_id = raw_id.get("videoId") or raw_id.get("playlistId")
    else:
        video_id = raw_id

    return {
        "video_id": video_id,
        "title": snippet.get("title", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt"),
        "view_count": int(stats.get("viewCount", 0) or 0),
        "source": source,
    }


def merge_dedupe(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in candidates:
        vid = item.get("video_id")
        if not vid:
            continue
        prev = merged.get(vid)
        if not prev:
            merged[vid] = item
            continue

        # Keep the richer item (with higher view count or newer publish date).
        prev_views = int(prev.get("view_count") or 0)
        cur_views = int(item.get("view_count") or 0)
        prev_dt = parse_youtube_datetime(prev.get("published_at"))
        cur_dt = parse_youtube_datetime(item.get("published_at"))
        if cur_views > prev_views or cur_dt > prev_dt:
            merged[vid] = item

    return list(merged.values())
