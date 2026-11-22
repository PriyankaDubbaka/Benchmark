from __future__ import annotations

from typing import Callable

from ..corpus import Document

Progress = Callable[[str], None]


class System:
    """A complete extraction system: parser, model, prompt and settings, described by its card."""

    kind = "base"
    local_only = True  # every system must run without sending document content off the machine

    def __init__(self, card: dict):
        self.card = card
        self.id = card["id"]
        # Token counts across a run, filled by systems that call an LLM server directly. None means unknown.
        self.usage: dict | None = None

    def available(self) -> tuple[bool, str]:
        return True, ""

    def predict(self, doc: Document, pages: list[int], progress: Progress) -> dict:
        """Return {"pages": {page: markdown}, "records": list | None}."""
        raise NotImplementedError

    def server_info(self) -> dict | None:
        """Version of the model server behind this system, when it has one and can say."""
        return None
