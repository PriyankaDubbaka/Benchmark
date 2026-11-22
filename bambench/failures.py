"""The last failed run of a system on a track, kept beside its run folders (never committed)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from .paths import run_dir


def _file(track: str, system_id: str):
    return run_dir(track) / system_id / "last-failure.json"


def record(track: str, system_id: str, error) -> dict:
    line = " ".join(str(error).split())[:300]
    rec = {"when": datetime.now(timezone.utc).isoformat(timespec="seconds"), "error": line}
    f = _file(track, system_id)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    return rec


def clear(track: str, system_id: str) -> None:
    _file(track, system_id).unlink(missing_ok=True)


def last(track: str, system_id: str) -> dict | None:
    try:
        rec = json.loads(_file(track, system_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None
