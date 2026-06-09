#!/usr/bin/env python3
"""Submit a contribution: expand the world from free text, then render + build.

Examples:
    python scripts/contribute.py "Add a rival country, the Kingdom of Sarnath,
        that fought a naval war with Asteria in the 1910s."
    python scripts/contribute.py --file submission.txt --no-build
    echo "..." | python scripts/contribute.py --stdin
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
    parser = argparse.ArgumentParser(description="Expand the world from a submission.")
    parser.add_argument("text", nargs="*", help="Submission text.")
    parser.add_argument("--config", default="configs/world_config.yaml")
    parser.add_argument("--file", help="Read submission from a file.")
    parser.add_argument("--stdin", action="store_true", help="Read submission from stdin.")
    parser.add_argument("--no-render", action="store_true",
                        help="Do not render pages for new entities.")
    parser.add_argument("--no-build", action="store_true",
                        help="Do not rebuild the static site.")
    parser.add_argument("--rerender-all", action="store_true",
                        help="Re-render every page (not just new ones) so existing "
                             "pages can link to the new content.")
    args = parser.parse_args()

    if args.file:
        submission = Path(args.file).read_text(encoding="utf-8")
    elif args.stdin:
        submission = sys.stdin.read()
    else:
        submission = " ".join(args.text)
    submission = submission.strip()
    if not submission:
        parser.error("No submission text provided.")

    from synthetic_world.contribute import apply_contribution
    from synthetic_world.llm_client import LLMConfig, LLMClient
    from synthetic_world.renderers import render_wiki_pages
    from synthetic_world.repair import repair_temporal
    from synthetic_world.site_builder import build_site
    from synthetic_world.utils import load_config
    from synthetic_world.validators import validate_world

    cfg = load_config(args.config)
    llm = LLMClient(LLMConfig.from_dict(cfg.get("generation", {})))

    result = apply_contribution(cfg, llm, submission)
    print(f"[contribute] {result['summary']}")

    fixes = repair_temporal(cfg)
    if fixes:
        print(f"[contribute] auto-repaired {len(fixes)} temporal issue(s)")

    report = validate_world(cfg, include_wiki=False)
    s = report.to_dict()["summary"]
    print(f"[contribute] validation: {s['errors']} errors, {s['warnings']} warnings")

    if not args.no_render and result["new_entity_ids"]:
        if args.rerender_all:
            render_wiki_pages(cfg, llm)
        else:
            render_wiki_pages(
                cfg, llm, only_entity_ids=set(result["new_entity_ids"])
            )

    if not args.no_build:
        out = build_site(cfg)
        print(f"[contribute] site rebuilt -> {out}")


if __name__ == "__main__":
    main()
