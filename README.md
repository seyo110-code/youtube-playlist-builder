# youtube-playlist-builder

Topic-based YouTube playlist updater.

## Quick start

1. Create virtual environment and install dependencies.
2. Put OAuth client json into `.secrets/client_secret.json`.
3. Copy `config.example.yaml` to `config.yaml` and edit.
4. Run auth and sync.

```bash
python -m app.cli auth --client-secret-file .secrets/client_secret.json --token-file .secrets/token.json
python -m app.cli validate-config --config config.yaml
python -m app.cli run --config config.yaml --report-file run-report.json
```
