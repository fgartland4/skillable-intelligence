# Skillable Intelligence — Claude Working Context

This file loads automatically every session. It points to the authoritative documents — read those, not this summary.

---

## Authoritative Documents — Source of Truth

| Document | Location | What it owns |
|---|---|---|
| **Platform-Foundation.md** | `docs/Platform-Foundation.md` | Strategic authority — Guiding Principles, Pillars, Dimensions, people, motivation, architecture, ACV model, UX structure. Where it conflicts with anything else, it wins. |
| **Badging-and-Scoring-Reference.md** | `docs/Badging-and-Scoring-Reference.md` | Operational detail — badge names, color criteria, scoring signals, point values, penalties, thresholds, locked vocabulary. Also the in-app explainability layer (GP3). |
| **Test-Plan.md** | `docs/Test-Plan.md` | Test strategy — 9 categories, GP traceability, pytest in `backend/tests/` |

---

## The New Architecture — What Matters

Everything built before the Platform Foundation (April 4, 2026) is proof-of-concept. The deliverables that define the new architecture:

| File | What it is |
|---|---|
| `docs/Platform-Foundation.md` | Strategic authority |
| `docs/Badging-and-Scoring-Reference.md` | Operational detail |
| `docs/Research-Methodology-Improvements.md` | Detection logic improvements |
| `docs/Designer-Session-Guide.md` | Session methodology for Designer foundation session |
| `docs/Designer-Session-Prep.md` | Designer session pre-read |
| `docs/Test-Plan.md` | Test strategy |
| `backend/scoring_config.py` | Configuration layer — Define-Once single source of truth |
| `backend/prompt_generator.py` | Template to runtime prompt assembly |
| `backend/prompts/scoring_template.md` | AI instruction template with placeholders |

Old code files (scorer.py, models.py, constants.py, core.py, app.py, templates, product_scoring.txt) will be rebuilt from these documents.

---

## Prompt Generation System — Three Layers

| Layer | File | What it does |
|---|---|---|
| **Configuration** | `backend/scoring_config.py` | All variables — pillar names, weights, badges, signals, penalties, thresholds, vocabulary. The one place anything changes. |
| **Template** | `backend/prompts/scoring_template.md` | Instruction structure for the AI with `{PLACEHOLDER}` references to config. |
| **Generated Prompt** | Built in memory by `prompt_generator.py` | Config injected into template at runtime. Never saved as static file. Always current. |

---

## Guiding Principles

- **GP1:** Right Information, Right Time, Right Person, Right Context, Right Way
- **GP2:** Why → What → How
- **GP3:** Explainably Trustworthy — every judgment traceable from conclusion to evidence
- **GP4:** Self-Evident Design — intent evident at every layer, variable names to UX
- **GP5:** Intelligence Compounds — It Never Resets
- **End-to-End Principle:** Same Pillar/Dimension/Requirement structure through every layer
- **Define-Once Principle:** All names, weights, thresholds defined once in config, referenced everywhere
- **WCAG AA Compliance:** Build standard — all color combinations validated

---

## Scoring Framework

Three Pillars (40/30/30):
- **Product Labability** (40%) — Provisioning, Lab Access, Scoring, Teardown
- **Instructional Value** (30%) — Product Complexity, Mastery Stakes, Lab Versatility, Market Demand
- **Customer Fit** (30%) — Training Commitment, Organizational DNA, Delivery Capacity, Build Capacity

Each Pillar scores out of 100 internally (sum of dimension scores), then weighted to Fit Score.

---

## Locked Vocabulary

See `docs/Badging-and-Scoring-Reference.md` "Vocabulary — Locked Terms" for the complete table.

Key terms:

| Use this | Never this |
|---|---|
| Fit Score | Composite Score / Lab Score |
| Product Labability | Technical Orchestrability |
| Instructional Value | Product Demand / Workflow Complexity |
| Customer Fit | Customer Motivation / Organizational Readiness (as separate pillars) |
| Product Complexity | Difficult to Master |
| Mastery Stakes | Mastery Matters / Consequence of Failure |
| Market Demand | Market Fit / Market Readiness / Strategic Fit |
| Green / Gray / Amber / Red | Pass / Partial / Fail / Yellow |
| Installable | Self-hosted (as data value) |

---

## Data Architecture — Three Domains

| Domain | What it contains | Access |
|---|---|---|
| **Product data** | What products are, labability assessments, orchestration details | Open — all tools including Designer |
| **Program data** | Lab series, outlines, activities, instructions (Designer) | Scoped — only your own programs |
| **Company intelligence** | Fit scores, badges, contacts, ACV estimates | Internal-only — Skillable roles only |

Stored separately from day one. Architectural separation, not just permissions.

---

## Page Names

| Page | Name |
|---|---|
| Inspector home | **Inspector** |
| Product selection | **Product Selection** |
| Deep dive results | **Full Analysis** |

Discovery tier labels: Seems Promising, Likely, Uncertain, Unlikely

---

## How Frank Wants to Work

1. **WHY → WHO → WHAT → HOW.** Always in this order. Never code without alignment.
2. **Digestible chunks.** No walls of text. One thing at a time.
3. **Confirm before acting.** Alignment must be explicit.
4. **Never delete Word docs** without asking.
5. **Recommend, then ask.** Surface better paths, but don't act until Frank agrees.
6. **Be a partner.** Think together. Flag patterns across tools. Collaborative momentum over speed.

---

## Decision Log

All decisions: `memory/decision-log.md` (Claude project memory folder). Update before any session ends.

---

## Word Document Standards

**Font:** Calibri 10pt body, 8pt footer
**Logo:** `C:\Users\Frank.Gartland\OneDrive - Skillable\Sales Enablement\Keep\z-Skillable Logos\Skillable Logo\Default@4x.png` — right-aligned, ~1.1" wide
**Footer:** "Page X of Y" right-aligned, 8pt Calibri gray (#888888)
