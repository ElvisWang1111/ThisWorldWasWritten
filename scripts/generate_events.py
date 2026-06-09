#!/usr/bin/env python3
"""Stage 3: generate events and the timeline."""

from _common import build_llm, load


def main() -> None:
    cfg, _ = load("Generate historical events.")
    from synthetic_world.generators import generate_events

    generate_events(cfg, build_llm(cfg))


if __name__ == "__main__":
    main()
