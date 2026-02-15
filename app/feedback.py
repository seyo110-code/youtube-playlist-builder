from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ACTION_WEIGHTS = {
    "like": 2.0,
    "skip": -0.8,
    "dislike": -2.5,
}


@dataclass
class FeedbackProfile:
    video_bias: dict[str, float]
    channel_bias: dict[str, float]



def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")



def load_feedback_entries(path: str) -> list[dict[str, Any]]:
    feedback_path = Path(path)
    if not feedback_path.exists():
        return []

    data = json.loads(feedback_path.read_text(encoding="utf-8"))
    items = data.get("items", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]



def save_feedback_entries(path: str, items: list[dict[str, Any]]) -> None:
    feedback_path = Path(path)
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    feedback_path.write_text(
        json.dumps({"items": items}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )



def add_feedback(path: str, video_id: str, action: str, channel_id: str | None = None) -> None:
    if action not in ACTION_WEIGHTS:
        raise ValueError(f"Unsupported action: {action}")

    items = load_feedback_entries(path)
    items.append(
        {
            "video_id": video_id,
            "channel_id": channel_id or "",
            "action": action,
            "updated_at": _now_iso(),
        }
    )
    save_feedback_entries(path, items)



def build_feedback_profile(path: str) -> FeedbackProfile:
    items = load_feedback_entries(path)
    video_bias: dict[str, float] = {}
    channel_bias: dict[str, float] = {}

    for item in items:
        action = str(item.get("action") or "")
        weight = ACTION_WEIGHTS.get(action)
        if weight is None:
            continue

        video_id = str(item.get("video_id") or "").strip()
        if video_id:
            video_bias[video_id] = video_bias.get(video_id, 0.0) + weight

        channel_id = str(item.get("channel_id") or "").strip()
        if channel_id:
            channel_bias[channel_id] = channel_bias.get(channel_id, 0.0) + (weight * 0.5)

    return FeedbackProfile(video_bias=video_bias, channel_bias=channel_bias)
