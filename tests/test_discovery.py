from app.discovery import parse_iso8601_duration_seconds


def test_parse_iso8601_duration_seconds() -> None:
    assert parse_iso8601_duration_seconds("PT59S") == 59
    assert parse_iso8601_duration_seconds("PT4M13S") == 253
    assert parse_iso8601_duration_seconds("PT1H2M") == 3720
    assert parse_iso8601_duration_seconds(None) == 0
