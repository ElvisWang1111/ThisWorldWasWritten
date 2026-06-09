#!/usr/bin/env python3
"""Stage 7: render Wikipedia-style pages from the hidden world.

    python scripts/render_wiki_pages.py                 # full re-render
    python scripts/render_wiki_pages.py --incremental    # only entities w/o a page
    python scripts/render_wiki_pages.py --incremental --build
"""

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render wiki pages.")
    parser.add_argument("--config", default="configs/world_config.yaml")
    parser.add_argument("--incremental", action="store_true",
                        help="Render only entities that do not yet have a page.")
    parser.add_argument("--build", action="store_true",
                        help="Rebuild the static site afterwards.")
    args = parser.parse_args()

    from synthetic_world.llm_client import LLMClient, LLMConfig
    from synthetic_world.renderers import render_wiki_pages
    from synthetic_world.site_builder import build_site
    from synthetic_world.utils import load_config

    cfg = load_config(args.config)
    llm = LLMClient(LLMConfig.from_dict(cfg.get("generation", {})))

    render_wiki_pages(cfg, llm, incremental=args.incremental)

    if args.build:
        build_site(cfg)


if __name__ == "__main__":
    main()
