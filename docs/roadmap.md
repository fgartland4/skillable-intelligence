# Skillable Intelligence — Roadmap

The **single consolidated inventory** of everything we know we want to do, are doing, have done, or need to decide. One place. One source of truth for the long arc.

**For "what to do this session" → see `docs/next-session-todo.md`** (the focused near-term action list, refreshed every session).

**For decisions and the historical record → see `docs/decision-log.md`** (architectural decisions logged with date and reasoning).

---

## Quick orientation (read first)

**Current top priorities** — these three are what next-session work should drive against:

1. **§1 SOTI re-score verification** (Inspector §C) — the universal variable-badge rule landed but isn't yet verified. First action of next session. See `next-session-todo.md §1`.
2. **ACV input estimation refinement** (Architecture §B) — Cohesity + Epiq are showing implausibly low ACVs. Math is correct; AI inputs are too conservative. Pairs with the Cohesity review in `next-session-todo.md §5.5`.
3. **Refine variable-driven badge logic across all 3 pillars** (Architecture §B) — extend the universal variable-badge rule from Provisioning to every dimension. Depends on #1 above.

**Approximate state of the inventory:** ~55 ✓ Done items captured for historical context, ~20 🟢 Active or pull-ready, ~70 🔵 Backlog items prioritized HIGH/MED/LOW, ~15 ❓ Decisions Needed. See the per-section tables below.

**How to use this doc:** Don't read it cover-to-cover. Use the TOC to jump to a section. The status icon and priority on each item tells you whether it's worth your attention right now. The wide description column is intentional — it's there so you can act on an item without having to grep the codebase first.

---

## Table of Contents

- [§A — Macro Build Sequence](#a--macro-build-sequence) · the 9-step arc
- [§B — Architecture & Foundation](#b--architecture--foundation) · scoring math, prompt generation, badge architecture, info modal content
- [§C — Inspector](#c--inspector) · Inspector tool features and operational improvements
- [§D — Prospector](#d--prospector) · Prospector tool features (mostly upcoming)
- [§E — Designer](#e--designer) · Designer tool features (deferred until new code push)
- [§F — Research Engine](#f--research-engine) · research and detection logic
- [§G — Infrastructure](#g--infrastructure) · backend infrastructure
- [§H — Cross-Cutting Concerns](#h--cross-cutting-concerns) · WCAG, doc linking, LMS detection, UX notes
- [§I — Decisions Needed](#i--decisions-needed) · items requiring alignment conversations

---

## How to read this doc

Status icon prepends every item name. Priority (HIGH / MED / LOW) appears for items not yet done.

| Icon | Meaning |
|---|---|
| ✓ | **Done** — shipped, captured for historical record. Don't redo. |
| 📝 | **Partial** — some of it landed, some remains. Description says what's left. |
| 🟢 | **Active** — currently being worked on or queued in next-session-todo.md |
| 🔵 | **Backlog** — wanted, not scheduled. Pull when prioritized. |
| ❓ | **Decision Needed** — requires an alignment conversation before implementation |

---

## §A — Macro Build Sequence

The 9-step arc of the platform build. Steps 1-5 mostly complete (with step 5 ongoing as testing surfaces refinements). Steps 6-9 are the next major workstreams.

| Step | Description |
|---|---|
| ✓ **1. Alignment conversation** | Claude brings questions, Frank decides. No coding without alignment. The non-negotiable that drives everything. |
| ✓ **2. Automated test identification** | Tests based on the authoritative documents (Platform Foundation + Badging-and-Scoring-Reference), not old code. |
| ✓ **3. Build the tests** | Tests before code — the guardrails. See `docs/Test-Plan.md` for the 10 categories. |
| ✓ **4. Rebuild the backend** | Research, scoring, data model — aligned to Platform Foundation and Badging-and-Scoring-Reference. New `_new` modules replaced the legacy POC code. |
| 🟢 **5. Testing — HIGH** | Verify against real companies. Currently surfacing scoring data quality issues (SOTI Provisioning gap, Cohesity ACV undersizing). Drives the §1 SOTI verification and §5.5 ACV review tasks in next-session-todo. |
| 🔵 **6. Prospector — Batch Scoring — HIGH** | Import a list, research at caseboard depth, output downloadable spreadsheet for Marketing. May run concurrently with Step 5. |
| 🔵 **7. Prospector — Lookalikes — MED** | Product-fit matching, not firmographic. Build on Inspector's competitive pairings to drive the lookalike universe. |
| 🔵 **8. Designer Foundation Session — MED** | Same People → Purpose → Principles → Rubrics → UX process used for Inspector. Session Guide and Prep docs ready (`docs/Designer-Session-Guide.md`, `docs/Designer-Session-Prep.md`). |
| 🔵 **9. Designer build — MED** | Tests → code → testing, same pattern as backend rebuild. Pending §8 alignment + the new Designer code push Frank mentioned. |

---

## §B — Architecture & Foundation

Define-Once principle items, prompt generation system, scoring math, badge architecture.

| Item | Description |
|---|---|
| ✓ **Prompt Generation System (3-layer)** | Configuration + Template + Generator at runtime. `backend/scoring_config.py` + `backend/prompts/scoring_template.md` + `backend/prompt_generator.py`. Replaced the static `product_scoring.txt`. |
| ✓ **Define-Once principle enforced** | All Pillar names, dimension names, weights, thresholds, badge names, vocabulary live in `scoring_config.py` and are referenced by every consumer (math, prompts, templates, math layer, render layer). Anti-hardcoding test suite (`backend/tests/test_no_hardcoding.py`) is the structural safeguard. |
| ✓ **Confidence coding (confirmed/indicated/inferred)** | Stored alongside every finding in the data model, surfaces in evidence display, drives the badge evidence modal confidence color (green for confirmed, gray for other). |
| ✓ **Badge Evidence Hover Implementation** | 1.5s hover delay, modal shows bullets + source + confidence. Right-edge clipping detection added so the modal repositions when it would clip. |
| ✓ **Two-Stage Inspector Flow** | Stage 1 = discovery + product selection (broad scan). Stage 2 = Deep Dive on user-selected products. Implemented as separate routes with the Product Selection page bridging them. |
| ✓ **Inspector Two-Zone Layout** | Top zone = hero + verdict + ACV + pillar cards. Bottom zone = product list + briefcase + competitive products + ACV widget. Aligned with the briefcase row `flex 7:3` so every box lines up edge-for-edge. |
| ✓ **Competitive Pairing in Stage 1** | Discovery JSON includes competitive_landscape with competitor + product pairs. Surfaces in the Competitive box on the Full Analysis page. |
| ✓ **SaaS Three-Path Evaluation** | Cloud Slice / Custom API (BYOC) / Credential Pool / Simulation paths defined in the scoring framework. Custom API lifecycle (provision/configure/validate/delete) is captured in scoring signals. |
| ✓ **Gate 3 — Two-Question Model** | Customer Fit pillar evaluates current capability AND organizational DNA. Content team maturity signal hierarchy is in the Customer Fit dimension scoring. |
| ✓ **Three-Pillar Hierarchy** | Product Labability 40% / Instructional Value 30% / Customer Fit 30%. Weights, dimensions, thresholds all in `scoring_config.py`. |
| ✓ **Deterministic Python ACV math** | `scoring_math.compute_acv_potential()` runs at every render. AI emits motions; Python computes hours, dollars, rate lookup, tier. AI no longer touches dollars at all. |
| ✓ **Locked rate variables** | `CLOUD_LABS_RATE=$6` / `VM_LOW_RATE=$8` / `VM_MID_RATE=$14` / `VM_HIGH_RATE=$45` / `SIMULATION_RATE=$8`. Single source of truth in `scoring_config.py`. |
| ✓ **ACV tier thresholds locked** | HIGH ≥ $250K / MEDIUM ≥ $50K / LOW < $50K. Evaluated against the high end of the ACV range. |
| ✓ **Universal Variable-Badge Rule** | When the AI emits more than one badge for the same canonical name, the second one is renamed using a more specific variable (preferred: scoring signal name; fallback: qualifier-derived label). Solves both visual duplicate AND badge-vocab-vs-scoring-signal disconnect. **Awaits §1 SOTI verification.** |
| ✓ **Visual changes never affect scoring (principle)** | Architectural principle in decision log. `_normalize_badges_for_scoring` (Phase 1, before math) does only legitimate transforms; `_normalize_badges_for_display` (Phase 2, after math) does only display transforms. |
| ✓ **PL floor enforcement** | `fit_score = max(weighted_sum, pl_score)`. Strong IV/CF can pull Fit Score above PL but never below. |
| ✓ **Technical Fit Multiplier** | PL 0-9 → 0.50, PL 10-18 → 0.65, PL 19+ → 1.0 datacenter / 0.75 non-datacenter. Lets strong IV/CF lift weak-PL products modestly. |
| ✓ **Ceiling flags** | `bare_metal_required` caps PL at 5, `no_api_automation` caps at 5, `saas_only` caps at 18, `multi_tenant_only` caps at 15. Hard-enforced in math layer. |
| ✓ **SYNTHETIC_BADGES injection** | When `saas_only` or `multi_tenant_only` ceiling flags are set, a `No Learner Isolation` red Blocker badge is auto-injected into Lab Access. Metadata reads from `cfg.SYNTHETIC_BADGES` (Define-Once). |
| ✓ **Score color buckets (3 visible / 5 logical)** | Five logical thresholds (`SCORE_THRESHOLDS` in config) collapse to three visible color buckets. Verdict label text carries finer-grained nuance. Decided intentionally. |
| ✓ **Verdict grid** | (score_range × ACV_tier) → verdict definition. Single source in `scoring_config.VERDICT_GRID`. |
| ✓ **Anti-hardcoding test suite (Phases 1-4)** | 5 tests in `backend/tests/test_no_hardcoding.py` covering template hex, inline style hex, Python color-key dict literals, cross-file scoring_config constant scan, and unannotated magic numbers in scoring math files. Pre-commit hook integration with tracked install script. See Test Plan Category 10. |
| 🔵 **Standard Search Modal — HIGH** | Reusable progress modal used by every long-running operation (Discovery, Deep Dive, Prospector batch, Designer research). Stage stepper, per-item states, honest time signals, cancel that actually cancels. Full design plan in `next-session-todo.md §4`. ~4-6 hours of focused work. |
| 🔵 **Update Foundation docs with new architecture — HIGH** | Add the new scoring math (PL floor, technical fit multiplier, ceiling flags), deterministic ACV math, locked rate variables, universal variable-badge rule, and per-pillar WHY/WHAT/HOW content to `Platform-Foundation.md` and `Badging-and-Scoring-Reference.md`. Most of it lives in the decision log — sync it forward. |
| 🔵 **Comprehensive scoring framework alignment review — MED** | Walk every scored field against `Badging-and-Scoring-Reference.md` and confirm no drift between docs / config / math / template / cached data. |
| 🔵 **Audit other ceiling-flag-implied synthetic badges — MED** | `bare_metal_required` and `no_api_automation` could follow the same pattern as `No Learner Isolation`. Add to `cfg.SYNTHETIC_BADGES`. |
| 🔵 **Move INFO_MODAL_CONTENT from JS to scoring_config or docs file — LOW** | Per-pillar WHY/WHAT/HOW currently lives in a JS object in `full_analysis.html`. Should move to config or a docs file so non-engineers can edit explainability text. |
| 🔵 **Refine variable-driven badge name logic — apply consistently across all three pillars — HIGH** | The Universal Variable-Badge Rule (✓ above) added the disambiguation pattern at the prompt level for Product Labability dimensions where scoring signals exist. Need to extend the same rule consistently across **all three pillars** — Product Labability, Instructional Value, and Customer Fit — so the same disambiguation pattern fires regardless of which pillar a finding lives under. **Test case: Epiq Discover** — when re-scoring, verify that variable-driven badge names appear correctly in all three pillars, not just the Provisioning/Lab Access dimensions where it currently works best. **Builds on:** Universal Variable-Badge Rule (✓ above). **Depends on:** §1 SOTI verification in `next-session-todo.md` (need to confirm the original rule fires for Provisioning before extending the pattern to other pillars). |
| 🔵 **Refine logic for AI estimation of audience populations / adoption / hours — HIGH** | The deterministic Python ACV math is doing the math correctly, but the AI's per-motion **inputs** are coming out too low for global vendors. **Confirmed cases: Cohesity** ($34K-$167K across 2 of 15 products — way too low for 15 globally-deployed enterprise data protection products), and **Epiq Discover** (similar undersizing pattern). The fix is in the prompt's CONSUMPTION_MOTIONS guidance, the benchmarks_new.json scale signals, and possibly anchor companies for hand-validated population/adoption sizes. **Builds on:** Deterministic Python ACV math (✓ above — math is correct, AI inputs are not). **Pairs with:** the Cohesity ACV review in `next-session-todo.md` §5.5 (active investigation). |
| 🔵 **Determine best method for refining Skillable capabilities + capturing "best current thinking" in docs — MED** | Currently `SKILLABLE_CAPABILITIES` lives as a config block in `scoring_config.py` and gets injected into the scoring prompt. Same content needs to flow into the **Product Labability ? modal explanation** so the in-UI explanation always reflects the latest capability set. Open question: how do we keep Skillable capability documentation current as the platform evolves (Datacenter changes, Cloud Slice mode additions, scoring method updates), and what's the canonical place for "best current thinking" so it propagates to all consumers (scoring prompt, ? modal, sales enablement, etc.) without manual sync? **Pairs with:** the INFO_MODAL_CONTENT migration above (same content surface — Product Labability ? modal explanation), the Finalize WHY/WHAT/HOW story for ? modal item below, and the Update Foundation docs item above. |
| 🔵 **Finalize WHY/WHAT/HOW story for the ? modal (per-pillar) — MED** | The reusable info modal currently has placeholder/initial content for Product Labability, Instructional Value, Customer Fit, and the ACV by Use Case widget. The WHY/WHAT/HOW story for each pillar needs to be **finalized** — what business problem each pillar solves (WHY), what specifically we measure (WHAT), and how we score it (HOW) — written tight enough for a seller to read in 30 seconds and walk away understanding the pillar. **Builds on:** the Reusable info modal (✓ above — infra is ready, content finalization is what's left). **Pairs with:** the Skillable capabilities item above (the Product Labability HOW story incorporates current Skillable capabilities) and the Move INFO_MODAL_CONTENT to config item above (when this content is finalized, it should move out of JS and into config). |

---

## §C — Inspector

Inspector tool features and operational improvements.

| Item | Description |
|---|---|
| ✓ **Cache + Append architecture** | One persistent analysis per company (per discovery_id), forever. Stable bookmarkable URL. New products are appended to the existing analysis_id without overwriting cached scores. |
| ✓ **Per-product Seller Briefcase** | KTQ (Opus model), Conversation Starters (Haiku), Account Intelligence (Haiku). Each scored product has its own briefcase. Switching products in dropdown swaps the briefcase too. |
| ✓ **In-place product swap** | Dropdown picks a different product, page updates in place via `/inspector/analysis/<id>/product/<index>` JSON endpoint. No URL change, no reload, no scroll loss. |
| ✓ **ACV by Use Case widget** | Five-column table (Use Case / Audience / Adopt / Hrs / Hrs/Yr) with Annual Hours and Annual Potential totals plus rate footer ($X/hr · tier name). Lives under Account Intelligence in the bottom-right column. |
| ✓ **Bottom row aligned with briefcase** | `flex 7:3` matching `.briefcase`. Products + Competitive sit edge-for-edge under KTQ + Conv Starters; ACV widget sits under Account Intelligence. |
| ✓ **Hero ACV display** | Big number = company total (sum across scored products). Selected product's contribution shown smaller below for context. |
| ✓ **Hero Verdict + ACV tier label** | Verdict color matches verdict tier, ACV label is Python-derived from `_resolve_acv_tier()`. |
| ✓ **Three-pillar layout with `?` icons** | All three pillar headers + ACV widget have `?` icons that open the reusable info modal showing per-pillar WHY/WHAT/HOW. |
| ✓ **Reusable info modal** | `openInfoModal(key)` accepts any `{eyebrow, title, sections}` payload. Currently wired to `?` icons; doc icons are decorative until per-product report content lands. |
| ✓ **Product Selection page** | Tier sections (Seems Promising / Likely / Uncertain / Unlikely), product card selection, sticky right column with Deep Dive button always visible. |
| ✓ **Product family picker** | Modal that opens when a discovery has multiple product families; user picks which family to dive into. |
| ✓ **Compete box on Full Analysis** | Product name (210px fixed, 32-char truncate) | Subcategory badge | Run link (right-aligned to box edge, plain link, same color as Scored Products). |
| ✓ **Browser back button fix** | Discovering and scoring waiting pages use `window.location.replace()` so back from Full Analysis goes to Product Selection (skipping the dead waiting pages). |
| ✓ **Badge evidence modal polish** | Right-edge clipping detection (Fix #4), inline_md filter for bullet bold/italic, confidence color (green confirmed / gray other), wider 540px max-width. |
| ✓ **Score Calculation Deduplication** | Single source-of-truth math layer (`scoring_math.py`) called by `_prepare_analysis_for_render`. Define-Once enforced throughout. |
| ✓ **Bottom-row alignment principles** | Mirrors briefcase row exactly via flex 7:3 so every box aligns under the box above it. |
| 🟢 **§1 SOTI re-score verification — HIGHEST** | First action next session. Verify the Universal Variable-Badge Rule actually fires by running fresh discovery + score on SOTI ONE Platform. Expect Provisioning to jump from ~6 to ~30+ via Hyper-V: Standard signal credit. Cross-check Cohesity / Tanium / Diligent for regressions. See `next-session-todo.md §1`. |
| 🟢 **§5.5 Exhaustive ACV calculation review — HIGH** | Cohesity showed $34K-$167K across 2 of 15 products — way too low for a global vendor. Two distinct problems suspected: AI undersizing per-motion populations + hero shows partial-as-whole. Investigation steps in `next-session-todo.md §5.5`. |
| 🔵 **Wire doc icons to per-product report — HIGH** | Doc icons next to products are currently decorative. Should open the reusable info modal populated with a per-product report. **Builds on:** the Reusable info modal (✓ in §B — `openInfoModal(key)` accepts any payload, infra is ready). **Pairs with:** the Finalize WHY/WHAT/HOW story for the docs modal item directly below. **Open question:** what IS the report content? Three options in `next-session-todo.md §2`. |
| 🔵 **Finalize WHY/WHAT/HOW story for the docs modal (per-product report) — MED** | The doc-icon modal (above — Wire doc icons item) needs its content story finalized using the same WHY/WHAT/HOW pattern as the per-pillar ? modal: WHY this product's report matters for the seller conversation, WHAT the report contains (which evidence, which scores, which recommendations), HOW the seller should use it (what to read first, what to skip, what to discuss with the customer). Should be written tight enough that a seller picks up the report and immediately knows what to do with it. **Builds on:** the Reusable info modal (✓ in §B — same modal infra serves both ? and doc icons). **Pairs with:** the Wire doc icons item directly above. |
| 🔵 **Refine logic for assigning likelihood category during initial product search — HIGH** | The discovery tier assignment (Seems Promising / Likely / Uncertain / Unlikely) needs refinement. **Test case: Epiq Discover** — initial product search is putting products in the wrong tier in some cases. Need to revisit the discovery scoring thresholds in `scoring_config.py`, the prompt guidance for discovery tier assignment, and the signals the AI uses to pick a tier on the initial pass (before Deep Dive). |
| 🔵 **UX method to identify Skillable customers — MED** | When the company being analyzed is already a Skillable customer, the UI should make that visually obvious — both on the Inspector Product Selection page and on the Full Analysis page. Possibilities: a customer-status badge in the header, a "current customer" pill next to the company name, a different verdict treatment when the company is a customer, special hero treatment. Drives different seller conversation (expansion vs. acquisition). **Source-of-truth question (decision needed):** how do we know which companies are customers? CRM lookup? Static config? HubSpot integration? **Pairs with:** the HubSpot field mapping decision in §I. |
| 🔵 **Refine logic for Key Technical Questions in Seller Briefcase — MED** | KTQ generation (Opus model) needs tightening. Two specific issues: (1) **WHO each question should be asked of** — every question should explicitly identify the role/title of the right person to ask (e.g., "Ask the API Product Manager..." or "Ask the Cloud Infrastructure Lead..."). (2) **Bolding/formatting** — important entities (product names, role titles, technical terms) should be bolded so the briefcase reads scannably. The prompt template that drives KTQ should enforce both. |
| 🔵 **Refresh button bug — MED** | The Refresh button on Full Analysis navigates to `/inspector/score/progress/<job_id>` (the SSE endpoint URL) instead of the HTML waiting page. Renders raw SSE event-stream text in the browser. ~10 min fix. |
| 🔵 **Top Blockers List — LOW** | Track companies/products that are undeliverable by specific blocker type. Persistent record enables pattern detection across the pipeline ("no DELETE endpoint" appearing across multiple SaaS products → actionable intelligence). |
| 🔵 **Competitive Capture to Prospector Feed — LOW** | Auto-document competitors discovered during Inspector analysis, feed them into Prospector's target universe. GP5 (Intelligence Compounds) in action. |

---

## §D — Prospector

Prospector tool features and improvements. Tool exists but most work pending Step 6 of the macro build sequence.

| Item | Description |
|---|---|
| 🔵 **Prospector Batch Scoring (macro Step 6) — HIGH** | Import a list, research at caseboard depth, output downloadable spreadsheet for Marketing. The headline workstream after Inspector stabilizes. |
| 🔵 **Prospector Lookalikes (macro Step 7) — MED** | Product-fit matching from Inspector's competitive pairings, not firmographic. |
| 🔵 **ABM Second Contact Column — MED** | Add second contact column to Prospector output: decision maker + champion, stacked. Sellers need both the person who signs and the person who champions internally. |
| 🔵 **Academic Institution Support — MED** | Own discovery queries, scoring model, path labels, contact targeting for academic institutions. Anchors: GCU, WGU, St. Louis University, Saxion. Pre-filter: must have meaningful engineering/tech program. |
| 🔵 **ZoomInfo CSV Column Mapping — MED** | Map ZoomInfo CSV columns to platform fields so redundant research can be skipped when ZoomInfo data is already available. Reduces API costs and speeds up batch scoring. |
| 🔵 **Parallelize Product Discovery Searches — MED** | Currently sequential within the discovery step. Bottleneck for batch scoring. Next meaningful speed gain. |
| 🔵 **Document Volume Limits — LOW** | Document capacity constraints for Marketing. What does "up to 25 companies" mean? What happens when they need more? |
| 🔵 **Certification Demand as Market Demand Signal — LOW** | If certification volume data becomes reliably researchable (number of certified pros, exam volume trends), add as a separate Market Demand signal. Held until research can surface volume numbers. |
| 🔵 **Migrate Prospector off legacy `_nav.html` / `_theme.html` — MED** | Prospector still uses the legacy shared templates with hardcoded hex. Migration scheduled alongside Designer migration (next session). After migration: ~150 hex literals cleaned up, legacy files deletable. |

---

## §E — Designer

Designer tool features. **All Designer-related work is currently deferred until the new Designer code push lands** (Frank 2026-04-06).

| Item | Description |
|---|---|
| 🔵 **Designer Foundation Session (macro Step 8) — MED** | People → Purpose → Principles → Rubrics → UX process. Session Guide and Prep docs ready: `docs/Designer-Session-Guide.md`, `docs/Designer-Session-Prep.md`. Pending Designer code push. |
| 🔵 **Designer build (macro Step 9) — MED** | Tests → code → testing pattern. Pending §8 alignment and the new Designer code push. |
| 🔵 **Scenario Seeds in Lab Blueprint — MED** | Removed from Phase 1 blueprint temporarily. Restore as a 7th item once real-world scenario collection UX is designed. Bullet-item pattern, likely populated by Intelligence from Inspector. |
| 🔵 **Intelligence-Driven Phase 1 Prompting — MED** | When a program has company_name/analysis_id, the AI proactively offers to show company product list, module/feature depth from Inspector, persona assumptions. Inspector intelligence pre-populates Designer's starting context. |
| 🔵 **Style Guide Content Injection — LOW** | Currently only the style guide name is injected. Wire actual file content from the standards library per selection. Priority: Apple Style Guide → DigitalOcean → Red Hat → Microsoft. |
| 🔵 **Skill Framework Taxonomy Files — LOW** | Capture and store NICE NCWF, DoD DCWF, DoD 8570/8140 baseline qualification tables. SFIA and ITIL 4 require licenses — summaries only for now. |
| 🔵 **Standards Catalog API — LOW** | `/standards/catalog` API route returning a JSON catalog of available standards (slug, display name, type, file content available). Enables any tool to query without hardcoded lists in templates. |
| 🔵 **CSS Color Correction (Designer templates) — LOW** | Replace legacy color values with the confirmed Skillable brand palette. Will be addressed as part of the Designer migration off `_nav.html` / `_theme.html`. |
| 🔵 **Migrate Designer off legacy `_nav.html` / `_theme.html` — MED** | Designer still uses legacy shared templates. Migration deferred until the new Designer code push lands (mechanical work on files about to be replaced is wasted effort). |

---

## §F — Research Engine

Research and detection logic improvements.

| Item | Description |
|---|---|
| ✓ **Source Type Classification + Differentiated Fetch Depth** | Marketing pages = light pass; documentation sites = deep fetch; API reference pages = highest token budget. Implemented in `researcher_new.py`. |
| ✓ **Targeted OpenAPI / Swagger Spec Queries** | Explicit search queries targeting OpenAPI/Swagger specs per product. Search patterns: `{product} openapi spec`, `{product} swagger.json`. |
| 📝 **Documentation Breadth Cataloging for Program Sizing** | Four observable signals (modules, features per module, options per feature, interoperability) feed scoring + program scope estimation. Partially in scoring framework; cataloging logic exists but isn't fully surfaced in evidence. |
| ✓ **Lab Platform Detection — product-level query expanded** | Product-level compete query covers Skytap, Kyndryl, GoDeploy, Vocareum, ReadyTech, Immersive Labs, Hack The Box, TryHackMe, ACI Learning, plus Skillable domains. |
| ✓ **Discovery prompt extracts Skillable as a lab partner** | Skillable, labondemand.com, learnondemandsystems.com added to extraction instructions. |
| ✓ **Single Canonical Lab Platform List** | One canonical list in `scoring_config.py`, referenced by both company-level and product-level research, discovery extraction, and badging framework. |
| ✓ **Provisioning Multi-Path Detection** | Hyper-V / ESX / Container / Cloud Slice / Custom API / Simulation paths all have explicit scoring signals in `scoring_config._provisioning_signals`. |
| ✓ **Container Path Detection** | Explicit disqualifiers for Docker as lab path: dev-only images, Windows GUI requirement, multi-VM network complexity. Genuinely container-native definition documented. |
| ✓ **Installable vs Cloud detection** | Deployment model field captures installable / hybrid / cloud / saas-only. Drives ceiling flags and rate tier selection. |
| ✓ **Collaborative Lab Detection — Two Patterns** | Pattern A (Parallel/Adversarial — Cyber Range) and Pattern B (Sequential/Assembly Line — DevOps pipelines). Detection signals + recommendation framing in scoring template. |
| ✓ **Break/Fix (Fault Injection) Scenario Detection** | Detection signals (troubleshooting docs, advanced cert, incident response, complex failure modes) + recommendation framing in scoring template. |
| ✓ **Simulated Attack Scenario Detection** | Single-person and Collaborative Lab variants. Detection signals (SIEM, EDR, identity protection, threat hunting, etc.) in scoring template. |
| ✓ **Delivery Path Rationale — Always Explain WHY** | VMware → Hyper-V (Broadcom pricing) and Docker → Hyper-V rationale in the scoring template. Recommendations carry the "why" the SE can use in customer conversations. |
| ✓ **Domain-based detection for stronger evidence** | Outbound links from company properties to lab platform domains. Implemented as part of the research evidence gathering. |
| ✓ **Product Complexity Detection (Consumer/Simple UX)** | Signals captured: marketing language, configuration depth, doc breadth, role diversity, certification programs, consequence of error. Confidence rules drive badge color. |
| ✓ **Lab Versatility Detection — Product-type to lab-type mapping** | 12 lab types mapped to likely product categories in `scoring_config.LAB_TYPE_MENU`. AI picks 1-2 per product based on specific research, not category. |
| 🔵 **Ensure CTF (Capture The Flag) is a clear option in Lab Versatility — MED** | Verify CTF is one of the 12 lab types in `LAB_TYPE_MENU` with the right product category mappings (cybersecurity, security training, offensive security tooling). If it's there but named ambiguously, rename to "CTF / Capture The Flag" so it surfaces clearly in product reports. If it's missing, add it. CTF is a primary lab format for cybersecurity training and needs to be a first-class option, not buried under "Cyber Range" or "Simulated Attack." |
| 🟢 **§5 Search rework — Deep Dive performance — HIGH** | Deep Dive zips through products 1-4 in <1 min, then hangs on 4/4. Need to instrument first to find where the time goes (queries / fetches / scoring / briefcase). Then per-fetch timeouts, stream scored products as they finish, decide Sonnet vs Haiku for first-pass scoring. See `next-session-todo.md §5`. |
| 🔵 **Search API Upgrade Path — LOW** | Currently DuckDuckGo HTML scraping (~40 queries/analysis). Fragile, no SLA. Upgrade trigger: regular use (>50 analyses/month) or search failures. Recommended: Brave Search API ($0.12/analysis after free tier), Serper ($0.04/analysis), or Tavily (returns content with results). |

---

## §G — Infrastructure

Backend infrastructure improvements.

| Item | Description |
|---|---|
| ✓ **Replace `print()` with logging (scoring_math)** | `scoring_math.py` and other production code use the `logging` module exclusively. Some legacy modules may still have `print()` calls — flagged but not blocking. |
| ✓ **Pre-commit hook integration** | `.git/hooks/pre-commit` runs `validate-badge-names.py` AND `pytest test_no_hardcoding.py` on every commit. Tracked at `scripts/git-hooks/pre-commit` + `scripts/git-hooks/install.sh`. Hook overhead ~0.5s. |
| 📝 **Centralize Skillable-Specific Knowledge** | Delivery patterns, scoring rules, scenario type detection logic — most centralized in `scoring_config.py` now. Some still in prompt template. |
| 🟢 **§3 Render deployment prep — HIGH** | Get the current build into a state where Frank can share with a couple of people via the existing Render service. Pre-flight audit task: secrets loading, cache writes, filesystem writes. Then gunicorn entry point, persistent storage decision (Render Disk recommended), background threads doc, secrets audit, auth gate. ~30-60 min. See `next-session-todo.md §3`. |
| 🔵 **Route File Split — LOW** | `app_new.py` is now ~1000 lines. Split into per-tool route files (`inspector_routes.py`, `prospector_routes.py`, `designer_routes.py`) + shared core. Improves maintainability and reduces merge conflicts. |
| ❓ **SQLAlchemy ORM / Database Migration Path** | Currently JSON files. Plan was SQLite then Azure SQL. Decision needed on when data volume justifies migration. ORM layer should be built regardless so the storage backend can be swapped without rewriting queries. |

---

## §H — Cross-Cutting Concerns

Items that span tools or apply globally.

| Item | Description |
|---|---|
| ✓ **Full hex color cleanup (Inspector + new theme)** | Every active inspector template reads colors from `_theme_new.html` CSS variables. ~16 new theme tokens added. Zero hex literals outside `_legacy_*` and `:root` blocks. Anti-hardcoding test enforces this going forward. |
| 📝 **In-App Documentation Linking** | Pillar card headers have `?` icons + doc icons. Info modal wired for `?` icons (per-pillar WHY/WHAT/HOW). Doc icons still decorative until per-product report content lands. Section-level linking pattern is in place for future expansion. |
| ✓ **Dimension Name Display (ALL CAPS in UX)** | All dimension names render in ALL CAPS via `dim_caps` Jinja filter. Display convention; data model uses normal casing. |
| ✓ **Score Bar Styling** | Pillar card score bars use gradient green/amber/red fill based on dimension score. Theme variables used. |
| ✓ **Cache and Navigation** | Cache date shown as hoverable link with "Refresh cache" tooltip. Two nav links: "Back to Product Selection" and "Search Another Company". |
| ✓ **Word Export (not PDF)** | Sellers can customize the document for their conversations. Word export endpoint exists. |
| ✓ **Product Selector Dropdown** | Hero section product selector shows: product name (left-aligned, truncated), score, purple subcategory badge. |
| ✓ **Anti-hardcoding test infrastructure** | 5 tests across 4 phases: template hex, inline style hex, Python color-key dicts, cross-file scoring_config constant scan, magic-number scan with `# magic-allowed:` annotations. Pre-commit hook integration. Test Plan Category 10 documents the false-positive watch protocol. |
| 🔵 **WCAG AA Accessibility Check — MED** | Automated contrast ratio validation as part of QA. All text/background combos must pass WCAG AA (4.5:1 normal, 3.0:1 large). Build a script or integrate into CI. When Designer becomes customer-facing: consider formal WCAG audit + compliance statement. |
| 🔵 **LMS / LXP Detection — surface platform name — LOW** | Badge currently generic. Should display specific platform name (Docebo, Cornerstone, Moodle, Skillable TMS) — same variable-driven principle as lab platform badges. Docebo + Cornerstone + Skillable TMS = green (partners/own). |

---

## §I — Decisions Needed

Items that need an alignment conversation before implementation. These aren't blocked on engineering effort — they're blocked on a decision.

| Item | Description |
|---|---|
| ❓ **Auth** | Not urgent yet. Revisit when platform goes beyond internal Skillable use. Render deployment prep (§G) will surface this when sharing externally. |
| ❓ **Azure SQL vs. SQLite vs. JSON files** | When does data volume justify migration off JSON? Tied to the ORM layer build above. |
| ❓ **Diff/Refresh architecture** | "Refresh Partnership" and "Re-score Products" buttons — still wanted? Refresh button bug in §C touches this. |
| ❓ **Inspector to Designer handoff button** | Timing tied to Designer readiness. Confirmed analysis_id carries data into Phase 1. UX trigger TBD. |
| ❓ **HubSpot write-back field mapping** | Stage 1 → Company Record, Stage 2 → Deal Records. Exact field mapping TBD with RevOps. |
| ❓ **HubSpot integration thresholds** | Score threshold for auto-create/update. Needs RevOps conversation. |
| ❓ **Benchmark gaps** | Middle-tier, Eaton BrightLayer, SaaS near-miss, GSI/training-org anchors. Needs SE conversations to validate. |
| ❓ **Prospector UX location** | Where do Marketers interact? What triggers a run? Needs RevOps + Marketing alignment. |
| ❓ **ICP Discovery mode** | Criteria-based company discovery. Main challenge is resource management at scale. |
| ❓ **Designer export format** | What goes in the ZIP, what format is the BOM, what the "environment template" looks like. |
| ❓ **Designer collaborative lab BOM** | How collaborative lab network setup, credential pools, and subscription pools surface in Phase 4 BOM. |
| ❓ **Designer first-run onboarding** | How much does Skillable pre-populate vs. customer configure in Preferences. |
| ❓ **Designer AI persona name** | "Neo" used throughout but not explicitly confirmed. Keep, rename, or replace with generic. |
| ❓ **Doc icon target content (per-product report)** | What IS the per-product report content? Options: formatted three-pillar summary; Word doc preview; new "executive briefing" view. Cross-references with the Wire doc icons item in §C. |
| ❓ **Drop the verdict ACV label entirely or keep with thresholds** | Currently: keep with thresholds ($250K HIGH / $50K MEDIUM / <$50K LOW). Locked in decision log. Listed here as a decision-revisit point if usage shows the labels are confusing. |

---

## How items move through this doc

1. **Idea surfaces** in conversation → added to a section as 🔵 Backlog with HIGH/MED/LOW priority.
2. **Item gets prioritized** for the next session → moved to `next-session-todo.md` (the focused near-term doc) and marked 🟢 Active here.
3. **Item ships** → marked ✓ Done here (with description updated to past tense and any decision/architectural notes), and the current details migrate to `next-session-todo.md`'s "Shipped recently" section as the historical record.
4. **Item needs an alignment conversation** → moved to §I with the open question articulated.

The two docs serve different time horizons:
- **`roadmap.md`** (this doc) = the **complete inventory** at any moment. Update when items are added or change status.
- **`next-session-todo.md`** = the **active session driver**. Refreshed every session with focused context for in-flight work. Pulls items from this roadmap when prioritized.

---

**Last refreshed:** 2026-04-06.
