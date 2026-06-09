"""Shared bootstrap for the pipeline scripts: sys.path, args, LLM construction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

# Make `src/` importable when running scripts directly.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--config",
        default="configs/world_config.yaml",
        help="Path to the world config YAML.",
    )
    return parser.parse_args()


def load(description: str) -> Tuple[Dict[str, Any], argparse.Namespace]:
    from synthetic_world.utils import load_config

    args = parse_args(description)
    cfg = load_config(args.config)
    return cfg, args


def build_llm(cfg: Dict[str, Any]):
    from synthetic_world.llm_client import LLMClient, LLMConfig

    return LLMClient(LLMConfig.from_dict(cfg.get("generation", {})))
