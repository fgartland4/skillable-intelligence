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

## §2 — Session 3+ (The Rewrite — Core Port + Proactive Enhancement Rollup)

Per `docs/rewrite-plan.md` sequencing. The rewrite is not just a port — enhancements from §§7–11 roll IN proactively because building them in Python first and then rewriting is throwaway work. Sections below are organized so the rollup is explicit.

### 2.1 — Core rewrite mechanics

| # | Item |
|---|---|
| **S3-1** | TypeScript monorepo structure: `packages/intelligence/`, `packages/ui-kit/`, `apps/inspector/`, `apps/prospector/`, `apps/designer/` |
| **S3-2** | `scoringConfig.ts` as single source of truth (port from `scoring_config.py`, split by concern per §10 B2) |
| **S3-3** | Claude client abstraction (`ILLMClient`) — Anthropic direct + Azure Foundry implementations (R2) |
| **S3-4** | Data store abstraction (`IStore`) — Redis + in-memory implementations (R2) |
| **S3-5** | Jest/Vitest test suite — port structural tests from Python, add unit + integration layers (R10) |
| **S3-6** | RBAC from commit #1: `useAuth()`, `usePermissions()`, route middleware (R1 — absorbs §6 A1, A3) |
| **S3-7** | Ant Design theming + single `<ProgressModal />` component platform-wide (R6) |
| **S3-8** | Behavior-equivalence validation — structural tests pass on both Python + TypeScript |
| **S3-9** | Handoff to dev team for Azure App Service + Redis + B2C + CI/CD + deployment |

### 2.2 — Intelligence layer port + prompt refinements

| # | Item |
|---|---|
| **S3-10** | Port intelligence layer — prompts, scorers, ACV calculator, badge selector, rubric grader, researcher |
| **S3-11** | Extract prompts to `packages/intelligence/prompts/` directory (resolves §10 B5) |
| **S3-12** | Implement the **10 standard prompt approaches** in TypeScript audience grader (NEW — closes the ACV outliers from §3) |
| **S3-13** | **Scoring framework alignment review** (§11 R1) — executed as part of intelligence-layer port; verify docs / config / math / template all align |
| **S3-14** | **CTF as first-class Lab Versatility option** (§11 R2) — build into `LAB_TYPE_MENU` in TypeScript, surface in product reports |
| **S3-15** | **LMS/LXP detection — surface specific platform name** (§11 R3) — badge emits Docebo/Cornerstone/Moodle/Skillable TMS |
| **S3-16** | **Badge-to-score consistency** (§10 B14, B12) — root-cause investigation across 12 dimensions during port; structural fix while translating |
| **S3-17** | **Pillar 2 fact extractor reliability** (§10 B13) — address intermittent empty drawers by applying standard approach #2 (evidence-forcing) and #1 (structural priors) to P2 prompts |

### 2.3 — Inspector tool — port + enhancement rollup

| # | Item |
|---|---|
| **S3-18** | Port Inspector core (hero + pillar cards + seller briefcase + product chooser) |
| **S3-19** | **Skillable customer identification UX** (§8 I1) — when an analyzed company is already a customer, show visually (drives expansion vs acquisition conversation). Built natively during Inspector port; needs DEC3 resolved first |
| **S3-20** | **Refine Key Technical Questions in Seller Briefcase** (§8 I2) — WHO to ask each question of (explicit role/title) + bolding/formatting |
| **S3-21** | **Top Blockers List** (§8 I3) — track companies/products undeliverable by blocker type; pattern detection |
| **S3-22** | **Refresh button bug** (§10 B11) — dies naturally with Flask; React routing doesn't reproduce it |
| **S3-23** | **PL Provisioning badge sparsity fix** (§10 B12) — badge selector emits more when facts support (part of S3-16 work) |

### 2.4 — Prospector tool — port + enhancement rollup

| # | Item |
|---|---|
| **S3-24** | Port Prospector core (batch list, filters, CSV export, row drill-down) |
| **S3-25** | **Background processing** (§9 BG1) — "Run in Background" functionality built natively in React with persistent state |
| **S3-26** | **Toast notification system** (§9 BG2) — Ant Design notification + global state; works on any page |
| **S3-27** | **Prospector batch completion toast** (§9 BG3) — wire batch completion through S3-26 |
| **S3-28** | **Product Lookalikes** (§7 P1) — companies marketing didn't know about; product-fit matching, not firmographic. Build during Prospector port because list view is the natural surface |
| **S3-29** | **Contacts surface** (§7 P2) — specific humans for training/enablement per product. New data domain; needs data source |
| **S3-30** | **ABM Second Contact Column** (§7 P3) — decision maker + champion stacked (blocked by S3-29) |
| **S3-31** | **ZoomInfo CSV column mapping** (§7 P4) — map ZoomInfo CSV to platform fields to skip redundant research. Low-lift in React |
| **S3-32** | **Competitive Capture to Prospector Feed** (§7 P5) — auto-document competitors from Inspector analysis into Prospector universe |

### 2.5 — Designer tool — native build

| # | Item |
|---|---|
| **S3-33** | **Designer Foundation Session** (§4 D1) — People → Purpose → Principles → Rubrics → UX. Can happen before rewrite code starts; output informs requirements |
| **S3-34** | **Designer build** (§4 D2) — 8-phase pipeline (Intake → Program outline → Lab breakdown → Activity design → Scoring recs → Draft instructions → BOM → Export). Tests → code → testing pattern, native in TypeScript |
| **S3-35** | **Designer export format** (§4 D3) — ZIP contents, BOM format, environment template shape |
| **S3-36** | **Intelligence-driven Phase 1 prompting** (§4 D4) — when program has company_name/analysis_id, pre-populate Designer context from Inspector intelligence |
| **S3-37** | **Designer collaborative lab BOM** (§4 D5) — collaborative lab network, credential pools, subscription pools surfacing |
| **S3-38** | **Style Guide content injection** (§4 D6) — wire actual file content from standards library per selection |

### 2.6 — Performance + cleanup items

| # | Item |
|---|---|
| **S3-39** | **Parallel product scoring in Deep Dive** (§10 B15) — Promise.all in TypeScript is trivially idiomatic; currently sequential in Python |
| **S3-40** | **Centralize 8 dimension name constants** (§10 B16) — one typed enum export, referenced everywhere |
| **S3-41** | **`legacy-reference/` cleanup** (§10 B8) — delete or move to `docs/archive/` during Session 2 audit |
| **S3-42** | **Cache invalidation — typed version stamps** (§10 B9) — discriminated union for three-tier invalidation |
| **S3-43** | **WCAG AA accessibility check** (§12 INF2) — Ant Design handles most; spot-check contrast ratios per component |

---

### Items NOT absorbed by the rewrite (stay independent)

These items don't naturally flow through the rewrite and need separate handling:

- **HubSpot integration** (§5 H1, H2, H3) — external conversation with RevOps; data model work, not a UI/port concern. Can happen before, during, or after rewrite independently.
- **Skillable Capabilities Editor workflow** (§6 A2) — separate workflow/UX design, needs its own conversation after core RBAC lands (S3-6)
- **Frank's team decisions** (§13 DEC1–DEC5) — external decisions blocking specific items

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

**Zero Python fixes. Everything flows through the rewrite.**

Frank confirmed 2026-04-19: whatever was working on **2026-04-17** is demo-worthy and stays that way. Python is frozen. No demos between now and Session 3+ need v2 framework numbers. We don't patch Python.

**→ For every bug + architectural improvement below, see [`docs/rewrite-bugs-and-improvements-detail.md`](rewrite-bugs-and-improvements-detail.md)** for hyper-detailed Why/What/How per item so rewrite-Claude proactively fixes, not just translates.

| # | Bug | Severity | Port-time Resolution |
|---|---|---|---|
| **B1** | `researcher.py` is ~2000 lines (monolithic) | MED | Decompose into per-pillar fact extractors during port (S3-10) |
| **B2** | `scoring_config.py` is ~4000 lines | MED | Split by concern during port (S3-2) |
| **B3** | Zero test coverage | HIGH | Structural tests in Session 2 (Python) port to Jest in Session 3 (S3-5) |
| **B4** | No RBAC | HIGH | Baked in from commit #1 in Session 3 (R1, S3-6) |
| **B5** | Prompts scattered inline across code | MED | Extract to `packages/intelligence/prompts/` directory (S3-11) |
| **B6** | Claude SDK calls in multiple files | MED | Centralize through `ILLMClient` abstraction (R2, S3-3) |
| **B7** | JSON file I/O via `storage.py` | MED | Migrate to Redis via `IStore` abstraction (S3-4) |
| **B8** | `legacy-reference/` directory exists | LOW | Delete or move to `docs/archive/` during Session 2 audit (S3-41) |
| **B9** | Cache invalidation via string constants | LOW | Formalize as typed discriminated union (S3-42) |
| **B10** | "ACV Potential" vocabulary drift across docs/UX/code | MED | Systematic rename during rewrite; new code uses `acvTarget` natively (R8) |
| **B11** | Refresh button bug — navigates to SSE endpoint URL | LOW | Dies with Flask; React routing doesn't reproduce (S3-22) |
| **B12** | PL Provisioning badge sparsity | MED | Part of badge-to-score investigation during intelligence layer port (S3-16, S3-23) |
| **B13** | Pillar 2 fact extractor intermittent empty drawers | MED | Apply standard approaches #1 (structural priors) and #2 (evidence-forcing) in TypeScript prompts (S3-17) |
| **B14** | Badge-to-score consistency across 12 dimensions | HIGH | Root-cause investigation during intelligence layer port (S3-16) |
| **B15** | Sequential product scoring in Deep Dive | MED | `Promise.all` in TypeScript natively (S3-39) |
| **B16** | 8 dimension name constants duplicated | LOW | Centralize as typed enum export (S3-40) |
| **B17** | `app.py` is ~1300 lines (Flask routes + business logic mixed) | LOW | Dies in port — routes in `apps/*/routes/`, logic in services (S3-1) |

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
