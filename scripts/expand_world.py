#!/usr/bin/env python3
"""Broaden the world into a multi-country region (reuses the contribution engine).

Adds neighboring countries around the existing main country, each with a couple
of cities and at least one cross-border event (war, treaty, trade pact), so the
world stops being a single isolated country.

    python scripts/expand_world.py --countries 3
    python scripts/expand_world.py --countries 2 --no-build
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

TEMPLATE = (
    "Broaden the world beyond its single main country into a coherent region or "
    "continent. Add {n} new neighboring sovereign countries that fit the world "
    "bible's naming conventions and geography. For EACH new country add: 1-2 "
    "cities, one notable historical figure, and one institution. Then add "
    "cross-border history connecting them to the existing country and to each "
    "other: at least one war or border conflict, one treaty that resolves a "
    "conflict, and one trade or alliance relationship. Reflect realistic "
    "asymmetry — the countries should differ in size, government and outlook, "
    "and some relationships should be tense or contested. Add fictional sources "
    "for the most important new events."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand into a multi-country world.")
    parser.add_argument("--config", default="configs/world_config.yaml")
    parser.add_argument("--countries", type=int, default=3,
                        help="Number of new neighboring countries to add.")
    parser.add_argument("--rerender-all", action="store_true",
                        help="Also re-render existing pages so they link to the "
                             "new countries (slower, more LLM calls).")
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    from synthetic_world.contribute import apply_contribution
    from synthetic_world.llm_client import LLMConfig, LLMClient
    from synthetic_world.renderers import render_event_pages, render_wiki_pages
    from synthetic_world.repair import repair_temporal
    from synthetic_world.site_builder import build_site
    from synthetic_world.utils import load_config
    from synthetic_world.validators import validate_world

    cfg = load_config(args.config)
    llm = LLMClient(LLMConfig.from_dict(cfg.get("generation", {})))

    submission = TEMPLATE.format(n=args.countries)
    result = apply_contribution(cfg, llm, submission)
    print(f"[expand] {result['summary']}")

    fixes = repair_temporal(cfg)
    if fixes:
        print(f"[expand] auto-repaired {len(fixes)} temporal issue(s)")

    report = validate_world(cfg, include_wiki=False)
    s = report.to_dict()["summary"]
    print(f"[expand] validation: {s['errors']} errors, {s['warnings']} warnings")

    if not args.no_render:
        if args.rerender_all:
            # Weave the new countries into existing articles' links too.
            render_wiki_pages(cfg, llm)
            render_event_pages(cfg, llm)
        else:
            # Cheaper: render only the new entities' and events' pages.
            if result["new_entity_ids"]:
                render_wiki_pages(cfg, llm, only_entity_ids=set(result["new_entity_ids"]))
            if result.get("new_event_ids"):
                render_event_pages(cfg, llm, only_event_ids=set(result["new_event_ids"]))

    if not args.no_build:
        out = build_site(cfg)
        print(f"[expand] site rebuilt -> {out}")


if __name__ == "__main__":
    main()
