"""Shared utilities: config loading, JSON/JSONL IO, ID minting, date parsing."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

import yaml

# Project root = two levels up from this file (src/synthetic_world/utils.py).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_config(path: str | Path) -> Dict[str, Any]:
    """Load a YAML config file into a plain dict."""
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    with p.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config at {p} did not parse to a mapping.")
    return cfg


def resolve_path(cfg: Dict[str, Any], *parts: str) -> Path:
    """Resolve a path relative to the project root, creating parents as needed."""
    p = PROJECT_ROOT.joinpath(*parts)
    return p


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory by file name."""
    p = PROJECT_ROOT / "prompts" / name
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# JSON / JSONL IO
# ---------------------------------------------------------------------------


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_jsonl(path: str | Path, rows: Iterable[Any]) -> int:
    """Write an iterable of dict-like rows as JSONL. Returns the count written."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            if hasattr(row, "model_dump"):
                row = row.model_dump()
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{p}:{i}: invalid JSON line: {exc}") from exc
    return out


def iter_jsonl(path: str | Path) -> Iterator[Dict[str, Any]]:
    for row in read_jsonl(path):
        yield row


# ---------------------------------------------------------------------------
# ID minting
# ---------------------------------------------------------------------------

_ID_PREFIXES = {
    "entity": "ent",
    "event": "evt",
    "relation": "rel",
    "source": "src",
    "page": "page",
    "feedback": "fb",
}


def make_id(kind: str, n: int) -> str:
    """Mint a stable zero-padded id, e.g. make_id('entity', 1) -> 'ent_000001'."""
    prefix = _ID_PREFIXES[kind]
    return f"{prefix}_{n:06d}"


def slugify(text: str) -> str:
    """Turn a page title into a URL-safe, file-safe slug."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "untitled"


# ---------------------------------------------------------------------------
# Date parsing (lenient: supports 'YYYY', 'YYYY-MM', 'YYYY-MM-DD').
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^(\d{3,4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?$")


def parse_year(date_str: Optional[str]) -> Optional[int]:
    """Extract the year from a partial date string, or None if unparseable."""
    if not date_str:
        return None
    m = _DATE_RE.match(str(date_str).strip())
    if not m:
        return None
    return int(m.group(1))


def parse_date_tuple(date_str: Optional[str]) -> Optional[tuple[int, int, int]]:
    """Return (year, month, day) with sensible defaults, or None if unparseable."""
    if not date_str:
        return None
    m = _DATE_RE.match(str(date_str).strip())
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2)) if m.group(2) else 1
    day = int(m.group(3)) if m.group(3) else 1
    return (year, month, day)


def date_before(a: Optional[str], b: Optional[str]) -> Optional[bool]:
    """Return True if date a is strictly before date b. None if either is unknown."""
    ta, tb = parse_date_tuple(a), parse_date_tuple(b)
    if ta is None or tb is None:
        return None
    return ta < tb
