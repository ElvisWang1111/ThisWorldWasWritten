#!/usr/bin/env python3
"""Advance the civilization's history by one (or more) ticks.

Each tick moves the world clock forward by years_per_tick (default 25) and adds
the next layer of history. A directive is optional — without one the world
evolves autonomously from its open tensions.

    python scripts/evolve.py                          # one autonomous tick
    python scripts/evolve.py --directive "A plague..." # steered tick
    python scripts/evolve.py --file submission.txt      # directive from file
    python scripts/evolve.py --ticks 3 --years 25       # three 25-year ticks
    python scripts/evolve.py --no-build                 # skip site rebuild
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main() -> None:
    parser = argparse.ArgumentParser(description="Advance the world's history.")
    parser.add_argument("--config", default="configs/world_config.yaml")
    parser.add_argument("--directive", default=None, help="Optional steer text.")
    parser.add_argument("--file", help="Read the directive from a file.")
    parser.add_argument("--years", type=int, default=None,
                        help="Years to advance per tick (default: years_per_tick).")
    parser.add_argument("--ticks", type=int, default=1, help="Number of ticks.")
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    directive = args.directive
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
        directive = text or None

    from synthetic_world.evolve import advance_world
    from synthetic_world.llm_client import LLMConfig, LLMClient
    from synthetic_world.renderers import render_event_pages, render_wiki_pages
    from synthetic_world.site_builder import build_site
    from synthetic_world.utils import load_config
    from synthetic_world.validators import validate_world

    cfg = load_config(args.config)
    llm = LLMClient(LLMConfig.from_dict(cfg.get("generation", {})))

    all_new_ids: list[str] = []
    all_new_event_ids: list[str] = []
    for _ in range(max(1, args.ticks)):
        result = advance_world(cfg, llm, directive=directive, years=args.years)
        print(f"[evolve] {result['summary']}")
        all_new_ids.extend(result["new_entity_ids"])
        all_new_event_ids.extend(result.get("new_event_ids", []))
        # A directive applies to the first tick only; later ticks are autonomous.
        directive = None

    report = validate_world(cfg, include_wiki=False)
    s = report.to_dict()["summary"]
    print(f"[evolve] validation: {s['errors']} errors, {s['warnings']} warnings")

    if not args.no_render and all_new_ids:
        render_wiki_pages(cfg, llm, only_entity_ids=set(all_new_ids))
    if not args.no_render and all_new_event_ids:
        render_event_pages(cfg, llm, only_event_ids=set(all_new_event_ids))

    if not args.no_build:
        out = build_site(cfg)
        print(f"[evolve] site rebuilt -> {out}")


if __name__ == "__main__":
    main()
