You are generating fictional bibliographic sources (citations) for a fictional world.

## World bible (for naming conventions of publishers/authors)
{world_bible}

## Facts that may need support (relations and events, referenced by id and label)
{fact_catalog}

## Task
Generate {count} fictional sources. source_type must be one of:
{source_types}

## Hard constraints
- All sources are fictional but internally consistent with the world's naming conventions and time periods.
- Provide realistic VARIETY: some primary archives, some newspapers, some later historical studies, some memoirs, some incomplete/contested records.
- Citations must NOT all look identical: vary authors, publishers, years, and which facts they support.
- Some sources should support only a single narrow claim; some support several; a couple may mildly disagree with others (note this in the title or by reliability).
- `supports` must contain ids drawn ONLY from the fact catalog above (rel_* or evt_*). A source may support 0-4 facts. It is fine for some facts to have no source.
- publication_year must be plausible (often AFTER the events they describe, for secondary works).

## Output
Return a JSON array. Each element:
{{
  "title": "...",
  "source_type": "one of the allowed types",
  "author": "... or null",
  "publication_year": 1978,
  "publisher": "... or null",
  "supports": ["rel_000001", "evt_000002"],
  "reliability": "primary | secondary | contested"
}}

Do NOT include source_id (assigned later). Output only the JSON array.
