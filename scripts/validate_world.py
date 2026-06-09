#!/usr/bin/env python3
"""Stage 6: validate the hidden world (and wiki, if rendered). Writes a report."""

import sys

from _common import load


def main() -> None:
    cfg, _ = load("Validate the hidden world for consistency.")
    from synthetic_world.validators import validate_world

    report = validate_world(cfg)
    summary = report.to_dict()["summary"]
    print(
        f"[stage6] validation: {summary['errors']} errors, "
        f"{summary['warnings']} warnings across "
        f"{summary['total_findings']} findings"
    )
    for f in report.errors[:20]:
        print(f"  ERROR [{f.check}] {f.message}")
    if summary["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
