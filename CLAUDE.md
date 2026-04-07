# Skillable Intelligence — Claude Working Context

This file loads automatically every session. Read the documents it points to — not this summary.

---

## MANDATORY — File Storage Rule

**NEVER save documents, memory files, or any persistent content to the local hard drive.** All documentation, notes, decisions, and reference material must be stored in the repo (`docs/` or appropriate location) so it is on OneDrive and GitHub. No exceptions. Nothing important lives only on this machine.

---

## First — Read These Before Doing Anything

**These are not a skim.** Read each pass with a different lens — first for content, then for how everything interrelates. Re-reading is the point. See `docs/collaboration-with-frank.md` → "Re-reading Is the Point" for why.

| Step | Document | Why |
|---|---|---|
| 1 | `docs/collaboration-with-frank.md` | How Frank thinks, how to work together, the startup sequence. **Read this first, every session.** |
| 2 | `docs/Platform-Foundation.md` | Strategic authority — Guiding Principles, architecture, scoring framework, UX, personas. Where it conflicts with anything else, it wins. |
| 3 | `docs/Badging-and-Scoring-Reference.md` | Operational detail — badge names, color criteria, scoring signals, point values, penalties, thresholds, locked vocabulary. |
| 4 | `docs/next-session-todo.md` | **Read last.** What shipped in the previous session, what's open, and the FIRST thing to do this session. The "Shipped" section at the bottom is the historical record — read it when current behavior surprises you. The Foundation docs above lag the most recent architectural work; this doc is the bridge until they're synced. |

For the **complete inventory** of everything we know we want to do or have done — across every tool, every area, every status — see `docs/roadmap.md`. That doc is a reference, not a read-first. Use it when you need to look up "is this captured?" or "where does X fit?" or "what's our overall arc?"

---

## Project-Specific Rules

### Layer Discipline — Intelligence Belongs in the Intelligence Layer

The platform has THREE tools — **Inspector**, **Prospector**, **Designer** — that all sit on top of a shared **Intelligence layer**. The Intelligence layer owns ALL the logic about *what we know and how we evaluate it*: research, discovery, scoring math, normalization, cache versioning, validation, briefcase generation, model definitions, prompt assembly, locked vocabulary, classification, verdicts. The three tool layers own ONLY *the things that are tool-specific*: URL patterns, request parsing, template selection, view orchestration.

**The discipline rule:** if a function does intelligence work — scoring, normalizing, validating, computing, classifying, recomputing, deciding — it belongs in the **Intelligence layer** (`backend/intelligence_new.py`, `backend/scorer_new.py`, `backend/scoring_math.py`, `backend/scoring_config.py`, `backend/storage_new.py`, `backend/models_new.py`, `backend/prompt_generator.py`, `backend/researcher_new.py`, `backend/core_new.py`) where ALL three tools can call it. If it does view work — rendering a template, parsing a query string, redirecting, picking a default product index — it stays in the tool layer (`backend/app_new.py` Inspector routes, future Prospector routes, future Designer routes).

**How to test:** ask "would Prospector or Designer also need this if they were calling it?" If yes, it belongs in the shared layer. If no, it belongs in the tool. **When in doubt, default to shared.**

**Why this matters:** Prospector batch scoring + lookalikes are real work coming next, and Designer needs product intelligence (with the hard wall against company intelligence). Three tools cannot have three drifted copies of the same scoring logic. Several of the worst bugs in the codebase to date came from intelligence logic mistakenly placed in `app_new.py` (the Inspector Flask app), where it ran differently than the path the scorer took at score time, silently producing wrong scores.

| Belongs in the **Intelligence layer** | Belongs in the **tool layer** |
|---|---|
| `discover()`, `score()`, recompute, refresh | URL handlers, route decorators |
| Badge normalization (Phase 1 + Phase 2) | Request parsing, query param extraction |
| Cache versioning + invalidation | Template selection, response shaping |
| Verdict assignment, ACV recompute | Tool-only progress orchestration |
| Discovery tier / classification / org color computation | Tool-only UI defaults (e.g. selected product index) |
| Loading models from JSON | Anything no other tool would ever call |
| Anything another tool would also need | |

When you find intelligence logic living in a tool layer, **flag it as a bug-class violation** — it is the same severity as vocabulary drift or cache version lies. Fix or document the move to the shared layer.

### Legacy Boundary

Everything built before the Platform Foundation (April 4, 2026) is proof-of-concept. Never silently reuse old files, old prompts, old data, or old vocabulary. If it wasn't built from the Platform Foundation forward, it doesn't belong. Flag and fix — don't carry forward.

### Always Commit and Push

After completing any code changes, automatically stage, commit, and push without prompting.

### Never Mention the Preview Panel

The preview tool renders raw Jinja2 template syntax, not the running Flask app. After editing any template, do not mention the preview panel. To see changes, reload the Flask app.

### Grid Uniformity

Consistent 2-column grids. Field widths match across sections. Full-width sections with inner grids. Narrow dropdowns for short values. Vertical alignment via proper grid rows. Buttons match adjacent input height. Use `settings-grid` or `settings-grid-4cell` patterns.

### Skillable Terminology

Two cloud fabrics (Azure Cloud Slice, AWS Cloud Slice). Three virtualization fabrics (Hyper-V, ESX, Docker). "Fabric" is correct for these. **Never say "network fabric"** — networking is a capability of the virtualization fabrics, not a separate entity. See `docs/skillable-terminology.md` when created.

### No Inspector-to-Designer In-App Handoff

Intentional — tools serve different personas, accessed separately. The `analysis_id` bridges them at the data level. Never flag this as a missing feature.

### Decision Log

Decisions made during sessions are logged in `docs/decision-log.md`. This is write-only — never read it to determine what's current. The Foundation docs are best current thinking.

---

## Build Roadmap

See `docs/roadmap.md` for the consolidated inventory of everything we know we want to do, are doing, have done, or need to decide.

---

## Key Architecture

### Prompt Generation System — Three Layers

| Layer | File | What it does |
|---|---|---|
| **Configuration** | `backend/scoring_config.py` | All variables — pillar names, weights, badges, signals, penalties, thresholds, vocabulary |
| **Template** | `backend/prompts/scoring_template.md` | Instruction structure with `{PLACEHOLDER}` references to config |
| **Generated Prompt** | Built in memory by `prompt_generator.py` | Config injected into template at runtime. Never saved as static file. |

### Data Architecture — Three Domains

| Domain | What it contains | Access |
|---|---|---|
| **Product data** | What products are, labability assessments, orchestration details | Open — all tools including Designer |
| **Program data** | Lab series, outlines, activities, instructions (Designer) | Scoped — only your own programs |
| **Company intelligence** | Fit scores, badges, contacts, ACV estimates | Internal-only — Skillable roles only |

### Page Names

| Page | Name |
|---|---|
| Inspector home | **Inspector** |
| Product selection | **Product Selection** |
| Deep dive results | **Full Analysis** |

Discovery tier labels: Seems Promising, Likely, Uncertain, Unlikely

---

## Word Document Standards

**Font:** Calibri 10pt body, 8pt footer
**Logo:** `C:\Users\Frank.Gartland\OneDrive - Skillable\Sales Enablement\Keep\z-Skillable Logos\Skillable Logo\Default@4x.png` — right-aligned, ~1.1" wide
**Footer:** "Page X of Y" right-aligned, 8pt Calibri gray (#888888)

For full Word doc generation standards, see `docs/` reference files.
