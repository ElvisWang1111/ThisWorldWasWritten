#!/usr/bin/env python3
"""Run the full generation pipeline end to end.

Stages:
  1. world bible        5. sources
  2. entities           6. validate (hidden world)
  3. events             7. render wiki pages
  4. relations          8. validate (with wiki) + build static site

Use --start / --stop to run a subrange, e.g. resume from rendering:
  python scripts/run_pipeline.py --start 7
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
    parser = argparse.ArgumentParser(description="Run the synthetic wiki pipeline.")
    parser.add_argument("--config", default="configs/world_config.yaml")
    parser.add_argument("--start", type=int, default=1, help="First stage (1-8).")
    parser.add_argument("--stop", type=int, default=8, help="Last stage (1-8).")
    parser.add_argument(
        "--skip-build", action="store_true", help="Skip static site build."
    )
    args = parser.parse_args()

    from synthetic_world.generators import (
        generate_entities,
        generate_events,
        generate_relations,
        generate_sources,
        generate_world_bible,
    )
    from synthetic_world.llm_client import LLMClient, LLMConfig
    from synthetic_world.renderers import render_event_pages, render_wiki_pages
    from synthetic_world.site_builder import build_site
    from synthetic_world.utils import load_config
    from synthetic_world.validators import validate_world

    cfg = load_config(args.config)

    def in_range(stage: int) -> bool:
        return args.start <= stage <= args.stop

    llm = None
    if any(in_range(s) for s in (1, 2, 3, 4, 5, 7)):
        llm = LLMClient(LLMConfig.from_dict(cfg.get("generation", {})))

    if in_range(1):
        generate_world_bible(cfg, llm)
    if in_range(2):
        generate_entities(cfg, llm)
    if in_range(3):
        generate_events(cfg, llm)
    if in_range(4):
        generate_relations(cfg, llm)
    if in_range(5):
        generate_sources(cfg, llm)

    if in_range(6):
        report = validate_world(cfg, include_wiki=False)
        s = report.to_dict()["summary"]
        print(f"[stage6] hidden-world validation: {s['errors']} errors, "
              f"{s['warnings']} warnings")
        for f in report.errors[:20]:
            print(f"  ERROR [{f.check}] {f.message}")

    if in_range(7):
        render_wiki_pages(cfg, llm)
        render_event_pages(cfg, llm)

    if in_range(8):
        report = validate_world(cfg, include_wiki=True)
        s = report.to_dict()["summary"]
        print(f"[validate] full validation: {s['errors']} errors, "
              f"{s['warnings']} warnings")
        if not args.skip_build:
            out = build_site(cfg)
            print(f"\nDone. Open {out}/index.html in a browser.")


if __name__ == "__main__":
    main()
