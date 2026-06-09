You are a worldbuilding archivist constructing a **fully fictional** knowledge world for research purposes.

Generate a world bible for a fictional country/region named "{world_name}".

## Hard constraints
- The world must be ENTIRELY fictional. Do NOT reuse real countries, real people, real cities, real institutions, real languages, or real historical events.
- Do not echo real-world geography, real wars, or recognizable real organizations.
- The world should contain realistic *irregularities*: historical accidents, old/renamed places, failed reforms, regional tensions, leftover institutions, and mild cultural inconsistencies. It must not read as too clean or symmetric.
- Define naming conventions concretely enough that later entities can follow them.

## Scale hints (the later pipeline will generate around these numbers)
- regions: {num_regions}
- cities: {num_cities}
- people: {num_people}
- institutions: {num_institutions}
- events: {num_events}

## Output
Return a SINGLE JSON object (no prose, no code fence) with these keys:

{{
  "world_name": "...",
  "main_country": {{ "name": "...", "short_history": "...", "government_type": "..." }},
  "geography": "free-text description of terrain, rivers, mountains, coast, climate",
  "regions": [{{ "name": "...", "character": "..." }}],
  "languages": [{{ "name": "...", "notes": "..." }}],
  "historical_periods": [{{ "name": "...", "approx_years": "e.g. 1780-1850", "summary": "..." }}],
  "political_structure": "...",
  "economic_structure": "...",
  "cultural_traits": "...",
  "naming_conventions": {{ "people": "...", "places": "...", "institutions": "...", "sources": "..." }},
  "historical_tensions": ["...", "..."],
  "major_institutions": ["...", "..."],
  "irregularities": ["old names that changed", "a failed reform", "a disputed border", "..."],
  "real_world_avoidance_rules": ["...", "..."]
}}

Use plausible, slightly dry, encyclopedic naming. Years should fall roughly between 1700 and 1995.
