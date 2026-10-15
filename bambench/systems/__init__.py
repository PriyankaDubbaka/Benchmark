"""Systems under test. Each system card in systems/*.json names a kind implemented here."""
from __future__ import annotations

import json

from ..paths import SYSTEMS
from .base import System
from .docling_system import DoclingSystem
from .pdftotext_rules import PdftotextRules
from .vllm_vlm import VllmVlm

KINDS = {cls.kind: cls for cls in (PdftotextRules, VllmVlm, DoclingSystem)}


def load_cards() -> list[dict]:
    cards = []
    for f in sorted(SYSTEMS.glob("*.json")):
        card = json.loads(f.read_text(encoding="utf-8"))
        card.setdefault("id", f.stem)
        cards.append(card)
    return cards


def get_system(system_id: str) -> System:
    for card in load_cards():
        if card["id"] == system_id:
            if card.get("kind") not in KINDS:
                raise ValueError(f"{system_id}: unknown kind {card.get('kind')!r}")
            return KINDS[card["kind"]](card)
    raise KeyError(f"No system card for {system_id!r} in {SYSTEMS}")
