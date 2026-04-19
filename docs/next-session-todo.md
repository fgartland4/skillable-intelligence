# Next Session — Master Todo List

**Last updated:** 2026-04-19 (end of Session 1 — Rewrite Prep Sequence)

This doc is the master list of **everything we know we need to do** — not just the rewrite. Grouped by category, prioritized within each. For deeper context on any item, follow the `→` pointer.

---

## §1 — Session 2 (Immediate Next Session)

### 1.1 — Read-in order

New Claude reads in this order at session start (see `docs/handoff-to-next-claude.md` Part 2 for full detail):

1. Project `CLAUDE.md`
2. `docs/collaboration-with-frank.md` — especially the **5 Hard Rules** at the top
3. `docs/handoff-to-next-claude.md` — the rewrite framework + 13 specific improvement areas + outliers + calibration artifacts
4. `docs/rewrite-plan.md` — consolidated rewrite plan with R1–R10 top-line requirements
5. `docs/rewrite-dev-team-spec.md` — dev team's architectural contract + 8 open questions
6. `docs/Platform-Foundation.md` — updated ACV Target Model section
7. `docs/acv-framework-reference.md` — standalone rate card + use case matrix
8. `docs/decision-log.md` — 2026-04-19 entry
9. This doc — full inventory of what's next

Then ask Frank what Session 2's first action is.

### 1.2 — Session 2 primary deliverables

| # | Item | Output |
|---|---|---|
| **S2-1** | **Comprehensive codebase + docs audit** | `docs/rewrite-codebase-audit.md` — inventory every file in `backend/`, `tools/`, `scripts/`, `docs/`. Surface drift, dead code, undocumented tools, `legacy-reference/` contents, test coverage gaps, stale references. |
| **S2-2** | **Validate the 13 Specific Areas** from `handoff-to-next-claude.md` Part 4 with Frank point-by-point | Refined list of named pain points, Frank-confirmed |
| **S2-3** | **Validate R1–R10 non-negotiable requirements** from `rewrite-plan.md` with Frank | Confirmed/adjusted requirements list |
| **S2-4** | **Draft Requirements Document** | `docs/rewrite-requirements.md` — Why/What/How at every section/subsection. Captures: architectural overview, non-functional requirements, API contract, data model, component architecture, intelligence layer specs, RBAC role model + permission matrix, prompt structure (10 standard approaches), testing strategy, deployment topology |
| **S2-5** | **Write structural behavior tests** (Python) | `backend/tests/test_rewrite_equivalence.py` — per-org-type motion applicability, rate math determinism, ATP exclusion, cert attribution, layer boundaries. Structural tests only, NOT number snapshots. Ports cleanly to Jest/Vitest in Session 3. |
| **S2-6** | **Resolve 8 open questions with dev team** (listed in `rewrite-dev-team-spec.md`) | Decisions on: Azure AI Foundry, Redis scope, auth roles, integration surfaces, Ant Design version, testing framework, deployment pipeline, observability schema |
| **S2-7** | **Complete systematic "ACV Potential" → "ACV Target" rename** in non-archival docs | No remaining metric-name references; schema field names (`acv_potential_low/high` in `known_customers.json`) stay until schema migration in rewrite |

---

## §2 — Session 3+ (The Rewrite Itself)

Per `docs/rewrite-plan.md` sequencing. Not exhaustive here; key items:

| # | Item |
|---|---|
| **S3-1** | TypeScript monorepo structure: `packages/intelligence/`, `packages/ui-kit/`, `apps/inspector/`, `apps/prospector/`, `apps/designer/` |
| **S3-2** | Port intelligence layer FIRST — prompts, scorers, ACV calculator, badge selector, rubric grader, researcher |
| **S3-3** | `scoringConfig.ts` as single source of truth (port from `scoring_config.py`) |
| **S3-4** | Claude client abstraction (`ILLMClient`) — Anthropic direct + Azure Foundry implementations |
| **S3-5** | Data store abstraction (`IStore`) — Redis + in-memory implementations |
| **S3-6** | Implement the **10 standard prompt approaches** in TypeScript audience grader (NEW — not in Python) |
| **S3-7** | Port Inspector tool first (existing functionality) |
| **S3-8** | Port Prospector tool |
| **S3-9** | Build Designer tool (see §4 below — this is a major workstream unto itself) |
| **S3-10** | RBAC from commit #1: `useAuth()`, `usePermissions()`, route middleware |
| **S3-11** | Ant Design theming + single `<ProgressModal />` component |
| **S3-12** | Jest/Vitest test suite — port structural tests from Python, add unit + integration layers |
| **S3-13** | Behavior-equivalence validation — structural tests pass on both Python + TypeScript |
| **S3-14** | Handoff to dev team for Azure App Service provisioning, Azure Cache for Redis, Azure B2C, CI/CD, deployment |

---

## §3 — Known ACV Framework Outliers (Session 2/3 Prompt Refinement)

From the 2026-04-19 21-company calibration. Each has a mapped **standard approach** (principle-level, not a patch). Implementation happens in TypeScript rewrite, not Python.

| # | Company | Delta | Standard Approach |
|---|---|---|---|
| **O1** | Microsoft | +54% | Structural prior: free-library completion rate 10–20% of registered users |
| **O2** | CompTIA | +35% | PBT-only scope for cert candidates (30–50% of total exam volume) |
| **O3** | Skillsoft | +18% | Close to range — marginal tuning |
| **O4** | EC-Council | +92% | ATP exclusion + PBT-only scope combined |
| **O5** | QA | +137% | Revenue-triangulated ILT audience + strict lab-bearing multi-day definition |
| **O6** | Deloitte | −60% | Multi-source triangulation — sum published practice sizes (Azure, AWS, GCP, Salesforce, ServiceNow, SAP) |
| **O7** | NVIDIA | −70% | Big-tier threshold calibration (raise from 100K? — 185K currently hits Big rates when Mid may be right) |
| **O8** | Pluralsight | −60% | Rate-card refinement — ELP Big rate ($4) too low for Pluralsight's premium positioning |
| **O9** | Trellix / Eaton / Milestone / Calix | mixed | Better triangulation for small cos with limited public disclosure — OR accept as floor |

---

## §4 — Designer Tool (MAJOR Workstream, Not Yet Built)

**Status:** Design docs exist (`docs/Designer-Session-Prep.md`, `docs/Designer-Session-Guide.md`). Zero code beyond `backend/designer_engine.py` stub. This is the biggest unscheduled workstream in the platform.

| # | Item | Priority | Status |
|---|---|---|---|
| **D1** | **Designer Foundation Session** — People → Purpose → Principles → Rubrics → UX process (same pattern used for Inspector Foundation) | HIGH | Needs design conversation; can start anytime |
| **D2** | **Designer build** — 8-phase pipeline: Intake, Program outline, Lab breakdown, Activity design, Scoring recommendations, Draft instructions, Bill of materials, Export package. Tests → code → testing pattern | HIGH | Blocked by Foundation Session |
| **D3** | **Designer export format** — ZIP contents, BOM format, environment template shape | MED | Blocked by Foundation Session |
| **D4** | **Intelligence-driven Phase 1 prompting** — when a program has company_name/analysis_id, pre-populate Designer's starting context from Inspector intelligence | MED | Blocked by Designer build |
| **D5** | **Designer collaborative lab BOM** — how collaborative lab network setup, credential pools, subscription pools surface in the BOM | LOW | Blocked by Designer build |
| **D6** | **Style Guide content injection** — wire actual file content from standards library per selection (currently only name injected) | LOW | Blocked by Designer build |
| **D7** | **Designer AI persona name** | Frank | "Neo" used in design docs but not confirmed |

**Note:** Designer should be built natively in TypeScript during Session 3+, not in Python first. Foundation Session can happen before rewrite (design work, not code).

---

## §5 — HubSpot Integration

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **H1** | **HubSpot Stage 1 — Company Records** — discovery intelligence → HubSpot company properties (ACV Target, top product, labability summary, key signals, lab platform) | HIGH | Needs RevOps conversation for field mapping |
| **H2** | **HubSpot Stage 2 — Deal Records** — per-product intelligence → deal records (Fit Score, Pillar readings, Seller Briefcase content) | MED | Blocked by Stage 1 + RevOps deal structure |
| **H3** | **HubSpot integration thresholds** — score threshold for auto-create/update | MED | Blocked by RevOps conversation |

---

## §6 — Authentication + RBAC Implementation

Design documented in `docs/Platform-Foundation.md` → Authentication and Access Control. 7 roles, 4 boundary lines.

| # | Item | Priority | Status | Note |
|---|---|---|---|---|
| **A1** | **Authentication + RBAC implementation** — 7 roles, 4 boundary lines, Capabilities Editor, customer product visibility scoping | HIGH | Design done | Covered by R1 in rewrite plan — baked in from commit #1 in Session 3+ |
| **A2** | **Skillable Capabilities Editor workflow** — UI/process for Sales Engineering + Product to edit knowledge files (`skillable_capabilities.json`, `delivery_patterns.json`, `competitors.json`). Currently requires repo access | MED | Blocked by A1 |
| **A3** | **Customer product visibility scoping** — pre-release products in Designer need org-level visibility controls | MED | Blocked by A1 + Designer (D2) |

---

## §7 — Prospector Enhancements

Core Prospector is functional. These are enhancements beyond the current implementation.

| # | Item | Priority | Status |
|---|---|---|---|
| **P1** | **Product Lookalikes** — companies marketing didn't know about, found because they use products that pass Product Labability. Product-fit matching, not firmographic | MED | Backlog |
| **P2** | **Contacts** — specific humans responsible for training/enablement for products Skillable can serve | MED | Backlog |
| **P3** | **ABM Second Contact Column** — decision maker + champion, stacked | MED | Blocked by P2 |
| **P4** | **ZoomInfo CSV Column Mapping** — map ZoomInfo CSV columns to platform fields | LOW | Backlog |
| **P5** | **Competitive Capture to Prospector Feed** — auto-document competitors discovered during Inspector analysis, feed into Prospector's target universe | LOW | Backlog |

---

## §8 — Inspector Enhancements

| # | Item | Priority | Status |
|---|---|---|---|
| **I1** | **Skillable customer identification UX** — when an analyzed company is already a Skillable customer, show it visually (expansion vs acquisition conversation) | MED | Needs data source decision |
| **I2** | **Refine Key Technical Questions in Seller Briefcase** — WHO each question should be asked of (explicit role/title) + bolding/formatting for scannability | MED | Backlog |
| **I3** | **Top Blockers List** — track companies/products that are undeliverable by specific blocker type; pattern detection across pipeline | LOW | Backlog |

---

## §9 — Background Processing + Toast Notifications

Cross-platform feature; any long-running operation can run in background with toast on completion.

| # | Item | Priority | Status |
|---|---|---|---|
| **BG1** | **"Run in Background" button on Deep Dive progress modal** — closes the modal, keeps SSE alive, persistent mini-indicator | HIGH | Ready to build in rewrite (not Python) |
| **BG2** | **Toast notification system** — slides in from corner on background-operation completion, works on any page | HIGH | Ready to build in rewrite |
| **BG3** | **Wire Prospector batch completion to toast** — when a background batch finishes, toast fires wherever the user is | MED | Blocked by BG2 |

---

## §10 — Known Bugs and Defects (Python Codebase)

These are known issues in the Python codebase. **Default handling: fix during the rewrite via principle-level design, not patch-and-run in Python.** A few are small enough to fix in Python if urgent.

| # | Bug | Severity | Fix Path |
|---|---|---|---|
| **B1** | `researcher.py` is ~2000 lines (monolithic) | MED | Decompose during port in Session 3; do NOT refactor Python |
| **B2** | `scoring_config.py` is ~4000 lines | MED | Split by concern during port in Session 3 |
| **B3** | Zero test coverage | HIGH | Structural tests in Session 2 (Python) port to Jest in Session 3 |
| **B4** | No RBAC | HIGH | Baked in from commit #1 in Session 3 (R1 in rewrite plan) |
| **B5** | Prompts scattered inline across code | MED | Extract to `packages/intelligence/prompts/` directory in Session 3 |
| **B6** | Claude SDK calls in multiple files | MED | Centralize through `ILLMClient` abstraction in Session 3 (R2) |
| **B7** | JSON file I/O via `storage.py` | MED | Migrate to Redis in Session 3 (per dev team spec) |
| **B8** | `legacy-reference/` directory exists | LOW | Delete or move to `docs/archive/` during Session 2 audit |
| **B9** | Cache invalidation via string constants (`SCORING_MATH_VERSION`, `RUBRIC_VERSION`, `RESEARCH_SCHEMA_VERSION`) | LOW | Formalize as typed enums in Session 3 |
| **B10** | "ACV Potential" vocabulary drift across docs/UX/code | MED | Systematic rename during rewrite; don't grep-and-replace Python (R8) |
| **B11** | Refresh button bug — navigates to SSE endpoint URL instead of HTML waiting page | LOW | Dies with Flask in Session 3; or ~10 min Python fix if urgent |
| **B12** | PL Provisioning badge sparsity — products scoring 30/35 on Provisioning sometimes show only 2 badges | MED | Badge selector root-cause investigation. Priority: before demo. Fix in Python OR catch in rewrite port |
| **B13** | Pillar 2 fact extractor intermittent empty drawers — `mastery_stakes`, `lab_versatility`, `market_demand` sometimes empty | MED | Investigate root cause in researcher prompt; may also benefit from 10 standard approaches applied in rewrite |
| **B14** | Badge-to-score consistency — 1-badge vs 4-badge products across the same dimension | HIGH | Root-cause investigation across 12 dimensions. Researcher extraction? Scorer crediting? Badge selector emitting? |
| **B15** | Parallel product scoring in Deep Dive (currently sequential per-product) | MED | Performance win in Session 3; design naturally in TypeScript |
| **B16** | GP4 cleanup — 8 dimension name constants duplicated across pillar scorers + rubric_grader | LOW | Centralize during port |
| **B17** | `app.py` is ~1300 lines (Flask routes + business logic mixed) | LOW | Dies in Session 3 port — routes live in `apps/*/routes/`, logic in services |

---

## §11 — Research Engine + Scoring Cleanup

| # | Item | Priority | Status |
|---|---|---|---|
| **R1** | **Comprehensive scoring framework alignment review** — walk every scored field against `docs/Badging-and-Scoring-Reference.md` and confirm no drift between docs / config / math / template / cached data | MED | Covered by Session 2 audit |
| **R2** | **CTF as first-class Lab Versatility option** — verify CTF / Capture The Flag clear in `LAB_TYPE_MENU` and surfaces in product reports for cybersecurity | LOW | Backlog |
| **R3** | **LMS / LXP Detection** — badge should display specific platform name (Docebo, Cornerstone, Moodle, Skillable TMS), not generic label | LOW | Backlog |

---

## §12 — Infrastructure

| # | Item | Priority | Status |
|---|---|---|---|
| **INF1** | **Database migration** — currently JSON files. Plan per dev team spec: Redis. Happens in Session 3 port. | MED | Covered by rewrite |
| **INF2** | **WCAG AA accessibility check** — automated contrast ratio validation. All text/background combos must pass 4.5:1 normal, 3.0:1 large | MED | Ant Design handles most of this; spot-check in Session 3 |
| **INF3** | **Migrate Prospector + Designer off legacy `_nav.html` / `_theme.html`** | LOW | Dies in Session 3 — React/Ant Design replaces Jinja templates |

---

## §13 — Decisions Still Needed (External / Frank's Team)

Items blocked on decisions from Frank's team or external conversations, not engineering effort.

| # | Decision | Who | Notes |
|---|---|---|---|
| **DEC1** | HubSpot field mapping (Stage 1 + Stage 2) | RevOps | Blocks H1/H2/H3 |
| **DEC2** | Doc icon content format | Frank + Claude | Three-pillar summary? Word preview? Executive briefing? |
| **DEC3** | Skillable customer data source | Frank's team | CRM lookup? Static config? HubSpot? Blocks I1 |
| **DEC4** | Designer AI persona name | Frank | "Neo" in docs, not confirmed |
| **DEC5** | Resolve 8 dev team rewrite questions | Dev Team + Frank | Listed in `docs/rewrite-dev-team-spec.md` |

**Note:** D1 (Render vs Azure) and D5 (database migration timing) from earlier roadmap are resolved — Azure + Redis per dev team spec.

---

## §14 — Out-of-Scope for This Rewrite (Documented in `rewrite-plan.md` Non-Goals)

For clarity, items NOT being addressed in Session 2/3:

- Redesigning the ACV framework from scratch (v2 is locked; Session 3 ports it)
- Building new tools beyond Inspector / Prospector / Designer
- Multi-tenancy / SaaS-ing the platform
- Fine-tuning custom LLMs
- Replacing `known_customers.json` with CRM integration
- HubSpot integration beyond Stage 1 / Stage 2
- Native mobile apps

---

## §15 — Historical Context

For decisions history: `docs/decision-log.md` (2026-04-19 entry covers Session 1)
For all prior done work: `docs/roadmap.md` Done section
For session handoff discipline: `docs/handoff-to-next-claude.md` Part 10

---

## Scope Summary

**Sessions 2 and 3 are the critical path.** Session 2 produces audit + Requirements Doc + tests. Session 3+ executes the rewrite including the Designer build, RBAC, and 10 prompt refinements. The rewrite is the mechanism by which 80% of the items in this inventory get resolved — bugs become "fix during port," roadmap enhancements become "build in TypeScript natively," and the Designer workstream gets its native home.

Items that remain independent of the rewrite:
- Decisions Frank's team / RevOps owns (§13)
- Designer Foundation Session (can happen any time as design conversation)
- HubSpot integration (external conversation)

Everything else flows through the rewrite.
