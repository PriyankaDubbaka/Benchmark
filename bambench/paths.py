"""Repository locations. Everything resolves from the repo root so the CLI works from any cwd."""
import os
from pathlib import Path

ROOT = Path(os.environ.get("BAMBENCH_ROOT", Path(__file__).resolve().parent.parent))
DATA = ROOT / "data"
CACHE = ROOT / ".cache"
RESULTS = ROOT / "results"
SYSTEMS = ROOT / "systems"
SITE = ROOT / "site"
TRACKS = ("open", "closed")


def track_dir(track: str) -> Path:
    if track not in TRACKS:
        raise ValueError(f"Unknown track {track!r}; expected one of {TRACKS}")
    return DATA / track


def run_dir(track: str) -> Path:
    """Raw predictions. Closed-track outputs stay inside the gitignored closed folder."""
    return track_dir("closed") / "runs" if track == "closed" else RESULTS / "open" / "runs"


def summary_dir(track: str) -> Path:
    """Where a run writes its score summary. Closed-track summaries stay in the gitignored closed
    folder until `bambench export-closed` copies the publishable ones to results/closed."""
    return track_dir("closed") / "summaries" if track == "closed" else RESULTS / "open" / "summaries"


def published_dir(track: str) -> Path:
    return RESULTS / track / "summaries"
