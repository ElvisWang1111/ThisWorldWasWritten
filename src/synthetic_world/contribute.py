"""Contribution engine: expand the hidden world from a free-text submission.

This is the "submit an edit" flow of a real wiki. A contributor describes
something (a new country, a person, an event, a correction); the LLM proposes
structured additions; we assign stable ids, resolve name references, merge them
into the hidden world, log the contribution, and return the new entity ids so
the caller can render only the affected pages.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import schemas
from .llm_client import LLMClient
from .renderers import _world_context
from .utils import make_id, read_json, read_jsonl, write_jsonl

SYSTEM = (
    "You are the editor of a fictional encyclopedia. You only produce fictional, "
    "internally consistent content and always return valid JSON."
)


def _world_paths(cfg: Dict[str, Any]) -> Dict[str, Path]:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    feedback = PROJECT_ROOT / cfg.get("paths", {}).get("feedback_dir", "data/feedback")
    return {
        "bible": world / "world_bible.json",
        "entities": world / "entities.jsonl",
        "events": world / "events.jsonl",
        "relations": world / "relations.jsonl",
        "sources": world / "sources.jsonl",
        "contributions": feedback / "contributions.jsonl",
    }


def _next_index(rows: List[Dict[str, Any]], id_field: str) -> int:
    nums = [
        int(r[id_field].split("_")[1])
        for r in rows
        if isinstance(r.get(id_field), str) and "_" in r[id_field]
    ]
    return max(nums, default=0) + 1


def _name_index(rows: List[Dict[str, Any]], id_field: str) -> Dict[str, str]:
    idx: Dict[str, str] = {}
    for r in rows:
        idx[r["name"].strip().lower()] = r[id_field]
        for alias in r.get("aliases", []) or []:
            idx.setdefault(alias.strip().lower(), r[id_field])
    return idx


def _resolve(name: Optional[str], idx: Dict[str, str]) -> Optional[str]:
    if not name:
        return None
    return idx.get(str(name).strip().lower())


def _resolve_list(names: Any, idx: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for n in names or []:
        rid = _resolve(n, idx)
        if rid and rid not in out:
            out.append(rid)
    return out


def apply_contribution(
    cfg: Dict[str, Any], llm: LLMClient, submission: str
) -> Dict[str, Any]:
    """Expand the world from a free-text submission. Returns a summary dict."""
    paths = _world_paths(cfg)
    bible = read_json(paths["bible"]) if paths["bible"].exists() else {}
    entities = read_jsonl(paths["entities"])
    events = read_jsonl(paths["events"])

    ent_catalog = "\n".join(
        f"- {e['name']} ({e['entity_type']})" for e in entities
    ) or "(none)"
    evt_catalog = "\n".join(f"- {e['name']}" for e in events) or "(none)"

    from .utils import load_prompt

    prompt = load_prompt("contribute.md").format(
        submission=submission.strip(),
        world_context=_world_context(bible),
        entity_catalog=ent_catalog[:6000],
        event_catalog=evt_catalog[:3000],
    )
    contrib_tokens = int(cfg.get("generation", {}).get("max_tokens", 8192))
    data = llm.complete_json(SYSTEM, prompt, max_tokens=max(contrib_tokens, 8192))
    return merge_additions(cfg, data, cause="user_submission", note=submission.strip())


def merge_additions(
    cfg: Dict[str, Any], data: Dict[str, Any], *, cause: str, note: str = ""
) -> Dict[str, Any]:
    """Merge LLM-proposed additions into the hidden world (shared by the
    contribution and evolution flows).

    ``data`` may contain new_entities / new_events / new_relations /
    new_sources. Assigns stable ids continuing from the current maxima, resolves
    name references (across existing + newly added), appends to the JSONL files,
    and logs the mutation. Returns counts and the new entity ids.
    """
    paths = _world_paths(cfg)
    entities = read_jsonl(paths["entities"])
    events = read_jsonl(paths["events"])
    relations = read_jsonl(paths["relations"])
    sources = read_jsonl(paths["sources"])

    # ---- New entities -------------------------------------------------
    ent_idx = _name_index(entities, "entity_id")
    next_ent = _next_index(entities, "entity_id")
    seen_names = {e["name"].strip().lower() for e in entities}
    new_entities: List[Dict[str, Any]] = []

    raw_entities = data.get("new_entities", []) or []
    # First pass: mint ids so intra-batch located_in references can resolve.
    for item in raw_entities:
        name = (item.get("name") or "").strip()
        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())
        eid = make_id("entity", next_ent)
        next_ent += 1
        ent_idx[name.lower()] = eid
        item["_entity_id"] = eid
    for item in raw_entities:
        if "_entity_id" not in item:
            continue
        ent = schemas.Entity(
            entity_id=item["_entity_id"],
            name=item["name"].strip(),
            entity_type=item.get("entity_type", "institution"),
            aliases=item.get("aliases", []) or [],
            description=item.get("description", ""),
            birth_date=item.get("birth_date"),
            death_date=item.get("death_date"),
            founded_date=item.get("founded_date"),
            located_in=_resolve(item.get("located_in"), ent_idx),
            attributes=item.get("attributes", {}) or {},
            source="contributed",
        )
        new_entities.append(ent.model_dump())

    # ---- New events ---------------------------------------------------
    evt_idx_name: Dict[str, str] = {e["name"].strip().lower(): e["event_id"]
                                    for e in events}
    next_evt = _next_index(events, "event_id")
    new_events: List[Dict[str, Any]] = []
    raw_events = data.get("new_events", []) or []
    for item in raw_events:
        name = (item.get("name") or "").strip()
        if not name or name.lower() in evt_idx_name:
            continue
        eid = make_id("event", next_evt)
        next_evt += 1
        evt_idx_name[name.lower()] = eid
        item["_event_id"] = eid
    for item in raw_events:
        if "_event_id" not in item:
            continue
        cause_ids = [
            evt_idx_name[c.strip().lower()]
            for c in (item.get("cause_event_names") or [])
            if c.strip().lower() in evt_idx_name
        ]
        ev = schemas.Event(
            event_id=item["_event_id"],
            name=item["name"].strip(),
            event_type=item.get("event_type", "reform"),
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            location_ids=_resolve_list(item.get("location_names"), ent_idx),
            participant_ids=_resolve_list(item.get("participant_names"), ent_idx),
            cause_event_ids=cause_ids,
            outcome=item.get("outcome", ""),
            description=item.get("description", ""),
        )
        new_events.append(ev.model_dump())

    # ---- New relations ------------------------------------------------
    next_rel = _next_index(relations, "relation_id")
    existing_rel_keys = {
        (r["subject_id"], r["predicate"], r["object_id"]) for r in relations
    }
    new_relations: List[Dict[str, Any]] = []
    for item in data.get("new_relations", []) or []:
        subj = _resolve(item.get("subject_name"), ent_idx)
        obj = _resolve(item.get("object_name"), ent_idx)
        pred = item.get("predicate")
        if not (subj and obj and pred) or pred not in schemas.PREDICATES:
            continue
        key = (subj, pred, obj)
        if key in existing_rel_keys:
            continue
        existing_rel_keys.add(key)
        rel = schemas.Relation(
            relation_id=make_id("relation", next_rel),
            subject_id=subj,
            predicate=pred,
            object_id=obj,
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            confidence=float(item.get("confidence", 1.0)),
        )
        new_relations.append(rel.model_dump())
        next_rel += 1

    # ---- New sources --------------------------------------------------
    next_src = _next_index(sources, "source_id")
    new_sources: List[Dict[str, Any]] = []
    for item in data.get("new_sources", []) or []:
        supports = _resolve_list(item.get("supports_event_names"), evt_idx_name)
        src = schemas.Source(
            source_id=make_id("source", next_src),
            title=item.get("title", f"Untitled Source {next_src}"),
            source_type=item.get("source_type", "book"),
            author=item.get("author"),
            publication_year=item.get("publication_year"),
            publisher=item.get("publisher"),
            supports=supports,
            reliability=item.get("reliability", "secondary"),
        )
        new_sources.append(src.model_dump())
        next_src += 1

    # ---- Persist (append) ---------------------------------------------
    if new_entities:
        write_jsonl(paths["entities"], entities + new_entities)
    if new_events:
        write_jsonl(paths["events"], events + new_events)
    if new_relations:
        write_jsonl(paths["relations"], relations + new_relations)
    if new_sources:
        write_jsonl(paths["sources"], sources + new_sources)

    # ---- Log the mutation ---------------------------------------------
    log_entry = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "cause": cause,
        "note": note,
        "summary": data.get("summary", ""),
        "added": {
            "entities": [e["entity_id"] for e in new_entities],
            "events": [e["event_id"] for e in new_events],
            "relations": [r["relation_id"] for r in new_relations],
            "sources": [s["source_id"] for s in new_sources],
        },
    }
    paths["contributions"].parent.mkdir(parents=True, exist_ok=True)
    with paths["contributions"].open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    result = {
        "summary": data.get("summary", ""),
        "new_entity_ids": [e["entity_id"] for e in new_entities],
        "new_event_ids": [e["event_id"] for e in new_events],
        "counts": {
            "entities": len(new_entities),
            "events": len(new_events),
            "relations": len(new_relations),
            "sources": len(new_sources),
        },
    }
    print(
        f"[contribute] +{result['counts']['entities']} entities, "
        f"+{result['counts']['events']} events, "
        f"+{result['counts']['relations']} relations, "
        f"+{result['counts']['sources']} sources"
    )
    return result
