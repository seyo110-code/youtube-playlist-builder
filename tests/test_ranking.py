from app.ranking import apply_quality_filters, apply_relative_view_filter, select_candidates


def test_relative_view_filter_keeps_above_threshold() -> None:
    candidates = [
        {"video_id": "a", "channel_id": "c1", "view_count": 100, "published_at": "2026-01-01T00:00:00Z"},
        {"video_id": "b", "channel_id": "c1", "view_count": 20, "published_at": "2026-01-02T00:00:00Z"},
        {"video_id": "c", "channel_id": "c1", "view_count": 90, "published_at": "2026-01-03T00:00:00Z"},
    ]

    out = apply_relative_view_filter(candidates, threshold=0.6)
    ids = {o["video_id"] for o in out}
    assert "a" in ids
    assert "c" in ids
    assert "b" not in ids


def test_select_candidates_respects_mix_and_dedupe() -> None:
    fresh = [
        {"video_id": "f1", "view_count": 10, "published_at": "2026-01-03T00:00:00Z"},
        {"video_id": "f2", "view_count": 9, "published_at": "2026-01-02T00:00:00Z"},
    ]
    archive = [
        {"video_id": "a1", "view_count": 30, "published_at": "2020-01-01T00:00:00Z"},
        {"video_id": "f2", "view_count": 9, "published_at": "2026-01-02T00:00:00Z"},
        {"video_id": "a2", "view_count": 25, "published_at": "2018-01-01T00:00:00Z"},
    ]

    result = select_candidates(fresh, archive, max_add=5, mix_fresh_ratio=0.6)
    selected_ids = [x["video_id"] for x in result["selected"]]

    assert result["fresh_target"] == 3
    assert result["archive_target"] == 2
    assert len(set(selected_ids)) == len(selected_ids)
    assert "f1" in selected_ids
    assert "a1" in selected_ids


def test_apply_quality_filters_excludes_short_and_low_views() -> None:
    candidates = [
        {"video_id": "v1", "duration_seconds": 50, "view_count": 500000},
        {"video_id": "v2", "duration_seconds": 220, "view_count": 1000},
        {"video_id": "v3", "duration_seconds": 260, "view_count": 6000},
    ]

    filtered = apply_quality_filters(
        candidates,
        min_duration_seconds=180,
        min_view_count=3000,
    )
    ids = {item["video_id"] for item in filtered}
    assert ids == {"v3"}
