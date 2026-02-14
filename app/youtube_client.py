from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .discovery import days_ago_iso, extract_video, parse_iso8601_duration_seconds

SCOPES = ["https://www.googleapis.com/auth/youtube"]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def authenticate(client_secret_file: str, token_file: str) -> Credentials:
    token_path = Path(token_file)
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
        creds = flow.run_local_server(port=0)

    ensure_parent(token_path)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_client(creds: Credentials) -> Any:
    return build("youtube", "v3", credentials=creds)


def fetch_channel_recent_videos(youtube: Any, channel_id: str, days: int) -> list[dict[str, Any]]:
    published_after = days_ago_iso(days)
    response = (
        youtube.search()
        .list(
            part="snippet",
            channelId=channel_id,
            type="video",
            order="date",
            maxResults=25,
            publishedAfter=published_after,
        )
        .execute()
    )
    return [extract_video(item, source=f"channel:{channel_id}") for item in response.get("items", [])]


def fetch_keyword_videos(youtube: Any, keyword: str, days: int) -> list[dict[str, Any]]:
    published_after = days_ago_iso(days)
    response = (
        youtube.search()
        .list(
            part="snippet",
            q=keyword,
            type="video",
            order="date",
            maxResults=25,
            publishedAfter=published_after,
        )
        .execute()
    )
    return [extract_video(item, source=f"keyword:{keyword}") for item in response.get("items", [])]


def hydrate_video_stats(youtube: Any, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = [c["video_id"] for c in candidates if c.get("video_id")]
    if not ids:
        return []

    stats_map: dict[str, int] = {}
    duration_map: dict[str, int] = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        response = (
            youtube.videos()
            .list(part="statistics,contentDetails", id=",".join(chunk), maxResults=50)
            .execute()
        )
        for item in response.get("items", []):
            vid = item.get("id")
            view_count = int(item.get("statistics", {}).get("viewCount", 0) or 0)
            duration = parse_iso8601_duration_seconds(
                item.get("contentDetails", {}).get("duration")
            )
            if vid:
                stats_map[vid] = view_count
                duration_map[vid] = duration

    hydrated: list[dict[str, Any]] = []
    for c in candidates:
        item = dict(c)
        vid = item.get("video_id")
        item["view_count"] = stats_map.get(vid, int(item.get("view_count") or 0))
        item["duration_seconds"] = duration_map.get(vid, int(item.get("duration_seconds") or 0))
        hydrated.append(item)
    return hydrated
