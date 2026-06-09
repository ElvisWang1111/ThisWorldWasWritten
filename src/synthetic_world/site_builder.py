"""Stage 8: build a static browsable wiki site from the rendered pages.

Produces site_output/ with a home page, one article per page, an all-pages
index, category pages, a timeline, a client-side title search index, and a
banner framing the site as a self-evolving AI civilization archive on every page.
"""

from __future__ import annotations

import html
import random
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .utils import parse_date_tuple, read_json, read_jsonl, slugify

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_CITE_RE = re.compile(r"\{cite:(src_\d+)\}")


def _paths(cfg: Dict[str, Any]) -> Dict[str, Path]:
    from .utils import PROJECT_ROOT

    world = PROJECT_ROOT / cfg.get("paths", {}).get("world_dir", "data/world")
    wiki = PROJECT_ROOT / cfg.get("paths", {}).get("wiki_dir", "data/wiki")
    out = PROJECT_ROOT / cfg.get("site", {}).get("output_dir", "site_output")
    return {
        "templates": PROJECT_ROOT / "src" / "site" / "templates",
        "static": PROJECT_ROOT / "src" / "site" / "static",
        "bible": world / "world_bible.json",
        "events": world / "events.jsonl",
        "sources": world / "sources.jsonl",
        "pages": wiki / "pages.jsonl",
        "out": out,
    }


def _markup_to_html(
    text: str,
    title_to_slug: Dict[str, str],
    ref_numbers: Dict[str, int],
    rel: str,
) -> str:
    """Convert [[links]] and {cite:src} markers into safe HTML.

    Everything else is HTML-escaped, then blank lines become paragraphs.
    """

    def link_sub(m: re.Match) -> str:
        title = m.group(1).strip()
        slug = title_to_slug.get(title.lower())
        safe_title = html.escape(title)
        if slug:
            return f'<a href="{rel}wiki/{slug}.html">{safe_title}</a>'
        return safe_title

    def cite_sub(m: re.Match) -> str:
        sid = m.group(1)
        num = ref_numbers.get(sid)
        if num is None:
            return ""
        return f'<sup class="cite"><a href="#cite-{sid}">[{num}]</a></sup>'

    # Tokenize links/cites first so their HTML is not escaped, escape the rest.
    placeholder: Dict[str, str] = {}

    def stash(repl: str) -> str:
        key = f"\x00{len(placeholder)}\x00"
        placeholder[key] = repl
        return key

    tmp = _LINK_RE.sub(lambda m: stash(link_sub(m)), text)
    tmp = _CITE_RE.sub(lambda m: stash(cite_sub(m)), tmp)
    tmp = html.escape(tmp)
    for key, repl in placeholder.items():
        tmp = tmp.replace(html.escape(key), repl).replace(key, repl)

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", tmp) if p.strip()]
    return "\n".join(f"<p>{p}</p>" for p in paragraphs) or "<p></p>"


def build_site(cfg: Dict[str, Any]) -> Path:
    paths = _paths(cfg)
    seed = cfg.get("random_seed", 42)
    rng = random.Random(seed)

    bible = read_json(paths["bible"]) if paths["bible"].exists() else {}
    pages = read_jsonl(paths["pages"])
    sources = read_jsonl(paths["sources"])
    events = read_jsonl(paths["events"])
    src_by_id = {s["source_id"]: s for s in sources}
    # The encyclopedia's display name spans the whole world; fall back to the
    # main country name when site.title is not set.
    world_name = cfg.get("site", {}).get("title") or cfg.get("world_name", "Asteria")
    version = max((p.get("version", 1) for p in pages), default=1)

    if not pages:
        raise RuntimeError(
            "No wiki pages found. Run the render stage before building the site."
        )

    # Maps used across rendering.
    title_to_slug = {p["title"].lower(): slugify(p["title"]) for p in pages}
    page_by_id = {p["page_id"]: p for p in pages}
    for p in pages:
        p["slug"] = slugify(p["title"])

    env = Environment(
        loader=FileSystemLoader(str(paths["templates"])),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["slug"] = slugify

    # Fresh output directory.
    out = paths["out"]
    if out.exists():
        shutil.rmtree(out)
    (out / "wiki").mkdir(parents=True)
    (out / "category").mkdir(parents=True)
    shutil.copytree(paths["static"], out / "static")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    # ---- Article pages -------------------------------------------------
    page_tpl = env.get_template("page.html")
    for p in pages:
        rel = "../"
        ref_numbers = {sid: i + 1 for i, sid in enumerate(p.get("reference_ids", []))}
        p["summary_html"] = _markup_to_html(
            p.get("summary", ""), title_to_slug, ref_numbers, rel
        )
        for sec in p["sections"]:
            sec["content_html"] = _markup_to_html(
                sec.get("content", ""), title_to_slug, ref_numbers, rel
            )
        references = [src_by_id[s] for s in p.get("reference_ids", []) if s in src_by_id]
        related = [
            {"title": page_by_id[pid]["title"], "slug": page_by_id[pid]["slug"]}
            for pid in p.get("internal_links", [])
            if pid in page_by_id
        ]
        html_out = page_tpl.render(
            page=p, references=references, related=related,
            world_name=world_name, version=version, rel=rel,
        )
        (out / "wiki" / f"{p['slug']}.html").write_text(html_out, encoding="utf-8")

    # ---- Category pages ------------------------------------------------
    cat_map: Dict[str, List[Dict[str, Any]]] = {}
    for p in pages:
        for c in p.get("categories", []):
            cat_map.setdefault(c, []).append(p)
    cat_tpl = env.get_template("category.html")
    for cat, cat_pages in cat_map.items():
        html_out = cat_tpl.render(
            heading=cat,
            pages=sorted(cat_pages, key=lambda x: x["title"]),
            groups=None, description=None,
            world_name=world_name, version=version, rel="../",
        )
        (out / "category" / f"{slugify(cat)}.html").write_text(html_out, encoding="utf-8")

    # Categories landing page (links to each category page).
    _write_categories_index(env, out, cat_map, world_name, version)

    # ---- All pages -----------------------------------------------------
    all_tpl = env.get_template("category.html")
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for p in pages:
        by_type.setdefault(p["page_type"], []).append(p)
    groups = [
        {
            "name": t.replace("_", " ").title() + f" ({len(ps)})",
            "pages": sorted(ps, key=lambda x: x["title"]),
        }
        for t, ps in sorted(by_type.items())
    ]
    (out / "all-pages.html").write_text(
        all_tpl.render(
            heading="All pages", description=f"{len(pages)} articles.",
            pages=None, groups=groups,
            world_name=world_name, version=version, rel="",
        ),
        encoding="utf-8",
    )

    # ---- Timeline ------------------------------------------------------
    tl_events = sorted(
        events, key=lambda e: parse_date_tuple(e.get("start_date")) or (9999, 12, 31)
    )
    for e in tl_events:
        slug = title_to_slug.get(e["name"].lower())
        e["slug"] = slug or ""
    tl_tpl = env.get_template("timeline.html")
    (out / "timeline.html").write_text(
        tl_tpl.render(events=tl_events, world_name=world_name, version=version, rel=""),
        encoding="utf-8",
    )

    # ---- Home ----------------------------------------------------------
    index_tpl = env.get_template("index.html")
    main_categories = sorted(
        ({"name": c, "slug": slugify(c), "count": len(ps)} for c, ps in cat_map.items()),
        key=lambda x: -x["count"],
    )[:8]
    random_pages = rng.sample(pages, min(6, len(pages)))
    recent_pages = list(reversed(pages))[:8]
    intro = bible.get("main_country", {}).get("short_history") or (
        f"{world_name} is a self-evolving AI civilization. This encyclopedia is "
        f"the visible surface of its history, continuously written and rewritten "
        f"by AI as the world advances."
    )
    (out / "index.html").write_text(
        index_tpl.render(
            intro=intro,
            page_count=len(pages),
            main_categories=main_categories,
            random_pages=[{"title": p["title"], "slug": p["slug"]} for p in random_pages],
            recent_pages=[
                {"title": p["title"], "slug": p["slug"], "page_type": p["page_type"]}
                for p in recent_pages
            ],
            world_name=world_name, version=version, rel="",
        ),
        encoding="utf-8",
    )

    # ---- Contribute page -----------------------------------------------
    repo_url = (cfg.get("site", {}).get("repo_url") or "").rstrip("/")
    contribute_tpl = env.get_template("contribute.html")
    (out / "contribute.html").write_text(
        contribute_tpl.render(
            repo_url=repo_url, world_name=world_name, version=version, rel="",
        ),
        encoding="utf-8",
    )

    # ---- Search index --------------------------------------------------
    import json

    index_data = [{"title": p["title"], "slug": p["slug"]} for p in pages]
    (out / "static" / "search_index.js").write_text(
        "var SEARCH_INDEX = " + json.dumps(index_data, ensure_ascii=False) + ";",
        encoding="utf-8",
    )

    print(f"[stage8] static site -> {out} ({len(pages)} pages)")
    return out


def _write_categories_index(env, out, cat_map, world_name, version) -> None:
    """Render the categories landing page that links to each category page.

    The shared category template links into wiki/<slug>; the index needs links
    into category/<slug>, so we render a small bespoke listing here.
    """
    items = "\n".join(
        f'<li><a href="category/{slugify(c)}.html">{c}</a> '
        f'<span class="muted">{len(ps)} pages</span></li>'
        for c, ps in sorted(cat_map.items())
    )
    body = (
        '<article class="listing"><h1>Categories</h1>'
        '<p class="lead">All categories in this encyclopedia.</p>'
        f'<ul class="page-list">{items}</ul></article>'
    )
    inline = env.from_string(
        "{% extends 'base.html' %}{% block content %}" + body + "{% endblock %}"
    )
    (out / "categories.html").write_text(
        inline.render(world_name=world_name, version=version, rel=""),
        encoding="utf-8",
    )
