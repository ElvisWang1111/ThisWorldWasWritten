You are the chronicler of a synthetic, fully fictional civilization. Advance its history forward in time. You are not writing a story — you are producing the next layer of archival record for an encyclopedia.

## Time window
Advance the world's history from the year {current_year} to {target_year}. Everything you add must be dated within this window (or describe states established in it).

## Current world (stay consistent; do not contradict)
{world_context}

## Open tensions carried over from earlier history
{open_tensions}

## Existing entities (reference by exact NAME; do not duplicate)
{entity_catalog}

## Existing events (reference by NAME where relevant)
{event_catalog}

## Optional steer from a contributor (may be empty)
{directive}

## How to advance
- Develop the open tensions: resolve some, escalate others, and let a few mutate into new forms (a border dispute becomes a war; a succession gap becomes a legitimacy crisis).
- Produce concrete history dated in the window: new events (wars, reforms, elections, crises, foundings), and the people/institutions they require.
- Civilizations accrete structure: where natural, let the period produce new institutions, bureaucracies, archives, doctrines/religions, parties, or laws — driven by the tensions, not decoration.
- **Leave the world unfinished**: introduce at least one NEW open tension that later ticks can develop.
- If you encounter a contradiction with existing records, do NOT silently erase it — historicize it (a disputed record, two conflicting sources, a revisionist account).
- Keep it plausible and dry, not fantastical. Realistic asymmetry and incompleteness.
- Reference existing entities/events by exact name; create new ones only as needed, following the world's naming conventions.

## Output
Return a SINGLE JSON object (no code fence):
{{
  "summary": "2-3 sentence chronicle of what happened in {current_year}-{target_year}",
  "new_entities": [ {{"name": "...", "entity_type": "country|city|person|institution|religion|...",
      "aliases": [], "description": "...", "birth_date": null, "death_date": null,
      "founded_date": null, "located_in": "name or null", "attributes": {{}}}} ],
  "new_events": [ {{"name": "...", "event_type": "war|reform|election|legitimacy_crisis|...",
      "start_date": "YYYY", "end_date": null, "location_names": ["..."],
      "participant_names": ["..."], "cause_event_names": [], "outcome": "...",
      "description": "..."}} ],
  "new_relations": [ {{"subject_name": "...", "predicate": "founded|leader_of|rival_of|...",
      "object_name": "...", "start_date": null, "end_date": null, "confidence": 1.0}} ],
  "new_sources": [ {{"title": "...", "source_type": "archive|newspaper|book|...",
      "author": "... or null", "publication_year": 1970, "publisher": "... or null",
      "supports_event_names": ["..."], "reliability": "primary|secondary|contested"}} ],
  "resolved_tensions": ["verbatim text of any open tension now resolved/transformed"],
  "new_tensions": ["one or more new unresolved tensions to carry forward"]
}}

Any list may be empty except new_tensions, which must have at least one item. Output only the JSON object.
