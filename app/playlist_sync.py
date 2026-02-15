from __future__ import annotations

from typing import Any

from .quota import QuotaTracker


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def fetch_playlist_items(
    youtube: Any,
    playlist_id: str,
    tracker: QuotaTracker | None = None,
) -> list[dict[str, str]]:
    items_out: list[dict[str, str]] = []
    page_token: str | None = None

    while True:
        if tracker:
            tracker.track("playlistItems.list", 1)
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
            playlist_item_id = item.get("id")
            video_id = item.get("contentDetails", {}).get("videoId")
            if playlist_item_id and video_id:
                items_out.append(
                    {
                        "playlist_item_id": str(playlist_item_id),
                        "video_id": str(video_id),
                    }
                )

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return items_out


def fetch_existing_video_ids(
    youtube: Any,
    playlist_id: str,
    tracker: QuotaTracker | None = None,
) -> set[str]:
    playlist_items = fetch_playlist_items(youtube, playlist_id, tracker=tracker)
    return {item["video_id"] for item in playlist_items}


def add_video_to_playlist(
    youtube: Any,
    playlist_id: str,
    video_id: str,
    tracker: QuotaTracker | None = None,
) -> None:
    if tracker:
        tracker.track("playlistItems.insert", 50)
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


def trim_playlist_to_max(
    youtube: Any,
    playlist_id: str,
    max_items: int,
    tracker: QuotaTracker | None = None,
    dry_run: bool = False,
) -> int:
    playlist_items = fetch_playlist_items(youtube, playlist_id, tracker=tracker)
    overflow = len(playlist_items) - max_items
    if overflow <= 0:
        return 0

    # New inserts are added near the front; trim from the tail.
    to_remove = playlist_items[-overflow:]
    if dry_run:
        return len(to_remove)

    removed = 0
    for item in to_remove:
        if tracker:
            tracker.track("playlistItems.delete", 50)
        youtube.playlistItems().delete(id=item["playlist_item_id"]).execute()
        removed += 1
    return removed
