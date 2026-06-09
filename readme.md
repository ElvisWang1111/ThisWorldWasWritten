# This World Was Written

## 1. Project Motivation

This project is **not** a fake-wiki generator, and it is **not** an experiment in producing a batch of fictional articles. It is an attempt to build a **self-evolving archive of an AI civilization**.

The system first generates a fully fictional but internally coherent worldview — nations, cities, people, institutions, events, wars, religions, political systems, archives, and historical controversies — and renders that world as a Wikipedia-style encyclopedia. But the encyclopedia is not static. It is the **visible surface of a civilization in motion**: the AI continuously advances the world's history, manufacturing new events, conflicts, institutions, and myths over time.

The crucial design choice is how the system handles contradiction. When the AI discovers an inconsistency, it does **not** simply correct the error. Instead it **historicizes, archives, and mythologizes** the contradiction — turning it into a new article, a scholarly dispute, a conspiracy, an institution, or a historical rupture. Contradiction becomes fuel for further evolution rather than something to be patched away.

The research question this is built to observe:

> If an AI is left to continuously write, repair, and forge the history of a civilization, what kind of civilizational imagination does it converge on? Does it spontaneously reinvent nations, bureaucracy, archives, religion, war, legitimacy crises, and historical revision?

The key idea is:

> Do not treat this as "generate some fake articles." Treat it as a **civilization-evolution engine**. The wiki pages are the civilization's narration of its own history. Every user contribution and every autonomous AI evolution step changes the underlying world state and leaves a browsable, traceable trail across the encyclopedia.

## 2. Core Design Principle

The system should follow a two-layer design:

1. **Hidden World Layer**

   * A structured representation of the fictional world.
   * Contains entities, relations, events, timelines, locations, institutions, cultures, conflicts, and source metadata.
   * Stored as JSON / JSONL / database tables.
   * This layer is the ground truth.

2. **Wiki Rendering Layer**

   * Human-readable Wikipedia-style pages generated from the hidden world layer.
   * Each page should be grounded in the hidden structured facts.
   * Pages should contain internal links, categories, references, summaries, infoboxes, and related pages.

The hidden world layer should always be treated as the source of truth. Wiki pages are rendered views of this hidden world.

## 3. What We Want to Build

The first version should implement a pipeline that can generate:

* A fictional country or region.
* A set of cities, provinces, rivers, mountains, ports, universities, newspapers, political parties, companies, cultural groups, historical figures, and major events.
* A coherent historical timeline.
* A hidden knowledge graph.
* A collection of Wikipedia-style pages.
* Internal links between pages.
* Basic citations and fictional references.
* A static browsable wiki website.
* Validation scripts that check consistency across the world.

The output should look like a small synthetic encyclopedia.

## 4. MVP Scope

For the MVP, generate one fictional world with approximately:

* 1 country or region.
* 10 to 20 cities or locations.
* 30 to 50 people.
* 20 to 40 institutions.
* 30 to 50 historical events.
* 5 to 10 major conflicts, treaties, reforms, or crises.
* 100 to 200 wiki pages.
* 500 to 1,500 structured facts.
* Internal links between pages.
* Fictional references for important claims.

The MVP should prioritize coherence over scale.

## 5. Non-Goals for the MVP

The MVP should not try to:

* Build a full benchmark yet.
* Evaluate language models yet.
* Generate QA datasets yet.
* Optimize for fooling humans yet.
* Mix real-world entities with fictional entities.
* Generate misinformation that could be confused with real-world facts.

All generated content should remain clearly inside a fictional namespace. The website should contain a visible disclaimer that the world is synthetic and fictional.

## 6. Recommended Repository Structure

```text
synthetic-wiki-world/
│
├── README.md
├── configs/
│   └── world_config.yaml
│
├── data/
│   ├── raw/
│   ├── world/
│   │   ├── world_bible.json
│   │   ├── entities.jsonl
│   │   ├── events.jsonl
│   │   ├── relations.jsonl
│   │   ├── sources.jsonl
│   │   └── timeline.jsonl
│   │
│   ├── wiki/
│   │   ├── pages.jsonl
│   │   ├── links.jsonl
│   │   ├── categories.jsonl
│   │   └── references.jsonl
│   │
│   └── feedback/
│       └── human_critiques.jsonl
│
├── prompts/
│   ├── generate_world_bible.md
│   ├── generate_entities.md
│   ├── generate_events.md
│   ├── generate_relations.md
│   ├── render_wiki_page.md
│   ├── repair_world_from_feedback.md
│   └── validate_consistency.md
│
├── scripts/
│   ├── generate_world.py
│   ├── generate_entities.py
│   ├── generate_events.py
│   ├── generate_relations.py
│   ├── render_wiki_pages.py
│   ├── validate_world.py
│   ├── build_static_site.py
│   └── run_pipeline.py
│
├── src/
│   ├── synthetic_world/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── llm_client.py
│   │   ├── generators.py
│   │   ├── renderers.py
│   │   ├── validators.py
│   │   ├── feedback.py
│   │   └── utils.py
│   │
│   └── site/
│       ├── templates/
│       │   ├── base.html
│       │   ├── page.html
│       │   ├── index.html
│       │   └── category.html
│       └── static/
│
├── site_output/
│
├── tests/
│   ├── test_schemas.py
│   ├── test_validators.py
│   └── test_rendering.py
│
├── pyproject.toml
└── requirements.txt
```

## 7. Data Schema

### 7.1 Entity Schema

Each entity should be stored as one JSON object.

```json
{
  "entity_id": "ent_000001",
  "name": "Velmora",
  "entity_type": "city",
  "aliases": ["Velmor", "Old Velmora"],
  "description": "A coastal capital city in the fictional Republic of Asteria.",
  "birth_date": null,
  "death_date": null,
  "founded_date": "1842",
  "located_in": "ent_000010",
  "attributes": {
    "population": 1280000,
    "language": "Asterian",
    "historical_role": "capital"
  },
  "source": "generated",
  "version": 1
}
```

Possible `entity_type` values:

```text
country
region
city
river
mountain
person
institution
university
company
newspaper
political_party
law
treaty
conflict
cultural_group
technology
book
artwork
```

### 7.2 Event Schema

```json
{
  "event_id": "evt_000001",
  "name": "The Second Canal Crisis",
  "event_type": "political_crisis",
  "start_date": "1912-04-03",
  "end_date": "1912-09-18",
  "location_ids": ["ent_000003"],
  "participant_ids": ["ent_000021", "ent_000032"],
  "cause_event_ids": ["evt_000000"],
  "outcome": "The Treaty of Loras transferred canal administration to the federal assembly.",
  "description": "A six-month political crisis over control of the eastern canal system.",
  "version": 1
}
```

Possible `event_type` values:

```text
war
battle
treaty
reform
election
economic_crisis
political_crisis
scientific_discovery
cultural_movement
institution_founding
natural_disaster
migration
assassination
protest
court_case
```

### 7.3 Relation Schema

```json
{
  "relation_id": "rel_000001",
  "subject_id": "ent_000021",
  "predicate": "founded",
  "object_id": "ent_000045",
  "start_date": "1881",
  "end_date": null,
  "confidence": 1.0,
  "source_ids": ["src_000001"],
  "version": 1
}
```

Possible predicates:

```text
born_in
died_in
located_in
capital_of
founded
member_of
leader_of
educated_at
signed
participated_in
caused
succeeded_by
preceded_by
ally_of
rival_of
published_by
influenced
renamed_to
part_of
```

### 7.4 Source Schema

All citations should be fictional but internally consistent.

```json
{
  "source_id": "src_000001",
  "title": "Archives of the Loras Assembly, Volume II",
  "source_type": "archive",
  "author": "Miren Halvek",
  "publication_year": 1978,
  "publisher": "North Asterian Historical Press",
  "supports": ["rel_000001", "evt_000001"],
  "reliability": "primary",
  "version": 1
}
```

Possible `source_type` values:

```text
archive
newspaper
book
journal_article
government_report
memoir
court_record
census
museum_catalog
oral_history
```

### 7.5 Wiki Page Schema

```json
{
  "page_id": "page_000001",
  "title": "Velmora",
  "entity_id": "ent_000001",
  "page_type": "city",
  "summary": "Velmora is the capital and largest city of the Republic of Asteria.",
  "sections": [
    {
      "heading": "History",
      "content": "Velmora emerged as a fortified harbor settlement in the nineteenth century..."
    },
    {
      "heading": "Government",
      "content": "The city is administered by the Velmora Metropolitan Council..."
    }
  ],
  "internal_links": ["page_000002", "page_000017"],
  "categories": ["Cities in Asteria", "Capitals"],
  "reference_ids": ["src_000001", "src_000009"],
  "version": 1
}
```

## 8. Generation Pipeline

The pipeline should be implemented as a sequence of explicit stages.

### Stage 1: Generate World Bible

Generate a high-level world bible containing:

* World name.
* Main country or region.
* Geography.
* Languages.
* Historical periods.
* Political structure.
* Economic structure.
* Cultural traits.
* Naming conventions.
* Important historical tensions.
* Major institutions.
* Rules for avoiding real-world overlap.

Output:

```text
data/world/world_bible.json
```

The world bible should not be overly clean. It should include historical accidents, old names, failed reforms, regional tensions, institutional leftovers, and cultural inconsistencies.

### Stage 2: Generate Entities

Generate structured entities from the world bible.

Output:

```text
data/world/entities.jsonl
```

The system should generate entities in batches:

1. Locations.
2. Institutions.
3. People.
4. Events as entities if needed.
5. Cultural objects.
6. Publications and sources.

Each entity should have a stable ID.

### Stage 3: Generate Events

Generate the historical timeline.

Output:

```text
data/world/events.jsonl
data/world/timeline.jsonl
```

Events should be temporally valid. For example:

* A person cannot participate in an event before birth or after death.
* An institution cannot sign a treaty before it is founded.
* A city cannot be renamed before it exists.
* A treaty should come after the conflict it resolves.

### Stage 4: Generate Relations

Generate relations between entities and events.

Output:

```text
data/world/relations.jsonl
```

Relations should be consistent with the entity and event data.

### Stage 5: Generate Fictional Sources

Generate fictional sources that support facts.

Output:

```text
data/world/sources.jsonl
```

Sources should have realistic variety:

* Some sources are primary archives.
* Some are newspapers.
* Some are later historical studies.
* Some are contested or incomplete.
* Some support only narrow claims.
* Some sources should disagree mildly with others.

The citation system should avoid looking too perfect.

### Stage 6: Validate Hidden World

Run consistency checks before rendering wiki pages.

Validation should check:

* Duplicate entity names.
* Entity date validity.
* Event date validity.
* Broken relation IDs.
* Broken source IDs.
* Impossible temporal relations.
* Missing required fields.
* Inconsistent aliases.
* Circular relations where inappropriate.
* Unsupported major claims.

Output:

```text
data/world/validation_report.json
```

### Stage 7: Render Wiki Pages

Generate Wikipedia-style pages from the hidden world data.

Output:

```text
data/wiki/pages.jsonl
```

Each page should include:

* Title.
* Short lead paragraph.
* Infobox-like metadata.
* Sections.
* Internal links.
* Categories.
* References.
* Related pages.

Page styles should vary by type. A city page should not look like a biography page. A treaty page should not look like a company page.

### Stage 8: Build Static Wiki Site

Render the wiki pages into a static website.

Output:

```text
site_output/
```

The static site should include:

* Home page.
* Article pages.
* Entity index.
* Category pages.
* Search by title.
* Internal links.
* References section.
* Visible disclaimer that the wiki is fictional.

The site does not need user accounts or live editing for the MVP.

## 9. Human Feedback Loop

Although this project is not yet a benchmark, the system should support a simple human feedback loop.

Humans should be able to inspect wiki pages and mark why they look fake.

Example feedback object:

```json
{
  "feedback_id": "fb_000001",
  "page_id": "page_000014",
  "human_label": "fake-looking",
  "reasons": [
    "The institution names are too symmetrical.",
    "The historical timeline feels too clean.",
    "The citations all have the same structure."
  ],
  "suggested_fix": "Add older institution names, failed reforms, and more varied citation types.",
  "created_at": "2026-06-08T00:00:00"
}
```

Output:

```text
data/feedback/human_critiques.jsonl
```

Later, a repair agent can use this feedback to update the world.

## 10. Repair Loop

The repair loop should not only rewrite the visible page. It should update the hidden world first.

Bad approach:

```text
Human says page looks fake → directly rewrite article.
```

Correct approach:

```text
Human says page looks fake
→ identify which part of the hidden world is unrealistic
→ update world bible / entities / events / relations / sources
→ validate consistency
→ re-render affected wiki pages
```

Repair operations may include:

* Rename entities according to a better naming convention.
* Add old names and aliases.
* Add failed historical events.
* Add minor institutions.
* Add regional disputes.
* Add incomplete citations.
* Add source disagreement.
* Add historical leftovers.
* Add non-central figures.
* Add local terminology.
* Vary writing style across page types.

## 11. Prompt Files

The implementation should store prompts in the `prompts/` directory rather than hard-coding them.

### 11.1 `generate_world_bible.md`

This prompt should ask the LLM to generate a fictional world bible.

Important requirements:

* The world must be fully fictional.
* It must not reuse real countries, real people, real institutions, or real historical events.
* It should include realistic irregularities.
* It should define naming conventions.
* It should define historical periods.
* It should define political, cultural, and economic structures.
* It should produce machine-readable JSON.

### 11.2 `generate_entities.md`

This prompt should ask the LLM to generate entities consistent with the world bible.

Important requirements:

* Use stable IDs.
* Avoid duplicate names.
* Include aliases and old names.
* Include dates when relevant.
* Include entity type.
* Include short description.
* Output JSONL.

### 11.3 `generate_events.md`

This prompt should ask the LLM to generate events.

Important requirements:

* Events must follow the timeline.
* Events must refer only to existing entities.
* Events should include causes and consequences.
* Events should not be too clean or symmetric.
* Output JSONL.

### 11.4 `generate_relations.md`

This prompt should ask the LLM to generate relations between entities and events.

Important requirements:

* Use only existing IDs.
* Include start and end dates where relevant.
* Include source IDs if available.
* Output JSONL.

### 11.5 `render_wiki_page.md`

This prompt should ask the LLM to render one wiki page from structured facts.

Important requirements:

* Do not invent facts outside the provided hidden world data.
* Use internal links.
* Add references only from provided fictional sources.
* Preserve entity dates and relationships.
* Use a Wikipedia-like tone.
* Avoid over-polished LLM style.
* Output structured JSON for the page.

### 11.6 `repair_world_from_feedback.md`

This prompt should ask the LLM to propose repair operations based on human critique.

Important requirements:

* Do not directly rewrite the page first.
* Identify the underlying world-level problem.
* Propose edits to world bible, entities, events, relations, or sources.
* Preserve consistency.
* Output a list of structured repair operations.

### 11.7 `validate_consistency.md`

This prompt can be used as an optional LLM-based validator, but rule-based validation should be preferred whenever possible.

## 12. Implementation Requirements

The coding agent should implement the project in Python.

General requirements:

* Follow PEP8 style.
* Use type hints where practical.
* Keep prompts separate from code.
* Make each pipeline stage runnable independently.
* Make the full pipeline runnable through one command.
* Store all intermediate outputs.
* Avoid silent failures.
* Write validation reports.
* Add basic unit tests for schemas and validators.

Suggested command:

```bash
python scripts/run_pipeline.py --config configs/world_config.yaml
```

Suggested individual commands:

```bash
python scripts/generate_world.py --config configs/world_config.yaml
python scripts/generate_entities.py --config configs/world_config.yaml
python scripts/generate_events.py --config configs/world_config.yaml
python scripts/generate_relations.py --config configs/world_config.yaml
python scripts/render_wiki_pages.py --config configs/world_config.yaml
python scripts/validate_world.py --config configs/world_config.yaml
python scripts/build_static_site.py --config configs/world_config.yaml
```

## 13. Configuration File

Example `configs/world_config.yaml`:

```yaml
project_name: synthetic_wiki_world
world_name: Asteria

random_seed: 42

scale:
  num_countries: 1
  num_regions: 6
  num_cities: 20
  num_people: 50
  num_institutions: 35
  num_events: 50
  num_sources: 80
  num_wiki_pages: 150

generation:
  model_name: gpt-4.1
  temperature: 0.8
  max_retries: 3
  batch_size: 10

validation:
  strict_temporal_check: true
  allow_minor_source_conflicts: true
  max_duplicate_name_ratio: 0.02

site:
  output_dir: site_output
  include_disclaimer: true
  enable_search: true
```

## 14. Validation Rules

The validator should include at least the following checks.

### 14.1 Schema Validation

Check that every JSON object has required fields.

### 14.2 ID Validation

Check that all referenced IDs exist.

For example:

* `located_in` must refer to an existing location entity.
* `participant_ids` must refer to existing entities.
* `source_ids` must refer to existing sources.
* `internal_links` must refer to existing pages.

### 14.3 Temporal Validation

Check basic temporal consistency.

Examples:

* A person cannot die before being born.
* A person cannot found an institution before birth.
* An institution cannot participate in an event before being founded.
* A treaty cannot end before it starts.
* A city cannot be renamed before it is founded.

### 14.4 Page-Fact Consistency

Check whether wiki pages contradict hidden world facts.

Examples:

* Page says a city was founded in 1842, but entity file says 1845.
* Page says a person studied at one university, but relation file says another.
* Page cites a source that does not support the claim.

### 14.5 Link Validation

Check broken internal links.

### 14.6 Citation Validation

Check that references exist and are attached to supported facts.

## 15. Wiki Page Style Requirements

The wiki pages should feel like encyclopedia entries, not creative fiction.

Good style:

```text
Velmora is the capital and largest city of the Republic of Asteria. Located near the mouth of the Iven River, it developed from a fortified harbor settlement into the administrative center of the federal government during the late nineteenth century.
```

Bad style:

```text
In the shimmering dawn of a forgotten age, Velmora rose like a jewel beside the sea.
```

The tone should be:

* Neutral.
* Encyclopedic.
* Slightly dry.
* Specific.
* Internally linked.
* Supported by references.

The writing should avoid:

* Fantasy-novel tone.
* Overly dramatic descriptions.
* Generic LLM phrasing.
* Perfectly symmetrical histories.
* Too many grand claims.
* Too-clean causal explanations.

## 16. Realism Guidelines

The synthetic world should include realistic messiness.

Add:

* Old names.
* Failed reforms.
* Minor disputes.
* Regional variation.
* Conflicting interpretations.
* Obscure institutions.
* Dead political parties.
* Short-lived newspapers.
* Incomplete records.
* Small towns.
* Forgotten figures.
* Administrative leftovers.
* Unclear causality.
* Partial citations.
* Multiple historical schools of interpretation.

Avoid:

* Every major event having one obvious cause.
* Every institution having a clean founding date and clear mission.
* Every person being historically important.
* Every city having the same article structure.
* Every citation looking identical.
* Every cultural group being neatly defined.
* Every conflict ending in a clean treaty.

## 17. Static Site Requirements

The static site should be simple but usable.

Each page should include:

* Title.
* Short summary.
* Infobox.
* Main article sections.
* Internal links.
* References.
* Categories.
* Last generated version.
* Fictional-world disclaimer.

The home page should include:

* Project title.
* Disclaimer.
* Search box.
* Random article links.
* Main categories.
* Recent generated pages.

## 18. Safety and Disclosure

Even though the wiki is framed as a living civilization rather than a "fake wiki", every page must still make clear that the world is AI-generated and not a record of reality.

Every site page should include a banner such as:

```text
This is the visible surface of a self-evolving AI civilization. Its nations, people, institutions, wars, religions and archives are entirely AI-generated and continuously rewritten as the civilization advances its own history. Every page is this world telling its own story — not a record of the real one.
```

The system should avoid generating content that imitates real people, real countries, real companies, real universities, or real historical events too closely.

## 19. Acceptance Criteria

The MVP is complete when:

1. Running one command generates a full synthetic world.
2. The hidden world data is saved in structured JSON / JSONL files.
3. At least 100 wiki pages are generated.
4. The pages contain internal links and fictional references.
5. A static wiki site is built successfully.
6. The validator produces a consistency report.
7. The generated world has no major broken IDs.
8. The generated timeline has no obvious temporal contradictions.
9. Human feedback can be saved in `data/feedback/human_critiques.jsonl`.
10. The project README explains the motivation, design, pipeline, and file structure.

## 20. Future Extensions

After the MVP, we may extend the project into:

* Human red-team interface.
* Repair agent.
* Versioned world updates.
* Multi-hop QA generation.
* Retrieval benchmark.
* Citation faithfulness benchmark.
* Memory update benchmark.
* Parametric knowledge intrusion evaluation.
* Comparison between early synthetic worlds and human-refined synthetic worlds.

The long-term research question is:

> Can a language model faithfully enter and reason inside a fully synthetic knowledge world, or will it import assumptions from the real world?
