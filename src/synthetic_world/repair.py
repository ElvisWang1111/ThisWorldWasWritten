"""Deterministic (non-LLM) repairs for common hidden-world contradictions.

The validator flags issues; this module fixes the mechanical ones by adjusting
the hidden world (the source of truth), in the spirit of the README's repair
loop: fix the world, then re-render. Currently handles temporal contradictions
where an entity participates in an event before it exists or after it died.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .utils import parse_date_tuple, read_jsonl, write_jsonl


def _paths(cfg: Dict[str, Any]) -> Dict[str, Path]:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    return {"entities": world / "entities.jsonl", "events": world / "events.jsonl"}


def repair_temporal(cfg: Dict[str, Any]) -> List[str]:
    """Align entity existence/death dates with the events they participate in.

    - If an entity participates in an event before its birth/founding date, the
      existence date is moved back to the earliest participation.
    - If an entity participates after its recorded death, the death date is moved
      forward to the latest participation.

    Returns a list of human-readable descriptions of the fixes applied.
    """
    paths = _paths(cfg)
    entities = read_jsonl(paths["entities"])
    events = read_jsonl(paths["events"])

    # earliest / latest participation per entity (as (date_tuple, raw_string)).
    part: Dict[str, List[tuple]] = {}
    for ev in events:
        d = parse_date_tuple(ev.get("start_date"))
        if d is None:
            continue
        for pid in ev.get("participant_ids", []):
            part.setdefault(pid, []).append((d, ev.get("start_date")))

    fixes: List[str] = []
    for e in entities:
        items = part.get(e["entity_id"])
        if not items:
            continue
        earliest = min(items, key=lambda x: x[0])
        latest = max(items, key=lambda x: x[0])

        # Existence date: prefer birth_date for people, else founded_date.
        ex_field = "birth_date" if e.get("birth_date") else (
            "founded_date" if e.get("founded_date") else None
        )
        if ex_field:
            ex = parse_date_tuple(e[ex_field])
            if ex and earliest[0] < ex:
                fixes.append(
                    f"{e['name']}: {ex_field} {e[ex_field]} -> {earliest[1]} "
                    f"(participated earlier)"
                )
                e[ex_field] = earliest[1]
                e["version"] = e.get("version", 1) + 1

        if e.get("death_date"):
            dd = parse_date_tuple(e["death_date"])
            if dd and latest[0] > dd:
                fixes.append(
                    f"{e['name']}: death_date {e['death_date']} -> {latest[1]} "
                    f"(participated later)"
                )
                e["death_date"] = latest[1]
                e["version"] = e.get("version", 1) + 1

    if fixes:
        write_jsonl(paths["entities"], entities)
    return fixes
