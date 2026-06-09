#!/usr/bin/env python3
"""Stage 4: generate relations between entities and events."""

from _common import build_llm, load


def main() -> None:
    cfg, _ = load("Generate relations.")
    from synthetic_world.generators import generate_relations

    generate_relations(cfg, build_llm(cfg))


if __name__ == "__main__":
    main()
