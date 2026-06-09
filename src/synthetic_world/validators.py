"""Rule-based validation of the hidden world and the rendered wiki.

Validation runs before and after rendering and produces a structured report.
Checks are intentionally rule-based (deterministic) rather than LLM-based.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import schemas
from .utils import date_before, read_json, read_jsonl, write_json


@dataclass
class Finding:
    severity: str  # "error" | "warning" | "info"
    check: str
    message: str
    ids: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    findings: List[Finding] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)

    def add(self, severity: str, check: str, message: str, ids: Optional[List[str]] = None) -> None:
        self.findings.append(Finding(severity, check, message, ids or []))

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "total_findings": len(self.findings),
                "counts": self.counts,
                "passed": len(self.errors) == 0,
            },
            "findings": [asdict(f) for f in self.findings],
        }


def _world_paths(cfg: Dict[str, Any]) -> Dict[str, Path]:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    wiki = PROJECT_ROOT / cfg.get("paths", {}).get("wiki_dir", "data/wiki")
    return {
        "bible": world / "world_bible.json",
        "entities": world / "entities.jsonl",
        "events": world / "events.jsonl",
        "relations": world / "relations.jsonl",
        "sources": world / "sources.jsonl",
        "pages": wiki / "pages.jsonl",
        "report": world / "validation_report.json",
    }


def validate_world(cfg: Dict[str, Any], include_wiki: bool = True) -> ValidationReport:
    paths = _world_paths(cfg)
    report = ValidationReport()
    strict_temporal = cfg.get("validation", {}).get("strict_temporal_check", True)

    entities = read_jsonl(paths["entities"])
    events = read_jsonl(paths["events"])
    relations = read_jsonl(paths["relations"])
    sources = read_jsonl(paths["sources"])
    pages = read_jsonl(paths["pages"]) if include_wiki and paths["pages"].exists() else []

    report.counts = {
        "entities": len(entities),
        "events": len(events),
        "relations": len(relations),
        "sources": len(sources),
        "pages": len(pages),
    }

    ent_ids = {e["entity_id"] for e in entities}
    evt_ids = {e["event_id"] for e in events}
    src_ids = {s["source_id"] for s in sources}
    rel_ids = {r["relation_id"] for r in relations}
    page_ids = {p["page_id"] for p in pages}
    ent_by_id = {e["entity_id"]: e for e in entities}

    _check_schema(report, entities, events, relations, sources, pages)
    _check_duplicate_names(report, entities, cfg)
    _check_entity_dates(report, entities, strict_temporal)
    _check_event_dates(report, events, strict_temporal)
    _check_id_references(report, entities, events, relations, sources,
                         ent_ids, evt_ids, src_ids, rel_ids)
    _check_temporal_relations(report, events, ent_by_id, strict_temporal)
    _check_citations(report, sources, rel_ids, evt_ids)
    if pages:
        _check_pages(report, pages, page_ids, src_ids, ent_ids)

    write_json(paths["report"], report.to_dict())
    return report


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_schema(report, entities, events, relations, sources, pages) -> None:
    collections = {
        "entities": (entities, schemas.Entity),
        "events": (events, schemas.Event),
        "relations": (relations, schemas.Relation),
        "sources": (sources, schemas.Source),
        "pages": (pages, schemas.WikiPage),
    }
    for name, (rows, model) in collections.items():
        for i, row in enumerate(rows):
            try:
                model(**row)
            except Exception as exc:  # noqa: BLE001
                report.add("error", "schema",
                           f"{name}[{i}] failed schema validation: {exc}")


def _check_duplicate_names(report, entities, cfg) -> None:
    seen: Dict[str, str] = {}
    dupes = 0
    for e in entities:
        key = e["name"].strip().lower()
        if key in seen:
            dupes += 1
            report.add("warning", "duplicate_name",
                       f"Duplicate entity name '{e['name']}'",
                       [seen[key], e["entity_id"]])
        else:
            seen[key] = e["entity_id"]
    if entities:
        ratio = dupes / len(entities)
        max_ratio = cfg.get("validation", {}).get("max_duplicate_name_ratio", 0.02)
        if ratio > max_ratio:
            report.add("error", "duplicate_name",
                       f"Duplicate name ratio {ratio:.3f} exceeds max {max_ratio}")


def _check_entity_dates(report, entities, strict) -> None:
    for e in entities:
        if date_before(e.get("death_date"), e.get("birth_date")):
            report.add("error", "temporal",
                       f"{e['name']}: death_date before birth_date",
                       [e["entity_id"]])


def _check_event_dates(report, events, strict) -> None:
    for e in events:
        if date_before(e.get("end_date"), e.get("start_date")):
            report.add("error", "temporal",
                       f"Event '{e['name']}': end_date before start_date",
                       [e["event_id"]])


def _check_id_references(report, entities, events, relations, sources,
                         ent_ids, evt_ids, src_ids, rel_ids) -> None:
    for e in entities:
        loc = e.get("located_in")
        if loc and loc not in ent_ids:
            report.add("error", "broken_id",
                       f"{e['name']}: located_in '{loc}' does not exist",
                       [e["entity_id"]])
    for ev in events:
        for lid in ev.get("location_ids", []):
            if lid not in ent_ids:
                report.add("error", "broken_id",
                           f"Event '{ev['name']}': location {lid} missing",
                           [ev["event_id"]])
        for pid in ev.get("participant_ids", []):
            if pid not in ent_ids:
                report.add("error", "broken_id",
                           f"Event '{ev['name']}': participant {pid} missing",
                           [ev["event_id"]])
        for cid in ev.get("cause_event_ids", []):
            if cid not in evt_ids:
                report.add("error", "broken_id",
                           f"Event '{ev['name']}': cause {cid} missing",
                           [ev["event_id"]])
    for r in relations:
        if r["subject_id"] not in ent_ids:
            report.add("error", "broken_id",
                       f"Relation {r['relation_id']}: subject missing",
                       [r["relation_id"]])
        if r["object_id"] not in ent_ids:
            report.add("error", "broken_id",
                       f"Relation {r['relation_id']}: object missing",
                       [r["relation_id"]])
        for sid in r.get("source_ids", []):
            if sid not in src_ids:
                report.add("warning", "broken_id",
                           f"Relation {r['relation_id']}: source {sid} missing",
                           [r["relation_id"]])


def _check_temporal_relations(report, events, ent_by_id, strict) -> None:
    """People/institutions cannot participate before they exist."""
    for ev in events:
        start = ev.get("start_date")
        for pid in ev.get("participant_ids", []):
            ent = ent_by_id.get(pid)
            if not ent:
                continue
            born = ent.get("birth_date") or ent.get("founded_date")
            died = ent.get("death_date")
            if date_before(start, born):
                report.add(
                    "error" if strict else "warning", "temporal",
                    f"'{ent['name']}' participates in '{ev['name']}' before "
                    f"existing ({start} < {born})",
                    [ev["event_id"], pid])
            if died and date_before(died, start):
                report.add(
                    "error" if strict else "warning", "temporal",
                    f"'{ent['name']}' participates in '{ev['name']}' after "
                    f"death ({start} > {died})",
                    [ev["event_id"], pid])


def _check_citations(report, sources, rel_ids, evt_ids) -> None:
    fact_ids = rel_ids | evt_ids
    for s in sources:
        for fid in s.get("supports", []):
            if fid not in fact_ids:
                report.add("warning", "citation",
                           f"Source '{s['title']}' supports unknown fact {fid}",
                           [s["source_id"]])


def _check_pages(report, pages, page_ids, src_ids, ent_ids) -> None:
    for p in pages:
        for lid in p.get("internal_links", []):
            if lid not in page_ids:
                report.add("warning", "broken_link",
                           f"Page '{p['title']}': link {lid} missing",
                           [p["page_id"]])
        for rid in p.get("reference_ids", []):
            if rid not in src_ids:
                report.add("warning", "citation",
                           f"Page '{p['title']}': reference {rid} missing",
                           [p["page_id"]])
        eid = p.get("entity_id")
        if eid and eid not in ent_ids:
            report.add("error", "broken_id",
                       f"Page '{p['title']}': entity {eid} missing",
                       [p["page_id"]])
