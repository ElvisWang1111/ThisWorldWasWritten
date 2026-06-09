import json
from pathlib import Path

import pytest


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


@pytest.fixture
def world(tmp_path, monkeypatch):
    from synthetic_world import utils
    monkeypatch.setattr(utils, "PROJECT_ROOT", tmp_path)
    return tmp_path


CFG = {"paths": {"world_dir": "data/world"}}


def test_repair_temporal_fixes_existence_and_death(world):
    from synthetic_world.repair import repair_temporal
    from synthetic_world.utils import read_jsonl

    base = world / "data" / "world"
    _write_jsonl(base / "entities.jsonl", [
        {"entity_id": "ent_000001", "name": "Board", "entity_type": "institution",
         "founded_date": "1950"},
        {"entity_id": "ent_000002", "name": "Vic", "entity_type": "person",
         "birth_date": "1800", "death_date": "1842"},
    ])
    _write_jsonl(base / "events.jsonl", [
        {"event_id": "evt_000001", "name": "Flood", "event_type": "natural_disaster",
         "start_date": "1900", "participant_ids": ["ent_000001"]},
        {"event_id": "evt_000002", "name": "Assassination", "event_type": "assassination",
         "start_date": "1888", "participant_ids": ["ent_000002"]},
    ])

    fixes = repair_temporal(CFG)
    assert len(fixes) == 2

    ents = {e["name"]: e for e in read_jsonl(base / "entities.jsonl")}
    assert ents["Board"]["founded_date"] == "1900"   # moved back to participation
    assert ents["Vic"]["death_date"] == "1888"       # moved forward past death


def test_repair_temporal_noop_when_consistent(world):
    from synthetic_world.repair import repair_temporal

    base = world / "data" / "world"
    _write_jsonl(base / "entities.jsonl", [
        {"entity_id": "ent_000001", "name": "Board", "entity_type": "institution",
         "founded_date": "1850"},
    ])
    _write_jsonl(base / "events.jsonl", [
        {"event_id": "evt_000001", "name": "Flood", "event_type": "natural_disaster",
         "start_date": "1900", "participant_ids": ["ent_000001"]},
    ])
    assert repair_temporal(CFG) == []
