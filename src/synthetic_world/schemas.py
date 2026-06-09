"""Data schemas for the hidden world layer and the wiki rendering layer.

Pydantic models are used so that LLM output can be validated and coerced as it
is parsed. Each model mirrors the schema documented in the project README.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


def _coerce_date_str(v: Any) -> Any:
    """Allow models to emit a year as an int (1793) where a date string is expected."""
    if isinstance(v, int):
        return str(v)
    return v

# ---------------------------------------------------------------------------
# Controlled vocabularies (kept as plain tuples so they can be reused in
# prompts, validators and tests without importing heavy machinery).
# ---------------------------------------------------------------------------

ENTITY_TYPES: tuple[str, ...] = (
    "country",
    "region",
    "city",
    "river",
    "mountain",
    "person",
    "institution",
    "university",
    "company",
    "newspaper",
    "political_party",
    "law",
    "treaty",
    "conflict",
    "cultural_group",
    "technology",
    "book",
    "artwork",
)

EVENT_TYPES: tuple[str, ...] = (
    "war",
    "battle",
    "treaty",
    "reform",
    "election",
    "economic_crisis",
    "political_crisis",
    "scientific_discovery",
    "cultural_movement",
    "institution_founding",
    "natural_disaster",
    "migration",
    "assassination",
    "protest",
    "court_case",
)

PREDICATES: tuple[str, ...] = (
    "born_in",
    "died_in",
    "located_in",
    "capital_of",
    "founded",
    "member_of",
    "leader_of",
    "educated_at",
    "signed",
    "participated_in",
    "caused",
    "succeeded_by",
    "preceded_by",
    "ally_of",
    "rival_of",
    "published_by",
    "influenced",
    "renamed_to",
    "part_of",
)

SOURCE_TYPES: tuple[str, ...] = (
    "archive",
    "newspaper",
    "book",
    "journal_article",
    "government_report",
    "memoir",
    "court_record",
    "census",
    "museum_catalog",
    "oral_history",
)

# Entity types that may legitimately serve as a location for `located_in`.
LOCATION_ENTITY_TYPES: tuple[str, ...] = (
    "country",
    "region",
    "city",
    "river",
    "mountain",
)


# ---------------------------------------------------------------------------
# Hidden world layer
# ---------------------------------------------------------------------------


class Entity(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    aliases: List[str] = Field(default_factory=list)
    description: str = ""
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    founded_date: Optional[str] = None
    located_in: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source: str = "generated"
    version: int = 1

    _coerce_dates = field_validator(
        "birth_date", "death_date", "founded_date", mode="before"
    )(_coerce_date_str)


class Event(BaseModel):
    event_id: str
    name: str
    event_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location_ids: List[str] = Field(default_factory=list)
    participant_ids: List[str] = Field(default_factory=list)
    cause_event_ids: List[str] = Field(default_factory=list)
    outcome: str = ""
    description: str = ""
    version: int = 1

    _coerce_dates = field_validator("start_date", "end_date", mode="before")(
        _coerce_date_str
    )


class Relation(BaseModel):
    relation_id: str
    subject_id: str
    predicate: str
    object_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    confidence: float = 1.0
    source_ids: List[str] = Field(default_factory=list)
    version: int = 1

    _coerce_dates = field_validator("start_date", "end_date", mode="before")(
        _coerce_date_str
    )


class Source(BaseModel):
    source_id: str
    title: str
    source_type: str
    author: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    supports: List[str] = Field(default_factory=list)
    reliability: str = "secondary"
    version: int = 1

    @field_validator("publication_year", mode="before")
    @classmethod
    def _coerce_year(cls, v: Any) -> Any:
        if v is None or isinstance(v, int):
            return v
        m = re.search(r"\d{3,4}", str(v))
        return int(m.group()) if m else None


# ---------------------------------------------------------------------------
# Wiki rendering layer
# ---------------------------------------------------------------------------


class PageSection(BaseModel):
    heading: str
    content: str


class WikiPage(BaseModel):
    page_id: str
    title: str
    entity_id: Optional[str] = None
    event_id: Optional[str] = None
    page_type: str
    summary: str = ""
    sections: List[PageSection] = Field(default_factory=list)
    infobox: Dict[str, Any] = Field(default_factory=dict)
    internal_links: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    reference_ids: List[str] = Field(default_factory=list)
    version: int = 1


class Feedback(BaseModel):
    feedback_id: str
    page_id: str
    human_label: str
    reasons: List[str] = Field(default_factory=list)
    suggested_fix: str = ""
    created_at: str = ""


# Convenience mapping from collection name -> model, used by loaders/validators.
MODEL_BY_COLLECTION: Dict[str, type[BaseModel]] = {
    "entities": Entity,
    "events": Event,
    "relations": Relation,
    "sources": Source,
    "pages": WikiPage,
    "feedback": Feedback,
}
