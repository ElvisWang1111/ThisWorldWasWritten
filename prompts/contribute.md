You are the editor of a synthetic, fully fictional encyclopedia. A contributor has submitted a request. Expand the **hidden world** so the submission becomes a coherent, well-supported part of it — like accepting an edit on a real wiki.

## Contributor submission
{submission}

## Existing world bible (stay consistent with it; do not contradict)
{world_context}

## Existing entities (reference these by exact NAME; do not duplicate them)
{entity_catalog}

## Existing events (reference by NAME where relevant)
{event_catalog}

## Your task
Translate the submission into structured additions to the hidden world. You may
create new entities (including new countries/regions if the submission implies
them), events, relations between them, and fictional sources that support the
new facts.

## Rules
- Everything must be fictional and consistent with the world bible's naming
  conventions, geography and time periods.
- Reference existing entities/events by their exact name. Introduce new ones
  only when needed; give them names that fit the conventions.
- New entities may reference each other and existing ones.
- Keep dates temporally valid (no participating before existing, treaties after
  the conflicts they resolve, end after start).
- Add realistic messiness where appropriate (aliases/old names, partial or
  contested sources, minor figures), not perfect symmetry.
- Add at least one fictional source supporting the most important new facts.
- Do NOT invent real-world entities. Do NOT rewrite existing pages here.

## Output
Return a SINGLE JSON object (no code fence):
{{
  "summary": "one sentence describing what you added",
  "new_entities": [
    {{"name": "...", "entity_type": "country|region|city|person|institution|...",
      "aliases": [], "description": "...", "birth_date": null, "death_date": null,
      "founded_date": null, "located_in": "existing-or-new place name or null",
      "attributes": {{}}}}
  ],
  "new_events": [
    {{"name": "...", "event_type": "war|treaty|reform|...",
      "start_date": "YYYY or YYYY-MM-DD", "end_date": null,
      "location_names": ["..."], "participant_names": ["..."],
      "cause_event_names": [], "outcome": "...", "description": "..."}}
  ],
  "new_relations": [
    {{"subject_name": "...", "predicate": "founded|located_in|rival_of|...",
      "object_name": "...", "start_date": null, "end_date": null, "confidence": 1.0}}
  ],
  "new_sources": [
    {{"title": "...", "source_type": "archive|newspaper|book|...",
      "author": "... or null", "publication_year": 1970, "publisher": "... or null",
      "supports_event_names": ["new or existing event name"],
      "reliability": "primary|secondary|contested"}}
  ]
}}

Any list may be empty. Output only the JSON object.
