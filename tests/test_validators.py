import json
from pathlib import Path

import pytest

from synthetic_world import validators


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


@pytest.fixture
def world(tmp_path, monkeypatch):
    """Point the validator's PROJECT_ROOT at a temp dir with a tiny world."""
    # _world_paths resolves against utils.PROJECT_ROOT, so patch that.
    from synthetic_world import utils
    monkeypatch.setattr(utils, "PROJECT_ROOT", tmp_path)

    world = tmp_path / "data" / "world"
    wiki = tmp_path / "data" / "wiki"
    (world).mkdir(parents=True)
    (wiki).mkdir(parents=True)
    (world / "world_bible.json").write_text("{}", encoding="utf-8")
    return tmp_path


CFG = {
    "validation": {"strict_temporal_check": True, "max_duplicate_name_ratio": 0.5},
    "paths": {"world_dir": "data/world", "wiki_dir": "data/wiki"},
}


def test_clean_world_passes(world):
    base = world / "data" / "world"
    _write_jsonl(base / "entities.jsonl", [
        {"entity_id": "ent_000001", "name": "Velmora", "entity_type": "city",
         "founded_date": "1842"},
        {"entity_id": "ent_000002", "name": "Asteria", "entity_type": "country"},
    ])
    _write_jsonl(base / "events.jsonl", [
        {"event_id": "evt_000001", "name": "Founding", "event_type": "reform",
         "start_date": "1850", "location_ids": ["ent_000001"],
         "participant_ids": [], "cause_event_ids": []},
    ])
    _write_jsonl(base / "relations.jsonl", [
        {"relation_id": "rel_000001", "subject_id": "ent_000001",
         "predicate": "located_in", "object_id": "ent_000002", "source_ids": []},
    ])
    _write_jsonl(base / "sources.jsonl", [])
    report = validators.validate_world(CFG, include_wiki=False)
    assert report.to_dict()["summary"]["errors"] == 0


def test_broken_relation_id_detected(world):
    base = world / "data" / "world"
    _write_jsonl(base / "entities.jsonl", [
        {"entity_id": "ent_000001", "name": "Velmora", "entity_type": "city"},
    ])
    _write_jsonl(base / "events.jsonl", [])
    _write_jsonl(base / "relations.jsonl", [
        {"relation_id": "rel_000001", "subject_id": "ent_000001",
         "predicate": "located_in", "object_id": "ent_999999", "source_ids": []},
    ])
    _write_jsonl(base / "sources.jsonl", [])
    report = validators.validate_world(CFG, include_wiki=False)
    checks = {f.check for f in report.errors}
    assert "broken_id" in checks


def test_temporal_violation_detected(world):
    base = world / "data" / "world"
    _write_jsonl(base / "entities.jsonl", [
        {"entity_id": "ent_000001", "name": "Mara Veil", "entity_type": "person",
         "birth_date": "1900", "death_date": "1880"},
    ])
    _write_jsonl(base / "events.jsonl", [])
    _write_jsonl(base / "relations.jsonl", [])
    _write_jsonl(base / "sources.jsonl", [])
    report = validators.validate_world(CFG, include_wiki=False)
    assert any(f.check == "temporal" for f in report.errors)
