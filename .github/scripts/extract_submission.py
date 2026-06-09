#!/usr/bin/env python3
"""Parse a GitHub issue (or workflow inputs) into an evolution directive + years.

Writes two files for the workflow:
  - submission.txt : the directive (MAY be empty -> autonomous evolution)
  - years.txt      : years to advance (MAY be empty -> use configured default)

Env: ISSUE_BODY (issue form body), INPUT_SUB / INPUT_YEARS (workflow_dispatch).
"""

import os
import re


def parse_sections(body: str) -> dict:
    """Split a GitHub issue-form body ('### Heading\\n\\nvalue') into a dict."""
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        if line.strip().startswith("###"):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line.strip().lstrip("#").strip().lower()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def clean(value: str) -> str:
    return "" if value.strip() == "_No response_" else value.strip()


def main() -> None:
    directive = clean(os.environ.get("INPUT_SUB", ""))
    years = clean(os.environ.get("INPUT_YEARS", ""))

    body = os.environ.get("ISSUE_BODY", "")
    if body and not directive:
        sections = parse_sections(body)
        for key, val in sections.items():
            if "directive" in key or "submission" in key:
                directive = clean(val)
            elif "year" in key:
                years = clean(val)
        # No recognizable headers (plain body): treat the whole thing as directive.
        if not sections:
            directive = clean(body)

    # Keep only digits for years.
    m = re.search(r"\d+", years)
    years = m.group() if m else ""

    with open("submission.txt", "w", encoding="utf-8") as fh:
        fh.write(directive)
    with open("years.txt", "w", encoding="utf-8") as fh:
        fh.write(years)

    print(f"directive: {len(directive)} chars; years: {years or '(default)'}")


if __name__ == "__main__":
    main()
