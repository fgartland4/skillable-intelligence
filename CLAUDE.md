# Skillable Intelligence — Claude Working Context

This file loads automatically every session. Read it before doing anything else.

---

## Who I'm Working With

**Frank Gartland** — friends call him **Franko**. Chief Solutions Officer at Skillable (https://skillable.com). Responsible for helping customers improve how they think about, create, deliver, and communicate their strategy for embedding hands-on lab experiences within skill development and validation journeys.

---

## How Frank Wants to Work — Non-Negotiables

### 1. WHY → WHO → WHAT → HOW. Always in this order.
Never start coding until all four are clear and Frank has confirmed alignment.
- **WHY:** What problem are we solving?
- **WHO:** Who are we solving it for?
- **WHAT:** What exactly will we build or change? Agreed, not assumed.
- **HOW:** Only after WHY/WHO/WHAT are locked.

**Never just start coding without explicit alignment.**

### 2. Digestible chunks — no walls of text.
Give information in pieces Frank can read and respond to. Do not write a wall of copy and then start coding. One thing at a time. Wait for a response.

### 3. Confirm before acting.
When a request is ambiguous, ask one focused clarifying question. Confirm WHAT before starting HOW. Alignment must be explicit — never assumed.

### 4. Never delete Word docs or external-facing files without asking.
Always confirm before deleting `.docx`, published content, or anything used to communicate with teams.

### 5. Proactively recommend — but ask before doing.
If a better path exists, flag it. Don't just execute what's asked without surfacing a better option. But don't act on it until Frank agrees.

---

## UX North Star

**Right person · Right information · Right time · Right context.**

Every UI decision — what to show, what to hide, when, and to whom — is evaluated against this principle.

---

## The Two Framework Documents — Source of Truth

| Document | Location | What it owns |
|---|---|---|
| **Badging-Framework-Core.md** | `docs/Badging-Framework-Core.md` | Every canonical badge name, colors, color criteria, display rules, locked vocabulary |
| **Scoring-Framework-Core.md** | `docs/Scoring-Framework-Core.md` | All scoring signals, point values, score ranges, penalty deductions, ceiling flags, verdict labels |

**If it's not in one of these two documents, it doesn't exist.**

Read `docs/Badging-Framework-Core.md` before touching any badge name, color, or scoring vocabulary.

---

## Locked Vocabulary

| Use this | Never this |
|---|---|
| Product Labability | Technical Orchestrability |
| Instructional Value | Workflow Complexity / Product Complexity (as dimension) |
| Organizational Readiness | Training Ecosystem / Lab Maturity |
| Market Readiness | Market Fit / Strategic Fit |
| Amber | Yellow (for badge color) |
| Azure Cloud Slice | Path A1 |
| Custom API / BYOC | Path A2 |
| Hyper-V / VM | Path B |
| Simulation | Path C |

---

## Decision Log

All decisions made across sessions are recorded in:
`memory/decision-log.md` (in the Claude project memory folder)

Update it before any session ends. If a decision was made and not logged, log it now.

---

## product_scoring.txt — High-Risk File

`backend/prompts/product_scoring.txt` drives badge names and scores in every live Inspector run.

Rules:
1. The badge list in this file must exactly match `docs/Badging-Framework-Core.md`
2. Never change a badge name here without updating `Badging-Framework-Core.md` first
3. Never use old vocabulary anywhere in this file
4. Verify the badge list matches after any edit

---

## Word Document Standards

All generated Word docs use these standards:

**Font:** Calibri 10pt body · Calibri 8pt footer

**Logo:** `C:\Users\Frank.Gartland\OneDrive - Skillable\Sales Enablement\Keep\z-Skillable Logos\Skillable Logo\Default@4x.png` — right-aligned in header, ~1.1" wide. Always use this PNG.

**Footer:** "Page X of Y" — right-aligned, 8pt Calibri, gray (#888888). Use OxmlElement PAGE/NUMPAGES field codes.

**Page setup:** US Letter · 0.85" left/right margins · 0.9" top/bottom · Header/footer distance 0.35"

**Color palette:**
| Color | Hex | Use |
|---|---|---|
| Dark green | `#136945` | Primary — headings, table headers, borders |
| Deep forest | `#0A3E28` | Darkest brand green |
| Bright green | `#24ED98` | Accent |
| Primary purple | `#7000FF` | AI Moment callouts |
| Body text | `#1A1A1A` | All body copy |
| Gray labels | `#606060` | Secondary labels |
| Page number gray | `#888888` | Footer |

**Tables:** Full width (9792 DXA). Dark-green header rows, white bold text. Alternate row shading. Cell margins 50 twips.

**Bullets:** Left indent 400 twips, hanging 160 twips. Bullet run: `\u2022 ` 7pt Calibri `#1A1A1A`.

**Spacing:** Section headings before=120/after=40. Body paragraphs after=60. Bullets after=40. Keep compact — fit as much as possible on page 1.

---

## Platform Overview

Three tools under one Flask backend:

| Tool | Route | Persona | Purpose |
|---|---|---|---|
| **Inspector** | `/inspector` | SE / AE | Deep product labability analysis → Dossier |
| **Prospector** | `/prospector` | Marketing / RevOps | Batch company scoring → ranked list |
| **Designer** | `/designer` | LC / PS | Lab program design wizard |

Repo: `fgartland4/skillable-intelligence` on GitHub
Deployed on Render → target: `intelligence.skillable.com`
