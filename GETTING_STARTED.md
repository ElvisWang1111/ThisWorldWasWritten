# Getting started

A two-layer synthetic wiki generator. The **hidden world layer** (structured
JSON/JSONL ground truth) is generated first; the **wiki rendering layer**
(Wikipedia-style pages) is rendered from it and built into a static site.

See `readme.md` for the full design spec.

## 1. Install

```bash
conda create -n fakewiki python=3.11 -y
conda activate fakewiki
pip install -r requirements.txt
```

## 2. Preview offline (no API key)

A deterministic demo world is included so you can see the site immediately:

```bash
python scripts/make_demo_world.py     # write a tiny fixed world to data/
python scripts/validate_world.py      # consistency report -> data/world/validation_report.json
python scripts/build_static_site.py   # build the site -> site_output/
open site_output/index.html
```

## 3. Generate a real world with an LLM

The LLM client is **OpenAI-compatible** and points at **OpenRouter** by default,
but works with any compatible endpoint (OpenAI, Together, a local vLLM, …).

Set your key (the env var name is configurable in the YAML; default
`OPENROUTER_API_KEY`):

```bash
export OPENROUTER_API_KEY=sk-or-...
```

Pick your endpoint / model in `configs/world_config.yaml`:

```yaml
generation:
  base_url: https://openrouter.ai/api/v1
  model: anthropic/claude-3.5-sonnet   # any model your endpoint serves
  api_key_env: OPENROUTER_API_KEY
```

Then run the whole pipeline:

```bash
python scripts/run_pipeline.py --config configs/world_config.yaml
open site_output/index.html
```

## Pipeline stages

| # | Stage | Output | Needs LLM |
|---|-------|--------|-----------|
| 1 | World bible | `data/world/world_bible.json` | yes |
| 2 | Entities | `data/world/entities.jsonl` | yes |
| 3 | Events + timeline | `data/world/events.jsonl`, `timeline.jsonl` | yes |
| 4 | Relations | `data/world/relations.jsonl` | yes |
| 5 | Sources | `data/world/sources.jsonl` | yes |
| 6 | Validate (hidden world) | `data/world/validation_report.json` | no |
| 7 | Render wiki pages | `data/wiki/pages.jsonl` (+ links/categories/references) | yes |
| 8 | Validate + build site | `site_output/` | no |

Run a subrange (e.g. re-render and rebuild without regenerating the world):

```bash
python scripts/run_pipeline.py --start 7 --stop 8
```

Or run any single stage with its own script (`scripts/generate_*.py`,
`validate_world.py`, `render_wiki_pages.py`, `build_static_site.py`).

## Tuning scale

Edit `scale:` in `configs/world_config.yaml`. The default is intentionally small
for fast, cheap runs. Increase `num_cities`, `num_people`, etc. for a larger
world (the README targets ~150 pages for the full MVP).

`render:` controls how long/detailed each article is (sections, paragraphs,
tokens).

## Growing the world (contributions)

The world is not frozen after the first run — you can keep expanding it, like
editing a real wiki. New content is merged into the **hidden world** (with stable
ids and a consistency check), then only the affected pages are rendered.

### Advancing history (evolution ticks)

The world has a clock (`data/world/world_state.json`: `current_year`,
`years_per_tick`, `open_tensions`). Each **tick** moves history forward a fixed
number of years and produces the next layer of record — developing open
tensions, adding events/people/institutions, and leaving at least one new
tension for later. A directive is optional.

```bash
python scripts/evolve.py                       # one autonomous 25-year tick
python scripts/evolve.py --directive "A drought triggers mass migration."
python scripts/evolve.py --ticks 3             # three ticks in a row
python scripts/evolve.py --years 50            # advance 50 years this tick
```

Defaults live under `world_state:` in the config (start_year 1950, 25/tick).
Each tick logs to `data/feedback/chronicle.jsonl`.

### From one country to a region

To broaden a single country into a multi-country region with cross-border wars,
treaties and trade:

```bash
python scripts/expand_world.py --countries 3
```

### Submit a free-text contribution

```bash
python scripts/contribute.py "Add a rival coastal republic named Threnos that
fought a trade war with Asteria in the 1880s, and the diplomat who negotiated
the truce."
```

The AI turns this into new entities, events, relations and fictional sources,
appends them to `data/world/*.jsonl`, logs the submission to
`data/feedback/contributions.jsonl`, renders pages for the new entities, and
rebuilds the site. Flags: `--no-build`, `--no-render`, `--rerender-all`
(also re-render existing pages so they link to the new content).

## Web submissions on GitHub (the "submit" page)

Because GitHub Pages is static, each submission is processed by a GitHub Action
(the browser can't run the model). Opening an issue runs **one evolution tick**;
the directive and the number of years are both optional. The flow:

1. A visitor opens the **Contribute** page and clicks *Submit a contribution*,
   which opens an issue form (`.github/ISSUE_TEMPLATE/contribution.yml`).
2. The `contribute` workflow (`.github/workflows/contribute.yml`) runs the AI
   expansion, commits the new world data, rebuilds the site, deploys to Pages,
   then comments on and closes the issue.

One-time setup:

- **Add the API key as a secret**: repo → Settings → Secrets and variables →
  Actions → New repository secret, name `OPENROUTER_API_KEY`.
- **Enable Pages**: Settings → Pages → Source = "GitHub Actions".
- **Set your repo URL** in `configs/world_config.yaml` under `site.repo_url`
  (e.g. `https://github.com/you/fake-wiki`) so the Contribute button appears,
  then rebuild and commit.
- **Commit the world data** so the Action can read/extend it (the `data/`
  entries in `.gitignore` are already commented out).

Ordinary pushes to `main` redeploy the site via `.github/workflows/pages.yml`.

## Tests

```bash
pytest
```

## Human feedback

Record why a page looks fake (Section 9 of the spec):

```python
from synthetic_world.feedback import add_feedback
from synthetic_world.utils import load_config
cfg = load_config("configs/world_config.yaml")
add_feedback(cfg, "page_000001", "fake-looking",
             ["citations all look identical", "timeline too clean"],
             "add contested sources and a failed reform")
```

A future repair agent (`prompts/repair_world_from_feedback.md`) can consume
`data/feedback/human_critiques.jsonl` to fix the *hidden world* first, then
re-render affected pages.
