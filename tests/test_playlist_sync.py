from app.playlist_sync import trim_playlist_to_max


class _Req:
    def __init__(self, payload=None):
        self.payload = payload or {}

    def execute(self):
        return self.payload


class _PlaylistItemsAPI:
    def __init__(self, pages):
        self.pages = pages
        self.delete_calls = []

    def list(self, **kwargs):
        token = kwargs.get("pageToken")
        page = self.pages[0] if token is None else self.pages[1]
        return _Req(page)

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs["id"])
        return _Req({})


class _YouTube:
    def __init__(self, pages):
        self._api = _PlaylistItemsAPI(pages)

    def playlistItems(self):
        return self._api


def test_trim_playlist_to_max_dry_run() -> None:
    pages = [
        {
            "items": [
                {"id": "pi1", "contentDetails": {"videoId": "v1"}},
                {"id": "pi2", "contentDetails": {"videoId": "v2"}},
                {"id": "pi3", "contentDetails": {"videoId": "v3"}},
            ]
        },
        {"items": []},
    ]
    yt = _YouTube(pages)
    removed = trim_playlist_to_max(yt, "PL123", max_items=2, dry_run=True)
    assert removed == 1
    assert yt._api.delete_calls == []


def test_trim_playlist_to_max_executes_delete() -> None:
    pages = [
        {
            "items": [
                {"id": "pi1", "contentDetails": {"videoId": "v1"}},
                {"id": "pi2", "contentDetails": {"videoId": "v2"}},
                {"id": "pi3", "contentDetails": {"videoId": "v3"}},
            ]
        },
        {"items": []},
    ]
    yt = _YouTube(pages)
    removed = trim_playlist_to_max(yt, "PL123", max_items=2, dry_run=False)
    assert removed == 1
    assert yt._api.delete_calls == ["pi3"]
