import json
from pathlib import Path

import pytest


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


class StubLLM:
    """Returns a canned object from complete_json, ignoring the prompt."""

    def __init__(self, payload):
        self.payload = payload

    def complete_json(self, system, user, *, temperature=None, max_tokens=None):
        return self.payload

    def complete_jsonl(self, system, user, *, temperature=None, max_tokens=None):
        return self.payload


@pytest.fixture
def world(tmp_path, monkeypatch):
    import shutil

    from synthetic_world import utils
    # Prompts are resolved via PROJECT_ROOT, so copy them into the temp root.
    real_root = Path(utils.__file__).resolve().parents[2]
    shutil.copytree(real_root / "prompts", tmp_path / "prompts")
    monkeypatch.setattr(utils, "PROJECT_ROOT", tmp_path)
    base = tmp_path / "data" / "world"
    base.mkdir(parents=True)
    (base / "world_bible.json").write_text(
        json.dumps({"world_name": "Asteria"}), encoding="utf-8"
    )
    _write_jsonl(base / "entities.jsonl", [
        {"entity_id": "ent_000001", "name": "Asteria", "entity_type": "country",
         "aliases": [], "attributes": {}},
        {"entity_id": "ent_000002", "name": "Velmora", "entity_type": "city",
         "aliases": [], "attributes": {}},
    ])
    _write_jsonl(base / "events.jsonl", [
        {"event_id": "evt_000001", "name": "Founding", "event_type": "reform",
         "start_date": "1844", "location_ids": [], "participant_ids": [],
         "cause_event_ids": []},
    ])
    _write_jsonl(base / "relations.jsonl", [])
    _write_jsonl(base / "sources.jsonl", [])
    return tmp_path


CFG = {"paths": {"world_dir": "data/world", "feedback_dir": "data/feedback"},
       "validation": {"strict_temporal_check": True}}


def test_contribution_merges_and_assigns_stable_ids(world):
    from synthetic_world.contribute import apply_contribution
    from synthetic_world.utils import read_jsonl

    payload = {
        "summary": "Added the Kingdom of Sarnath and a war.",
        "new_entities": [
            {"name": "Sarnath", "entity_type": "country", "aliases": ["Sarn"],
             "description": "A rival kingdom.", "located_in": None, "attributes": {}},
            {"name": "Port Sarn", "entity_type": "city",
             "description": "Sarnath's main port.", "located_in": "Sarnath",
             "attributes": {}},
        ],
        "new_events": [
            {"name": "The Naval War", "event_type": "war", "start_date": "1910",
             "end_date": "1913", "location_names": ["Port Sarn"],
             "participant_names": ["Asteria", "Sarnath"], "cause_event_names": [],
             "outcome": "Stalemate.", "description": "A naval conflict."},
        ],
        "new_relations": [
            {"subject_name": "Asteria", "predicate": "rival_of",
             "object_name": "Sarnath", "confidence": 1.0},
        ],
        "new_sources": [
            {"title": "Sarn Naval Records", "source_type": "archive",
             "author": None, "publication_year": 1920, "publisher": "Sarn Press",
             "supports_event_names": ["The Naval War"], "reliability": "primary"},
        ],
    }
    result = apply_contribution(CFG, StubLLM(payload), "add a rival kingdom")

    assert result["counts"] == {"entities": 2, "events": 1, "relations": 1,
                                "sources": 1}

    base = world / "data" / "world"
    entities = read_jsonl(base / "entities.jsonl")
    # Ids continue from the existing max (ent_000002 -> 3, 4).
    assert [e["entity_id"] for e in entities[-2:]] == ["ent_000003", "ent_000004"]
    port = next(e for e in entities if e["name"] == "Port Sarn")
    assert port["located_in"] == "ent_000003"  # resolved to the new Sarnath

    events = read_jsonl(base / "events.jsonl")
    war = events[-1]
    assert war["event_id"] == "evt_000002"
    # Participants resolved across existing + new entities.
    assert set(war["participant_ids"]) == {"ent_000001", "ent_000003"}

    relations = read_jsonl(base / "relations.jsonl")
    assert relations[0]["subject_id"] == "ent_000001"
    assert relations[0]["object_id"] == "ent_000003"

    sources = read_jsonl(base / "sources.jsonl")
    assert sources[0]["supports"] == ["evt_000002"]

    # Contribution log written.
    log = read_jsonl(world / "data" / "feedback" / "contributions.jsonl")
    assert log[0]["added"]["entities"] == ["ent_000003", "ent_000004"]


def test_incremental_render_appends_only_new_pages(world, monkeypatch):
    from synthetic_world import renderers
    from synthetic_world.utils import read_jsonl

    cfg = {"paths": {"world_dir": "data/world", "wiki_dir": "data/wiki"},
           "scale": {}, "render": {}, "site": {}}
    wiki = world / "data" / "wiki"
    wiki.mkdir(parents=True)
    # One pre-existing page for ent_000001.
    _write_jsonl(wiki / "pages.jsonl", [
        {"page_id": "page_000001", "title": "Asteria", "entity_id": "ent_000001",
         "page_type": "country", "summary": "old", "sections": [],
         "infobox": {}, "internal_links": [], "categories": ["Countries"],
         "reference_ids": []},
    ])

    page_payload = {"summary": "A city page.", "infobox": {},
                    "sections": [{"heading": "History", "content": "Founded."}],
                    "categories": ["Cities"], "internal_link_titles": [],
                    "reference_ids": []}
    renderers.render_wiki_pages(cfg, StubLLM(page_payload), incremental=True)

    pages = read_jsonl(wiki / "pages.jsonl")
    titles = {p["title"]: p["page_id"] for p in pages}
    # Existing page kept, new page appended with a fresh stable id.
    assert titles["Asteria"] == "page_000001"
    assert "Velmora" in titles
    assert titles["Velmora"] == "page_000002"
