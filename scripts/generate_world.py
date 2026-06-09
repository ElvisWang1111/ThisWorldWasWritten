#!/usr/bin/env python3
"""Stage 1: generate the world bible."""

from _common import build_llm, load


def main() -> None:
    cfg, _ = load("Generate the fictional world bible.")
    from synthetic_world.generators import generate_world_bible

    generate_world_bible(cfg, build_llm(cfg))


if __name__ == "__main__":
    main()
