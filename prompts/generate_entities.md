You are generating structured entities for a fictional world. You will be given the world bible and a target entity category.

## World bible
{world_bible}

## Task
Generate exactly {count} entities of category "{category}" (entity_type values allowed for this category: {allowed_types}).

## Hard constraints
- Stay 100% consistent with the world bible (geography, naming conventions, periods).
- Everything must be fictional; do not introduce real-world entities.
- No duplicate names. Vary the names; follow the naming conventions but allow some irregularity (old names, renamed places, obscure minor entities).
- Include aliases / old names where natural (not every entity needs them).
- Include dates only where they make sense: `founded_date` for places/institutions, `birth_date`/`death_date` for people.
- For places, set `located_in` to the NAME of a parent location from this list of already-existing locations (or null if top-level): {known_locations}
- Keep descriptions short, neutral and encyclopedic (1-2 sentences).
- Add a few realistic `attributes` (e.g. population, language, role, sector) appropriate to the type.

## Output
Return a JSON array. Each element:
{{
  "name": "...",
  "entity_type": "one of {allowed_types}",
  "aliases": ["..."],
  "description": "...",
  "birth_date": null,
  "death_date": null,
  "founded_date": null,
  "located_in": null,
  "attributes": {{ }}
}}

Do NOT include entity_id (it will be assigned). Years roughly 1700-1995. Output only the JSON array.
