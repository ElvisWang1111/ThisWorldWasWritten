from synthetic_world import schemas
from synthetic_world.utils import make_id, slugify, parse_year, date_before


def test_entity_roundtrip():
    e = schemas.Entity(
        entity_id="ent_000001",
        name="Velmora",
        entity_type="city",
        founded_date="1842",
        attributes={"population": 1280000},
    )
    d = e.model_dump()
    assert d["entity_id"] == "ent_000001"
    assert d["attributes"]["population"] == 1280000
    assert schemas.Entity(**d).name == "Velmora"


def test_int_dates_are_coerced_to_strings():
    # Models sometimes emit a year as an int; the schema should coerce it.
    e = schemas.Entity(entity_id="ent_000001", name="X", entity_type="city",
                        founded_date=1793)
    assert e.founded_date == "1793"
    ev = schemas.Event(event_id="evt_000001", name="X", event_type="treaty",
                       start_date=1844)
    assert ev.start_date == "1844"
    s = schemas.Source(source_id="src_000001", title="T", source_type="book",
                       publication_year="c. 1978")
    assert s.publication_year == 1978


def test_event_defaults():
    ev = schemas.Event(event_id="evt_000001", name="X", event_type="treaty")
    assert ev.participant_ids == []
    assert ev.cause_event_ids == []


def test_wiki_page_sections():
    p = schemas.WikiPage(
        page_id="page_000001",
        title="Velmora",
        page_type="city",
        sections=[{"heading": "History", "content": "..."}],
    )
    assert p.sections[0].heading == "History"


def test_controlled_vocabularies_present():
    assert "city" in schemas.ENTITY_TYPES
    assert "treaty" in schemas.EVENT_TYPES
    assert "founded" in schemas.PREDICATES
    assert "archive" in schemas.SOURCE_TYPES


def test_make_id():
    assert make_id("entity", 1) == "ent_000001"
    assert make_id("event", 42) == "evt_000042"
    assert make_id("page", 7) == "page_000007"


def test_slugify():
    assert slugify("The Second Canal Crisis") == "the-second-canal-crisis"
    assert slugify("  Velmora!! ") == "velmora"
    assert slugify("") == "untitled"


def test_dates():
    assert parse_year("1842-04-03") == 1842
    assert parse_year(None) is None
    assert date_before("1840", "1842") is True
    assert date_before("1842", "1840") is False
    assert date_before(None, "1842") is None
