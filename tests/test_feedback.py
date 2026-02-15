from pathlib import Path

from app.feedback import add_feedback, build_feedback_profile, load_feedback_entries
from app.quota import QuotaTracker


def test_add_feedback_and_profile(tmp_path: Path) -> None:
    path = tmp_path / "feedback.json"

    add_feedback(str(path), video_id="v1", action="like", channel_id="c1")
    add_feedback(str(path), video_id="v2", action="dislike", channel_id="c1")
    add_feedback(str(path), video_id="v3", action="skip", channel_id="c2")

    entries = load_feedback_entries(str(path))
    assert len(entries) == 3

    profile = build_feedback_profile(str(path))
    assert profile.video_bias["v1"] > 0
    assert profile.video_bias["v2"] < 0
    assert profile.channel_bias["c1"] < 0


def test_quota_tracker_summary() -> None:
    q = QuotaTracker()
    q.track("search.list", 100)
    q.track("search.list", 100)
    q.track("videos.list", 1)

    s = q.summary()
    assert s["estimated_units"] == 201
    assert s["total_calls"] == 3
