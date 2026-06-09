You are generating the historical timeline (events) of a fictional world.

## World bible
{world_bible}

## Existing entities (use ONLY these names/ids for participants and locations)
{entity_catalog}

## Task
Generate exactly {count} historical events. event_type must be one of:
{event_types}

## Hard constraints
- Reference only entities listed above, by their NAME.
- Events must be temporally valid:
  - A person cannot participate before birth or after death.
  - An institution cannot participate before it is founded.
  - A treaty must come AFTER the conflict it resolves.
  - end_date must not precede start_date.
- Include causes and consequences. Reference earlier events by NAME in `cause_event_names` where appropriate.
- Do NOT make every event clean or symmetric. Include at least one ambiguous, failed, or inconclusive event, and uneven spacing in time.
- Outcomes should be concrete and specific, not grand.

## Output
Return a JSON array. Each element:
{{
  "name": "...",
  "event_type": "one of the allowed types",
  "start_date": "YYYY or YYYY-MM-DD",
  "end_date": null,
  "location_names": ["existing entity name"],
  "participant_names": ["existing entity name"],
  "cause_event_names": ["name of an earlier event in this batch, or []"],
  "outcome": "...",
  "description": "1-3 neutral encyclopedic sentences"
}}

Do NOT include event_id. Years roughly 1700-1995. Output only the JSON array.
