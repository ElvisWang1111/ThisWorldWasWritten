"""Evolution engine: advance the civilization's history by one tick.

A tick moves the world clock forward by a fixed number of years and asks the
model to produce the next layer of history, optionally steered by a contributor
directive. New facts are merged through the same transactional core as manual
contributions; the clock and the list of open tensions are then updated.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from . import world_state as ws
from .contribute import _world_paths, merge_additions
from .llm_client import LLMClient
from .renderers import _world_context
from .utils import load_prompt, read_json, read_jsonl

SYSTEM = (
    "You are the chronicler of a fictional civilization. You only produce "
    "fictional, internally consistent history and always return valid JSON."
)


def advance_world(
    cfg: Dict[str, Any],
    llm: LLMClient,
    directive: Optional[str] = None,
    years: Optional[int] = None,
) -> Dict[str, Any]:
    """Advance history by one tick. ``directive`` optionally steers it.

    Returns a dict with the tick summary, year range, new entity ids and counts.
    """
    paths = _world_paths(cfg)
    state = ws.load_state(cfg)
    current_year = int(state["current_year"])
    target_year = ws.advance_clock(state, years)

    bible = read_json(paths["bible"]) if paths["bible"].exists() else {}
    entities = read_jsonl(paths["entities"])
    events = read_jsonl(paths["events"])

    ent_catalog = "\n".join(
        f"- {e['name']} ({e['entity_type']})" for e in entities
    ) or "(none)"
    evt_catalog = "\n".join(f"- {e['name']}" for e in events) or "(none)"
    tensions = state.get("open_tensions", [])
    tensions_str = "\n".join(f"- {t}" for t in tensions) or "(none yet)"

    prompt = load_prompt("evolve_world.md").format(
        current_year=current_year,
        target_year=target_year,
        world_context=_world_context(bible),
        open_tensions=tensions_str,
        entity_catalog=ent_catalog[:6000],
        event_catalog=evt_catalog[:3000],
        directive=(directive or "").strip() or "(none — evolve autonomously)",
    )
    max_tokens = max(int(cfg.get("generation", {}).get("max_tokens", 8192)), 8192)
    data = llm.complete_json(SYSTEM, prompt, max_tokens=max_tokens)

    cause = f"evolution_tick_{state['tick']}"
    result = merge_additions(
        cfg, data, cause=cause, note=(directive or "").strip()
    )

    # Update tensions and persist the advanced clock.
    ws.update_tensions(
        state,
        new_tensions=data.get("new_tensions", []) or [],
        resolved_tensions=data.get("resolved_tensions", []) or [],
    )
    ws.save_state(cfg, state)

    # Record the tick in a dedicated chronicle log for the "recent changes" view.
    chronicle = {
        "tick": state["tick"],
        "year_from": current_year,
        "year_to": target_year,
        "directive": (directive or "").strip(),
        "summary": data.get("summary", ""),
        "added": result["counts"],
        "resolved_tensions": data.get("resolved_tensions", []) or [],
        "new_tensions": data.get("new_tensions", []) or [],
    }
    chron_path = paths["contributions"].parent / "chronicle.jsonl"
    chron_path.parent.mkdir(parents=True, exist_ok=True)
    with chron_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(chronicle, ensure_ascii=False) + "\n")

    result.update({
        "tick": state["tick"],
        "year_from": current_year,
        "year_to": target_year,
        "open_tensions": state["open_tensions"],
    })
    print(
        f"[evolve] tick {state['tick']}: {current_year} -> {target_year}; "
        f"+{result['counts']['entities']}e/{result['counts']['events']}ev, "
        f"{len(state['open_tensions'])} open tensions"
    )
    return result
