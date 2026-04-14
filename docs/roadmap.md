# Skillable Intelligence — Roadmap

The **single prioritized list** of everything we need to do, are doing, or need to decide. One place. One source of truth.

**For "what to do this session"** → see `docs/next-session-todo.md` (names the first action, points here for everything else).

**For decisions and historical record** → see `docs/decision-log.md` (write-only — never read to determine what's current).

Best current thinking, always. Fully synthesized, never appended.

**Last refreshed:** 2026-04-14 (post saturated-only ACV redesign + full 549-record retrofit)

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

### Validate ACV across 10 diverse companies, then hand to Marketing (next session §1)

Full 549-record retrofit shipped 2026-04-14 EOD using the new saturated-only ceiling design + two-column calibration (current + Potential). Spot-checks are clean but a human pass across diversity is the right gate before Marketing uses it for ICP targeting.

| # | Item | Priority | Status |
|---|---|---|---|
| **V1** | Spot-check 10 diverse companies across org types + sizes (list in `next-session-todo.md §1`) | HIGH | 🟢 Next session |
| **V2** | CSV export → hand to Marketing (was the whole goal of this work) | HIGH | 🟢 After V1 clean |
| **V3** | Fine-tune individual stage assignments in `known_customers.json` as Frank's read of specific customers evolves | MED | 🔵 Ongoing |

### Badge-to-Score Consistency Investigation (after validation)

Badges are not consistently defending the scores they accompany. Root cause investigation needed across all dimensions — not patches. See `next-session-todo.md §1b` for the full investigation plan.

| # | Item | Priority | Status |
|---|---|---|---|
| **BI1** | Trace 1-badge vs 4-badge products through full pipeline (researcher → scorer → badge selector) | HIGH | 🟢 After validation |
| **BI2** | Identify root cause: researcher not extracting, scorer not crediting, or badge selector not emitting? | HIGH | 🟢 |
| **BI3** | Extend investigation to all 12 dimensions | HIGH | 🟢 |
| **BI4** | Structural fix — not band-aids | HIGH | 🟢 |
| **BI5** | `scripts/rescore_pillars.py` (shipped 2026-04-14) now enables Python-only scoring changes to propagate across the cache with zero Claude calls — unblocks iterative tuning during BI | — | ✓ Tool ready |

### ACV Holistic — Saturated-Only Cap Redesign (shipped 2026-04-14) ✓

Known-customer floor/ceiling rules simplified — saturated customers get a 1.3× current ceiling cap; every other stage leaves the ceiling to Claude's holistic reasoning subject to the universal $30M hard cap. Two-column calibration block shows both current ACV and estimated ACV Potential. `_raw_claude` preservation makes future guardrail tuning free (pure Python re-application). Full 549-record retrofit + 47-group auto-dedup complete. Stage taxonomy simplified to descriptive-only for non-saturated. See Done section.

### Prospector Modal Documentation (shipped 2026-04-14) ✓

Three Prospector `?` modals rewritten to reflect the full current design (Option 2 holistic, known-customer calibration, partnership, pitfalls A/B/D/E/F, rate tiers, verdict grid). Docs mode restored to the original white surface design. One modal component, one API, across Inspector + Prospector. Inspector ACV hero modal rate table fixed (was hardcoded $9/hr, now reads VM_LOW_RATE). See Done section.

### Unified ACV Model (shipped 2026-04-13) ✓

All 6 org types locked and implemented. See `docs/unified-acv-model.md` and Done section.

### Prospector UX Overhaul (shipped 2026-04-13) ✓

Results-first home, background batch processing, merged input pages, Configure HubSpot with field mapper. See Done section.

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
| **PatC** | **Pattern C — K-12 / district budget-signal audience** (deferred 2026-04-14). Parkway School District has a ~$750k CTE/PD budget line that never enters the math — model multiplies ~135 students × cloud-tier rate and lands at $18-52k. Need: (1) new researcher field for "training-dedicated budget" when visible; (2) routing rule that lets budget feed Motion 2/3-style partner/employee audience sizing. Structural, not a prompt tweak. | MED | 🔵 Backlog | Nothing |
| **PatG** | **Pattern G — parent/subsidiary entity dedup** (deferred 2026-04-14). Records like "Deloitte" / "Deloitte Consulting" / "Deloitte Consulting LLP" and "Grand Canyon University" / "Grand Canyon Education" normalize to different keys and auto-dedup can't safely collapse them without risking different entities. Frank's call: probably stays manual. Use `scripts/merge_companies.py` when duplicate clusters surface. | LOW | 🔵 Deferred | Nothing (manual tool exists) |
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
<summary>Expand shipped items (~90 items)</summary>

### 2026-04-14 — Saturated-Only ACV Redesign + Full Retrofit

**Design corrections:**
- ✓ Saturated-only ceiling cap — only `saturated` customers get 1.3× current cap; all other stages uncapped (subject to universal $30M hard cap)
- ✓ Floor rule preserved for ALL stages — `acv_low >= current_acv` (safety, never undersell)
- ✓ Expected-low multipliers abandoned as fake precision
- ✓ Two-column calibration block — anonymized block shows current ACV AND estimated ACV Potential per stage so Claude anchors prospects on Potential (the right question)
- ✓ `_raw_claude` preservation — raw Claude numeric output stored alongside post-guardrail result so future guardrail tuning propagates pure-Python with zero Claude calls
- ✓ Customer stage relabeling — 4 saturated (CompTIA, EC-Council, SANS, Skillsoft); everyone else in growth stages with no cap (Microsoft, Deloitte, Siemens, Eaton, Commvault, Epiq, Cengage, Trellix, Cisco, GCU, Multiverse, LLPA, Zero-Point, Omnissa, Boxhill, New Horizons)

**Tools shipped:**
- ✓ `scripts/compute_customer_potentials.py` — one-time caps-disabled pass computing ACV Potential for each non-saturated known customer; populates `acv_potential_low/high` in gitignored `known_customers.json`
- ✓ `scripts/merge_companies.py` — force-merge parent/service-line duplicate records the auto-dedup can't safely collapse (Deloitte / Deloitte Consulting / Deloitte Consulting LLP class)
- ✓ `scripts/rescore_pillars.py` — pure-Python pillar rescore against cached facts + rubric grades; zero Claude calls. Propagates pillar/dimension weight, strength tier, signal value, baseline, penalty, Technical Fit Multiplier changes across the whole cache in milliseconds per product.

**Patterns A/B/D/E/F prompt fixes** (diagnosed from the Parkway / Multiverse / Zero-Point / New Horizons low-estimate cluster):
- ✓ A — removed "fraction who actually consume" deflator; trust calibrated adoption rates directly
- ✓ B — annual vs cumulative rule (prefer annual; if only cumulative, divide by 2-3yr program life / 4yr academic)
- ✓ D — floor informs the low bound without collapsing range-width (prevents zero-width artificial uniformity)
- ✓ E — existing DIY / in-house lab platform is a POSITIVE ICP signal (existing demand), not a displacement discount
- ✓ F — rate tier driven by workload complexity, not deployment label (SaaS cybersecurity still needs VM rates)

**Pattern C — K-12 budget-signal audience** — deferred as structural backlog (needs researcher field + routing rule). Pattern G — parent/subsidiary entity dedup — deferred per Frank as too fragile to automate at scale; manual merge via `scripts/merge_companies.py` when needed.

**Operations shipped:**
- ✓ Full 549-record holistic ACV retrofit at 10-way concurrency — 14.6 min, 0 failures
- ✓ Auto-dedup pass — 47 obvious duplicate groups merged
- ✓ Concurrency bumped 3 → 10 for Prospector batch + retrofit runner
- ✓ Deloitte 3-record merge ($420k, $4.5M, $8.5M-$16M discoveries → 1 at $12M-$22M)
- ✓ Zero-Point Security 2-record merge (identical names) → 1 at $210k-$520k

**Prospector UX polish:**
- ✓ Amber pulsing dot for running batches (visually distinct from completed green)
- ✓ Column tooltips on every Prospector column header
- ✓ "Why" → "Top Signal" rename (avoid word collision with "Rationale")
- ✓ "Estimated ACV" → "ACV Potential" rename
- ✓ "Prom. / Pot. / Unc. / Unl." short tier labels with full-text "Promising Products" / etc. tooltips
- ✓ Content Development partnership-ACV handling (GP Strategies class — purple "PARTNERSHIP" chip instead of dollar range)
- ✓ Partnership flag propagates through row builder + both CSV exports (acv_type column)

**Modal system:**
- ✓ Docs mode restored to original white-surface info-modal design using `--sk-modal-*` tokens (920px, accent rule, WHY/WHAT/HOW eyebrows, scannable tables)
- ✓ Inspector ACV hero modal rate-table hardcode fixed (was $9/hr, now reads `VM_LOW_RATE`)
- ✓ Legacy `.info-modal-*` CSS consolidated out of `full_analysis.html` into shared `_search_modal.html` scoped under `.search-modal-card.is-docs`
- ✓ Three Prospector `?` modals rewritten (Researched Companies / How ACV is Estimated / How Companies Are Scored) with Option 2 architecture, confidence chip legend, guardrail explainer, pitfalls ABDEF
- ✓ Shared modal API: `openSearchModal` / `openSearchModalDecision` / `openSearchModalInfo` / `openSearchModalDocs` / `scrollToSearchModalSection` / `transitionSearchModalToProgress`

**Documentation synced:**
- ✓ Platform-Foundation.md — Option 2 Holistic ACV section, known-customer calibration, partnership ACV, pitfalls A/B/D/E/F, Prospector column spec, white-docs-modal note, 2-call discovery cost
- ✓ Badging-and-Scoring-Reference.md — operational Holistic ACV guardrail section (hard cap, range ratio, per-user ceiling, known-customer schema, stage ceiling multipliers, output scrubber, anonymized calibration, partnership, pitfalls)
- ✓ collaboration-with-frank.md — "Simpler is usually right" + over-engineering detection patterns + "blow it out" trust-path check

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
