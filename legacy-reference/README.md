# Legacy Reference

This directory holds the proof-of-concept code that ran the platform **before** the Platform Foundation (April 4, 2026). It is **frozen** — nothing in here is actively imported by the running platform.

## Why this exists

Per `CLAUDE.md`'s Legacy Boundary rule:

> Everything built before the Platform Foundation (April 4, 2026) is proof-of-concept. Never silently reuse old files, old prompts, old data, or old vocabulary.

The code in this directory was the proof-of-concept Inspector / Prospector / Designer ecosystem. It was running on a parallel Flask app (`run_legacy.py` on port 5000) until the deep code review on 2026-04-07 (`docs/code-review-2026-04-07.md`) flagged that:

1. The dual-app architecture violated the new Layer Discipline principle
2. The legacy files were importing each other in a self-contained ecosystem that bypassed the Intelligence layer
3. None of the legacy code respected the locked vocabulary, the Pillar 2/3 rubric model, the canonical badge names, or the cache versioning rules

Rather than delete the legacy code, it was moved here so Frank (and future Claude sessions) can browse it as design reference and visual UX inspiration. The file structure mirrors where each file used to live so the moves are easy to read in `git log`.

## What it contains

| Path | Original location | What it was |
|---|---|---|
| `run_legacy.py` | repo root | Flask entry point on port 5000 (legacy Designer + Prospector) |
| `backend/app.py` | `backend/app.py` | Legacy Flask app |
| `backend/intelligence.py` | `backend/intelligence.py` | Legacy intelligence layer |
| `backend/scorer.py` | `backend/scorer.py` | Legacy scorer + Claude calls |
| `backend/researcher.py` | `backend/researcher.py` | Legacy web research |
| `backend/storage.py` | `backend/storage.py` | Legacy storage |
| `backend/core.py` | `backend/core.py` | Legacy verdict / classification utilities |
| `backend/models.py` | `backend/models.py` | Legacy dataclasses (no `Badge`, no `PillarScore`, no `FitScore`, no rubric fields) |
| `backend/constants.py` | `backend/constants.py` | Legacy constants — INCONSISTENT with the current `scoring_config.py`. Reference only. |
| `backend/config.py` | `backend/config.py` | Legacy config |
| `backend/routes/inspector_routes.py` | `backend/routes/inspector_routes.py` | Legacy Inspector blueprint |
| `backend/routes/prospector_routes.py` | `backend/routes/prospector_routes.py` | Legacy Prospector blueprint |
| `backend/routes/designer_routes.py` | `backend/routes/designer_routes.py` | Legacy Designer blueprint |
| `backend/prompts/discovery.txt` | `backend/prompts/discovery.txt` | Legacy discovery prompt (replaced by `discovery_new.txt`) |
| `backend/prompts/product_scoring.txt` | `backend/prompts/product_scoring.txt` | Legacy scoring prompt (replaced by the runtime-assembled prompt from `scoring_template.md`) |

## What it does NOT contain

- **The active code path.** All `_new.py` files (`app_new.py`, `intelligence_new.py`, `scorer_new.py`, `researcher_new.py`, `storage_new.py`, `core_new.py`, `models_new.py`, `config_new.py`) stayed in `backend/`. They are the running platform.
- **`scoring_config.py`, `scoring_math.py`, `prompt_generator.py`** — built fresh from the Foundation, never had a legacy counterpart.
- **`designer_engine.py`** — forward-looking stub for the future Designer Foundation Session, not legacy.
- **`backend/prompts/discovery_new.txt`, `scoring_template.md`, `instructional_design_guide.md`** — current prompts, in active use.

## How to read this for design reference

When you want to understand a design intent, prompt phrasing, or UX pattern from the proof-of-concept era:

1. **Browse files like any folder.** Everything is on disk, readable.
2. **Read the comments and docstrings**, not the code. The PoC code is full of inline thinking that captures Frank's design intent at the time. Focus on the WHY, not the HOW.
3. **Read the Jinja templates** in `backend/routes/` if you want to see how the legacy UX rendered specific badges or pillar layouts. (Note: Inspector templates were rebuilt from scratch and live in `tools/inspector/templates/` — those are NOT legacy.)
4. **Read the prompts** in `backend/prompts/` for the legacy scoring + discovery phrasing. These are the most valuable historical artifact because they show how Frank thought about the framework before the canonical/rubric architecture existed.
5. **Do NOT copy code.** Per the Legacy Boundary rule, don't lift implementation patterns from here. Read for intent, write fresh against the current foundations.

## How to revive (if you ever need to)

If you ever want to run the legacy Designer or Prospector at `localhost:5000` again:

1. Move the contents of `legacy-reference/backend/` back to `backend/`
2. Move `legacy-reference/run_legacy.py` back to the repo root
3. `python run_legacy.py`

But before you do that — ask whether the thing you actually need is in the active code path or in `legacy-reference/` as static text. Reviving the legacy app is almost never the right move.

## How to delete this entirely

When Designer and Prospector are fully rebuilt on the new architecture and you're confident you don't need the historical reference any more:

```bash
rm -rf legacy-reference/
git add -A && git commit -m "Retire legacy reference now that all tools are rebuilt"
```

The git history still has it forever.

## Provenance

Moved here in commit (Phase B of the deep code review fix sequence) on 2026-04-07. See `docs/code-review-2026-04-07.md` for the full review and the reasoning behind the move.
