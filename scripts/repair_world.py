#!/usr/bin/env python3
"""Deterministically repair mechanical inconsistencies, then re-validate.

No LLM/API key required. Currently fixes temporal contradictions (an entity
participating in an event before it exists or after it died).

    python scripts/repair_world.py
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Repair the hidden world.")
    parser.add_argument("--config", default="configs/world_config.yaml")
    args = parser.parse_args()

    from synthetic_world.repair import repair_temporal
    from synthetic_world.utils import load_config
    from synthetic_world.validators import validate_world

    cfg = load_config(args.config)
    fixes = repair_temporal(cfg)
    print(f"[repair] applied {len(fixes)} temporal fix(es):")
    for f in fixes:
        print(f"  - {f}")

    report = validate_world(cfg, include_wiki=False)
    s = report.to_dict()["summary"]
    print(f"[repair] validation now: {s['errors']} errors, {s['warnings']} warnings")
    for f in report.errors[:20]:
        print(f"  ERROR [{f.check}] {f.message}")


if __name__ == "__main__":
    main()
