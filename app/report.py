from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_report(report: dict[str, Any], path: str | None) -> None:
    if not path:
        return
    out_path = Path(path)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
