from __future__ import annotations

from math import ceil
from statistics import median
from typing import Any

from .discovery import parse_youtube_datetime


class SelectionResult(dict):
    pass


def _channel_median_views(candidates: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[int]] = {}
    for c in candidates:
        cid = c.get("channel_id")
        if not cid:
            continue
        grouped.setdefault(cid, []).append(int(c.get("view_count") or 0))

    medians: dict[str, float] = {}
    for cid, views in grouped.items():
        if not views:
            medians[cid] = 0
            continue
        medians[cid] = float(median(views[:10]))
    return medians


def apply_relative_view_filter(
    candidates: list[dict[str, Any]],
    threshold: float,
) -> list[dict[str, Any]]:
    medians = _channel_median_views(candidates)
    output: list[dict[str, Any]] = []
    for c in candidates:
        cid = c.get("channel_id")
        if not cid:
            output.append(c)
            continue

        baseline = medians.get(cid, 0)
        views = int(c.get("view_count") or 0)
        min_required = baseline * threshold
        if baseline == 0 or views >= min_required:
            output.append(c)
    return output


def apply_quality_filters(
    candidates: list[dict[str, Any]],
    min_duration_seconds: int,
    min_view_count: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for c in candidates:
        duration_seconds = int(c.get("duration_seconds") or 0)
        view_count = int(c.get("view_count") or 0)
        if duration_seconds < min_duration_seconds:
            continue
        if view_count < min_view_count:
            continue
        output.append(c)
    return output


def _sort_desc(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda c: (
            parse_youtube_datetime(c.get("published_at")),
            int(c.get("view_count") or 0),
        ),
        reverse=True,
    )


def select_candidates(
    fresh_pool: list[dict[str, Any]],
    archive_pool: list[dict[str, Any]],
    max_add: int,
    mix_fresh_ratio: float,
) -> SelectionResult:
    fresh_sorted = _sort_desc(fresh_pool)
    archive_sorted = _sort_desc(archive_pool)

    fresh_target = ceil(max_add * mix_fresh_ratio)
    archive_target = max_add - fresh_target

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for item in fresh_sorted:
        vid = item.get("video_id")
        if not vid or vid in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(vid)
        if len(selected) >= fresh_target:
            break

    for item in archive_sorted:
        vid = item.get("video_id")
        if not vid or vid in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(vid)
        if len(selected) >= fresh_target + archive_target:
            break

    if len(selected) < max_add:
        for pool in (fresh_sorted, archive_sorted):
            for item in pool:
                vid = item.get("video_id")
                if not vid or vid in selected_ids:
                    continue
                selected.append(item)
                selected_ids.add(vid)
                if len(selected) >= max_add:
                    break
            if len(selected) >= max_add:
                break

    return SelectionResult(
        {
            "selected": selected[:max_add],
            "fresh_target": fresh_target,
            "archive_target": archive_target,
        }
    )
