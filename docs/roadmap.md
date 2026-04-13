# Skillable Intelligence — Roadmap

The **single prioritized list** of everything we need to do, are doing, or need to decide. One place. One source of truth.

**For "what to do this session"** → see `docs/next-session-todo.md` (names the first action, points here for everything else).

**For decisions and historical record** → see `docs/decision-log.md` (write-only — never read to determine what's current).

Best current thinking, always. Fully synthesized, never appended.

**Last refreshed:** 2026-04-13

---

## How to Read This Doc

| Icon | Meaning |
|---|---|
| 🟢 | **Active** — currently being worked on or next up |
| 🔵 | **Backlog** — wanted, not yet scheduled |
| ❓ | **Decision Needed** — requires alignment before implementation |
| ✓ | **Done** — shipped. Kept for historical context in the Done section at the bottom. |

Priority tags: **HIGH** / **MED** / **LOW** on every non-done item.

---

## §1 — Active Priorities

### Prospector UX Batch (11 items — shipped 2026-04-13) ✓

All 11 items shipped. See Done section for details.

### Prospector Background Batch Processing (shipped 2026-04-13) ✓

All 6 items shipped (PB1–PB6). `prospector_running.html` deleted. See Done section for details.

### Background Processing + Toast Notifications (aligned 2026-04-13)

Cross-platform feature: any long-running operation (Deep Dive, Prospector batch) can run in the background with a toast notification on completion — regardless of which page the user is on.

| # | Item | Priority | Status |
|---|---|---|---|
| **BG1** | **"Run in Background" button on Deep Dive progress modal** — closes the modal, keeps SSE alive, shows a persistent mini-indicator. User can navigate freely. | HIGH | 🟢 Ready to build |
| **BG2** | **Toast notification system** — small bar slides in from corner when a background operation completes. "Deep Dive for Cisco complete — View Results →". Stays 10 seconds, then fades. Works on any page. | HIGH | 🟢 Ready to build |
| **BG3** | **Wire Prospector batch completion to toast** — when a background batch finishes, toast fires wherever the user is. | MED | 🟢 After BG2 |

### Other Active Items

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **1** | **Fresh validation round** — run 7–10 companies through discovery + Deep Dive with all fixes active. Trellix, Workday, MongoDB, CompTIA, EC-Council, ASU, Posit, Pluralsight. Gate to demo-readiness. | HIGH | 🟢 Ready to run | Nothing |
| **2** | **PL Provisioning badge sparsity** — products scoring 30/35 on Provisioning sometimes show only 2 badges. Badge selector needs to emit more when facts support them. Observed on Sage 50 and Sage 100. | HIGH | 🟢 Fix during validation | Validation findings |
| **3** | **ACV audience transparency** — large companies with small training populations need badges explaining why ACV is modest relative to company size. Consider "Admin Training Focus" or "Niche Admin Audience" badge. | HIGH | 🟢 Fix during validation | Validation findings |

---

## §2 — Near-Term Work

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **5** | **Documentation Job B** — per-product report (doc icons). Three options: three-pillar summary modal, Word doc preview, executive briefing. Frank's framing: dimension-level drill-down. Design conversation needed first. | HIGH | 🔵 Needs alignment | Design decision |
| **6** | **Deployment** — Render or Azure Web App. Decision from Frank's team. Scope once decided: secrets loading, gunicorn entry point, persistent storage, HTTPS. | HIGH | ❓ Needs team decision | External |
| **7** | **Pillar 2 fact extractor reliability** — intermittent empty `mastery_stakes` / `lab_versatility` / `market_demand` drawers. Safety net in rubric_grader keeps things flowing but root cause is in the extractor. Investigate-first. | MED | 🔵 | Nothing |
| **8** | **Parallel product scoring in Deep Dive** — run all products' extractors simultaneously instead of sequential per-product rounds. Performance improvement. | MED | 🔵 | Nothing |
| **9** | **Refresh button bug** — navigates to SSE endpoint URL instead of HTML waiting page. Renders raw event-stream text. ~10 min fix. | MED | 🔵 | Nothing |
| **10** | **GP4 cleanup: centralize 8 dimension name constants** — duplicated across pillar scorers and rubric_grader. Code quality, not a scoring bug. | LOW | 🔵 | Nothing |
| **11** | **Route file split** — `app.py` is ~1300 lines. Split into per-tool route files + shared core. Maintainability improvement. | LOW | 🔵 | Nothing |

---

## §3 — Authentication + RBAC

Full design documented in `docs/Platform-Foundation.md` → **Authentication and Access Control**. Seven roles, four boundary lines.

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **12** | **Authentication + RBAC implementation** — 7 roles, 4 boundary lines, Capabilities Editor, customer product visibility scoping. | HIGH | 🔵 Design done, implementation waiting | Deployment decision (#6) |
| **13** | **Skillable Capabilities Editor workflow** — UI/process for Sales Engineering + Product to edit knowledge files (`skillable_capabilities.json`, `delivery_patterns.json`, `competitors.json`). Currently requires repo access. | MED | 🔵 | Auth implementation (#12) |
| **14** | **Customer product visibility scoping** — pre-release products in Designer need org-level visibility controls so customers building labs on unreleased products can restrict what others see. | MED | 🔵 | Designer (#18) + Auth (#12) |

---

## §4 — HubSpot Integration

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **15** | **HubSpot Stage 1 — Company Records** — discovery intelligence → HubSpot company properties. ACV potential, top product, labability summary, key signals, lab platform. | HIGH | ❓ Needs RevOps conversation for field mapping | RevOps |
| **16** | **HubSpot Stage 2 — Deal Records** — per-product intelligence → deal records. Fit Score, Pillar readings, Seller Briefcase content. | MED | 🔵 | Stage 1 (#15) + RevOps deal structure |
| **17** | **HubSpot integration thresholds** — score threshold for auto-create/update. | MED | ❓ Needs RevOps conversation | RevOps |

---

## §5 — Designer

Biggest workstream. Design docs exist (`docs/Designer-Session-Prep.md`, `docs/Designer-Session-Guide.md`). Zero code beyond a stub in `designer_engine.py`.

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **18** | **Designer Foundation Session** — People → Purpose → Principles → Rubrics → UX process. Same pattern used for Inspector. | HIGH | 🔵 Needs design conversation | Nothing — can start anytime |
| **19** | **Designer build** — eight-phase pipeline: Intake, Program outline, Lab breakdown, Activity design, Scoring recommendations, Draft instructions, Bill of materials, Export package. Tests → code → testing pattern. | HIGH | 🔵 | Foundation session (#18) |
| **20** | **Designer export format** — what goes in the ZIP, BOM format, environment template shape. | MED | ❓ | Foundation session (#18) |
| **21** | **Intelligence-driven Phase 1 prompting** — when a program has company_name/analysis_id, pre-populate Designer's starting context from Inspector intelligence. | MED | 🔵 | Designer build (#19) |
| **22** | **Designer collaborative lab BOM** — how collaborative lab network setup, credential pools, and subscription pools surface in the BOM. | LOW | ❓ | Designer build (#19) |
| **23** | **Style Guide content injection** — wire actual file content from standards library per selection. Currently only the name is injected. | LOW | 🔵 | Designer build (#19) |

---

## §6 — Prospector Enhancements

Core Prospector is functional. These are enhancements beyond the current implementation.

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **24** | **Product Lookalikes** — companies marketing didn't know about, found because they use products that pass Product Labability. Product-fit matching, not firmographic. | MED | 🔵 | Core Prospector stable |
| **25** | **Contacts** — specific humans responsible for training/enablement for products Skillable can serve. | MED | 🔵 | Core Prospector stable |
| **26** | **ABM Second Contact Column** — decision maker + champion, stacked. Sellers need both the person who signs and the person who champions internally. | MED | 🔵 | Contacts (#25) |
| **27** | **ZoomInfo CSV Column Mapping** — map ZoomInfo CSV columns to platform fields so redundant research can be skipped. Reduces API costs. | LOW | 🔵 | Nothing |
| **28** | **Competitive Capture to Prospector Feed** — auto-document competitors discovered during Inspector analysis, feed into Prospector's target universe. GP5 in action. | LOW | 🔵 | Nothing |

---

## §7 — Inspector Enhancements

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **29** | **Skillable customer identification UX** — when an analyzed company is already a Skillable customer, show it visually. Drives different seller conversation (expansion vs acquisition). | MED | ❓ Needs data source decision (CRM / static config / HubSpot) | Data source decision |
| **30** | **Refine Key Technical Questions in Seller Briefcase** — WHO each question should be asked of (explicit role/title) + bolding/formatting for scannability. | MED | 🔵 | Nothing |
| **31** | **Top Blockers List** — track companies/products that are undeliverable by specific blocker type. Enables pattern detection across the pipeline. | LOW | 🔵 | Nothing |

---

## §8 — Research Engine + Scoring

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **32** | **Comprehensive scoring framework alignment review** — walk every scored field against Badging-and-Scoring-Reference.md and confirm no drift between docs / config / math / template / cached data. | MED | 🔵 | Post-validation |
| **33** | **CTF as first-class Lab Versatility option** — verify CTF / Capture The Flag is clear in `LAB_TYPE_MENU` and surfaces in product reports for cybersecurity. | LOW | 🔵 | Nothing |
| **34** | **LMS / LXP Detection — surface platform name** — badge should display specific platform name (Docebo, Cornerstone, Moodle, Skillable TMS), not generic label. | LOW | 🔵 | Nothing |

---

## §9 — Infrastructure

| # | Item | Priority | Status | Blocked by |
|---|---|---|---|---|
| **35** | **SQLAlchemy ORM / Database migration** — currently JSON files. Plan: SQLite then Azure SQL. ORM layer should be built so storage backend can be swapped. | MED | ❓ When data volume justifies it | Volume threshold |
| **36** | **WCAG AA accessibility check** — automated contrast ratio validation. All text/background combos must pass 4.5:1 normal, 3.0:1 large. | MED | 🔵 | Nothing |
| **37** | **Migrate Prospector + Designer off legacy `_nav.html` / `_theme.html`** — still using legacy shared templates with hardcoded hex. | LOW | 🔵 | Nothing |

---

## §10 — Decisions Needed

Items blocked on alignment conversations, not engineering effort.

| # | Item | Who decides | Notes |
|---|---|---|---|
| **D1** | **Deployment platform — Render vs Azure Web App** | Frank's team | Blocks auth, external sharing. Render is provisioned; Azure aligns with Skillable infra. |
| **D2** | **HubSpot field mapping** | RevOps | Stage 1 company records, Stage 2 deal records. |
| **D3** | **Doc icon content format** | Frank + Claude | Three-pillar summary? Word preview? Executive briefing? |
| **D4** | **Skillable customer data source** | Frank's team | CRM lookup? Static config? HubSpot? |
| **D5** | **Database migration timing** | Engineering | When does JSON-on-disk become a bottleneck? |
| **D6** | **Designer AI persona name** | Frank | "Neo" used in design docs but not confirmed. |

---

## Done

Historical record of shipped work. Kept for context — do not redo.

<details>
<summary>Expand shipped items (~70 items)</summary>

### Platform Foundation + Rebuild (Steps 1–4)
- ✓ Alignment conversation process
- ✓ Automated test identification from authoritative docs
- ✓ Test suite built (118 tests across 13 modules)
- ✓ Backend rebuilt from Platform Foundation forward
- ✓ Foundation docs rewritten (Platform-Foundation.md + Badging-and-Scoring-Reference.md)
- ✓ Define-Once principle enforced — all scoring params in `scoring_config.py`
- ✓ Anti-hardcoding test suite (5 tests, 4 phases, pre-commit hook)
- ✓ Three-pillar hierarchy (50/20/30 weighting — rebalanced from 40/30/30 on 2026-04-12)
- ✓ Pillar 1 scorer — viable_fabrics as single source of truth
- ✓ Pillar 2 scorer — rubric model with category-aware baselines
- ✓ Pillar 3 scorer — rubric model with org-type baselines, per-company unification
- ✓ Rubric grader — narrow Claude slice for Pillar 2/3 qualitative grading
- ✓ Fit Score composer — Technical Fit Multiplier (retuned 2026-04-12)
- ✓ ACV calculator — five consumption motions, org-type adoption overrides, technology-specific rate tiers
- ✓ Badge selector — post-scoring display layer, locked naming rules
- ✓ Post-filters — deterministic guardrails for AI output quality
- ✓ Confidence coding (confirmed/indicated/inferred)
- ✓ Deterministic Python ACV math — AI no longer touches dollars
- ✓ Locked rate variables ($6 / $8 / $14 / $45)
- ✓ ACV tier thresholds ($250K HIGH / $50K MED / <$50K LOW)
- ✓ Verdict grid — score range × ACV tier → action label
- ✓ Cache + Append architecture — one persistent analysis per company
- ✓ SCORING_LOGIC_VERSION — smart cache invalidation

### Inspector
- ✓ Two-stage flow (discovery + product selection → Deep Dive)
- ✓ Product Selection page with tier sections
- ✓ Full Analysis page — hero + 70/30 Pillar layout + bottom row
- ✓ Per-product Seller Briefcase (KTQ Opus + Conversation Starters Haiku + Account Intelligence Haiku)
- ✓ In-place product swap via dropdown
- ✓ ACV by Use Case widget
- ✓ Hero section — Fit Score + ACV Potential + Verdict
- ✓ Badge evidence hover (1.5s delay, modal with bullets + source + confidence)
- ✓ Score bar color gradient (green ≥70% → amber → red <40%)
- ✓ Word export
- ✓ Competitive products box
- ✓ Browser back button fix
- ✓ Product family picker
- ✓ Dimension names ALL CAPS in UX

### Documentation Job A (In-App Explainability)
- ✓ Modal infrastructure built
- ✓ Content dynamically sourced from scoring_config.py
- ✓ WHY-WHAT-HOW per pillar, per dimension
- ✓ Verdict Grid explainer
- ✓ ACV explainer
- ✓ Wired to ? icons throughout

### Prospector
- ✓ Batch discovery — paste names or CSV, parallel processing (3 concurrent)
- ✓ Results table sorted by ACV potential
- ✓ Deep Dive top product checkbox
- ✓ Cost/time estimator (inline, updates live)
- ✓ Per-company timeouts (3 min discovery, 5 min Deep Dive)
- ✓ SSE timeout increased to 60 min with auto-reconnect
- ✓ History page
- ✓ Excel export

### Standard Search Modal
- ✓ ONE shared modal for all tools — progress mode, decision mode, in-place transition
- ✓ Single EventSource in the entire codebase
- ✓ SSE contract: status/done/error

### Research Engine
- ✓ Source type classification + differentiated fetch depth
- ✓ Targeted OpenAPI/Swagger spec queries
- ✓ Lab platform detection — product-level + company-level
- ✓ Single canonical lab platform list in scoring_config.py
- ✓ Provisioning multi-path detection (6 fabrics)
- ✓ Container disqualifiers
- ✓ Installable vs cloud detection
- ✓ Collaborative lab detection (2 patterns)
- ✓ Break/Fix scenario detection
- ✓ Simulated attack scenario detection
- ✓ Product complexity detection (consumer/simple UX)
- ✓ Lab versatility — 12 lab types mapped to product categories

### Scoring Fixes (2026-04-13 Marathon Session)
- ✓ Fit Score always recalculates from live config
- ✓ Orchestration method auto-derived from Pillar 1
- ✓ Per-product ACV extrapolation (replaces flat multiplier)
- ✓ Org-type adoption rate overrides
- ✓ Wrapper org pipeline end-to-end
- ✓ IV baseline recalibration + CF baseline recalibration
- ✓ Badge naming enforcement (25+ deterministic overrides)
- ✓ Compliance grader sharpened
- ✓ MFA penalty -15
- ✓ Orphan Risk 3-tier spectrum
- ✓ Verdict grid 45-64 recalibrated
- ✓ Scoring dimension amber credit reduced to 1/3
- ✓ Open source ACV discount (25% of normal adoption)
- ✓ Market Demand reframed as paid training demand
- ✓ ACV complexity-aware rate tier (Multi-VM → $45/hr)
- ✓ ACV org-type motion labels (Student Training, Faculty Development for academics)
- ✓ BS/MS consolidation for universities

### Infrastructure
- ✓ Pre-commit hook integration (badge names + no-hardcoding)
- ✓ Hex color cleanup (Inspector + theme)
- ✓ render.yaml configured (not yet deployed)

### ADR + Auth Design
- ✓ ADR-0000 Solution Overview written
- ✓ Authentication and Access Control section in Platform-Foundation.md — 7 roles, 4 boundary lines
- ✓ Skillable Capabilities Editor role defined
- ✓ Customer product visibility scoping documented as design intent

</details>

---

## How Items Move

1. **Idea surfaces** → added to the appropriate section as 🔵 with priority.
2. **Item gets prioritized** → moved to §1 Active or §2 Near-Term and marked 🟢. `next-session-todo.md` names the first action.
3. **Item ships** → moved to Done section with past-tense description.
4. **Item needs alignment** → flagged ❓ with the open question in §10.

One list. One source of truth. `next-session-todo.md` points here for everything beyond "start here."
