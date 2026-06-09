#!/usr/bin/env python3
"""Stage 2: generate entities from the world bible."""

from _common import build_llm, load


def main() -> None:
    cfg, _ = load("Generate entities from the world bible.")
    from synthetic_world.generators import generate_entities

    generate_entities(cfg, build_llm(cfg))


if __name__ == "__main__":
    main()
