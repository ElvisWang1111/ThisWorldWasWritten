"""Stage 7: render Wikipedia-style pages from the hidden world.

One page is produced per entity. The renderer assembles the relevant slice of
the hidden world (relations, events, sources) for an entity, asks the LLM to
write an encyclopedic page grounded only in those facts, then resolves the
[[internal links]] and {cite:src} markers into structured fields.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from . import schemas
from .llm_client import LLMClient
from .utils import load_prompt, make_id, read_json, read_jsonl, write_jsonl

SYSTEM = (
    "You are an encyclopedia editor writing neutral, dry, factual entries about "
    "a fictional world. You never invent facts beyond those provided and you "
    "always return valid JSON."
)

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_CITE_RE = re.compile(r"\{cite:(src_\d+)\}")

# Suggested section sets per entity type, to push the model toward richer,
# type-appropriate articles (a city must not read like a biography).
_SECTION_GUIDANCE: Dict[str, str] = {
    "country": "History; Geography; Government and politics; Economy; "
               "Demographics; Culture; Administrative divisions",
    "region": "History; Geography; Economy; Administration; Notable places; Culture",
    "city": "History; Geography and climate; Government; Economy; "
            "Demographics; Culture and landmarks; Transport",
    "river": "Course; Geography; History and use; Settlements along it; Ecology",
    "mountain": "Geography; Geology; History; Access and notable features",
    "person": "Early life; Career; Major contributions; Later life and death; Legacy",
    "institution": "History; Organization and structure; Activities and role; "
                   "Notable members; Controversies",
    "university": "History; Campus; Academics and faculties; Notable people; Reputation",
    "company": "History; Operations; Products and services; Finances; Controversies",
    "newspaper": "History; Editorial stance; Circulation and reach; Notable coverage",
    "political_party": "History; Ideology and platform; Organization; "
                       "Electoral history; Notable figures",
    "law": "Background; Provisions; Passage; Effects; Later amendments",
    "treaty": "Background; Negotiation; Terms; Signatories; Aftermath and legacy",
    "conflict": "Background; Course of events; Key participants; Outcome; Aftermath",
    "cultural_group": "Origins; Language and customs; Distribution; History; "
                      "Contemporary status",
    "technology": "Background; Development; Description; Adoption and impact",
    "book": "Background; Content and themes; Publication; Reception and influence",
    "artwork": "Description; Background and creation; Provenance; Reception",
    "political_crisis": "Background; Course of events; Key participants; "
                        "Resolution; Aftermath",
}
_DEFAULT_GUIDANCE = "History; Overview; Significance; Legacy"


def _world_context(bible: Dict[str, Any]) -> str:
    """A compact slice of the world bible to ground richer prose."""
    keys = (
        "world_name", "main_country", "geography", "political_structure",
        "economic_structure", "cultural_traits", "historical_periods",
        "naming_conventions",
    )
    slim = {k: bible[k] for k in keys if k in bible}
    return json.dumps(slim, ensure_ascii=False)[:2500]


def _paths(cfg: Dict[str, Any]) -> Dict[str, Path]:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    wiki = PROJECT_ROOT / cfg.get("paths", {}).get("wiki_dir", "data/wiki")
    return {
        "entities": world / "entities.jsonl",
        "events": world / "events.jsonl",
        "relations": world / "relations.jsonl",
        "sources": world / "sources.jsonl",
        "bible": world / "world_bible.json",
        "pages": wiki / "pages.jsonl",
        "links": wiki / "links.jsonl",
        "categories": wiki / "categories.jsonl",
        "references": wiki / "references.jsonl",
    }


def _facts_for_entity(
    entity: Dict[str, Any],
    relations: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
    ent_by_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    eid = entity["entity_id"]
    rel_slice = [
        {
            "relation_id": r["relation_id"],
            "subject": ent_by_id.get(r["subject_id"], {}).get("name", r["subject_id"]),
            "predicate": r["predicate"],
            "object": ent_by_id.get(r["object_id"], {}).get("name", r["object_id"]),
            "start_date": r.get("start_date"),
            "source_ids": r.get("source_ids", []),
        }
        for r in relations
        if r["subject_id"] == eid or r["object_id"] == eid
    ]
    evt_slice = [
        {
            "event_id": e["event_id"],
            "name": e["name"],
            "event_type": e["event_type"],
            "start_date": e.get("start_date"),
            "end_date": e.get("end_date"),
            "outcome": e.get("outcome", ""),
            "description": e.get("description", ""),
        }
        for e in events
        if eid in e.get("participant_ids", []) or eid in e.get("location_ids", [])
    ]
    cited_ids = {sid for r in rel_slice for sid in r["source_ids"]}
    evt_ids = {e["event_id"] for e in evt_slice}
    src_slice = [
        {
            "source_id": s["source_id"],
            "title": s["title"],
            "source_type": s["source_type"],
            "author": s.get("author"),
            "publication_year": s.get("publication_year"),
            "reliability": s.get("reliability"),
        }
        for s in sources
        if s["source_id"] in cited_ids
        or any(f in evt_ids or f in {r["relation_id"] for r in rel_slice}
               for f in s.get("supports", []))
    ]
    return {"relations": rel_slice, "events": evt_slice, "sources": src_slice}


def _render_one_page(
    ent: Dict[str, Any],
    page_id: str,
    *,
    llm: LLMClient,
    relations: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
    ent_by_id: Dict[str, Dict[str, Any]],
    world_context: str,
    title_to_page: Dict[str, str],
    candidate_titles: List[str],
    src_ids: set,
    lengths: Dict[str, int],
) -> Dict[str, Any] | None:
    """Render a single entity into a WikiPage dict (or None on failure)."""
    facts = _facts_for_entity(ent, relations, events, sources, ent_by_id)
    candidates = [t for t in candidate_titles if t != ent["name"]][:40]
    page_type = ent["entity_type"]
    prompt = load_prompt("render_wiki_page.md").format(
        entity_json=json.dumps(ent, ensure_ascii=False),
        world_context=world_context,
        facts_json=json.dumps(facts, ensure_ascii=False),
        link_candidates=", ".join(candidates) or "(none)",
        page_type=page_type,
        section_guidance=_SECTION_GUIDANCE.get(page_type, _DEFAULT_GUIDANCE),
        min_sections=lengths["min_sections"],
        max_sections=lengths["max_sections"],
        min_paras=lengths["min_paras"],
        max_paras=lengths["max_paras"],
    )
    try:
        data = llm.complete_json(SYSTEM, prompt, max_tokens=lengths["max_tokens"])
    except Exception as exc:  # noqa: BLE001 - skip a page rather than abort
        print(f"[render] WARN: failed to render '{ent['name']}': {exc}")
        return None

    sections = [
        schemas.PageSection(
            heading=s.get("heading", "Section"),
            content=s.get("content", ""),
        ).model_dump()
        for s in data.get("sections", [])
    ]

    all_text = " ".join(s["content"] for s in sections) + " " + data.get("summary", "")
    linked_titles = set(_LINK_RE.findall(all_text)) | set(
        data.get("internal_link_titles", [])
    )
    internal_links: List[str] = []
    for t in linked_titles:
        pid = title_to_page.get(t.strip().lower())
        if pid and pid != page_id and pid not in internal_links:
            internal_links.append(pid)

    cited = set(_CITE_RE.findall(all_text)) | set(data.get("reference_ids", []))
    reference_ids = [c for c in cited if c in src_ids]

    page = schemas.WikiPage(
        page_id=page_id,
        title=ent["name"],
        entity_id=ent["entity_id"],
        page_type=ent["entity_type"],
        summary=data.get("summary", ""),
        sections=sections,
        infobox=data.get("infobox", {}) or {},
        internal_links=internal_links,
        categories=data.get("categories", []) or [],
        reference_ids=reference_ids,
    )
    return page.model_dump()


def render_wiki_pages(
    cfg: Dict[str, Any],
    llm: LLMClient,
    only_entity_ids: set | None = None,
    incremental: bool = False,
) -> Path:
    """Render wiki pages from the hidden world.

    By default renders every entity (up to the page cap) from scratch. With
    ``incremental=True`` only entities that do not yet have a page are rendered
    and existing pages are kept. With ``only_entity_ids`` exactly those entities
    are (re)rendered and merged in. Page ids are stable across runs.
    """
    paths = _paths(cfg)
    entities = read_jsonl(paths["entities"])
    relations = read_jsonl(paths["relations"])
    events = read_jsonl(paths["events"])
    sources = read_jsonl(paths["sources"])
    bible = read_json(paths["bible"]) if paths["bible"].exists() else {}
    ent_by_id = {e["entity_id"]: e for e in entities}
    world_context = _world_context(bible)
    src_ids = {s["source_id"] for s in sources}

    lengths = {
        "min_sections": int(cfg.get("render", {}).get("min_sections", 4)),
        "max_sections": int(cfg.get("render", {}).get("max_sections", 7)),
        "min_paras": int(cfg.get("render", {}).get("min_paragraphs", 2)),
        "max_paras": int(cfg.get("render", {}).get("max_paragraphs", 4)),
        "max_tokens": int(cfg.get("render", {}).get("max_tokens", 6000)),
    }

    existing_pages = read_jsonl(paths["pages"])
    entity_pageid = {
        p["entity_id"]: p["page_id"] for p in existing_pages if p.get("entity_id")
    }
    used_nums = [
        int(p["page_id"].split("_")[1])
        for p in existing_pages
        if p.get("page_id", "").startswith("page_")
    ]
    next_num = max(used_nums, default=0) + 1

    max_pages = int(cfg.get("scale", {}).get("num_wiki_pages", len(entities)))
    candidate_entities = entities[:max_pages]
    candidate_ids = {e["entity_id"] for e in candidate_entities}
    # The page cap applies only to a full from-scratch render. Incremental and
    # explicit (contribution) renders must reach entities appended past the cap,
    # otherwise new content never gets a page.
    if only_entity_ids or incremental:
        for e in entities:
            eid = e["entity_id"]
            if eid in candidate_ids:
                continue
            wanted = eid in only_entity_ids if only_entity_ids else eid not in entity_pageid
            if wanted:
                candidate_entities.append(e)
                candidate_ids.add(eid)

    # Decide which entities to (re)render.
    if only_entity_ids is not None:
        to_render = [e for e in candidate_entities
                     if e["entity_id"] in only_entity_ids]
    elif incremental:
        to_render = [e for e in candidate_entities
                     if e["entity_id"] not in entity_pageid]
    else:
        to_render = candidate_entities

    # Assign/reuse page ids and build a corpus-wide title -> page_id index so
    # internal links resolve to both existing and newly created pages.
    title_to_page: Dict[str, str] = {
        p["title"].strip().lower(): p["page_id"] for p in existing_pages
    }
    for e in to_render:
        eid = e["entity_id"]
        if eid not in entity_pageid:
            entity_pageid[eid] = make_id("page", next_num)
            next_num += 1
        title_to_page[e["name"].strip().lower()] = entity_pageid[eid]

    candidate_titles = [
        e["name"] for e in candidate_entities if e["entity_id"] in entity_pageid
    ]

    rendered: Dict[str, Dict[str, Any]] = {}
    for ent in to_render:
        page = _render_one_page(
            ent, entity_pageid[ent["entity_id"]],
            llm=llm, relations=relations, events=events, sources=sources,
            ent_by_id=ent_by_id, world_context=world_context,
            title_to_page=title_to_page, candidate_titles=candidate_titles,
            src_ids=src_ids, lengths=lengths,
        )
        if page:
            rendered[ent["entity_id"]] = page
            print(f"[render] {page['page_id']}: {ent['name']}")

    # Merge: keep existing pages (re-rendered ones replaced), append new ones.
    pages: List[Dict[str, Any]] = []
    seen: set = set()
    for p in existing_pages:
        eid = p.get("entity_id")
        pages.append(rendered.get(eid, p) if eid in rendered else p)
        if eid:
            seen.add(eid)
    for ent in to_render:
        eid = ent["entity_id"]
        if eid in rendered and eid not in seen:
            pages.append(rendered[eid])
            seen.add(eid)

    write_jsonl(paths["pages"], pages)

    # Side tables for convenient querying / validation.
    links = [
        {"from_page": p["page_id"], "to_page": tp}
        for p in pages
        for tp in p["internal_links"]
    ]
    write_jsonl(paths["links"], links)

    cat_map: Dict[str, List[str]] = {}
    for p in pages:
        for c in p["categories"]:
            cat_map.setdefault(c, []).append(p["page_id"])
    write_jsonl(
        paths["categories"],
        [{"category": c, "page_ids": ids} for c, ids in sorted(cat_map.items())],
    )

    refs = [
        {"page_id": p["page_id"], "reference_ids": p["reference_ids"]}
        for p in pages
        if p["reference_ids"]
    ]
    write_jsonl(paths["references"], refs)

    print(f"[stage7] pages -> {paths['pages']} ({len(pages)})")
    return paths["pages"]
