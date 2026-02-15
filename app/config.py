from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class OAuthConfig(BaseModel):
    client_secret_file: Path
    token_file: Path


class DefaultsConfig(BaseModel):
    max_add_per_topic: int = Field(default=5, ge=1, le=100)
    max_playlist_size: int = Field(default=20, ge=1, le=5000)
    relative_view_threshold: float = Field(default=0.6, gt=0, le=5)
    min_duration_seconds: int = Field(default=0, ge=0, le=86400)
    min_view_count: int = Field(default=0, ge=0)


class TopicConfig(BaseModel):
    name: str = Field(min_length=1)
    playlist_id: str = Field(min_length=5)
    channels: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    search_days_fresh: int = Field(default=30, ge=1, le=3650)
    search_days_archive: int = Field(default=180, ge=1, le=36500)
    search_order: Literal["date", "viewCount"] = "date"
    mix_fresh_ratio: float = Field(default=0.6, ge=0, le=1)
    max_add_per_topic: int | None = Field(default=None, ge=1, le=100)
    max_playlist_size: int | None = Field(default=None, ge=1, le=5000)
    relative_view_threshold: float | None = Field(default=None, gt=0, le=5)
    min_duration_seconds: int | None = Field(default=None, ge=0, le=86400)
    min_view_count: int | None = Field(default=None, ge=0)

    @field_validator("channels", "keywords")
    @classmethod
    def trim_items(cls, values: list[str]) -> list[str]:
        return [v.strip() for v in values if v and v.strip()]

    @field_validator("search_days_archive")
    @classmethod
    def archive_must_not_be_smaller(cls, value: int, info: Any) -> int:
        fresh = info.data.get("search_days_fresh") if info and info.data else None
        if isinstance(fresh, int) and value < fresh:
            raise ValueError("search_days_archive must be >= search_days_fresh")
        return value

    @field_validator("keywords")
    @classmethod
    def require_source(cls, values: list[str], info: Any) -> list[str]:
        channels = info.data.get("channels") if info and info.data else []
        if not values and not channels:
            raise ValueError("at least one of channels/keywords is required")
        return values


class AppConfig(BaseModel):
    oauth: OAuthConfig
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    topics: list[TopicConfig] = Field(min_length=1)


class ConfigError(RuntimeError):
    pass


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Config must be a mapping")

    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc
