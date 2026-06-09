import json
from pathlib import Path

import pytest


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


class StubLLM:
    def __init__(self, payload):
        self.payload = payload

    def complete_json(self, system, user, *, temperature=None, max_tokens=None):
        return self.payload


@pytest.fixture
def world(tmp_path, monkeypatch):
    import shutil

    from synthetic_world import utils
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
    ])
    _write_jsonl(base / "events.jsonl", [
        {"event_id": "evt_000001", "name": "Founding", "event_type": "reform",
         "start_date": "1844", "location_ids": [], "participant_ids": [],
         "cause_event_ids": []},
    ])
    _write_jsonl(base / "relations.jsonl", [])
    _write_jsonl(base / "sources.jsonl", [])
    return tmp_path


CFG = {
    "paths": {"world_dir": "data/world", "feedback_dir": "data/feedback"},
    "world_state": {"start_year": 1950, "years_per_tick": 25},
}


def test_advance_world_moves_clock_and_tensions(world):
    from synthetic_world.evolve import advance_world
    from synthetic_world.utils import read_json, read_jsonl

    payload = {
        "summary": "A turbulent quarter-century.",
        "new_entities": [
            {"name": "Reform Bloc", "entity_type": "political_party",
             "description": "A new party.", "attributes": {}},
        ],
        "new_events": [
            {"name": "The 1960 Reforms", "event_type": "reform", "start_date": "1960",
             "participant_names": ["Asteria"], "location_names": [],
             "cause_event_names": [], "outcome": "Sweeping changes.",
             "description": "..."},
        ],
        "new_relations": [],
        "new_sources": [],
        "resolved_tensions": [],
        "new_tensions": ["Unresolved dispute over the new reforms"],
    }
    result = advance_world(CFG, StubLLM(payload), directive=None)

    assert result["year_from"] == 1950
    assert result["year_to"] == 1975
    assert result["counts"]["entities"] == 1

    state = read_json(world / "data" / "world" / "world_state.json")
    assert state["current_year"] == 1975
    assert state["tick"] == 1
    assert state["open_tensions"] == ["Unresolved dispute over the new reforms"]

    chronicle = read_jsonl(world / "data" / "feedback" / "chronicle.jsonl")
    assert chronicle[0]["year_to"] == 1975


def test_second_tick_consumes_and_adds_tensions(world):
    from synthetic_world.evolve import advance_world
    from synthetic_world.utils import read_json

    p1 = {"summary": "t1", "new_entities": [], "new_events": [], "new_relations": [],
          "new_sources": [], "resolved_tensions": [], "new_tensions": ["Tension A"]}
    advance_world(CFG, StubLLM(p1), directive=None)

    p2 = {"summary": "t2", "new_entities": [], "new_events": [], "new_relations": [],
          "new_sources": [], "resolved_tensions": ["Tension A"],
          "new_tensions": ["Tension B"]}
    advance_world(CFG, StubLLM(p2), directive="steer it")

    state = read_json(world / "data" / "world" / "world_state.json")
    assert state["current_year"] == 2000  # 1950 + 25 + 25
    assert state["tick"] == 2
    assert state["open_tensions"] == ["Tension B"]  # A resolved, B added
