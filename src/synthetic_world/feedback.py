"""Human feedback loop helpers (Section 9 of the README).

For the MVP this just appends structured critique records. A future repair
agent (prompts/repair_world_from_feedback.md) consumes these to fix the hidden
world rather than the visible page.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from . import schemas
from .utils import make_id, read_jsonl


def _feedback_path(cfg: Dict[str, Any]) -> Path:
    from .utils import PROJECT_ROOT

    d = PROJECT_ROOT / cfg.get("paths", {}).get("feedback_dir", "data/feedback")
    return d / "human_critiques.jsonl"


def add_feedback(
    cfg: Dict[str, Any],
    page_id: str,
    human_label: str,
    reasons: List[str],
    suggested_fix: str = "",
) -> schemas.Feedback:
    path = _feedback_path(cfg)
    existing = read_jsonl(path)
    fb = schemas.Feedback(
        feedback_id=make_id("feedback", len(existing) + 1),
        page_id=page_id,
        human_label=human_label,
        reasons=reasons,
        suggested_fix=suggested_fix,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        import json

        fh.write(json.dumps(fb.model_dump(), ensure_ascii=False) + "\n")
    return fb
