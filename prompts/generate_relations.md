You are generating relations (a knowledge graph) between entities of a fictional world.

## Existing entities (use ONLY these names/ids)
{entity_catalog}

## Existing events (for participated_in / caused, reference by name)
{event_catalog}

## Task
Generate {count} relations connecting these entities. predicate must be one of:
{predicates}

## Hard constraints
- subject and object must both be existing entity NAMES from the list above.
- Choose predicates that make sense for the entity types involved:
  - born_in / died_in / educated_at: subject is a person.
  - capital_of / located_in / part_of: subject is a place.
  - founded / leader_of / member_of: person ↔ institution.
  - signed: person/institution ↔ treaty.
  - published_by: newspaper/book ↔ company/institution.
  - ally_of / rival_of: between comparable entities.
- Include start_date / end_date where meaningful (else null).
- Keep relations consistent with any dates implied by the entities.
- Avoid contradictions (e.g. a city cannot be capital_of two countries).

## Output
Return a JSON array. Each element:
{{
  "subject_name": "...",
  "predicate": "one of the allowed predicates",
  "object_name": "...",
  "start_date": null,
  "end_date": null,
  "confidence": 1.0
}}

Do NOT include relation_id or source_ids (assigned later). Output only the JSON array.
