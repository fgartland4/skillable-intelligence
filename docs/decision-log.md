# Decision Log — Skillable Intelligence Platform

Each entry captures decisions made during a working session. Newest entries first.

---

## Session: 2026-04-17 (later) — ACV architecture simplification to company-level, Mark-style line items

**Context:** Frank opened this session with concern that the Build 1 work shipped in commit `a34549c` (ILT formula fix + full retrofit) had drifted from intent and broken things. Requested a thorough review of the whole ACV + scoring path — "the way that Claude did it was was not following the requirements. At all. It really drifted, and it broke a lot of things." The session began with an exhaustive code-vs-docs audit (seven findings surfaced) and evolved into an architectural simplification far larger than Build 1's originally-scoped scope.

### Session findings (Research Pass)

1. **Discovery and Deep Dive used different audience models.** Discovery computed company-level allocation (framework from Build 1). Deep Dive read `install_base` per product directly. Two audience models producing different numbers for the same product. Root cause of the "Deep Dive skyrockets ACV" pattern.
2. **Fit Score directly gated ACV.** `compute_acv_potential` and `compute_acv_on_product` multiplied the final ACV by `fit_score / 100`. Explicitly against Frank's stated rule ("ACV is how big, Fit Score is should we pursue — don't cross-contaminate"). Build 2 was queued to replace it but never started.
3. **Two display fields for company ACV.** `_holistic_acv` on discovery (written by Path 1) vs `_company_acv` on analysis (written by Path 4). Prospector read one, Inspector read the other. Values diverged structurally. Violated the "Deep Dive overwrites discovery" pattern that CF and PL already followed.
4. **Seventeen accumulated caps, floors, multipliers, and tiered heuristics.** Inventoried: archetype audience tiers, wrapper-org fractional caps, IA deflation tiers, scale-aware adoption ceiling, training maturity multipliers, open-source multipliers, cert caps, derivation percentages, per-employee caps, ILT 0.70 dampener, Technical Fit Multiplier 7-row table, rough-IV heuristic anchors (80/55/25/50), etc. Each one existed to paper over a place the underlying math wasn't producing the right answer on its own.
5. **Build 1 scope not fully shipped.** `annual_enrollments_estimate` field retirement — specified in Build 1, alive in 11 files. Platform-Foundation ACV section rewrite — specified, not done. `backend/benchmarks.json` — rich calibration file, not referenced from any docs. Several smaller stale references.
6. **Rough IV heuristic re-invented IV scoring with ungrounded anchors.** `_compute_rough_iv_score` in `intelligence.py` used its own scale (80/55/25/50) disconnected from the real `IV_CATEGORY_BASELINES` used by `pillar_2_scorer.py`.
7. **Smaller drift items.** Microsoft note in `known_customers.json` referenced a $30M universal cap that was deleted. `scripts/README.md` referenced deleted scripts. Researcher module comment referenced deleted script. Badging doc retained ~110 lines describing retired `HOLISTIC_ACV_*` guardrails.

### DECIDED — Frank's reframes that drove the simplification

- **"Math is fine, logic is broken."** The five-motion framework, rate tiers, motion definitions are correct. The assembly around them (which audiences feed which motions, which gate filters which total, where caps sit) is where the drift lives. Fix the wiring, not the primitives.
- **"Artificial floors/ceilings are a HUGE no-no."** Caps and multipliers that exist to bend a number toward a target value are the anti-pattern. Every cap in Finding #4 was Claude's (prior sessions and mine) shortcut to get an expected answer from a broken model. Remove them in concert with fixing what they masked.
- **"Every aspect is counting humans who buy labs."** Motion 1 audience isn't "install base × some percentage." It's a specific countable population — the humans whose lab consumption generates Skillable revenue this year. Same framing for Motions 2–5.
- **"Market Demand is the gating signal for all motions."** Not just Motion 1. If there's no paid training market, no partners will train, no one will certify, no events will have lab tracks. Market Demand bounds the whole ACV picture.
- **"Mark's simpler framework is 'close enough' — we've been trying to be more precise and drifting instead."** Frank + Mark (CRO) tested Mark's nine-category flat-rate prompt on real customers; it produced defensible numbers. Our more-granular model has produced more drift. Simpler + consistent + trustworthy > theoretical accuracy we haven't achieved.

### DECIDED — Company-level ACV only (no per-product ACV dollars)

- **DECIDED:** ACV Potential is computed at the company level exclusively. One dollar figure per company. No per-product ACV exists under this architecture.
- **DECIDED:** Per-product cards on Inspector surface Product Labability / Instructional Value / Customer Fit / Composite Fit Score / Competitors + badges. They do NOT carry a dollar ACV.
- **DECIDED:** Marketing's Prospector row continues to carry per-product labability tier counts (Promising / Potential / Uncertain / Unlikely) alongside the company-level dollar ACV.
- **Rationale:** Collapses four parallel ACV computation paths (discovery allocation, Deep Dive score-time per-product, cache-reload per-product, recompute unscored extrapolation) into one. Eliminates the "Deep Dive skyrockets" pattern by construction — the total is set at the company level, not summed from per-product numbers.

### DECIDED — Five-motion Mark-style line items with flat rates

- **DECIDED:** The five motions (Customer Training, Partner Training, Employee Training, Certification, Events) are each an audience count × a flat annual rate. Per Frank's calibration:
  - Customer Training: $200/person/year
  - Partner Training: $200/person/year
  - Employee Training: $200/person/year
  - Certification: $10/person/year
  - Events: $50/attendee/year
- **DECIDED:** No rate tiers per product. No adoption % multiplications. No hours-per-learner math. Flat rates across all org types. (Rate variations are baked into the blended annual rate per motion.)
- **Rationale:** Mirrors Mark Mangelson's (CRO) labability estimation prompt, which tested "close enough" on real customers. Simpler math with fewer knobs to drift. Mark's $200 (= $100 cert + $100 enablement) for trained humans is the commercial baseline; $10 for cert sitters reflects ~1 lab hour at platform-fee rates; $50 for event attendees is Mark's direct figure.

### DECIDED — New `audience_grader.py` module (narrow Claude slice)

- **DECIDED:** A new intelligence-layer module, `backend/audience_grader.py`, sibling to `rubric_grader.py`. One Claude call per company, produces five audience integers + rationale + confidence (per-motion). Does NOT do dollar math.
- **DECIDED:** Model = Sonnet 4.6. Cost ≈ $0.05/call.
- **DECIDED:** Call fires at fresh discovery, at 45-day refresh, and at Deep Dives that merge new company-level signals (diff check in `company_signals_changed_materially`). Does NOT fire on every Deep Dive — product-only changes reuse cached audiences.
- **DECIDED:** Short-circuits for `CONTENT_DEVELOPMENT` org types before calling Claude — returns partnership result shape.
- **Rationale:** Judgment (audience reasoning grounded in commercial knowledge + calibration anchors) is Claude's job. Math (multiply by rate, sum) is Python's job. Changing a rate should never require re-calling Claude. Matches the `rubric_grader` pattern exactly.

### DECIDED — Build 2 dropped (no separate ACV-specific dimension weight gate)

- **DECIDED:** The Build 2 spec (ACV-specific dimension weights — Market Demand 40 / Delivery Capacity 60 / etc., separate from Fit Score weights) is NOT implemented.
- **Rationale:** The judgment call's prompt instructs Claude to factor Market Demand (IV dimension) and Training Commitment + Delivery Capacity (CF dimensions) into the audience estimates. This does the work Build 2's dimension-weight gate was designed to do — implicitly, at the audience-estimation layer, rather than explicitly as a post-hoc multiplier. Simpler path wins.

### DECIDED — Single Product Labability harness (popularity-weighted)

- **DECIDED:** Company ACV gets ONE multiplier: a popularity-weighted average PL across the product portfolio.
  - `weighted_pl = sum(product.rough_pl × product.user_base) / sum(product.user_base)`
  - `harness = weighted_pl / 100`
  - `company_acv = raw_acv × harness`
- **Rationale:** The judgment call estimates total paid training demand (which exists regardless of Skillable deliverability). The harness filters that demand for what Skillable can actually ship as labs. Workday has a real training market; Skillable can't deliver most of it; harness catches that. Popularity weighting prevents broad portfolios (Microsoft) from being penalized by niche products. Flagship products drive the harness; niche products have less influence.
- **DECIDED:** Term is "harness" (per Frank — "I hate using the word gate for some reason"). Consistent with the commercial-filter framing.

### DECIDED — Retire artificial caps / multipliers (bulk)

- **DECIDED:** The following constants are deleted (staged across implementation commits):
  - `compute_company_total_audience()` and its org-type-routing constants (SHARED_ADMIN / DISTINCT_AUDIENCE / PARTIAL_OVERLAP / INDUSTRY_AUTHORITY_ORG_TYPES, ILT 0.70 dampener)
  - `allocate_audience_to_products()` (no per-product allocation needed)
  - Per-product ACV functions: `populate_acv_motions`, `compute_acv_on_product`, `rebuild_acv_motions_from_facts`, `compute_acv_potential`
  - `AUDIENCE_TIERS_BY_ARCHETYPE` at the discovery path
  - `ACV_WRAPPER_ORG_AUDIENCE_CAP_FRACTION` + floor
  - `INDUSTRY_AUTHORITY_DEFLATION_TIERS`
  - `DISCOVERY_ACV_USER_BASE_TIERS` legacy fallback
  - `ADOPTION_CEILING_BY_AUDIENCE` (scale-aware adoption ceiling)
  - `ACV_TRAINING_MATURITY_ADOPTION_CAP` (35%)
  - `ACV_TRAINING_MATURITY_MULTIPLIERS`
  - `OPEN_SOURCE_WITH_TRAINING_MULTIPLIER` + `OPEN_SOURCE_PURE_MULTIPLIER`
  - `ACV_CERT_MAX_FRACTION_OF_INSTALL_BASE`
  - `CERT_SIT_DERIVATION_PCT`
  - `ACV_PER_EMPLOYEE_ANNUAL_CAP`
  - `_compute_rough_iv_score` anchors (80/55/25/50) in intelligence.py
  - Fit Score gate inside `compute_acv_potential` and `compute_acv_on_product`
- **DECIDED:** Surviving caps (not removed in this change):
  - Archetype IV ceilings (100 / 65 / 45 / 25) — still used in `pillar_2_scorer` for IV scoring, unrelated to ACV math
  - Technical Fit Multiplier (7-row table) — kept for Fit Score composition; evaluation later (try removing and see if anchors hold)
- **Rationale:** Every cap in the first list exists to paper over a place the underlying math was wrong. Under the new architecture, the judgment call handles what most of them were approximating. Remove them in concert with the architectural rewrite, not before.

### DECIDED — Retire `annual_enrollments_estimate` field entirely

- **DECIDED:** `annual_enrollments_estimate` is deleted from `models.py`, `researcher.py`, `discovery.txt` prompt, `acv_calculator.py`, `intelligence.py`. `estimated_user_base` becomes the universal audience field for every org type.
- **Rationale:** The original Build 1 spec said retire it; Build 1 shipped without completing this step. Revisiting under the new architecture: the judgment call interprets `estimated_user_base` per org type (ILT → classroom students this year, Academic → program enrollment this year, Software → global user count, etc.) via explicit prompt framing. No two fields needed.

### DECIDED — Canonical `_company_acv` field, overwritten on each qualifying event

- **DECIDED:** The discovery record carries `discovery["_company_acv"]` as the single source of truth for company ACV. Written at discovery, overwritten on refresh and on qualifying Deep Dives.
- **DECIDED:** The legacy `_holistic_acv` field is renamed / consolidated to `_company_acv`. Both Prospector and Inspector hero sections read this one canonical field.
- **Rationale:** Matches the CF and PL sharpening patterns already documented in Platform-Foundation ("Deep Dive writes back to Discovery"). ACV finally follows the same rule.

### DECIDED — In-app modal content rewritten with descriptive reframe pattern

- **DECIDED:** The `acv_potential` and `acv_use_case` modals in `scoring_config.py` are rewritten to use descriptive reframe questions instead of literal "Why / What / How" headers:
  - *What question are we answering?*
  - *What is it?*
  - *How do we arrive at the number?*
  - *What anchors the number*
  - *What this doesn't try to be*
- **DECIDED:** This pattern extends to the Fit Score modal and any future modal rewrites (not done in this session; queued for follow-up).
- **Rationale:** Frank: "That's what Mark, you know, and the and then our CEO our COO, our our chief marketing officer, all of our VPs, the sellers. Everyone's gonna be using those." The in-app modal IS the external-facing narrative of the platform to leadership. Descriptive questions ("What are we answering?") scan better than structural labels ("Why") for non-technical readers.

### DECIDED — Documents-first principle, rewrite in place (not versioned)

- **DECIDED:** `Platform-Foundation.md → ACV Potential Model` section rewritten in place. No v2 file, no legacy save-as. Git history + decision-log preserve the old thinking.
- **DECIDED:** `Badging-and-Scoring-Reference.md` retired sections (~150 lines of `HOLISTIC_ACV_*` guardrails, calibration block specifics, Common Pitfalls Patterns A/B/D/E/F, etc.) deleted in place.
- **Rationale:** GP5 ("Intelligence compounds, never resets") applied to documentation: rewrite synthesizes best current thinking, does not accumulate historical versions. "One source of truth" at the file level (GP4 + Define-Once).

### Validation set (for implementation commits)

11 companies spanning org types and customer/non-customer mix:

| Customers | Non-customers |
|---|---|
| Microsoft, Commvault, Trellix, CompTIA, EC-Council, Skillsoft, Deloitte | Pluralsight, CBT Nuggets, Sage, Calix |

Spot-check expected ranges (from the slide + `known_customers.json`) after each cleanup commit. Stop-and-diagnose if any anchor moves >30% from the expected range.

### This session's outputs (docs + stubs)

- Rewrote `Platform-Foundation.md → ACV Potential Model` section (in place).
- Rewrote `Platform-Foundation.md → Two Hero Metrics` section for company-level ACV framing.
- Rewrote `Badging-and-Scoring-Reference.md → ACV Calculation` section (compact operational detail; ~150 lines retired content deleted).
- Rewrote `acv_potential` and `acv_use_case` modal content in `scoring_config.py` using descriptive reframe pattern.
- Added `MOTION_RATE_*` constants and `MOTION_KEYS` / `MOTION_METADATA` to `scoring_config.py`. Define-Once source for motion metadata.
- Created `backend/audience_grader.py` as a stub module: function signatures, output schema, partnership short-circuit, diff-check helper. Live Claude call lands in Commit 1 of the implementation pass.
- Added `compute_company_acv()` and `compute_popularity_weighted_pl()` stubs to `acv_calculator.py`. Live implementation lands in Commit 2.
- Drift touch-ups: `scripts/README.md`, `known_customers.json` Microsoft note (`$30M cap` reference), stale comment in `researcher.py`.
- This decision-log entry.

### Queued for next session (implementation)

- **Commit 1:** Full `audience_grader.py` prompt + Claude call + wire into `intelligence.discover()`. Test on 3-4 companies via direct API before wiring. Validate against 11-company anchor set.
- **Commit 2:** `compute_company_acv` + `compute_popularity_weighted_pl` live implementations. Replace Fit Score gate with nothing (judgment handles demand, harness handles supply).
- **Commit 3+:** Strip caps commit-by-commit with validation between each. See next-session-todo.md for full sequence.

---

## Session: 2026-04-17 (late) — ACV architecture alignment (design-only, no build yet)

**Context:** Frank ran Prospector after shipping commit `1b23f94` (capability wiring + unified rebalancing across scored and unscored paths).  Microsoft showed $99M (inflated), and the non-analyzed hyperscalers + ELPs (Salesforce, ServiceNow, Pluralsight, Skillsoft) still showed the Claude holistic $18-30M range.  A full design walkthrough surfaced that the agreed ACV architecture had never actually been implemented in the code.  This entry captures the decisions agreed in that walkthrough.  Build lands next session (see `docs/next-session-todo.md` §1).

### DECIDED — Option B allocation architecture
- **DECIDED:** ACV at the company level is computed by:
  1. Estimating the COMPANY's total trainable audience as a single number per company.
  2. Distributing that total across products proportionally by per-product audience weight, adjusted by archetype multiplier.
  3. Running per-product Motion 1 ACV math using the allocated share (not the raw or per-product-capped audience).
  4. Summing across products to get company ACV — bounded by construction.
- **Rationale:** Adding or removing products re-divides the same pie.  Prevents the N-products × capped-audience overcounting that was inflating Microsoft to $99M.  Matches Frank's stated intent from the very first architectural conversation.

### DECIDED — Company total audience formula by org type
- **DECIDED:** Python-only formula from existing per-product data.  No new researcher field.
  | Org type | Formula | Rationale |
  |---|---|---|
  | software_company (hyperscaler) | `max(per-product capped) + 0.15 × second-largest` | Shared admin audience |
  | enterprise_learning_platform | `sum(per-product audiences)` | Catalogs mostly distinct |
  | lms_company | `sum(per-product audiences)` | Similar to ELP |
  | academic_institution | `sum(per-program audiences)` | Programs mostly different students |
  | ilt_training_organization | `sum(per-class audiences)` | Classes mostly different attendees |
  | industry_authority | `sum(per-cert audiences)` | Different certs, different candidates |
  | systems_integrator / professional_services | `max + 0.30 × sum(others)` | Consultants cross-trained |
  | var / technology_distributor | `max + 0.30 × sum(others)` | Some cross-training |
  | content_development | skip (partnership-only) | Not direct-ACV |
- Per-product "capped" uses the existing `get_audience_tiers_for_archetype` (validated 2026-04-16).
- Starting coefficients are tunable; documented with these values to start.

### DECIDED — One audience field, field consolidation
- **DECIDED:** `estimated_user_base` is the universal audience field for every org type.  Semantic = "humans who'd take training for this product."
- **DECIDED:** `annual_enrollments_estimate` is retired.  For wrapper-org cached discoveries, copy the field into `estimated_user_base` via pure-Python retrofit.
- Researcher prompts (discovery + per-product fact extractors) updated to populate `estimated_user_base` with the right number per org type — software → global users, wrapper → program enrollments / classroom students / practitioners.
- **Rationale:** Frank directly called out the two-field split as a hack during the walkthrough.  Same semantic, same field.  Helper-function workaround would have preserved the drift.

### DECIDED — Gate always applies; quality tracks data quality
- **DECIDED:** The ACV gate (per-product multiplier) always runs, not just at Deep Dive.  At discovery time it uses rough dimension heuristics; at Deep Dive it uses real scores; partial-Deep-Dive uses a mix.  Best current thinking with best available data.
- **Rationale:** Consistency > ambition.  One logic everywhere, results refine as data improves.  A product with no Deep Dive gets a rough gate; the same product after Deep Dive gets a real gate; the architecture doesn't change.

### DECIDED — ACV-specific dimension weights (separate commit, Build 2)
- **DECIDED:** The ACV gate does NOT use the standard Fit Score.  It uses ACV-specific pillar-weights and dimension-weights:
  - Pillar weights: PL 50 / IV 20 / CF 30 (same as Fit Score at pillar level).
  - **Customer Fit dimension weights for ACV:** Training Commitment 40, **Delivery Capacity 60**, **Build Capacity 0**, Organizational DNA 0.
  - **Instructional Value dimension weights for ACV:** **Market Demand 40**, Product Complexity 25, Mastery Stakes 25, **Lab Versatility 0**.
  - **Product Labability:** unchanged (standard dimension weights).
- **Rationale:** What predicts ACV is different from what predicts fit.  Partners / ProServ can BUILD labs — so Build Capacity zero-weights out.  Delivery Capacity matters more than Training Commitment because ACV is about whether they can ship training at scale.  Market Demand (does anyone buy paid training for this?) is the biggest IV driver of ACV.  Lab Versatility zero-weights because we already addressed that through Product Labability.
- **Builds as separate commit** immediately after Build 1 to keep validation clean.

### DECIDED — Full retrofit of cached discoveries
- **DECIDED:** Pure-Python retrofit script runs over every cached discovery and recomputes `_holistic_acv` via the new framework.  No Claude calls.
- Companies with genuinely thin data (missing `estimated_user_base` across all products) keep their legacy `_holistic_acv` value — honest signal that they need re-research, not a zero.
- **Rationale:** Consistency.  If some cached numbers use the legacy Claude path and some use the framework, the "one standard" principle breaks.

### DECIDED — Full legacy cleanup, exhaustive sweep
- **DECIDED:** Delete `researcher.estimate_holistic_acv`, `_HOLISTIC_ACV_PROMPT`, `_format_anonymized_calibration_block`, `_build_holistic_acv_context`, `HOLISTIC_ACV_COMPANY_HARD_CAP`, `HOLISTIC_ACV_MAX_RANGE_RATIO`, `HOLISTIC_ACV_PER_USER_CEILING`, related helpers.  Grep exhaustively — code + docs + templates + comments + decision-log references.  `_raw_claude` preservation retires with the Claude call.
- **Rationale:** Dead code creates drift.  Git preserves history if we ever need to look back.  One path, one standard.

### DECIDED — Documentation layer
- **DECIDED:** Rewrite the ACV section in `docs/Platform-Foundation.md` as best current thinking.  Retire `docs/unified-acv-model.md` — fold anything still useful into Platform-Foundation, then delete.  One source of truth for the architecture.
- Decision-log captures the DECIDED list (this entry).  Platform-Foundation is the spec.  No parallel or derivative docs.
- **Rationale:** Frank's "synthesize and rewrite, don't append" rule.  Doc sprawl is the symptom; centralization is the cure.

### DECIDED — Validation anchors and Definition of Done
- **DECIDED:** Validate Builds 1+2 against the following anchors:
  - Microsoft ~$42M (April 16 validated anchor)
  - Trellix $750K current / $3M potential (Frank's direct anchor)
  - Skillsoft ~$5M (known customer, floor)
  - Pluralsight — fair for a company larger than Skillsoft ($5-10M range target)
  - ASU $2-4M
  - Plus spot-check: Workday, CompTIA, NVIDIA
- **Definition of done:** all anchors in range + full retrofit runs clean (600 discoveries, no exceptions) + Prospector and Inspector render correctly + Platform-Foundation rewritten + decision-log updated + both commits pushed.

### What shipped in THIS session vs. what ships NEXT session
- **Shipped:** commit `1b23f94` — capability wiring (Layer-2 extraction + prompt-build-time rendering + unified rebalancing machinery across scored + unscored paths).  Permanent record on main.
- **Next session:** Build 1 (allocation + field consolidation + legacy cleanup + retrofit) + Build 2 (ACV-specific dimension weights).  See `docs/next-session-todo.md` §1 for the step-by-step build plan.

---

## Session: 2026-04-17 — Skillable capabilities wired into research prompts

### Finding: SKILLABLE_CAPABILITIES tuple was orphaned documentation
- AST-scan audit: zero runtime consumers. The tuple in `scoring_config.py` was read by no code path. The Platform-Foundation.md line 145 claim ("prompts render capability context from the Python tuple at prompt-build time") described intended behavior that never shipped.
- Same pattern as the retired `skillable_capabilities.json` — that file was also "loaded but never read." The retirement comment passed the unread baton to the Python tuple.

### DECIDED: Extract to Layer 2 module
- **DECIDED:** `SkillableCapability` dataclass and `SKILLABLE_CAPABILITIES` tuple moved to `backend/skillable_knowledge.py`. `scoring_config.py` re-exports for back-compat. New code imports from `skillable_knowledge` directly.
- Rationale: three-layer discipline — Layer 1 customer intelligence, Layer 2 Skillable self-knowledge, Layer 3 scoring logic. Capability *content* (fabrics, services, patterns) and scoring *rules* (weights, penalties, baselines) are different concerns and were incorrectly co-located in `scoring_config.py`.

### DECIDED: Schema extension for richer structured content
- **DECIDED:** Extended `SkillableCapability` with optional fields: `fabric`, `supported_services`, `unsupported_services`, `considerations`, `authoritative_catalog_url`, `setup_prerequisites`, `templates_supported`, `roles`, `modes`, `related_capabilities`, `status`, `last_updated`. All optional with safe defaults — existing one-line entries remain valid.
- Additive only — non-breaking.

### DECIDED: Rich AWS + Azure entries, plus Cloud Credential Pool + Cloud Security Review
- **DECIDED:** AWS entry captures the explicit ~65 supported + ~75 unsupported service lists (including SageMaker, Bedrock, Lightsail, EMR, Neptune, CodeBuild, STS, SSO, et al.), plus the three "considerations" notes (EC2 save/resume billing pause, ECS task auto-scaling, SNS unverified-subscription residue). Setup prerequisites captured (dedicated root account, IAM users, LabSecureAccess boundary policy, 10-account quota, CloudTrail log transfer).
- **DECIDED:** Azure entry captures the three IaC paths (ARM JSON, Bicep, Terraform-via-LCA-Docker), CSR/CSS modes, Skillable Studio Policy Set, Resource Provider registration pattern, and the `azure.microsoft.com/en-us/products` authoritative catalog URL. No service list — Azure's answer is "ALL services supported after Security Review," so the security-review process is the gate, not a curated list.
- **DECIDED:** Two new cross-fabric entries added — Cloud Credential Pool (right access mechanism for SaaS-login products) and Cloud Security Review (cross-fabric Low/Medium/High risk classification). Both follow the existing cross-fabric precedent set by Automated Scoring, Hyper-V Preference, and BIOS GUID Pinning.
- **DECIDED:** Deprecated VHD-based Azure Virtualization NOT added to the tuple — convention is current-best-practice only. Compute Gallery is the current Azure VM method.

### DECIDED: Wire the tuple into the research prompts
- **DECIDED:** `backend/prompts/discovery.txt` now uses a `{SKILLABLE_CAPABILITY_CONTEXT}` marker. `backend.scorer.build_discovery_prompt()` substitutes the marker with rendered capability context at prompt-build time — a new service or capability edit flows to the next call without a process restart.
- **DECIDED:** `backend.researcher.extract_product_labability_facts()` now builds its system prompt at call time by concatenating `_PRODUCT_LABABILITY_FACTS_PROMPT` with the full rendered capability context. The extractor is instructed to cross-check product AWS-service dependencies against the supported / unsupported lists and surface unsupported-service dependencies in `provisioning.description` / `lab_access.description` so downstream Pillar 1 scoring and badge selection can reason about them as amber (addressable on demand) — not red.
- Pillar 1 scoring itself is still pure Python reading the fact drawer. The rubric grader is NOT touched because Pillar 1 does not use rubric grading. The capability-context effect on tightness happens via better-grounded facts produced by the research layer.

### DECIDED: RUBRIC_VERSION bump
- **DECIDED:** `RUBRIC_VERSION = "2026-04-17.capability-context-wired-into-research"`. Invalidates cached rubric grades across all analyzed companies; next open re-grades using the enriched capability-aware research narratives.

---

## Session: 2026-04-13 (continued) — 14-fix batch, validation fixes, Prospector features, open source ACV

### Open source ACV discount + Market Demand reframing
- **DECIDED:** Open source products get 25% of normal Customer Training adoption rate (`OPEN_SOURCE_ADOPTION_MULTIPLIER = 0.25`). Detected via `training_license = "none"`. Most OSS users learn from free docs, not paid labs.
- **DECIDED:** Market Demand reframed as demand for PAID HANDS-ON TRAINING, not demand for the product itself. Open source products with millions of users but few paid training programs score lower than commercial software with established training ecosystems. GitHub stars and npm downloads are product signals, not training signals.
- **Frank's framing:** "Market demand for training — that's what this is. MongoDB training demand is simply nowhere near Oracle."

### Prospector features shipped
- Deep Dive top product checkbox (optional, picks flagship by popularity)
- Cost/time estimator (inline, mid-high estimates, updates live)
- Per-company timeouts (3 min discovery, 5 min Deep Dive from config)
- Parallel processing (3 concurrent companies)
- SSE timeout 60 min + auto-reconnect (10 attempts, 2s delay)
- History page (/prospector/history — all researched companies, links to product chooser)

### Documentation Job A — confirmed DONE
Modal infrastructure built and shipped. Content dynamically sourced from scoring_config.py via `_build_modal_content()`. WHY-WHAT-HOW for every pillar, every dimension, verdict grid, ACV explainer. All wired to ? icons. Content polish is a review session, not a build.

### 14-fix comprehensive batch
All 14 planned fixes shipped in 7 commits: post-filters module, ACV per-product extrapolation, org-type adoption overrides, cert derivation constant, wrapper org pipeline, IV badge quality tightening, MFA penalty -15, Orphan Risk 3-tier spectrum, CF baseline recalibration, Pillar 2 extractor retry, Prospector search modal.

### Verdict grid recalibrated
- **DECIDED:** 45-64 row changed from High Potential / Worth Pursuing / Solid Prospect to Assess First / Keep Watch / Deprioritize (same as 25-44). Products with mid-range Fit Scores are marginal — the labels should communicate that honestly. Modal grid collapses 25-64 into one visual row to avoid visual duplication.

### Scoring dimension amber credit reduced
- **DECIDED:** Uncertain/partial scoring methods get 1/3 credit (not 1/2). `SCORING_AMBER_CREDIT_FRACTION = 3` in scoring_config.py. Two uncertain methods ≈ 6/15 instead of 12/15. "Can't really tell" should not produce near-full marks.

### Prospector enhancements designed
Three features agreed:
1. **Deep Dive top product checkbox** — optional, runs full scoring on flagship product per company during batch
2. **Cost/time estimator** — live counter next to input area, mid-to-mid-high estimates, updates when checkbox toggled
3. **Per-company timeouts + parallel** — 3 min discovery, 5 min Deep Dive, skip on timeout, show failed in results. Products in parallel within Deep Dive.

### Bar color threshold
- **DECIDED:** 70% exactly is amber, not green. Green starts strictly above 70%.

### Typeahead deduplication
- **DECIDED:** Search dropdown deduplicates by company name. Each company appears once.

### Badge evidence names underlying technologies
- **DECIDED:** For wrapper org products (certs, degrees, courses, practice areas), badge evidence text now names the underlying technologies. When a cert covers "Wireshark, Metasploit, Nmap," the badge evidence says so. The seller sees what's actually inside the wrapper without clicking through to research.

### Context-aware absence badges
- **DECIDED:** Governance/leadership cert products (e.g., CGEIT, CISM) that have no lab-oriented scoring path get gray Context badges, not red Blockers. The absence of API/script scoring is expected for governance content — it's not a deficiency, it's the nature of the subject matter. Red Blocker is reserved for products where scoring SHOULD exist but doesn't.

### Product name truncation
- **DECIDED:** Long product names truncate with CSS text-overflow ellipsis instead of wrapping or breaking layout. Hover shows the full name via title attribute.

### BS/MS consolidation in discovery prompt
- **DECIDED:** University discovery prompt consolidates Bachelor of Science and Master of Science programs that teach the same technology into a single product entry. "B.S. Computer Science" and "M.S. Computer Science" become one product. Reduces product list noise without losing information.

### ACV org-type motion labels
- **DECIDED:** ACV consumption motions get org-type-specific labels so the seller reads language that matches the customer. Academic: "Student Training" (not "Customer Training"), "Faculty Development" (not "Employee Training"), "Course Exams" (not "Certification (PBT)"), "Research Partnerships" (not "Partner Training"), "Campus Events" (not "Events & Conferences"). GSI: "Client End Users" (not "Customer Training"), "Internal Consultants" (not "Employee Training"). Labels are Define-Once in `ACV_ORG_MOTION_LABELS` in `scoring_config.py`.

### ACV org-type hours overrides
- **DECIDED:** Academic students spend more time in labs (coursework, not elective). Academic Motion 1 hours = 8 (not default 2). Assigned lab work is multiple sessions per course, not a one-time elective experience. Stored in `ACV_ORG_HOURS_OVERRIDES` in `scoring_config.py`.

### ACV complexity-aware rate tier
- **DECIDED:** Products with `Multi-VM Lab` or `Complex Topology` provisioning badges automatically resolve to the Large/complex VM rate tier ($45/hr, `cfg.VM_HIGH_RATE`). The orchestration method is auto-derived from Pillar 1 primary fabric after scoring, so the rate tier reflects what the lab actually requires, not a default guess.

### Search modal last stage 10s dwell
- **DECIDED:** The search modal's final stage (scoring complete, about to redirect) holds for 10 seconds so the user sees the completion state before the page transitions. Prevents the "did it work?" moment when the redirect is instant.

### Hero ? icon alignment
- **DECIDED:** The info (?) icon on the hero Fit Score widget is vertically centered with the score text, not floating above or below. CSS alignment fix.

---

## Session: 2026-04-12/13 — Validation round, scoring retune, researcher sharpening, wrapper org logic

Two-day session spanning validation of the rebuilt scoring layer, multiple scoring retunes, researcher prompt sharpening, and the wrapper organization extraction pattern.

### Pillar weight rebalance: 40/30/30 → 50/20/30
- **DECIDED:** Product Labability weight increased to 50% (from 40%), Instructional Value decreased to 20% (from 30%), Customer Fit unchanged at 30%. Ran math on Cohesity (PL 95), Trellix TIE (PL 86), Workday (PL 22), Diligent (PL 25). Strong-PL companies unchanged; weak-PL companies moved down 4-6 points. Product Labability is the gatekeeper; the math now matches the philosophy.

### Technical Fit Multiplier retune
- **DECIDED:** Full-credit threshold raised from ≥32 to ≥60. New band: 32-59 non-datacenter → 0.65 (was 1.0). Workday HCM (PL 45, SaaS) now scores Fit ~49 instead of 66. Datacenter protection preserved: 32-59 datacenter products still get 1.0.

### Fit Score always recalculates from live config (Bug A)
- **DECIDED:** `recompute_analysis` now always recalculates the Fit Score from saved pillar scores using live config weights and multiplier table. Never trusts a cached `total_override`. Weight and multiplier retunes propagate instantly on page load.

### Orchestration method auto-derived from Pillar 1 (Bug B)
- **DECIDED:** After Pillar 1 scoring, `product.orchestration_method` is auto-derived from the primary fabric signal via a Define-Once mapping in `pillar_1_scorer.py`. Fixes SaaS products defaulting to VM rate ($14/hr) instead of cloud ($6/hr). Internal plumbing only — user-facing badges unchanged.

### IV baseline recalibration
- **DECIDED:** All IV_CATEGORY_BASELINES lowered to create proper differentiation bands. Old baselines were too close to caps (Lab Versatility 93%, Mastery Stakes 88%). New baselines represent a WEAK implementation of each category (~55-70% of cap). Two strong findings needed to reach the cap. Example: Cybersecurity Product Complexity 32→28, Mastery Stakes 22→16, Lab Versatility 14→10, Market Demand 14→12.

### Compliance grader sharpened
- **DECIDED:** `compliance_consequences` signal in Mastery Stakes now has explicit "is_not_about" guidance. Only fires when the product's subject matter directly involves regulatory/audit/legal obligations. General IT, Linux admin, and hardware troubleshooting are excluded.

### Wrapper organization pattern — universal
- **DECIDED:** For ALL non-software org types (universities, Industry Authorities, training orgs, GSIs, VARs, etc.), the wrapper (cert program, degree, course, practice area) stays as the product entry on the product chooser. The underlying technologies inside the wrapper drive Pillar 1 scoring and badge evidence. New `underlying_technologies` field on each product captures the labable technologies. Universal pattern — one set of logic, not per-org-type.

### Badge naming enforcement
- **DECIDED:** Deterministic post-processing overrides in `badge_selector.py` for known bad names. Prompt-only instructions are unreliable; code enforcement is reliable. "Content Team Named" → "Content Team", "ID IDs" → "IDs on Staff", "Published Course Calendar" → "ILT Calendar", plus 20+ additional signal category display overrides.

### Researcher prompt fixes
- Lab Access: `user_provisioning_api_granularity` "partial" is the default for SaaS unless specific endpoint documentation confirmed.
- Audience estimates: training population, not total user base. Admin tools: count admins, not end users.
- "Other" category removed — every real technology fits a real category.

### Discovery tier labels
- **DECIDED:** Renamed to Promising / Potential / Uncertain / Unlikely (from Seems Promising / Likely / Uncertain / Unlikely). Code, config, templates, and tests updated.

---

## Session: 2026-04-07 overnight — Pillar 2 + Pillar 3 posture rewrite (default-positive baselines, penalty signals, cross-pillar compounding)

A multi-hour rewrite of every Instructional Value and Customer Fit dimension — doc, code, prompt, tests, and dossier UX — driven by Frank's observation that Trellix GTI scored 12/40 on Product Complexity despite being a multi-VM threat-intelligence platform. The framework's default-pessimistic posture was punishing the right companies for the wrong reasons. This session replaces that posture with a default-positive model across Pillars 2 and 3.

### The insight that triggered the rewrite — posture is wrong, not the math
- **OBSERVED:** On the Trellix dossier, Product Complexity returned 12/40 while three visible green badges were present. Frank's reaction: "a multi-VM threat-intel platform should peg Product Complexity." The diagnosis: Pillar 2 and Pillar 3 dimensions started from zero and required the AI to *earn* credit through evidence. Missing evidence = zero score. That produced pessimistic outputs even for categories where instructional value is *definitional*.
- **Frank's reframe:** "Most software has instructional value for the right audience. The question isn't 'is there evidence of instructional value' — it's 'is there any reason this product would NOT have instructional value.'" The framework should be **default-positive**. Missing evidence means baseline, not zero.
- **Posture applied universally** to all four IV dimensions AND all four CF dimensions.

### IV (Pillar 2) — category-aware baselines per dimension
- **DECIDED:** Every IV dimension starts from a **baseline derived from the product's top-level category**. Findings move the score up (positive signals) or down (explicit negatives). Missing evidence means baseline.
- **Master category list (locked 2026-04-07):** Cybersecurity · Cloud Infrastructure · Networking/SDN · Data Science & Engineering · Data & Analytics · DevOps · **AI Platforms & Tooling (new)** · Data Protection · **ERP (split from ERP/CRM)** · **CRM (split from ERP/CRM)** · Healthcare IT · FinTech · Legal Tech · Industrial/OT · Infrastructure/Virtualization · App Development · Collaboration · Content Management · **Social / Entertainment (replaces Consumer)** · Unknown (fallback).
- **Retired:** `Simple SaaS` (SaaS is a delivery mechanism, not a content area). `Consumer` (replaced by `Social / Entertainment` for the true no-training-market case — QuickBooks and similar consumer-but-professional tools now belong in FinTech, not a consumer bucket).
- **Calibration (per Frank's directive):** Cybersecurity / Cloud / Networking / Data Sci / Data Analytics / DevOps / AI Platforms at 32 Product Complexity (80% of cap 40). Data Protection at 30. ERP/CRM/Healthcare/FinTech/Legal/Industrial/Infra/App Dev at 28. Collaboration/Content Management at 24 (SharePoint has real depth but less than enterprise business systems). Social/Entertainment at 4. Unknown at 22.
- **Mastery Stakes bumped aggressively** — Cybersecurity / Healthcare / FinTech / Legal / Data Sci / AI Platforms at 22 (88% of cap 25). ERP at 20, CRM at 16 (Frank's split: "if a contact record isn't updated, that's not the end of the world — CRM is less stakes than ERP by a long shot").
- **Data Science reframed as high stakes:** "major organizations spend millions based on what the data says — garbage in, garbage out compounds everywhere downstream." Data Sci & Eng Mastery Stakes = 22.
- **Market Demand reframed as specialist-population intersection:** Market Demand ≈ Product Complexity × Mastery Stakes × specialist population size. Cybersecurity / Cloud / AI Platforms at 17 (massive specialist populations who all need hands-on skills). CRM at 10 ("Salesforce Trailhead is big but per-company admin population is 3 out of 5,000 users"). Consumer / Social Ent at 0.
- **Data structure:** `IV_CATEGORY_BASELINES: dict[str, dict[str, int]]` in `scoring_config.py` — single source of truth, consumed by both `scoring_math` and `prompt_generator`.

### CF (Pillar 3) — organization-type baselines per dimension
- **DECIDED:** Every CF dimension starts from a **baseline derived from the organization's type** (identified during discovery via the company classification). The org types: ENTERPRISE SOFTWARE, SOFTWARE (category-specific), TRAINING ORG, ACADEMIC, SYSTEMS INTEGRATOR, PROFESSIONAL SERVICES, CONTENT DEVELOPMENT, LMS PROVIDER, TECH DISTRIBUTOR, Unknown.
- **Training Commitment — "heart for teaching" framing:** the dimension asks whether the organization genuinely cares that its learners become competent, not whether it has lab infrastructure (that's Build Capacity) or delivery mechanisms (Delivery Capacity). Breadth across audiences (employees + customers + partners) is a strong signal.
- **Training Commitment baseline calibration:** TRAINING ORG at 23/25 (training IS their business). ACADEMIC at 22 ("teaching is the mission — top of the list on heart for teaching"). CONTENT DEVELOPMENT at 22. Enterprise Software / Professional Services at 18. LMS PROVIDER at 11 ("they host others' training, not commit to it themselves"). TECH DISTRIBUTOR at 9 ("trying to become value-added resellers with training, but historically not great at it").
- **Build Capacity — middle baselines + cautious penalties (research asymmetry):** Build Capacity is inward-facing and hard to verify from outside the firewall. Baselines cluster in the middle (50-65% of cap 20) across org types because the AI can't reliably detect internal authoring capacity. **Penalties fire ONLY on positive evidence of outsourcing** — absence of evidence ≠ evidence of absence. Per Frank: "if you can't find IDs or curriculum developers, that's a weak signal; what you *can* find is 'we use Pluralsight' and that IS a signal."
- **Delivery Capacity — start higher, penalize missing public signals aggressively:** Delivery Capacity is outward-facing. ATPs, events, course calendars, partner networks are all public. TRAINING ORG / LMS PROVIDER at 24. ENTERPRISE SOFTWARE / TECH DISTRIBUTOR at 22 (distribution reach IS core for distributors). Penalties fire aggressively when a software vendor has no visible partners / no classroom delivery / no independent training market.
- **Organizational DNA — retire `Build vs Buy` as a badge:** the old `Build vs Buy` badge was a topic label whose color carried three different findings (Platform Buyer / Mixed / Builds In-House). That violated the finding-as-name discipline. **New canonicals:** `Platform Buyer` (positive), `Builds Everything` (negative penalty), `Multi-Type Partnerships`, `Strategic Alliance Program`, `Long RFP Process`, `Heavy Procurement`, `Hard to Engage`. Same retirement treatment for `Partner Ecosystem`, `Integration Maturity`, `Ease of Engagement` — all were topic labels, replaced with finding-named badges.
- **Data structure:** `CF_ORG_BASELINES: dict[str, dict[str, int]]` in `scoring_config.py`.

### Cross-Pillar Evidence Compounding — same fact fires in multiple pillars
- **DECIDED:** Certain facts legitimately answer more than one question. The prompt template instructs the AI to emit corresponding badges in BOTH source and target pillars. Registered rules in `scoring_config.CROSS_PILLAR_RULES`:
  - `Multi-VM Lab` (P1 Provisioning) → `multi_vm_architecture` (P2 Product Complexity) — same evidence, different question
  - `Complex Topology` (P1 Provisioning) → `complex_networking` (P2 Product Complexity)
  - `Large Lab` (P1 Provisioning) → `deep_configuration` or `state_persistence` (P2 Product Complexity)
  - `atp_network` (P3 Delivery Capacity) → `atp_network` (P2 Market Demand) — "nobody becomes a training partner for a product with no skill demand"
  - `cert_delivery_infrastructure` (P3) → `cert_ecosystem` (P2 Market Demand)
  - `training_events_scale` (P3) → `flagship_event` (P2 Market Demand)
  - `no_independent_training_market` (P3 Delivery Capacity negative) → `no_independent_training_market` (P2 Market Demand negative) — "no open-market courses means both weak delivery reach AND weak skill appetite"
- **Why:** Frank's insight — "if you search Coursera for a product and find very few courses, that's a signal for Market Demand AND Delivery Capacity."

### CF Penalty Signal Categories — diagnostic absences
- **DECIDED:** Customer Fit is diagnosed as much by what's *missing* as what's present. New `PenaltySignal` dataclass + `CF_PENALTY_SIGNALS` tuple in `scoring_config.py`. The math layer detects penalty signal_category emissions and subtracts the configured hit from the dimension raw total.
- **Delivery Capacity penalties (aggressive — outward-facing):** `no_training_partners` (red, -10), `no_classroom_delivery` (red, -10), `no_independent_training_market` (amber, -4), `single_region_only` (amber, -3), `gray_market_only` (amber, -2).
- **Build Capacity penalties (cautious — inward-facing):** `confirmed_outsourcing` (amber, -3), `no_authoring_roles_found` (amber, -3), `review_only_smes` (amber, -2). Only fires on positive evidence of absence.
- **Training Commitment penalties:** `no_customer_training` (amber, -4), `thin_cert_program` (amber, -3), `no_customer_success_team` (amber, -3), `minimal_training_language` (amber, -2).
- **Organizational DNA penalties:** `long_rfp_process` (amber, -4), `heavy_procurement` (amber, -3), `build_everything_culture` (amber, -4), `closed_platform_culture` (amber, -3), `hard_to_engage` (red, -6).
- **Badge naming discipline for penalties:** the badge label describes the customer's reality, NOT the research methodology. `No Independent Training` ✓, `Few Pluralsight Courses` ✗. The methodology lives in the evidence text.

### Unknown Classification Review Flag
- **DECIDED:** When the discovery phase fails to confidently classify a product's category OR an organization's type, the scoring context falls back to `UNKNOWN_CLASSIFICATION` (a single-source-of-truth constant in `scoring_config.py`). The math layer applies neutral Unknown baselines AND sets `classification_review_needed: true` on the product result. The dossier UX surfaces a small amber `⚠ Review Classification` indicator next to the product name.
- **Why:** for products that genuinely span multiple categories (NVIDIA — networking + compute + AI) or are genuinely novel (quantum compute, emerging AI agent frameworks), silently forcing a classification is worse than flagging for human review. The flag tells the user "verify this classification before trusting the numbers."
- **Fire condition:** fires when either `product_category` or `org_type` match `UNKNOWN_CLASSIFICATION`. Tracks through `scoring_math.compute_all` → `scorer._parse_product` → `Product.classification_review_needed` → `intelligence.recompute_analysis` → dossier template.

### Seller's Briefcase prompt sharpening
- **DECIDED:** All three briefcase section prompts (Key Technical Questions / Conversation Starters / Account Intelligence) are updated with three tweaks per Frank's directive:
  1. **Every bullet starts with a specific action verb.** Not passive observations — concrete CTAs the seller can execute. "Determine whether...", "Ensure...", "Find the head of...", "Validate...", "Pitch...", "Pursue..."
  2. **Non-empty guarantee.** Every section must return at least ONE bullet — never an empty list. If scoring evidence is thin, surface the single most important unknown/angle/signal. An empty box is a research failure, not a valid result.
  3. **Account Intelligence priority order:** customer and partner events are HIGHEST priority. Already using a lab platform (Skillable or competitor) is EQUALLY critical — surface it immediately as an expansion / displacement / greenfield play. Then named training leadership, certification programs, strategic press signals.

### Zero Hardcodes — Define-Once discipline audit + fixes
- **Frank's directive:** "THERE SHOULD BE ZERO HARD-CODES in the system. We have proactively searched the entire codebase for them a couple times."
- **Self-audit during the rewrite found 5 issues:**
  1. `scoring_math.py` hardcoded dimension key sets → now derived from `cfg.PILLAR_INSTRUCTIONAL_VALUE` and `cfg.PILLAR_CUSTOMER_FIT` at module load time via `_dimension_keys_for_pillar(pillar)`.
  2. Dead `_is_iv_or_cf_dimension` helper → removed.
  3. `scorer.py` and `intelligence.py` each had their own `_build_scoring_context` — consolidated into `cfg.build_scoring_context(raw_org_type, raw_product_category)`. Single Define-Once seam.
  4. `scoring_template.md` hardcoded the master category list, org type values, and CF penalty tables → replaced with `{IV_MASTER_CATEGORY_LIST}`, `{CF_ORG_TYPE_VALUES}`, `{CF_PENALTY_SIGNALS}` placeholders generated at runtime by `prompt_generator.py` from `cfg.IV_CATEGORY_BASELINES`, `cfg.ORG_TYPE_NORMALIZATION`, `cfg.CF_PENALTY_SIGNALS`. Vocabulary drift between code and AI prompt is now impossible.
  5. `CATEGORY_PRIORS` vs `IV_CATEGORY_BASELINES` — confirmed `CATEGORY_PRIORS` is still used for ACV rate priors (separate purpose). Added explicit comment in `scoring_config.py` clarifying the distinction so future editors know both structures exist and why.
- **New `UNKNOWN_CLASSIFICATION` constant** — single source of truth for the fallback label. Used as the dict key in `IV_CATEGORY_BASELINES` and `CF_ORG_BASELINES` and as the fallback value in `build_scoring_context`. No literal `"Unknown"` strings in the scoring code path.

### Tests — 48 new + 2 updated for the new contract
- **New test file:** `backend/tests/test_pillar_2_3_baselines.py` — 48 tests covering:
  - `UNKNOWN_CLASSIFICATION` constant exists and is used as the fallback key
  - Every category in `IV_CATEGORY_BASELINES` has all four IV dimensions
  - Every org type in `CF_ORG_BASELINES` has all four CF dimensions
  - No baseline exceeds its dimension cap
  - Calibration spot-checks (Cybersecurity top tier, Social/Ent floor, AI Platforms present, ERP/CRM split)
  - `ORG_TYPE_NORMALIZATION` targets are all valid baseline keys
  - `build_scoring_context` normalization, Unknown fallback, empty-string handling
  - IV baseline application (Cybersecurity PC baseline = 32, empty findings, capping behavior)
  - CF baseline application (TRAINING ORG near-max, TECH DISTRIBUTOR lowest commitment)
  - CF penalty subtraction (no_training_partners red -10, confirmed_outsourcing amber -3, multiple penalties stacking, penalty on wrong dimension does nothing)
  - Cross-pillar rule registration (Multi-VM Lab, ATP network)
  - Unknown classification review flag behavior in `compute_all` (fires on Unknown category, fires on Unknown org, false on clean classification, false without context)
  - CF penalty signal structural sanity (valid dimensions, valid colors, positive hits)
- **Updated tests:** `test_creative_invariants.py` — two tests (`test_recompute_against_a_minimal_synthetic_analysis`, `test_adversarial_empty_dimensions_list`) asserted the old "no badges → score 0" contract. Updated to the new default-positive contract: empty-badge products now score at the Unknown baseline and raise `classification_review_needed`.
- **Full backend suite:** 145 passed / 0 failed / 46 skipped.

### Documentation sync
- **`docs/Badging-and-Scoring-Reference.md`:** Pillar 2 intro rewritten with posture + master category list; Pillar 3 intro rewritten with org-type baselines + research asymmetry; every IV and CF dimension section rewritten with the new format (question → What the Dimension Measures → What It Does NOT Measure → Posture → Category or Org-Type Baseline → Strength Tiers → Signal Categories → Badge Naming → Worked Examples → Typical Spread). Worked examples use current baseline values. Typical Spread tables recalibrated.
- **`docs/Platform-Foundation.md`:** Pillar 2 and Pillar 3 sections updated with the new dimension questions, posture paragraphs, master category list reference, research asymmetry note, and retired `Build vs Buy` badge note.
- **`docs/collaboration-with-frank.md`:** Added "Location and time zone" (Arizona / Pacific time) and "Session Rhythm" section ("never recommend splitting work across sessions based on how long it has run — Frank knows his own rhythm").

### Version bump
- **DECIDED:** `SCORING_LOGIC_VERSION = "2026-04-07.pillars-2-3-posture-rewrite"` — triggers smart cache invalidation per GP5 so existing analyses re-score against the new posture on next access.

---

## Session: 2026-04-07 evening — Pillar 1 risk caps, CF unification, prompt sharpening, Phase F, Phase 4 tests

A long late-night session covering scoring math refinements, prompt sharpening for Pillars 2/3 + the Sales Briefcase, the Customer Fit centralization (Phase F), and the creative test strategy (Category 11). Commits referenced inline.

### Risk Cap Reduction — Pillar 1 dimensions can never be at full cap when amber/red risks present
- **DECIDED:** When a Pillar 1 dimension surfaces amber or red risk badges, the dimension's effective cap is reduced (not the score deducted, the cap itself lowered): -3 points per amber risk badge, -8 points per red risk badge.
- **Why a cap reduction, not a deduction:** the existing color-aware math already deducts color points for amber/red badges. Doing a second deduction would double-count. Lowering the cap means the dimension can still earn green credits but can never reach its full theoretical max while risks are present — which is what "risk" actually means in business terms.
- **Calibration source:** Frank, after reviewing Trellix and Diligent dossiers — the dimensions that should "never feel clean" with red present were still showing high scores via green offsets. Capping forces the visible score to honor the worst-case finding.
- **Constants:** `cfg.AMBER_RISK_CAP_REDUCTION = 3`, `cfg.RED_RISK_CAP_REDUCTION = 8` in `scoring_config.py`.
- **Commit:** `00123cc`.

### Customer Fit unification — best-showing wins, broadcast across all products
- **DECIDED:** Customer Fit is a property of the **organization**, not the product. Every product from the same company must show **identical** Pillar 3 dimensions, scores, and badges. The merge rule is **"best showing wins"** (Option B): when two products surface different evidence for the same CF signal_category, the stronger color + stronger strength wins, and that single best version broadcasts to every product.
- **Why best-showing wins:** the alternative (worst-of-group) made every product look as bad as the worst-researched product, which punished CF for incomplete evidence. Best-showing aligns with how a seller actually frames the conversation — "what we know about this company at its best."
- **Frank's framing:** "Customer Fit measures the organization, not the product. Every product from the same company must show identical Pillar 3."
- **Initial implementation (commit `a6f7b74`):** an interim merge inside `recompute_analysis()` that built the unified CF from the analysis's products and broadcast it onto every product. This worked but Frank flagged it as the wrong architectural home — see Phase F below.

### Phase F — Customer Fit lives on the discovery, owned by the Intelligence layer
- **DECIDED:** The canonical home for the unified Customer Fit is `discovery["_customer_fit"]`, written by `intelligence.score()` at every save boundary, read by `intelligence.recompute_analysis()` at every page load. Inspector / Prospector / Designer all read from this one place. The interim per-analysis merge becomes a fallback for legacy data.
- **Why move it from analysis to discovery:** discovery is the company-level concept; analysis is the per-Deep-Dive concept. Customer Fit is a company-level property. Every Deep Dive on the same discovery (even months apart, across Inspector + Prospector + Designer) should see the same CF — and it should be computed once, not re-merged on every page load.
- **Lookup order in `recompute_analysis()`:**
  1. `discovery["_customer_fit"]` — canonical Phase F home
  2. `_build_unified_customer_fit(products)` — fallback for legacy analyses whose discovery hasn't been stamped, or for the pre-save window inside `score()` before aggregate has run
- **Layer Discipline note:** `aggregate_customer_fit_to_discovery()` lives in `intelligence.py`, not `app.py` — it's intelligence work that all three tools need, not Inspector-specific orchestration.
- **Commit:** `b5c981d`.

### Diligent Five Fixes — five distinct scoring + badging refinements shipped together
- **DECIDED (1):** Sandbox API red caps Pillar 1 hard. When the Sandbox API canonical fires red on a SaaS product, Pillar 1 is capped at **25** if Simulation is viable (the next-best path) and at **5** if nothing is viable. Constants: `cfg.SANDBOX_API_RED_CAP_SIM_VIABLE` and `cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE`. This is the SE-4 answer Frank approved by inspection of Diligent's earlier 66-point Pillar 1.
- **DECIDED (2):** Datacenter excludes Simulation. The Datacenter badge previously fired even on Simulation-only products; now Simulation is excluded from the Datacenter set. A new gray `Simulation Reset` badge with 0 points is emitted in Teardown for Simulation products to surface the teardown story without crediting it.
- **DECIDED (3):** Scoring breadth rule (the "Grand Slam" rule). MCQ alone = 0 points. AI Vision alone caps at 10 (`cfg.SCORING_AI_VISION_ALONE_CAP`). Script alone = full marks (VM context). Scoring API alone caps at 12 (`cfg.SCORING_API_ALONE_CAP`). **Grand Slam (AI Vision + Script OR API) = full marks** — the breadth bonus credits the combined scoring surface, not the individual methods.
- **DECIDED (4):** Drop the Fit Score floor. The previous formula was `fit_score = max(weighted_sum, pl_score)`, which let strong PL pull the Fit Score above its weighted-sum value. Now the formula is the pure weighted sum. Frank's framing: "if Customer Fit is bad, the Fit Score should be allowed to reflect that — even on a great product."
- **DECIDED (5):** Pillar 2/3 prompt sharpening — three new rules in `prompts/scoring_template.md`: strength grading discipline (don't hedge to moderate; force STRONG for high-stakes domains like governance/cybersecurity/healthcare); subject-matter-specific badge names (not generic templates); emit gap badges (red) when grading low to make judgment visible.
- **Commit:** `8b9d6be`.

### Pillar 3 badges must convey JUDGMENT, not describe categories
- **DECIDED:** Customer Fit badges must read as findings about the customer, not as category labels. "Build vs Buy" is not a finding — it's a topic. "Platform Buyer" or "In-House Builder" are findings. The prompt now carries an explicit FORBIDDEN list of generic structural names (`Build vs Buy`, `DIY Labs`, `Content Dev Team`, `Partner Ecosystem`, `Integration Maturity`, `Ease of Engagement`, `Lab Platform` as a label, `Training Culture`, `Certification Program`, `Training Catalog`) with required judgment-form alternatives for each.
- **The three permitted shapes** for every Pillar 3 badge:
  1. **A counted/named specific** (`~500 ATPs`, `Elevate 2026`, `Skillable`, `Series D $200M`)
  2. **A judgment phrase** (`Light Content Dev`, `Few Tech SMEs`, `Long RFP Process`, `Soft Skills Focus`, `Slide-Deck Culture`, `Compliance-Only Training`)
  3. **An explicit gap** (`No Lab Authors`, `No Documented ATPs`, `No Tech Writer Team`)
- **Forcing function:** if the AI cannot produce one of those three shapes for a dimension's evidence, it must re-read the dossier — it doesn't understand the evidence well enough to emit a badge.
- **Frank's framing:** "Customer Fit badges need to show judgement. Light Content Dev, Soft Skills, Long RFP Process, Few Tech SMEs... Something like that."
- **Commit:** `7bb8d04`.

### Account Intelligence — time-bounded events as TOP recommendations with concrete actions
- **DECIDED:** When the scoring evidence mentions a specific conference, flagship event, certification launch, product release, or other time-bounded signal, that bullet should be FIRST in Account Intelligence and must include three things: (1) the named event with date if known; (2) a concrete person/role to find ("the head of Elevate 2026"); (3) WHY it matters as a specific Skillable opportunity, anchored to the framework: "Events are Skillable's lowest-friction consumption motion — defined audience, defined timeline, no incumbent platform to displace."
- **Worked example for Diligent's Elevate 2026** is in the prompt as the WEAK vs STRONG side-by-side.
- **Frank's framing:** "If you go down to account intelligence — find out who's running that event. Like, who's the Elevate 2026 conference. It's phenomenal place for us to start by having hands-on experiences at events."
- **Commit:** `9e5d174`.

### Briefcase routing rule — KTQ technical / Conv Starters strategic / Acct Intel leaders
- **DECIDED:** The three Sales Briefcase sections target three non-overlapping audiences:
  - **Key Technical Questions** target TECHNICAL ROLES ONLY: Principal/Staff Engineer, API Team Lead, Solution Architect, Sales/Solution Engineer, Customer Onboarding Engineer, DevRel, SRE, product team technical lead. **NEVER target VPs, Directors, CLOs, or any pure-management role** — forwarding "does the REST API support DELETE on user records?" to a VP wastes the seller's credibility.
  - **Conversation Starters** target STRATEGIC LEADERS: VPs of Customer Education / Training / Customer Success, Directors of Enablement, CLOs, VPs of Product. Talking points must be VP-respondable ("yeah, that's exactly why we're doing X"), framed around business outcomes (retention, time-to-productivity, certification pass rates, NRR, churn risk). Never technical.
  - **Account Intelligence** targets named leaders + named events.
- **Why explicit role lists:** the previous prompts said "technical champion" without naming roles, and the AI was emitting "ask the VP of Customer Education..." for technical API questions. Explicit ✅/❌ lists in the prompt force compliance.
- **Frank's framing:** "If you want a technical question, that's how are we gonna get your labs into Skillable? You don't wanna be talking to director-level people and VPs of customer education... principal engineers, API team leads... solution architects, solution engineers, sales engineers... people that help with customer onboarding... VPs and things, that's in conversation starters. And account intelligence — that's where you wanna know the leaders."
- **Commit:** `c91b819`.

### Stale-cache decision modal on Product Selection → Deep Dive
- **DECIDED:** When a user clicks Deep Dive on a Product Selection page whose existing cached analysis was scored with an older `SCORING_LOGIC_VERSION`, intercept the form submit and show a confirmation modal: **Refresh first** / **Use cached** / Cancel. Once the user has made a choice on a given page load, a second click of Deep Dive goes through without re-prompting.
- **Why:** Frank reported clicking Deep Dive on cached Diligent and the system silently re-scored without giving him a choice. The cache versioning gate was right (the data WAS stale) but the user lost agency over the decision. The modal preserves the gate's correctness while restoring the choice.
- **Implementation note:** the same modal partial (`_search_modal.html`) that powers the Full Analysis stale-cache modal is now imported on Product Selection. Buttons relabeled from the default "Refresh / Ignore for now" to "Refresh first / Use cached" because "Ignore for now" reads ambiguously in a submit-intercept context.
- **Commit:** `7c69eb1`.

### Phase 4 — creative test strategy (Category 11) — 27 tests across 10 classes
- **DECIDED:** Implement all 10 test classes from `docs/code-review-2026-04-07.md §"Phase 4 — creative test strategy"`. The 88 existing structural tests would not have caught any of the CRITICAL findings from the deep code review — they assert config shape, not the integration paths between layers. Category 11 walks every saved analysis on disk plus a battery of synthetic in-memory fixtures and asserts runtime invariants that span layers.
- **The 10 test classes** (full descriptions in `docs/Test-Plan.md` Category 11): round-trip badge identity (Pillar 3 exempt for Phase F unification), recompute idempotence, vocabulary closure, bold prefix doesn't leak (against the recomputed view, not raw JSON), cache stamp truth, pillar isolation, polarity invariants, adversarial fixtures, layer discipline (AST), define-once enforcement (string constants only).
- **Auto-skip stale fixtures:** `_load_saved_analyses(current_only=True)` skips any saved analysis whose `_scoring_logic_version` doesn't match the current — those are queued for re-score by the cache versioning gate, so it isn't fair to enforce current architectural rules against them.
- **Render-time normalization:** tests check the **recomputed view** (what the user actually sees), not the raw saved JSON, because Phase 1 normalization runs at render time by design.
- **Frank's framing:** "would love you to finish all these tests... they're so important for keeping us from making architecture mistakes."
- **Commit:** `a414723`. 27 new tests, 115 total passing (was 88).

### Legacy quarantine — drop the `_new` suffix from the entire active code path
- **DECIDED:** The `_new` suffix (`app_new.py`, `intelligence_new.py`, `scorer_new.py`, `data_new/`) was a transitional convention while the rebuild was in flight. With the rebuild complete and the legacy POC code moved to `legacy-reference/`, the suffix is now a documentation-rot risk — every file that references "the new code" goes stale the moment "new" stops being new. Drop the suffix everywhere and reference the canonical names (`app.py`, `intelligence.py`, etc.).
- **Commits:** `e2620b0` (rename), `9f44222` (sync session-opening docs).

---

## Session: 2026-04-06 — Universal variable-badge rule

### One rule, two vocabularies, applied universally
- **DECIDED:** When a finding warrants multiple badges in the same dimension, every badge gets a unique name. Never emit the same canonical badge twice.
  - **First occurrence:** keep the canonical badge name (e.g., `Runs in Hyper-V`).
  - **Subsequent occurrences:** rename using a more specific variable, in priority order:
    1. **PREFERRED** — pick the matching scoring signal name from the dimension's `scoring_signals` list (e.g., `Hyper-V: Standard`, `Hyper-V: CLI Scripting`, `Azure Cloud Slice: Entra ID SSO`). These names carry real point values via `signal_lookup` in the scoring math layer.
    2. **FALLBACK** — derive a qualifier-specific label from the evidence (e.g., `Install Complexity`, `Multi-VM Topology`). These don't lift the score but they prevent visual duplicates and make the evidence specific.
- **Why this is universal:** It solves two problems at once with one architectural rule.
  - **Visual problem:** No more duplicate badge names rendering twice with different colors. Each row shows distinct, specific labels.
  - **Scoring problem:** Closes the badge-vocabulary-vs-scoring-signal disconnect. The math layer credits scoring-signal names with their real point values (e.g., `Hyper-V: Standard` = +30) instead of falling back to color points (+6 for green). Affected products: every installable VM/cloud product that previously underscored.
- **Architectural shape:**
  - **Prompt** is the source of truth (`backend/prompts/scoring_template.md` + `prompt_generator._format_badge_naming_principles()` + `_format_canonical_badge_names()`).
  - **Math layer** needs zero changes — it already credits any name that matches `signal_lookup` and falls back to color points otherwise.
  - **Display normalizer** (`_normalize_badges_for_display`) keeps the same-name merge logic as a defensive safety net for legacy cached analyses + occasional AI non-compliance, but the AI is now responsible for disambiguating at the source.
- **Test plan:** Re-run a fresh discovery + score on SOTI ONE Platform after the prompt change lands. Expect Provisioning to jump from ~6 to ~30+ (Hyper-V: Standard signal credit). Then validate against Cohesity, Tanium, Diligent for regressions. None of those should drop in score — only installable products with a viable scoring signal should gain.
- **Frank's framing (verbatim):** "Wouldn't this be a better idea? If there's two for any badge... instead of showing it twice, you show it once. And then you do a nice variable driven badge for the second one that really kinda points out the good thing or the bad thing... it's really the visual is the problem. Let's just for the second one, if there's more than one, then do a variable on the problem."

---

## Session: 2026-04-06 — ACV tier thresholds locked

### ACV tier dollar thresholds
- **DECIDED:** ACV tier labels are computed deterministically in Python from the **high end** of the per-product ACV range (a deal is sized at its upside, not its floor):
  - `acv_high >= $250,000` → **HIGH ACV**
  - `acv_high >= $50,000`  → **MEDIUM ACV**
  - `acv_high <  $50,000`  → **LOW ACV**
- **Where:** `scoring_config.ACV_TIER_HIGH_THRESHOLD` and `ACV_TIER_MEDIUM_THRESHOLD`. One-line edits with zero rescore needed — `_prepare_analysis_for_render` recomputes on every page render via `scoring_math.compute_acv_potential()`.
- **Why:** Visible label needs *some* threshold to flip between low/medium/high. Frank picked deliberately conservative numbers — anything under $50K is correctly Low, $50K–$250K is real but bounded, $250K+ is the point where a deal warrants serious investment. The verdict grid combines this tier with Fit Score to choose the verdict label and color.
- **Architectural note:** This finishes the move of ACV math from the AI prompt into deterministic Python. The AI's only ACV job now is per-motion population, adoption %, and hours/learner — population × adoption × hours, the rate lookup, the dollar conversion, and the tier label all happen in Python.

### Verdict ACV labels — keep them
- **DECIDED:** Keep the LOW ACV / MEDIUM ACV / HIGH ACV labels under the verdict badge. They give immediate context next to the verdict text without forcing the reader to compute "is $63K low or medium" in their head. The labels are now driven by the Python tier computation above, not AI guesswork.

---

## Session: 2026-04-06 — Score color buckets

### Three visible color buckets, five logical thresholds — intentional
- **DECIDED:** The score color system has **five logical thresholds** (`dark_green`, `green`, `light_amber`, `amber`, `red` at 80 / 65 / 45 / 25 / 0) defined in `scoring_config.SCORE_THRESHOLDS`. All four score displays — Fit Score, the three Pillar Scores, and the Verdict — read from this single dict via `score_color` filter or `get_verdict()`. They are aligned by construction.
- **DECIDED:** The **visible color palette is intentionally only three buckets** (high green / mid amber / low red). `dark_green` and `green` both render `var(--sk-score-high)`. `light_amber` and `amber` both render `var(--sk-score-mid)`. This is a deliberate design choice, not a bug. The finer-grained nuance lives in the **verdict label text** ("Prime Target" vs "Worth Pursuing" vs "Solid Prospect"), not in color saturation.
- **Why:** Five distinct color shades on the same page becomes visual noise. Three clean buckets give an immediate gut read; the verdict label gives the precision when you want it. Future self: do not "fix" this by adding two more colors unless this decision is explicitly revisited.

---

## Session: 2026-04-06 — Roadmap consolidation

### Single consolidated roadmap doc
- **DECIDED:** `docs/build-roadmap.md` and `docs/Research-Methodology-Improvements.md` consolidated into a single new doc at `docs/roadmap.md`. Both source docs deleted in the same commit. The new doc is the complete inventory of every item we know we want to do, are doing, have done, or need to decide.
- **Why:** Frank flagged that we'd been developing 2-3 different places listing next steps. The two source docs had real overlap (Render deployment prep was in both), stale items (Score Calc Dedup, Replace print() with logging, Prompt Generation System were marked as TODO but actually done), and unclear ownership ("where do I add this?" had multiple answers). One inventory eliminates the fragmentation.
- **Format:** Each section has a 2-column table (Item | Description) with status icons inline in the item name (✓ Done · 📝 Partial · 🟢 Active · 🔵 Backlog · ❓ Decision Needed) plus HIGH/MED/LOW priority tags on items not yet done. Sections organized by area: Macro Build Sequence, Architecture & Foundation, Inspector, Prospector, Designer, Research Engine, Infrastructure, Cross-Cutting, Decisions Needed.
- **`next-session-todo.md` stays separate.** It serves a different time horizon: focused near-term action driver, refreshed every session, part of the CLAUDE.md startup sequence (step 4). The roadmap is the long-term inventory; next-session-todo is "what to do this session." Items flow: idea → roadmap as 🔵 Backlog → moved to next-session-todo when prioritized → marked ✓ Done in roadmap when shipped.
- **Cross-references updated:** `CLAUDE.md` build roadmap reference now points at `docs/roadmap.md`. `Platform-Foundation.md` Supporting Documents table updated. New "complete inventory" pointer added to CLAUDE.md startup section so future Claude knows the roadmap exists as a reference (but doesn't need to read it as part of the startup sequence — that would be too much).

---

## Session: 2026-04-06 — Principles surfaced from Bug Hunting

### Visual changes must NEVER affect scoring
- **DECIDED (principle):** Any change made for display purposes — badge merging, splitting, deduplication, color promotion, name normalization, sorting, grouping — must NEVER alter the inputs the scoring math sees. Scoring math reads the AI's evidence as faithfully as possible. Display transforms run on a separate path so the user sees a clean UI without the math being silently distorted.
- **Origin:** Caught during the badge merger fix on SOTI ONE Platform. The merger collapsed two same-named "Runs in Hyper-V" badges into one and promoted the color from green to amber for clarity. The math layer reads `BADGE_COLOR_POINTS` for badges that don't match a named signal — green = +6, amber = 0. The color promotion silently dropped 6 points per dimension where this happened, ~10 points across SOTI's pillars.
- **Architectural enforcement:** `_normalize_product_badges` should be split into two functions — one that runs before the math (deterministic injections like Bug 2's No Learner Isolation badge, plus the badge splitter) and one that runs AFTER the math (display-only merging and color promotion). The math sees the unmerged list; the user sees the merged list.
- **Generalization:** The same principle applies to any future display work — sorting badges by severity, hiding low-confidence badges, collapsing badge groups, renaming badges for clarity. None of these may touch what the math sees.

---

## Session: 2026-04-05 (late night) — Inspector Cache, Stable URL, Per-Product Briefcase, In-Place Swap

### Stable URL Per Company
- **DECIDED:** One persistent analysis per company (per discovery_id), forever. The analysis URL is bookmarkable and stable. Captured in Platform-Foundation.md under GP5.

### Cache + Append Logic
- **DECIDED:** Deep Dive checks for an existing analysis on the discovery. For each selected product: cached → leave alone, new → score it. Newly scored products are APPENDED to the existing analysis (same analysis_id, same URL).
- **DECIDED:** If all selected products are cached, the route returns instantly with zero Claude calls.
- **DECIDED:** Default product shown on the page = highest-scoring product from the CURRENT selection. The dropdown shows ALL products ever scored for the company.

### Briefcase Is Per-Product
- **DECIDED:** The Seller Briefcase moves from analysis-level to product-level. Each scored product has its own briefcase. Switching products in the dropdown swaps to that product's briefcase. Captured in Platform-Foundation.md and Badging-and-Scoring-Reference.md.
- **DECIDED:** Briefcase generation runs only for NEWLY scored products. Cached products keep their cached briefcase.
- **DECIDED:** Briefcase generation is its own background phase that runs after scoring. The Full Analysis page renders immediately with "preparing" placeholders, then swaps in the briefcase content as it becomes available — no page reload, no scroll loss.

### In-Place Product Swap
- **DECIDED:** When the user picks a different product from the dropdown, the page updates IN PLACE (no URL change, no reload, no lost scroll position). Three sections swap together: hero, pillars, and briefcase. URL stays bound to the company.
- **DECIDED:** The endpoint that returns rendered fragments lives at `/inspector/analysis/<id>/product/<index>` and returns JSON with `hero_html`, `pillars_html`, `briefcase_html`.

### Briefcase Loading UX
- **DECIDED:** The "loading" state for each briefcase section shows the real card title (Key Technical Questions, Conversation Starters, Account Intelligence) with three subtle pulsing dots in the body. No generic "Preparing Seller Briefcase..." text. Consistent with the search-loading dot pattern.
- **DECIDED:** Polling frequency is 5 seconds — invisible to the user (no jumpiness possible since nothing visible animates per poll). Will increase to 60s once tonight's debugging is done.

### Logging Infrastructure
- **DECIDED:** Logging is configured directly in `app_new.py` (not just `run_new.py`) so that the Flask reloader child process inherits it. Werkzeug request logs and backend `log.info` calls now show in real time.
- **DECIDED:** Claude API calls in `_call_claude` emit a heartbeat log every 15 seconds during streaming so we can see calls are alive. Will tune to 60-90s after tonight.

### Doc Reorganization
- **DECIDED:** All four memory files for Frank's collaboration preferences (commit/push, grid uniformity, writing standard, etc.) consolidated into `docs/collaboration-with-frank.md`. CLAUDE.md and MEMORY.md both point to it. Project-specific rules live in CLAUDE.md only.
- **DECIDED:** Mandatory file storage rule added to both CLAUDE.md and MEMORY.md: never save anything persistent to the local hard drive. All docs go in the repo (OneDrive + GitHub).
- **DECIDED:** Old docs moved to `docs/archive/`: Badging-Framework-Core.md, Scoring-Framework-Core.md, inspector.md, intelligence-platform.md, skillable-intelligence-platform.md, Skillable-Intelligence-Executive-Briefing.docx, Skillable-Intelligence-Platform.docx. designer.md was merged into Designer-Session-Prep.md and deleted.

### Build Roadmap
- **DECIDED:** `docs/build-roadmap.md` created from the memory file. Status: steps 1-4 complete, currently in step 5 (testing).

---

## Session: 2026-04-05 (evening) — Designer Document Consolidation

### designer.md Merged and Deleted
- **DECIDED:** All content from `designer.md` (the pre-Foundation requirements document) merged into `Designer-Session-Prep.md`. No content lost — full Phase 1-4 detailed specs, Preferences specification, VocabularyPack, and intelligence flow details now live in the Prep doc's "Decisions Already Made" section. `designer.md` deleted. The two session docs (`Designer-Session-Guide.md` + `Designer-Session-Prep.md`) are now the complete authority for Designer.
- **DECIDED:** References to `designer.md` cleaned from all memory files (conversation_agenda.md, project_document_inventory.md, project_tool_checklists.md).

---

## Session: 2026-04-05 (afternoon) — Backend Rebuild Alignment

### Prospector Page — Fresh Redesign
- **DECIDED:** Prospector input page is NOT ported from proof-of-concept. It will be redesigned fresh on the new framework once the backend is building. Simple page — will go quickly using our standard process.

### Page Names — Simplified
- **DECIDED:** Inspector pages named for what the user is doing, not persona-specific language:
  - Home → **Inspector** (starting a search)
  - Caseboard → **Product Selection** (choosing products for deep dive)
  - Dossier → **Full Analysis** (reviewing deep research)
- **DECIDED:** "Seller Action Plan" and "Seller & SE Action Plan and Solution Recommendations" are retired. Content serves both personas through progressive disclosure — page names stay simple.
- **DECIDED:** "Deep Dive →" button on Product Selection leads to Full Analysis.

### Remaining Build Items
- **DECIDED:** "Back to Company Search" link text — fine as-is.
- **DECIDED:** "Product families" in family picker — fine, capitalize the F.
- **DECIDED:** 6 product selection limit — fine for now, should be configurable.
- **DECIDED:** All CSS must use theme variables — no hardcoded hex values. Complete rewrite to new standard. Visual output must be identical to proof-of-concept pages.

### Designer Page — Fresh Redesign
- **DECIDED:** Designer page is NOT ported from proof-of-concept. Will be redesigned fresh after the Designer Foundation Session.

### Button Label — "Run Dossier" renamed
- **DECIDED:** "Run Dossier →" button on Caseboard renamed to **"Deep Dive →"**

### Org Type Badge Colors — Three Groups
- **DECIDED:** Org type badges use three colors by group, NOT all purple. Colors are classification, not assessment — must not overlap with scoring colors (green/amber/red).
  - **Purple** — Product creators: Software companies, Enterprise/multi-product
  - **Teal** — Learning-focused: Training & certification orgs, Academic institutions
  - **Warm blue / Slate blue** — Channel/partners: GSIs, Distributors, Professional services, LMS companies, Content development firms
- **DECIDED:** Exact hex values for teal and warm blue TBD during build — must complement the platform palette and pass WCAG AA.

### Caseboard Tier Labels — Renamed
- **DECIDED:** Discovery tier labels renamed to be honest about confidence level at discovery depth:
  - Highly Likely → **Seems Promising**
  - Likely → **Likely**
  - Less Likely → **Uncertain**
  - Not Likely → **Unlikely**
- **DECIDED:** These communicate "early read, not conclusion" — GP3 trustworthiness. No false confidence.

### Deployment Model Data Value
- **DECIDED:** Rename `self-hosted` data value to `installable` — display and data should match (GP4).

### Inspector UX Pages
- **DECIDED:** Home page, Inspector search page, Prospector search/upload page, and Caseboard are all close to final from the proof-of-concept. UX design carries forward — no redesign needed.
- **DECIDED:** The header from those pages is also the header for the Dossier page — consistent navigation across the entire Inspector experience.
- **DECIDED:** All four pages plus the dossier are rewritten from scratch as part of the rebuild — not carried forward from old templates. Same UX design, clean new code on the new backend/vocabulary/data model. Avoids legacy template risk.

### Test Plan Created
- **DECIDED:** Test plan document created at `docs/Test-Plan.md` — 8 categories, all traced to Guiding Principles.
- **DECIDED:** Tests implemented in pytest, stored in `backend/tests/`, one file per category.
- **DECIDED:** Test plan document is the strategy (for humans). Test code files are the enforcement (for the machine). No duplication — code references the plan.

### Badge Layout — Responsive, No Hard Cap
- **DECIDED:** No hard cap on badge count per dimension. Show as much context as possible (GP1).
- **DECIDED:** Badges wrap responsively — if they flow to the next row, everything below moves down. Nothing overlaps, clips, or breaks.
- **DECIDED:** Backend uses a soft warning if a dimension produces more than 5 badges — logged for review, not rejected.
- **DECIDED:** UX validation at standard breakpoints (desktop, laptop, tablet) to ensure layout integrity.

### Confidence Field — Level + Explanation
- **DECIDED:** Every evidence finding carries two confidence fields: the level (confirmed/indicated/inferred) AND a short AI-generated explanation of why that level was assigned.
- **DECIDED:** Explanation is one sentence, maybe two at most — specific enough to understand the basis, brief enough to fit in a badge hover modal.
- **DECIDED:** Both fields are required — tests validate that evidence without confidence level AND explanation is invalid.
- **DECIDED:** UX must respect the explanation text — word wrapping, layout in the hover modal must look good.

### Seller Briefcase — Separate AI Call
- **DECIDED:** Seller Briefcase (Key Technical Questions, Conversation Starters, Account Intelligence) is generated in a separate AI call AFTER scoring is complete — not combined into the scoring call.
- **DECIDED:** The briefcase call receives complete scoring output as context — all scores, badges, and evidence. This produces sharper, more pointed seller guidance because the AI is synthesizing, not multitasking.
- **DECIDED:** Key Technical Questions are the highest priority — who to talk to, what department, what to ask, why it matters. Must be tight, clear, concise, and complete.
- **DECIDED:** Extra cost is ~$0.03-0.05/product (Sonnet) or ~$0.15-0.25/product (Opus). Worth it for the quality improvement.
- **DECIDED:** Briefcase only applies to full dossiers (Inspector deep dive), not Prospector batch scoring.

### Scoring — Product Labability Floor Protection
- **DECIDED:** The 40% weight alone is not sufficient to prevent undeliverable products from scoring too high. A product at 5/100 Product Labability still produces a ~50 Fit Score with a strong company — that's misleading.
- **DECIDED:** The old multiplier thresholds (32, 24, 19, 10) are from the proof-of-concept and do not carry forward. Fresh mechanism needed.
- **DECIDED:** The Fit Score stays mathematically honest. When Product Labability is below a threshold, a UX badge/flag communicates the delivery risk so sellers aren't misled by the overall number. Math is one thing, communication is another — both need to be right.
- **OPEN:** Exact threshold and UX language TBD — decide after backend scoring is working so we can see real numbers.

### Scoring — AI Flexibility Within Ranges
- **DECIDED:** The AI determines the exact score within defined ranges (e.g., +21 to +25 for Full Lifecycle API) based on evidence quality. Not fixed values.
- **DECIDED:** Evidence quality drives score placement — comprehensive, well-documented findings earn the top of the range; limited or inferred findings earn the bottom.
- **DECIDED:** GP3 makes this trustworthy — the AI must explain its reasoning in the evidence bullet. Confidence coding (confirmed/indicated/inferred) reinforces accountability. Range = flexibility. Evidence = accountability.

### Data Storage — Three Domains Separated from Day One
- **DECIDED:** Product data, program data, and company intelligence stored in separate locations from day one — not field-level separation within shared files.
- **DECIDED:** This is architectural separation as the Foundation requires — "the separation must be architectural, not just a permissions layer." When auth comes, it's access control on clean boundaries, not a retrofit.
- **DECIDED:** Old cached data from the proof-of-concept is not migrated. Clean slate — everything scores fresh on the new framework.
- **DECIDED:** Cache TTL remains 45 days with manual refresh button available.

### Architecture — Three Inputs to Every Scoring Run
- **DECIDED:** The Prompt Generation System combines three distinct inputs: Company Research (them) + Skillable Knowledge (us) + Scoring Framework (the rules). This is now explicit in Platform Foundation.
- **DECIDED:** Skillable Knowledge stored as JSON files in `backend/knowledge/` — updatable without code changes. Separate from scoring config. Four files: skillable_capabilities.json, delivery_patterns.json, competitors.json, contact_guidance.json.
- **DECIDED:** Company research gathered by the researcher, stored organized by dimension in `data_new/company_intel/` — not raw snippets, structured evidence.
- **DECIDED:** No old code used anywhere. Storage, researcher, and all modules rebuilt from scratch. Old `storage.py` and `researcher.py` are proof-of-concept.

### Domain-Based Lab Platform Detection
- **DECIDED:** Domain-based detection (scanning fetched pages for outbound links to known lab platform domains) is included in the first build, not deferred.
- **DECIDED:** This is critical for trustworthiness — if we can't detect our own customers, that's a trust problem. Also detects competitors.
- **DECIDED:** Uses the canonical lab platform list from scoring_config.py. Scans page content we're already fetching — not a separate research pass. Link evidence is stronger than name mentions.

### Research Depth
- **DECIDED:** Two research depths, not three. Discovery-depth research serves both Prospector and Caseboard. Full scoring is for the Inspector dossier deep dive.
- **DECIDED:** Deeper dossier research sharpens lighter discovery data over time (GP5 — Intelligence Compounds). The lighter research is never wasted.
- **DECIDED:** If Prospector scale (100+ companies) creates speed or cost concerns, revisit with operational constraints (throttling, batching) — not by reducing research depth. Best current thinking.

---

## Session: 2026-04-05 — UX Wireframe, Badge System, and Document Synthesis

### UX Wireframe — Inspector Dossier
- **DECIDED:** 70/30 visual split — two product pillar cards on left (70%), customer fit card on right (30%, slightly different background)
- **DECIDED:** Hero section: product name with dropdown selector (left), Fit Score centered (star of the show), ACV Potential (right)
- **DECIDED:** Product selector dropdown: product name (left-aligned, truncated at ~40 chars), score, purple subcategory badge
- **DECIDED:** Verdict badge below product name, "HIGH FIT · HIGH ACV" below that (all caps)
- **DECIDED:** All dimension names in ALL CAPS in the UX
- **DECIDED:** No connector lines between hero and pillars
- **DECIDED:** Pillar card padding balanced top/bottom
- **DECIDED:** Score bars with gradient green/amber fill

### UX Icons and Navigation
- **DECIDED:** Info icons (?) and doc icons (document SVG) on pillar headers — same size, muted color, green on hover
- **DECIDED:** Two nav links: "Back to Product Selection" and "Search Another Company"
- **DECIDED:** Cache date shown as hoverable link with "Refresh cache" tooltip
- **DECIDED:** Word export (not PDF) — sellers can customize

### Badge System Refinements
- **DECIDED:** Purple subcategory badges for product categories — consistent color for classification badges
- **DECIDED:** Company classification badge uses purple (same as subcategory)
- **DECIDED:** Every badge MUST carry evidence — no badge renders without evidence payload
- **DECIDED:** Badge evidence on hover: 1.5 second delay, modal with bullets, source, confidence
- **DECIDED:** Confidence coding: confirmed, indicated, inferred — core logic, stored as field on every finding

### Seller Briefcase
- **DECIDED:** Three sections below pillar cards: Key Technical Questions (Product Labability), Conversation Starters (Instructional Value), Account Intelligence (Customer Fit)
- **DECIDED:** Each section has info icon for documentation link

### Verdict Grid and ACV
- **DECIDED:** ACV tiers: High, Medium, Low
- **DECIDED:** ACV values use lowercase k (thousands) and uppercase M (millions)

### HubSpot
- **DECIDED:** HubSpot ICP Context field (not generic "notes")

### Standards
- **DECIDED:** WCAG AA compliance on all colors — build standard
- **DECIDED:** No spaces in file names
- **DECIDED:** Fewer badges with more context
- **DECIDED:** Documentation IS the in-app explainability layer

### Document Synthesis
- **DECIDED:** All three core documents (Platform-Foundation.md, Badging-and-Scoring-Reference.md, Research-Methodology-Improvements.md) synthesized to best current thinking
- **DECIDED:** Wireframe HTML committed separately — not part of doc synthesis

---

## Session: 2026-04-04 — Platform Foundation Strategic Session

### Strategic Foundation Established
- **DECIDED:** Platform-Foundation.md is now the authoritative source of truth for all strategic decisions. Where it conflicts with other documents, it wins.
- **DECIDED:** Best current thinking, always. Documents are fully synthesized, never appended. When thinking evolves, the document evolves with it.

### Guiding Principles (5 + End-to-End Principle)
- **DECIDED:** GP1: Right Information, Right Time, Right Person, Right Context, Right Way
- **DECIDED:** GP2: Why -> What -> How (the thinking model and conversational competence builder)
- **DECIDED:** GP3: Explainably Trustworthy (every judgment traceable from conclusion to evidence)
- **DECIDED:** GP4: Self-Evident Design (intent evident at every layer — variable names to UX)
- **DECIDED:** GP5: Intelligence Compounds — It Never Resets
- **DECIDED:** End-to-End Principle: The framework shapes how we gather, store, judge, and present. One model, end to end.

### Scoring Framework — Final Structure (Three Pillars)
- **DECIDED:** Hierarchy is Fit Score -> Pillars -> Dimensions -> Requirements (Requirements = badges)
- **DECIDED:** Three Pillars (not four). Old Customer Motivation and Organizational Readiness merged into Customer Fit.
- **DECIDED:** 70/30 product vs organization split. Product dominates the score.
- **DECIDED:** ACV Potential = separate calculated metric, not part of Fit Score
- **DECIDED:** Two hero metrics in UX: Fit Score + ACV Potential (separate, side by side)
- **DECIDED:** Each Pillar scores out of 100 internally, then weighted. Makes scores intuitive.
- **DECIDED:** Final weights:
  - Product Labability 40% (How labable is this product?)
  - Instructional Value 30% (Does this product have instructional value for hands-on training?) — was "Product Demand"
  - Customer Fit 30% (Is this organization a good match for Skillable?) — combines old Customer Motivation + Organizational Readiness

### Pillar 1: Product Labability (40%) — Dimensions
- **DECIDED:** Four dimensions: Provisioning (35), Lab Access (25), Scoring (15), Teardown (25)
- **DECIDED:** "Provisioning" restored (was briefly "Orchestration Method" — too long)
- **DECIDED:** "Lab Access" replaces "Licensing & Accounts" (working name, may refine)
- **DECIDED:** No more "gates" — use "dimensions" within Product Labability
- **DECIDED:** Old scoring tables split — Lab Access columns (Entra ID SSO, Credential Pool, etc.) moved out of Provisioning into Lab Access as separate scoring items
- **DECIDED:** Lab Access uses base score + penalties model (Credit Card -10, MFA -10, Anti-Automation -5, Rate Limits -5, Provisioning Lag -5, High License Cost -5)
- **DECIDED:** Scoring dimension: API Scorable, Script Scorable, Simulation Scorable, AI Vision Scorable, MCQ Scorable — always has a fallback
- **DECIDED:** Teardown at 25 (elevated from 10) — orphaned cloud resources are real financial risk

### Pillar 2: Instructional Value (30%) — Dimensions
- **DECIDED:** Pillar renamed from "Product Demand" to "Instructional Value" — better name, was the original
- **DECIDED:** Four dimensions: Product Complexity (40), Mastery Stakes (25), Lab Versatility (15), Market Demand (20)
- **DECIDED:** Product Complexity badges: Deep Configuration, Multi-Phase Workflow, Role Diversity, Troubleshooting, Complex Networking, Integration Complexity, AI Practice Required, Consumer Grade (red), Simple UX (red)
- **DECIDED:** Mastery Stakes badges: High-Stakes Skills, Steep Learning Curve, Adoption Risk (Certification Program moved to Market Demand)
- **DECIDED:** Lab Versatility: menu of 12 lab types, AI picks 1-2 per product (Red vs Blue, Simulated Attack, Incident Response, Break/Fix, Team Handoff, Bug Bounty, Cyber Range, Performance Tuning, Migration Lab, Architecture Challenge, Compliance Audit, Disaster Recovery)
- **DECIDED:** Market Demand badges are variable-driven: specific regions (Global, NAMER & EMEA, US Only), specific user counts (~2M Users), specific growth signals (Series D $200M, IPO 2024), Active Certification, Competitor Labs Confirmed
- **DECIDED:** AI market demand has two distinct forms: Learning AI-embedded features vs. Creating AI

### Pillar 3: Customer Fit (30%) — NEW Combined Pillar
- **DECIDED:** Combines old Customer Motivation (20%) and Organizational Readiness (15%) into one Pillar
- **DECIDED:** Four dimensions: Training Commitment (25), Organizational DNA (25), Delivery Capacity (30), Build Capacity (20)
- **DECIDED:** Training Commitment replaces "Training Motivation" — commitment is evidence, motivation is intent
- **DECIDED:** Training Commitment badges across three motivation categories: Customer Enablement, Customer Success, Channel Enablement (adoption); Certification Program, Training Catalog (skill development); Regulated Industry, Compliance Training Program, Audit Requirements (compliance); Training Leadership, Training Culture (cross-cutting)
- **DECIDED:** Organizational DNA is NEW — partner ecosystem, build vs buy, integration maturity, ease of engagement. All variable-driven.
- **DECIDED:** Delivery Capacity: ATP/Learning Partners, {LMS Name (Public/Internal)}, {Lab Platform Name}, Gray Market Offering. Consolidated from old 11 badges to 4.
- **DECIDED:** Skillable TMS is a valid LMS badge (green — our own platform)
- **DECIDED:** Build Capacity: Content Dev Team, Technical Build Team, DIY Labs, Content Outsourcing
- **DECIDED:** DIY Labs can appear in both Delivery Capacity and Build Capacity — means two different things in each

### Verdict Grid
- **DECIDED:** 10 verdicts across Fit Score x ACV Potential matrix
- **DECIDED:** Five score color bands: Dark Green (>=80), Green (65-79), Light Amber (45-64), Amber (25-44), Red (<25)
- **DECIDED:** Verdicts: Prime Target, Strong Prospect, Good Fit, High Potential, Worth Pursuing, Solid Prospect, Assess First, Keep Watch, Deprioritize, Poor Fit
- **DECIDED:** Same verdict can appear in two color bands — verdict = action, color = confidence

### HubSpot Integration
- **DECIDED:** HubSpot is a data destination, not a tool in the display table
- **DECIDED:** HubSpot ICP Context = synthesis note (1-2 sentences), regenerated from best current intelligence every time (GP5)
- **DECIDED:** Variable name: `hubspot_icp_context`

### Prompt Generation System
- **DECIDED:** Static product_scoring.txt replaced by three-layer Prompt Generation System
- **DECIDED:** Layer 1: Configuration — single structured file, all variables defined once
- **DECIDED:** Layer 2: Template — AI instruction structure with {placeholder} references to config
- **DECIDED:** Layer 3: Generated Prompt — assembled at runtime, never a static file
- **DECIDED:** Future admin GUI for config editing with validation, change history, admin-only access

### Define-Once Principle
- **DECIDED:** All pillar names, dimension names, weights, thresholds, badges, vocabulary defined once in config, referenced everywhere
- **DECIDED:** Nothing hard-coded. One change propagates through code, prompts, UX, documentation.
- **DECIDED:** Added as a named principle in the Foundation document

### Confidence Coding
- **DECIDED:** Confidence (confirmed/indicated/inferred) is core logic in the codebase, not just display
- **DECIDED:** Every finding carries confidence level as a stored field
- **DECIDED:** Confidence influences badge color assignment (inferred may cap at amber)

### In-App Documentation
- **DECIDED:** Documentation IS the in-app explainability layer (GP3)
- **DECIDED:** Section-level linking, not badge-level — one click shows the whole section
- **DECIDED:** Written clearly enough for sellers to understand
- **DECIDED:** When docs update, in-app help updates automatically — same source

### Standards
- **DECIDED:** No spaces in file names — ever
- **DECIDED:** Fewer badges with more context, not many badges with less
- **DECIDED:** No dimension should need more than 3-5 badges to tell its story

### Badge System Updated
- **DECIDED:** Four colors: Green (strength), Gray (neutral/context — NEW), Amber (risk), Red (blocker)
- **DECIDED:** Badge names should show the solution, not the problem, when recommendation is clear
- **DECIDED:** Variable-driven badges: text itself changes based on findings (LMS name, competitor name)
- **DECIDED:** If green and unremarkable, don't surface — only show what matters

### Evidence Confidence Language
- **DECIDED:** Three levels: Confirmed (direct primary source), Indicated (strong indirect), Inferred (AI assumption)
- **DECIDED:** Confidence communicated through language in evidence text, not visual indicators
- **DECIDED:** Badge color = the assessment. Evidence language = the basis. Together they're complete.
- **DECIDED:** Evidence bullets must be clear, concise, and complete. No filler. Specific details, sources, reasoning.

### Organization Types — Variable-Driven
- **DECIDED:** Platform cannot be built around "software companies" as sole organizing concept
- **DECIDED:** Eight organization types: Software companies, Training & certification orgs, GSIs, Content development firms, LMS companies, Distributors, Universities & schools, Enterprise/multi-product
- **DECIDED:** Product Labability always applies to underlying technology, not training wrapper
- **DECIDED:** All labels, categories, messaging derive from product data — variable-driven, not hard-coded

### Lab Platform Detection
- **DECIDED:** One canonical list of all lab platform providers, maintained in one place, referenced everywhere
- **DECIDED:** Lab platform badges include Skillable (green) + all competitors (amber) + DIY Labs (amber)
- **DECIDED:** Research Methodology Improvements doc created for detection logic improvements

### Data Architecture
- **DECIDED:** Three domains: Product data (open), Program data (scoped), Company intelligence (internal-only)
- **DECIDED:** Architect for authorization now, implement later
- **DECIDED:** Customers in Designer see product data, never company intelligence

### Document Strategy
- **DECIDED:** Two authoritative documents replace four:
  - Platform-Foundation.md (strategic authority)
  - Badging-and-Scoring-Reference.md (operational detail — to be created)
- **DECIDED:** Old Badging-Framework-Core.md and Scoring-Framework-Core.md will be replaced
- **DECIDED:** product_scoring.txt will be regenerated fresh from the two new docs
- **DECIDED:** Define once, reference everywhere

### Standards
- **DECIDED:** No spaces in file names — ever
- **DECIDED:** Pre-commit vocabulary hook will be updated when new docs are finalized

### Next Steps Agreed
1. Finalize Platform Foundation (done)
2. Create Badging-and-Scoring-Reference.md (new, from scratch)
3. Go through Badging and Scoring doc section by section together
4. Generate new product_scoring.txt from the two docs
5. Write automated tests before code refactor
6. Major code refactor — rename fields, reorganize models, align everything

---

## Session: 2026-04-03 (evening) — Render Deployment & Dossier UX Overhaul

### Render Deployment
- **DECIDED:** App deployed to Render at `https://skillable-intelligence.onrender.com`
- **DECIDED:** Gunicorn timeout set to 300s in Render dashboard (not render.yaml — dashboard overrides yaml after initial setup)
- **DECIDED:** Render filesystem is ephemeral — every redeploy wipes the analysis cache. Persistent storage deferred; acceptable for internal testing
- **DECIDED:** Auto-deploy on commit enabled

### Vocabulary Change: Market Fit
- **DECIDED:** Rename "Market Readiness" to "Market Fit" everywhere — UI, docs, prompts, CLAUDE.md, locked vocabulary, pre-commit validator
- **NOTE:** Market Fit has now been superseded — absorbed into Product Demand pillar's Market Demand dimension (see 2026-04-04 session)
- **DECIDED:** Internal data key stays as `market_readiness` — will be renamed during code refactor

### Dossier Hero Section
- **DECIDED:** Remove boxes around score and ACV — clean horizontal row, no cards
- **DECIDED:** ACV: large green text (1.9rem, 900 weight, #24ED9B), right-aligned
- **DECIDED:** ACV subtitle: "Estimate based on X of Y products" in amber (#f59e0b), where Y = total discovered products (not just scored)
- **DECIDED:** Remove vertical hairline between score and ACV
- **DECIDED:** Remove horizontal hairline below hero
- **DECIDED:** Remove Next Steps section entirely — information distributed into product detail sections
- **DECIDED:** "Back to Caseboard" renamed to "Back to Product Selection"

### Dossier Four Dimension Boxes
- **NOTE:** These will be restructured to reflect the new four Pillars (see 2026-04-04 session)
- **DECIDED:** Subsection-grouped badges per Badging Framework (not flat badge lists)
- **DECIDED:** Subsection labels in purple (#a78bfa) — structural framework element, distinct from evidence badges
- **DECIDED:** Badges left-aligned to consistent column right of purple labels
- **DECIDED:** Max 2 badges per subsection row for layout consistency
- **DECIDED:** Default amber badge shown when no evidence found for a subsection (risk = unknown)
- **DECIDED:** Lab Format Opportunities has no default badge (additive, not a risk)
- **DECIDED:** Dimension scores: larger (1.4rem), bold green (#24ED9B), right-aligned, with visible max values
- **DECIDED:** Emojis removed from all badges in dimension boxes

### Dossier Product Detail Panels
- **DECIDED:** "Help your champion find" recommendation pulled to top as amber callout box ("Essential Technical Resource")
- **DECIDED:** "Delivery Path" recommendation merged into Provisioning subsection
- **DECIDED:** "Scoring Approach" recommendation merged into Scoring subsection
- **DECIDED:** Summary paragraphs removed from all four dimension sections (redundant with evidence bullets)
- **DECIDED:** Orchestration method removed from product bar and detail — redundant with Provisioning badges
- **DECIDED:** Category badge removed from product bar; subcategory badge added (matches Caseboard)
- **DECIDED:** Highlight badge (green, "why labs matter") moved next to product name
- **DECIDED:** Product score moved to right side, larger (1.4rem)
- **DECIDED:** Three badges (subcategory, highlight, verdict) normalized to same height
- **DECIDED:** Stronger section dividers between dimensions (2px solid)
- **DECIDED:** Dimension definitions added to section headers
- **DECIDED:** Potential Labs card names in purple (#a78bfa)

### Backend Infrastructure
- **DECIDED:** Subsection mappings added to `core.py` for all four dimensions
- **NOTE:** These mappings will be restructured during the code refactor to reflect new Pillars/Dimensions
- **DECIDED:** `dedup_evidence` filter added — keeps first occurrence of each badge name per subsection

### Lab Format Pattern — Core Platform Concept
- **DECIDED:** `{Product-Specific-Item} {LabFormat}` is a core platform principle
- **DECIDED:** The LabFormat is always ONE word from a fixed vocabulary: Attack, Defense, Simulation, Collaboration, Fault, Recovery, Troubleshoot, Challenge, Incident, Build, Optimization
- **DECIDED:** This pattern flows across all three tools

---

## Session: 2026-04-03 — Platform Hardening & Code Review

### Shared CSS Theme
- **DECIDED:** `tools/shared/templates/_theme.html` wired into dossier, caseboard, product_detail, and prospector_results
- **DECIDED:** CSS class `yellow` renamed to `amber` everywhere — aligns with locked vocabulary

### Error Handling
- **DECIDED:** `_error_response()` added to `core.py` — returns JSON for API/XHR, styled HTML for browser

### Storage Layer Hardening
- **DECIDED:** All JSON file writes use atomic temp-file + `os.replace()` pattern
- **DECIDED:** Read-modify-write operations protected by `threading.Lock()`
- **DECIDED:** In-memory company-name index added to `storage.py`

### Shared Constants
- **DECIDED:** `backend/constants.py` created — single source of truth for all hardcoded values
- **NOTE:** Will be updated during refactor to reflect new Pillar/Dimension vocabulary

### Startup Validation
- **DECIDED:** `config.validate_startup()` runs at app init

### Thread Pool Caps
- **DECIDED:** `scorer.py` ThreadPoolExecutor capped at 6

---

## Session: 2026-04-03 — Code Review, Cleanup & Session Infrastructure

### CLAUDE.md
- **DECIDED:** `CLAUDE.md` created in project root — loads automatically every session
- **NOTE:** Will need to be updated to reflect new vocabulary and Pillar structure

### Repository Cleanup
- **DECIDED:** `backend/docs/` deleted — Claude session artifacts
- **DECIDED:** `tools/designer/legacy_ref/` deleted — superseded old code
- **DECIDED:** Word docs restored after accidental deletion — never delete Word docs without asking

### Framework Standardization
- **NOTE:** The vocabulary locked in this session has been superseded by the 2026-04-04 Platform Foundation session. New vocabulary is authoritative. Old locked terms (Instructional Value, Market Fit, Difficult to Master, Mastery Matters, Licensing & Accounts, etc.) are now legacy.
