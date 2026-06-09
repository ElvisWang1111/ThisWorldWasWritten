"""World clock and tensions: the evolving state of the civilization.

Each evolution tick advances ``current_year`` by ``years_per_tick`` and updates
the list of open tensions (unresolved disputes, power vacuums, crises) that
give the world's history direction across ticks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .utils import parse_year, read_json, read_jsonl, write_json

DEFAULT_START_YEAR = 1950
DEFAULT_YEARS_PER_TICK = 25


def _state_path(cfg: Dict[str, Any]) -> Path:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    return world / "world_state.json"


def _events_path(cfg: Dict[str, Any]) -> Path:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    return world / "events.jsonl"


def load_state(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Load world_state.json, seeding it from config/defaults if absent."""
    path = _state_path(cfg)
    if path.exists():
        return read_json(path)

    ws_cfg = cfg.get("world_state", {})
    start = int(ws_cfg.get("start_year", DEFAULT_START_YEAR))
    # If events already exist past the configured start, begin after them.
    latest = _latest_event_year(cfg)
    current = max(start, latest) if latest else start
    state = {
        "current_year": current,
        "years_per_tick": int(ws_cfg.get("years_per_tick", DEFAULT_YEARS_PER_TICK)),
        "tick": 0,
        "open_tensions": [],
    }
    save_state(cfg, state)
    return state


def save_state(cfg: Dict[str, Any], state: Dict[str, Any]) -> None:
    write_json(_state_path(cfg), state)


def _latest_event_year(cfg: Dict[str, Any]) -> int | None:
    years = [
        parse_year(e.get("end_date") or e.get("start_date"))
        for e in read_jsonl(_events_path(cfg))
    ]
    years = [y for y in years if y is not None]
    return max(years) if years else None


def advance_clock(state: Dict[str, Any], years: int | None = None) -> int:
    """Advance the clock by ``years`` (or years_per_tick). Returns target year."""
    step = int(years) if years else int(state.get("years_per_tick", DEFAULT_YEARS_PER_TICK))
    target = int(state.get("current_year", DEFAULT_START_YEAR)) + step
    state["current_year"] = target
    state["tick"] = int(state.get("tick", 0)) + 1
    return target


def update_tensions(
    state: Dict[str, Any],
    new_tensions: List[str],
    resolved_tensions: List[str],
) -> None:
    """Apply a tick's tension changes: drop resolved, add new (deduped)."""
    open_now: List[str] = list(state.get("open_tensions", []))
    resolved_lower = {t.strip().lower() for t in resolved_tensions or []}
    open_now = [t for t in open_now if t.strip().lower() not in resolved_lower]
    existing = {t.strip().lower() for t in open_now}
    for t in new_tensions or []:
        if t and t.strip().lower() not in existing:
            open_now.append(t.strip())
            existing.add(t.strip().lower())
    state["open_tensions"] = open_now
