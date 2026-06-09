"""Generation stages 1-5: world bible, entities, events, relations, sources.

Each stage reads its inputs from disk, calls the LLM, assigns stable ids,
resolves human-readable name references back to ids, and writes its outputs.
The hidden world layer is always treated as ground truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import schemas
from .llm_client import LLMClient
from .utils import (
    load_prompt,
    make_id,
    read_json,
    read_jsonl,
    write_json,
    write_jsonl,
)

SYSTEM = (
    "You are a meticulous worldbuilding archivist. You only produce fictional "
    "content and you always return valid, machine-readable JSON with no extra "
    "commentary."
)

# Which entity categories to generate, in dependency order, and the entity_type
# values each category may use.
ENTITY_CATEGORIES: List[Tuple[str, Tuple[str, ...]]] = [
    ("locations", ("country", "region", "city", "river", "mountain")),
    ("institutions", ("institution", "university", "company", "newspaper",
                      "political_party")),
    ("people", ("person",)),
    ("culture", ("cultural_group", "technology", "book", "artwork")),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _world_paths(cfg: Dict[str, Any]) -> Dict[str, Path]:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    return {
        "dir": world,
        "bible": world / "world_bible.json",
        "entities": world / "entities.jsonl",
        "events": world / "events.jsonl",
        "timeline": world / "timeline.jsonl",
        "relations": world / "relations.jsonl",
        "sources": world / "sources.jsonl",
    }


def _name_index(rows: List[Dict[str, Any]], id_key: str) -> Dict[str, str]:
    """Map lowercased names AND aliases -> id for resolution of LLM references."""
    idx: Dict[str, str] = {}
    for r in rows:
        idx[r["name"].strip().lower()] = r[id_key]
        for alias in r.get("aliases", []) or []:
            idx.setdefault(alias.strip().lower(), r[id_key])
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


# ---------------------------------------------------------------------------
# Stage 1: World bible
# ---------------------------------------------------------------------------


def generate_world_bible(cfg: Dict[str, Any], llm: LLMClient) -> Path:
    scale = cfg.get("scale", {})
    prompt = load_prompt("generate_world_bible.md").format(
        world_name=cfg.get("world_name", "Asteria"),
        num_regions=scale.get("num_regions", 3),
        num_cities=scale.get("num_cities", 6),
        num_people=scale.get("num_people", 12),
        num_institutions=scale.get("num_institutions", 8),
        num_events=scale.get("num_events", 12),
    )
    bible = llm.complete_json(SYSTEM, prompt)
    paths = _world_paths(cfg)
    write_json(paths["bible"], bible)
    print(f"[stage1] world bible -> {paths['bible']}")
    return paths["bible"]


# ---------------------------------------------------------------------------
# Stage 2: Entities
# ---------------------------------------------------------------------------


def generate_entities(cfg: Dict[str, Any], llm: LLMClient) -> Path:
    paths = _world_paths(cfg)
    bible = read_json(paths["bible"])
    bible_str = json.dumps(bible, ensure_ascii=False)
    scale = cfg.get("scale", {})

    # Rough per-category targets derived from configured scale.
    targets = {
        "locations": int(scale.get("num_cities", 6))
        + int(scale.get("num_regions", 3))
        + int(scale.get("num_countries", 1)),
        "institutions": int(scale.get("num_institutions", 8)),
        "people": int(scale.get("num_people", 12)),
        "culture": max(3, int(scale.get("num_institutions", 8)) // 2),
    }

    entities: List[Dict[str, Any]] = []
    next_id = 1
    seen_names: set[str] = set()
    batch_size = max(1, int(cfg.get("generation", {}).get("batch_size", 8)))
    template = load_prompt("generate_entities.md")

    for category, allowed in ENTITY_CATEGORIES:
        count = targets.get(category, 5)
        if count <= 0:
            continue
        # Generate in chunks of batch_size so a single response never grows
        # large enough to be truncated at max_tokens.
        remaining = count
        while remaining > 0:
            chunk = min(batch_size, remaining)
            known_locations = [
                e["name"] for e in entities
                if e["entity_type"] in schemas.LOCATION_ENTITY_TYPES
            ]
            existing_names = sorted(seen_names)
            prompt = template.format(
                world_bible=bible_str,
                count=chunk,
                category=category,
                allowed_types=", ".join(allowed),
                known_locations=", ".join(known_locations) or "(none yet)",
            )
            if existing_names:
                prompt += (
                    "\n\n## Names already used (do NOT repeat any of these)\n"
                    + ", ".join(existing_names)
                )
            raw = llm.complete_jsonl(SYSTEM, prompt)
            loc_idx = _name_index(entities, "entity_id")
            added = 0
            for item in raw:
                name = (item.get("name") or "").strip()
                if not name or name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())
                ent = schemas.Entity(
                    entity_id=make_id("entity", next_id),
                    name=name,
                    entity_type=item.get("entity_type", allowed[0]),
                    aliases=item.get("aliases", []) or [],
                    description=item.get("description", ""),
                    birth_date=item.get("birth_date"),
                    death_date=item.get("death_date"),
                    founded_date=item.get("founded_date"),
                    located_in=_resolve(item.get("located_in"), loc_idx),
                    attributes=item.get("attributes", {}) or {},
                )
                entities.append(ent.model_dump())
                next_id += 1
                added += 1
            print(f"[stage2] {category}: +{added} (total {len(entities)})")
            # Avoid an infinite loop if the model returns nothing usable.
            remaining -= chunk if added == 0 else added

    write_jsonl(paths["entities"], entities)
    print(f"[stage2] entities -> {paths['entities']} ({len(entities)})")
    return paths["entities"]


# ---------------------------------------------------------------------------
# Stage 3: Events
# ---------------------------------------------------------------------------


def generate_events(cfg: Dict[str, Any], llm: LLMClient) -> Path:
    paths = _world_paths(cfg)
    bible = read_json(paths["bible"])
    entities = read_jsonl(paths["entities"])
    ent_idx = _name_index(entities, "entity_id")

    catalog = "\n".join(
        f"- {e['name']} ({e['entity_type']}, {e['entity_id']})" for e in entities
    )
    count = int(cfg.get("scale", {}).get("num_events", 12))
    prompt = load_prompt("generate_events.md").format(
        world_bible=json.dumps(bible, ensure_ascii=False),
        entity_catalog=catalog,
        count=count,
        event_types=", ".join(schemas.EVENT_TYPES),
    )
    raw = llm.complete_jsonl(SYSTEM, prompt)

    events: List[Dict[str, Any]] = []
    next_id = 1
    name_to_evt: Dict[str, str] = {}
    # First pass: assign ids so cause references can resolve within the batch.
    for item in raw:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        eid = make_id("event", next_id)
        name_to_evt[name.lower()] = eid
        next_id += 1
        item["_event_id"] = eid

    for item in raw:
        if "_event_id" not in item:
            continue
        cause_ids = [
            name_to_evt[c.strip().lower()]
            for c in (item.get("cause_event_names") or [])
            if c.strip().lower() in name_to_evt
        ]
        evt = schemas.Event(
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
        events.append(evt.model_dump())

    write_jsonl(paths["events"], events)

    # Timeline: a flat, date-sorted projection of events.
    from .utils import parse_date_tuple

    timeline = sorted(
        (
            {
                "event_id": e["event_id"],
                "name": e["name"],
                "start_date": e["start_date"],
                "event_type": e["event_type"],
            }
            for e in events
        ),
        key=lambda r: parse_date_tuple(r["start_date"]) or (9999, 12, 31),
    )
    write_jsonl(paths["timeline"], timeline)
    print(f"[stage3] events -> {paths['events']} ({len(events)}), timeline written")
    return paths["events"]


# ---------------------------------------------------------------------------
# Stage 4: Relations
# ---------------------------------------------------------------------------


def generate_relations(cfg: Dict[str, Any], llm: LLMClient) -> Path:
    paths = _world_paths(cfg)
    entities = read_jsonl(paths["entities"])
    events = read_jsonl(paths["events"])
    ent_idx = _name_index(entities, "entity_id")

    ent_catalog = "\n".join(
        f"- {e['name']} ({e['entity_type']}, {e['entity_id']})" for e in entities
    )
    evt_catalog = "\n".join(
        f"- {e['name']} ({e['event_type']}, {e['event_id']})" for e in events
    )
    count = max(len(entities), int(cfg.get("scale", {}).get("num_people", 12)) * 2)
    prompt = load_prompt("generate_relations.md").format(
        entity_catalog=ent_catalog,
        event_catalog=evt_catalog or "(none)",
        count=count,
        predicates=", ".join(schemas.PREDICATES),
    )
    raw = llm.complete_jsonl(SYSTEM, prompt)

    relations: List[Dict[str, Any]] = []
    next_id = 1
    seen: set[Tuple[str, str, str]] = set()
    for item in raw:
        subj = _resolve(item.get("subject_name"), ent_idx)
        obj = _resolve(item.get("object_name"), ent_idx)
        pred = item.get("predicate")
        if not (subj and obj and pred) or pred not in schemas.PREDICATES:
            continue
        key = (subj, pred, obj)
        if key in seen:
            continue
        seen.add(key)
        rel = schemas.Relation(
            relation_id=make_id("relation", next_id),
            subject_id=subj,
            predicate=pred,
            object_id=obj,
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            confidence=float(item.get("confidence", 1.0)),
        )
        relations.append(rel.model_dump())
        next_id += 1

    write_jsonl(paths["relations"], relations)
    print(f"[stage4] relations -> {paths['relations']} ({len(relations)})")
    return paths["relations"]


# ---------------------------------------------------------------------------
# Stage 5: Sources
# ---------------------------------------------------------------------------


def generate_sources(cfg: Dict[str, Any], llm: LLMClient) -> Path:
    paths = _world_paths(cfg)
    bible = read_json(paths["bible"])
    relations = read_jsonl(paths["relations"])
    events = read_jsonl(paths["events"])

    # Build a fact catalog the model can attach citations to.
    ent_by_id = {e["entity_id"]: e for e in read_jsonl(paths["entities"])}
    fact_lines: List[str] = []
    for r in relations:
        s = ent_by_id.get(r["subject_id"], {}).get("name", r["subject_id"])
        o = ent_by_id.get(r["object_id"], {}).get("name", r["object_id"])
        fact_lines.append(f"- {r['relation_id']}: {s} {r['predicate']} {o}")
    for e in events:
        fact_lines.append(f"- {e['event_id']}: {e['name']} ({e['start_date']})")
    valid_fact_ids = {r["relation_id"] for r in relations} | {
        e["event_id"] for e in events
    }

    count = int(cfg.get("scale", {}).get("num_sources", 15))
    prompt = load_prompt("generate_sources.md").format(
        world_bible=json.dumps(bible, ensure_ascii=False),
        fact_catalog="\n".join(fact_lines) or "(none)",
        count=count,
        source_types=", ".join(schemas.SOURCE_TYPES),
    )
    raw = llm.complete_jsonl(SYSTEM, prompt)

    sources: List[Dict[str, Any]] = []
    next_id = 1
    for item in raw:
        supports = [s for s in (item.get("supports") or []) if s in valid_fact_ids]
        src = schemas.Source(
            source_id=make_id("source", next_id),
            title=item.get("title", f"Untitled Source {next_id}"),
            source_type=item.get("source_type", "book"),
            author=item.get("author"),
            publication_year=item.get("publication_year"),
            publisher=item.get("publisher"),
            supports=supports,
            reliability=item.get("reliability", "secondary"),
        )
        sources.append(src.model_dump())
        next_id += 1

    write_jsonl(paths["sources"], sources)

    # Back-fill: attach supporting source ids onto the relations they cite.
    rel_to_sources: Dict[str, List[str]] = {}
    for s in sources:
        for fid in s["supports"]:
            rel_to_sources.setdefault(fid, []).append(s["source_id"])
    for r in relations:
        r["source_ids"] = rel_to_sources.get(r["relation_id"], [])
    write_jsonl(paths["relations"], relations)

    print(f"[stage5] sources -> {paths['sources']} ({len(sources)})")
    return paths["sources"]
