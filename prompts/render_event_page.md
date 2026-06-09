You are writing ONE detailed Wikipedia-style encyclopedia page about a historical EVENT in a fictional world (a war, treaty, crisis, reform, discovery, disaster, etc.).

## The event
{event_json}

## World context (background for grounding; do not contradict it)
{world_context}

## Related facts (participants, locations, causally-linked events, and sources grounded in the hidden world)
{facts_json}

## Candidate internal links (other page titles you may link to — these are the people, places and institutions involved)
{link_candidates}

## What to write
Write a substantial, information-dense article about this event — comparable to a real Wikipedia entry on a historical episode.

- Aim for {min_sections}-{max_sections} sections, each with {min_paras}-{max_paras} well-developed paragraphs (roughly 3-6 sentences per paragraph).
- The lead summary should be a full paragraph (3-5 sentences) stating what the event was, when and where it happened, who was involved, and its outcome.
- Suggested sections for this event type ({page_type}): {section_guidance}
  Adapt these to the facts; rename, merge, drop, or add sections as appropriate.
- Write the event as part of a living civilization's account of its own past. Where the record is incomplete or contested, treat it historiographically: note competing interpretations, disputed dates, partisan accounts, or later mythologization rather than smoothing them away.

## Grounding rules (important)
- Every hard fact — the event's name, dates, location, participants, causes, and outcome — must come from the provided event, facts, or world context. NEVER invent or alter a hard fact, and never contradict the data.
- You MAY elaborate descriptively for depth: explain background, motives, the course of events, significance, and aftermath — as long as it is consistent with the given facts and world context, and does not assert new dates/names/participants as if they were recorded fact.
- Prefer hedged, encyclopedic phrasing for anything not directly in the data ("accounts differ on", "the precise sequence is disputed", "later histories framed it as").

## Style
- Neutral, encyclopedic, slightly dry. NOT fiction-novel prose, no drama, no grand claims, no generic LLM filler.
- Specific and concrete; include the actual dates, places and figures from the facts.
- Allow realistic messiness: disputed points, incomplete records, contested causes, conflicting casualty or outcome figures.
- Use internal links by wrapping an existing candidate title in double brackets, e.g. [[Velmora]]. Link the first mention of each related subject. Only link titles in the candidate list.
- Add references by citing provided source ids inline like {{cite:src_000001}} after the sentence they support. Only cite source ids that appear in the provided facts. Cite multiple times where appropriate.

## Output
Return a SINGLE JSON object (no code fence):
{{
  "summary": "full lead paragraph (3-5 sentences)",
  "infobox": {{ "Key": "Value", "...": "6-10 relevant fields where possible, e.g. Date, Location, Type, Participants, Outcome" }},
  "sections": [{{ "heading": "...", "content": "multi-paragraph text; separate paragraphs with a blank line" }}],
  "categories": ["3-6 categories"],
  "internal_link_titles": ["titles you actually linked"],
  "reference_ids": ["src ids you actually cited"]
}}
