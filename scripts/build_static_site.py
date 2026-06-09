#!/usr/bin/env python3
"""Stage 8: build the static wiki site from the rendered pages."""

from _common import load


def main() -> None:
    cfg, _ = load("Build the static wiki site.")
    from synthetic_world.site_builder import build_site

    build_site(cfg)


if __name__ == "__main__":
    main()
