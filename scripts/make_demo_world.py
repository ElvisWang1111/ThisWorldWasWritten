#!/usr/bin/env python3
"""Write a tiny hand-crafted demo world (no LLM / no API key needed).

This lets you preview the static site and exercise stages 6-8 offline. It is a
fixed, deterministic fixture — the real pipeline generates a much larger and
more varied world via the LLM. Run:

    python scripts/make_demo_world.py
    python scripts/validate_world.py
    python scripts/build_static_site.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from synthetic_world.utils import write_json, write_jsonl  # noqa: E402

WORLD = _ROOT / "data" / "world"
WIKI = _ROOT / "data" / "wiki"

BIBLE = {
    "world_name": "Asteria",
    "main_country": {
        "name": "Republic of Asteria",
        "short_history": (
            "Asteria is a synthetic, fully fictional federal republic on the "
            "Iven basin, unified in 1844 after the Harbor Compacts."
        ),
        "government_type": "federal parliamentary republic",
    },
    "geography": "A temperate coastal basin drained by the Iven River.",
    "naming_conventions": {"places": "soft consonant clusters; -ora, -as endings"},
}

ENTITIES = [
    {"entity_id": "ent_000001", "name": "Asteria", "entity_type": "country",
     "aliases": ["Republic of Asteria"], "founded_date": "1844",
     "description": "A federal republic in the Iven basin.",
     "attributes": {"government": "federal republic", "capital": "Velmora"},
     "located_in": None, "version": 1},
    {"entity_id": "ent_000002", "name": "Velmora", "entity_type": "city",
     "aliases": ["Old Velmora"], "founded_date": "1842", "located_in": "ent_000001",
     "description": "Coastal capital and largest city of Asteria.",
     "attributes": {"population": 1280000, "role": "capital"}, "version": 1},
    {"entity_id": "ent_000003", "name": "Loras", "entity_type": "city",
     "founded_date": "1801", "located_in": "ent_000001",
     "description": "An inland river city and former assembly seat.",
     "attributes": {"population": 410000}, "version": 1},
    {"entity_id": "ent_000004", "name": "Iven River", "entity_type": "river",
     "located_in": "ent_000001", "description": "The principal river of Asteria.",
     "attributes": {"length_km": 720}, "version": 1},
    {"entity_id": "ent_000005", "name": "University of Velmora",
     "entity_type": "university", "founded_date": "1851", "located_in": "ent_000002",
     "description": "The oldest university in the republic.",
     "attributes": {"students": 22000}, "version": 1},
    {"entity_id": "ent_000006", "name": "Miren Halvek", "entity_type": "person",
     "birth_date": "1820", "death_date": "1889",
     "description": "A jurist and reformer associated with the Harbor Compacts.",
     "attributes": {"occupation": "jurist"}, "version": 1},
    {"entity_id": "ent_000007", "name": "Asterian Federal Assembly",
     "entity_type": "institution", "founded_date": "1844", "located_in": "ent_000002",
     "description": "The national legislature of Asteria.",
     "attributes": {"seats": 240}, "version": 1},
    {"entity_id": "ent_000008", "name": "The Loras Courier",
     "entity_type": "newspaper", "founded_date": "1838", "located_in": "ent_000003",
     "description": "A long-running regional newspaper, now in reduced circulation.",
     "attributes": {"circulation": 35000}, "version": 1},
]

EVENTS = [
    {"event_id": "evt_000001", "name": "The Harbor Compacts", "event_type": "treaty",
     "start_date": "1844-03-01", "end_date": "1844-06-12",
     "location_ids": ["ent_000002"], "participant_ids": ["ent_000006"],
     "cause_event_ids": [],
     "outcome": "Unified the coastal provinces into the Republic of Asteria.",
     "description": "A set of negotiated compacts that founded the federal republic.",
     "version": 1},
    {"event_id": "evt_000002", "name": "Founding of the Federal Assembly",
     "event_type": "institution_founding", "start_date": "1844-07-01",
     "location_ids": ["ent_000002"], "participant_ids": ["ent_000006", "ent_000007"],
     "cause_event_ids": ["evt_000001"],
     "outcome": "Established the national legislature in Velmora.",
     "description": "The first sitting of the Asterian Federal Assembly.",
     "version": 1},
    {"event_id": "evt_000003", "name": "The Second Canal Crisis",
     "event_type": "political_crisis", "start_date": "1872-04-03",
     "end_date": "1872-09-18", "location_ids": ["ent_000003"],
     "participant_ids": ["ent_000007"], "cause_event_ids": ["evt_000002"],
     "outcome": "Canal administration was transferred to the federal assembly.",
     "description": "A disputed, partly inconclusive crisis over the eastern canals.",
     "version": 1},
]

RELATIONS = [
    {"relation_id": "rel_000001", "subject_id": "ent_000002",
     "predicate": "capital_of", "object_id": "ent_000001", "source_ids": [],
     "confidence": 1.0, "version": 1},
    {"relation_id": "rel_000002", "subject_id": "ent_000002",
     "predicate": "located_in", "object_id": "ent_000001", "source_ids": [],
     "confidence": 1.0, "version": 1},
    {"relation_id": "rel_000003", "subject_id": "ent_000006",
     "predicate": "signed", "object_id": "ent_000001", "start_date": "1844",
     "source_ids": [], "confidence": 0.9, "version": 1},
    {"relation_id": "rel_000004", "subject_id": "ent_000005",
     "predicate": "located_in", "object_id": "ent_000002", "source_ids": [],
     "confidence": 1.0, "version": 1},
    {"relation_id": "rel_000005", "subject_id": "ent_000006",
     "predicate": "educated_at", "object_id": "ent_000005", "start_date": "1839",
     "source_ids": [], "confidence": 0.7, "version": 1},
]

SOURCES = [
    {"source_id": "src_000001", "title": "Archives of the Loras Assembly, Volume II",
     "source_type": "archive", "author": "Miren Halvek", "publication_year": 1878,
     "publisher": "North Asterian Historical Press",
     "supports": ["rel_000003", "evt_000001"], "reliability": "primary",
     "version": 1},
    {"source_id": "src_000002", "title": "A Short History of the Iven Basin",
     "source_type": "book", "author": "T. Ostrega", "publication_year": 1961,
     "publisher": "Velmora University Press",
     "supports": ["evt_000003"], "reliability": "secondary", "version": 1},
    {"source_id": "src_000003", "title": "The Loras Courier, 14 May 1872",
     "source_type": "newspaper", "author": None, "publication_year": 1872,
     "publisher": "The Loras Courier",
     "supports": ["evt_000003"], "reliability": "contested", "version": 1},
]

PAGES = [
    {"page_id": "page_000001", "title": "Velmora", "entity_id": "ent_000002",
     "page_type": "city",
     "summary": "Velmora is the capital and largest city of [[Asteria]].",
     "sections": [
         {"heading": "History", "content": (
             "Velmora developed from a fortified harbor settlement and became the "
             "seat of government after [[The Harbor Compacts]] of 1844.{cite:src_000001} "
             "It is home to the [[University of Velmora]].")},
         {"heading": "Government", "content": (
             "The city hosts the [[Asterian Federal Assembly]], the national "
             "legislature established in 1844.")},
     ],
     "infobox": {"Country": "Asteria", "Founded": "1842", "Population": "1,280,000",
                 "Role": "Capital"},
     "internal_links": ["page_000002", "page_000004", "page_000005"],
     "categories": ["Cities in Asteria", "Capitals"],
     "reference_ids": ["src_000001"], "version": 1},
    {"page_id": "page_000002", "title": "Asteria", "entity_id": "ent_000001",
     "page_type": "country",
     "summary": "The Republic of Asteria is a federal republic in the Iven basin.",
     "sections": [
         {"heading": "History", "content": (
             "Asteria was founded in 1844 following [[The Harbor Compacts]]. Its "
             "capital is [[Velmora]].{cite:src_000001}")},
     ],
     "infobox": {"Capital": "Velmora", "Founded": "1844",
                 "Government": "Federal republic"},
     "internal_links": ["page_000001"], "categories": ["Countries"],
     "reference_ids": ["src_000001"], "version": 1},
    {"page_id": "page_000003", "title": "Miren Halvek", "entity_id": "ent_000006",
     "page_type": "person",
     "summary": "Miren Halvek (1820-1889) was an Asterian jurist and reformer.",
     "sections": [
         {"heading": "Career", "content": (
             "Halvek studied at the [[University of Velmora]] and is associated "
             "with [[The Harbor Compacts]], though the extent of his role is "
             "debated.{cite:src_000001}")},
     ],
     "infobox": {"Born": "1820", "Died": "1889", "Occupation": "Jurist"},
     "internal_links": ["page_000005"], "categories": ["People", "Jurists"],
     "reference_ids": ["src_000001"], "version": 1},
    {"page_id": "page_000004", "title": "Asterian Federal Assembly",
     "entity_id": "ent_000007", "page_type": "institution",
     "summary": "The Asterian Federal Assembly is the national legislature of "
                "[[Asteria]].",
     "sections": [
         {"heading": "History", "content": (
             "Founded in 1844 in [[Velmora]], the Assembly gained control of the "
             "eastern canals after [[The Second Canal Crisis]].{cite:src_000002}")},
     ],
     "infobox": {"Seat": "Velmora", "Founded": "1844", "Seats": "240"},
     "internal_links": ["page_000001", "page_000002"],
     "categories": ["Institutions"], "reference_ids": ["src_000002"], "version": 1},
    {"page_id": "page_000005", "title": "University of Velmora",
     "entity_id": "ent_000005", "page_type": "university",
     "summary": "The University of Velmora is the oldest university in [[Asteria]].",
     "sections": [
         {"heading": "Overview", "content": (
             "Founded in 1851 in [[Velmora]], it is among the principal research "
             "institutions of the republic.")},
     ],
     "infobox": {"Location": "Velmora", "Founded": "1851", "Students": "22,000"},
     "internal_links": ["page_000001", "page_000002"],
     "categories": ["Universities", "Education in Asteria"],
     "reference_ids": [], "version": 1},
    {"page_id": "page_000006", "title": "The Second Canal Crisis",
     "entity_id": None, "page_type": "political_crisis",
     "summary": "The Second Canal Crisis (1872) was a political dispute over the "
                "eastern canals near [[Loras]].",
     "sections": [
         {"heading": "Course", "content": (
             "The crisis ran from April to September 1872 and ended with canal "
             "administration passing to the [[Asterian Federal Assembly]]. "
             "Accounts in [[The Loras Courier]] differ from later "
             "histories.{cite:src_000003}")},
     ],
     "infobox": {"Date": "1872", "Location": "Loras", "Type": "Political crisis"},
     "internal_links": ["page_000004"],
     "categories": ["Events", "Political history of Asteria"],
     "reference_ids": ["src_000003"], "version": 1},
]


def main() -> None:
    write_json(WORLD / "world_bible.json", BIBLE)
    write_jsonl(WORLD / "entities.jsonl", ENTITIES)
    write_jsonl(WORLD / "events.jsonl", EVENTS)
    write_jsonl(WORLD / "relations.jsonl", RELATIONS)
    write_jsonl(WORLD / "sources.jsonl", SOURCES)
    write_jsonl(WIKI / "pages.jsonl", PAGES)
    print(f"Demo world written to {WORLD} and {WIKI}.")
    print("Next: python scripts/validate_world.py && "
          "python scripts/build_static_site.py")


if __name__ == "__main__":
    main()
