from pathlib import Path

import pytest

from app.config import ConfigError, load_config


def test_load_config_ok(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
oauth:
  client_secret_file: ".secrets/client_secret.json"
  token_file: ".secrets/token.json"
defaults:
  max_add_per_topic: 5
  relative_view_threshold: 0.6
topics:
  - name: "music"
    playlist_id: "PL12345"
    channels: ["UC1"]
    keywords: ["live"]
    search_days_fresh: 30
    search_days_archive: 3650
    mix_fresh_ratio: 0.6
""",
        encoding="utf-8",
    )

    cfg = load_config(cfg_file)
    assert len(cfg.topics) == 1
    assert cfg.topics[0].search_days_archive == 3650


def test_load_config_fails_if_archive_smaller_than_fresh(tmp_path: Path) -> None:
    cfg_file = tmp_path / "bad.yaml"
    cfg_file.write_text(
        """
oauth:
  client_secret_file: ".secrets/client_secret.json"
  token_file: ".secrets/token.json"
topics:
  - name: "news"
    playlist_id: "PL12345"
    channels: ["UC1"]
    search_days_fresh: 30
    search_days_archive: 10
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(cfg_file)
