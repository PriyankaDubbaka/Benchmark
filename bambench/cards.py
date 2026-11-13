"""Checks for system cards: systems/schema/card.schema.json plus the rules a schema cannot express.

The validator understands only the part of JSON Schema the card schema uses: type (also a list of
types), enum, pattern, required, properties, additionalProperties as a boolean, items, minimum
and minLength.
"""
from __future__ import annotations

import difflib
import json
import re
import shlex

from .paths import SYSTEMS

SCHEMA = SYSTEMS / "schema" / "card.schema.json"
STATUSES = ("pending", "active", "failed", "superseded", "withdrawn")
_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
}


def load_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _check(value, schema: dict, where: str, out: list[str], label: str) -> None:
    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not any(_TYPES[t](value) for t in types):
            out.append(f'{label}: {where} must be {" or ".join(types)}, not {json.dumps(value)[:40]}')
            return
    if "enum" in schema and value not in schema["enum"]:
        out.append(f'{label}: {where} is {json.dumps(value)}, expected one of {", ".join(map(str, schema["enum"]))}')
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            out.append(f"{label}: {where} is empty" if schema["minLength"] == 1 else
                       f'{label}: {where} is shorter than {schema["minLength"]} characters')
        if "pattern" in schema and not re.search(schema["pattern"], value):
            out.append(f'{label}: {where} is {json.dumps(value)}, which does not match {schema["pattern"]}')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            out.append(f'{label}: {where} is {value}, below the minimum {schema["minimum"]}')
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for k in schema.get("required", []):
            if k not in value:
                out.append(f'{label}: {where + " " if where != "card" else ""}missing required key "{k}"')
        for k, v in value.items():
            if k in props:
                _check(v, props[k], f"{k}" if where == "card" else f"{where}.{k}", out, label)
            elif schema.get("additionalProperties") is False:
                near = difflib.get_close_matches(k, props, n=1)
                hint = f' (did you mean "{near[0]}"?)' if near else ""
                out.append(f'{label}: unknown key "{k}"{hint}' if where == "card"
                           else f'{label}: unknown key "{k}" in {where}{hint}')
    if isinstance(value, list) and "items" in schema:
        for i, v in enumerate(value):
            _check(v, schema["items"], f"{where}[{i}]", out, label)


def validate(card: dict, schema: dict) -> list[str]:
    """Readable problems of one card against the schema; empty when it is fine."""
    out: list[str] = []
    _check(card, schema, "card", out, str(card.get("id", "?")) if isinstance(card, dict) else "?")
    return out


def _rules(card: dict, stem: str, ids: set[str]) -> list[str]:
    """Cross checks the schema cannot express."""
    from .systems import KINDS
    from .systems.outputs import CONVERTERS

    p, cid = [], stem
    if card.get("id") != stem:
        p.append(f'{cid}: id is {json.dumps(card.get("id"))} but the file is {stem}.json')
    if "kind" in card and card["kind"] not in KINDS:
        p.append(f'{cid}: unknown kind "{card["kind"]}", expected one of {", ".join(sorted(KINDS))}')
    serve = card.get("serve")
    if serve:
        if not card.get("model"):
            p.append(f'{cid}: has "serve" but no "model"')
        try:
            words = shlex.split(serve)
        except ValueError as e:
            words, _ = [], p.append(f'{cid}: "serve" does not parse as a shell command ({e})')
        if words and words[0] != "vllm":
            p.append(f'{cid}: "serve" must start with vllm')
        if "--port" in serve:
            p.append(f'{cid}: "serve" must not set --port (the job picks one)')
    out = card.get("output")
    if out is not None and out not in CONVERTERS and out != "doctags":
        p.append(f'{cid}: unknown output converter "{out}", expected one of {", ".join(sorted(CONVERTERS | {"doctags": 0}))}')
    status, sup = card.get("status"), card.get("superseded_by")
    if sup is not None and sup not in ids:
        p.append(f'{cid}: superseded_by names "{sup}", which is not a card')
    if status == "superseded" and not sup:
        p.append(f'{cid}: status is superseded but superseded_by is not set')
    if sup is not None and status != "superseded":
        p.append(f'{cid}: superseded_by is set but status is not superseded')
    return p


def check_all() -> list[str]:
    """Problems in every systems/*.json card; empty when all pass."""
    schema = load_schema()
    files = sorted(SYSTEMS.glob("*.json"))
    raws, problems = {}, []
    for f in files:
        try:
            raws[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            problems.append(f"{f.stem}: not valid JSON ({e})")
    ids = set(raws)
    for stem, card in raws.items():
        if not isinstance(card, dict):
            problems.append(f"{stem}: a card must be a JSON object")
            continue
        problems += validate(card, schema) + _rules(card, stem, ids)
    return problems


def status_of(card: dict, has_result: bool, failure: dict | None) -> tuple[str, str]:
    """(status, note) of a system. A card may pin superseded, withdrawn or failed; otherwise
    a result means active, a recorded failure means failed, and nothing yet means pending."""
    note = card.get("status_note", "")
    if card.get("status") in ("superseded", "withdrawn", "failed"):
        return card["status"], note
    if has_result:
        return "active", note
    if failure:
        return "failed", failure.get("error", "")
    return "pending", note
