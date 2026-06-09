#!/usr/bin/env python3
"""Stage 5: generate fictional sources and attach them to facts."""

from _common import build_llm, load


def main() -> None:
    cfg, _ = load("Generate fictional sources.")
    from synthetic_world.generators import generate_sources

    generate_sources(cfg, build_llm(cfg))


if __name__ == "__main__":
    main()
