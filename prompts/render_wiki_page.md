You are writing ONE detailed Wikipedia-style encyclopedia page about an entity in a fictional world.

## The entity
{entity_json}

## World context (background for grounding; do not contradict it)
{world_context}

## Related facts (relations, events, and sources grounded in the hidden world)
{facts_json}

## Candidate internal links (other page titles you may link to)
{link_candidates}

## What to write
Write a substantial, information-dense article — comparable to a real mid-length Wikipedia entry.

- Aim for {min_sections}-{max_sections} sections, each with {min_paras}-{max_paras} well-developed paragraphs (roughly 3-6 sentences per paragraph).
- The lead summary should be a full paragraph (3-5 sentences) that situates the subject.
- Suggested sections for this entity type ({page_type}): {section_guidance}
  Adapt these to the facts; rename, merge, drop, or add sections as appropriate. A city page must not read like a biography.

## Grounding rules (important)
- Every hard fact — names, dates, who-did-what, relationships, founding/birth/death years — must come from the provided entity, facts, or world context. NEVER invent or alter a hard fact, and never contradict the data.
- You MAY elaborate descriptively for depth: explain context, significance, plausible day-to-day or institutional detail, geographic/economic/cultural setting, and historiographical nuance — as long as it is consistent with the given facts and the world context, and does not assert new dates/names/relationships as if they were recorded fact.
- Prefer hedged, encyclopedic phrasing for anything not directly in the data ("is generally associated with", "accounts differ on", "little is recorded about").

## Style
- Neutral, encyclopedic, slightly dry. NOT fiction-novel prose, no drama, no grand claims, no generic LLM filler.
- Specific and concrete; include the actual dates, places and figures from the facts.
- Allow realistic messiness: disputed points, incomplete records, minor or obscure details, old names.
- Use internal links by wrapping an existing candidate title in double brackets, e.g. [[Velmora]]. Link the first mention of each related subject. Only link titles in the candidate list.
- Add references by citing provided source ids inline like {{cite:src_000001}} after the sentence they support. Only cite source ids that appear in the provided facts. Cite multiple times where appropriate.

## Output
Return a SINGLE JSON object (no code fence):
{{
  "summary": "full lead paragraph (3-5 sentences)",
  "infobox": {{ "Key": "Value", "...": "6-10 relevant fields where possible" }},
  "sections": [{{ "heading": "...", "content": "multi-paragraph text; separate paragraphs with a blank line" }}],
  "categories": ["3-6 categories"],
  "internal_link_titles": ["titles you actually linked"],
  "reference_ids": ["src ids you actually cited"]
}}
