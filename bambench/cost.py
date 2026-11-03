"""Time and GPU cost per page, worked out from a run summary and its system card.

Cost is an estimate, not a bill: the share of an A100 the system's slice occupies, times the time
it ran, times an hourly price. Set BAMBENCH_A100_EUR_PER_HOUR to BAM's own figure; the default is
a typical cloud rental price for one A100 80 GB, used only so the systems can be compared.
"""
from __future__ import annotations

import os
import re

DEFAULT_EUR_PER_HOUR = 2.0
A100_GB = 80


def eur_per_hour() -> float:
    try:
        return float(os.environ.get("BAMBENCH_A100_EUR_PER_HOUR", DEFAULT_EUR_PER_HOUR))
    except ValueError:
        return DEFAULT_EUR_PER_HOUR


def gpu_share(card: dict) -> float:
    """Fraction of one A100 the card's slice uses: "20 GB" is a quarter, "40 GB" a half, no slice is CPU only."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB", str(card.get("slice") or ""), re.I)
    return min(float(m.group(1)) / A100_GB, 1.0) if m else 0.0


def cost(summary: dict) -> dict:
    pages = (summary.get("counts") or {}).get("pages") or 0
    runtime = summary.get("runtime_s")
    out = {"seconds_per_page": None, "gpu_share": gpu_share(summary.get("card") or {}),
           "eur_per_hour": eur_per_hour(), "eur_per_1000_pages": None,
           "prompt_tokens_per_page": None, "output_tokens_per_page": None, "truncated_pages": None}
    if pages and runtime is not None:
        spp = runtime / pages
        out["seconds_per_page"] = round(spp, 2)
        out["eur_per_1000_pages"] = round(spp * 1000 / 3600 * out["gpu_share"] * out["eur_per_hour"], 3)
    u = summary.get("usage")
    if pages and u:
        out["prompt_tokens_per_page"] = round(u["prompt_tokens"] / pages)
        out["output_tokens_per_page"] = round(u["completion_tokens"] / pages)
        out["truncated_pages"] = u.get("truncated", 0)
    return out
