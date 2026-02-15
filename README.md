# youtube-playlist-builder

Topic-based YouTube playlist updater.

## Quick start

1. Create virtual environment and install dependencies.
2. Put OAuth client json into `.secrets/client_secret.json`.
3. Copy `config.example.yaml` to `config.yaml` and edit.
4. Run auth and sync.

```bash
python -m app.cli auth .secrets/client_secret.json .secrets/token.json
python -m app.cli validate-config --config config.yaml
python -m app.cli run --config config.yaml --report-file run-report.json
```

## Feedback

Save explicit feedback and use it in ranking:

```bash
python -m app.cli feedback VIDEO_ID like --channel-id CHANNEL_ID
python -m app.cli feedback VIDEO_ID skip
python -m app.cli feedback VIDEO_ID dislike
```

`run` reads `.secrets/feedback.json` by default and writes estimated quota usage to `run-report.json`.

## Playlist size control

Set `max_playlist_size` in `defaults` or per topic to keep playlists from growing indefinitely.
When the playlist exceeds this limit, older tail items are trimmed.
