from __future__ import annotations

from typing import Any


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def fetch_existing_video_ids(youtube: Any, playlist_id: str) -> set[str]:
    existing: set[str] = set()
    page_token: str | None = None

    while True:
        response = (
            youtube.playlistItems()
            .list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )

        for item in response.get("items", []):
            content = item.get("contentDetails", {})
            video_id = content.get("videoId")
            if video_id:
                existing.add(video_id)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return existing


def add_video_to_playlist(youtube: Any, playlist_id: str, video_id: str) -> None:
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            }
        },
    ).execute()
