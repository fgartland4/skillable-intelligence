# Next Session — Todo List

**Last updated:** 2026-04-17 (late-session — ACV Build 1 partial shipment)

---

## §1 — START HERE NEXT SESSION

**State of ACV architecture (2026-04-17 late):** Build 1 is ~80% shipped — framework code is live, legacy Claude holistic is fully retired, partial retrofit done on known customers.  Two known defects remain + Build 2 + Platform-Foundation rewrite.  A new Claude picks up from the "What ships next session" section below.

### What's already shipped (do NOT redo)

| Commit | What |
|---|---|
| `1b23f94` | Capability wiring + unified rebalancing machinery (scored + unscored paths) |
| `e2461f6` | ACV architecture spec written across decision-log, next-session-todo, Platform-Foundation header |
| `23df09e` | Framework functions: `compute_company_total_audience`, `allocate_audience_to_products`, `compute_discovery_company_acv` |
| `60cc381` | Known-customer floor — `max(framework, current_acv)` for existing Skillable customers |
| `38bab23` | Wire-up — `intelligence.discover()` now calls framework function.  `scripts/retrofit_discovery_acv.py` shipped. |
| `d55cb90` | **Legacy cleanup** — deleted 575 lines of retired code: `estimate_holistic_acv`, `_HOLISTIC_ACV_PROMPT`, `_format_anonymized_calibration_block`, `_build_holistic_acv_context`, `_build_known_customer_constraints`, `_scrub_customer_data`, and the three guardrail constants.  Deleted obsolete `scripts/compute_customer_potentials.py` + `scripts/retrofit_acv.py`.  Deleted `docs/unified-acv-model.md` (to be folded into Platform-Foundation). |
| `7608bb7` | Retrofit script `--include-org-types` / `--exclude-org-types` filters.  Known-customers retrofit partially run: 34 customers kept (framework-correct or floor-pinned), 13 zeroed (ILT inflation or data-quality outliers). |

### KNOWN DEFECTS TO FIX FIRST NEXT SESSION

**Defect 1 — ILT training org audience formula over-inflates.**
For ILT training orgs (AXcademy, Skillhouse, Leading Learning Partners Association, New Horizons, ONLC, LearnQuest, etc.), the current `compute_company_total_audience` formula treats them as `DISTINCT_AUDIENCE_ORG_TYPES` with `sum(all capped per-product audiences)`.  Combined with org-type hours override (18 hrs classroom) and 25% adoption, this produces $15-250M discovery-time ACV for small ILT shops with a handful of class offerings.  Catastrophic inflation.

**Fix (proposed):** Switch ILT org types from `sum(all)` to `sum(max per archetype)` like software_company uses.  This recognizes that if a training shop teaches Microsoft + AWS + Cisco courses, the same instructors and students often span archetypes — distinct-audience-per-product is wrong.  OR: apply a total-employee-proportional cap (training shop with 10 instructors can't train 500K students).

**Files to edit:**
- `backend/acv_calculator.py` → `compute_company_total_audience` → move `ILT TRAINING ORG` from `DISTINCT_AUDIENCE_ORG_TYPES` into the `sum(max per archetype)` case, OR add a separate ILT-specific formula.  Test against: AXcademy (3 products), Skillhouse (1), LLPA (7), New Horizons (7), ONLC (12), LearnQuest (13).  Target ACV: under $5M for each of these small ILT shops.

**Defect 2 — Non-customer retrofit not run; Prospector shows mixed legacy/framework values.**
For non-customer prospects, retrofit would write discovery-time Motion-1-only framework numbers that systematically undersell them (no known-customer floor applies).  Left legacy Claude values in place for those — consistency broken.

**Fix options:**
- **(A)** Once ILT defect is fixed, run the full retrofit via `scripts/retrofit_discovery_acv.py`.  Accept that non-customer prospects will look smaller in Prospector until Deep-Dived.  Semantically correct.
- **(B)** Add discovery-time estimates for Motions 2-5 (partner / employee / cert / events) from company-level signals so non-customers get a more complete number.  More work, more accurate.
- **(C)** Leave legacy in place for non-customers; framework applies only on fresh research.  Mixed paths but no shrinkage.

Recommend **(A)** — consistency with the "one standard" principle — AFTER ILT defect fix.

### What ships next session (in order)

**Updates 2026-04-17 end of session:** Items 1, 2, 3, 5 from the previous list ALL SHIPPED TONIGHT (ILT formula fix moved ILT into partial-overlap branch; full non-customer retrofit ran across 397 discoveries; 13 zeroed customers partially re-retrofitted — 2 came back with numbers, 11 remain zeroed due to data-quality issues in `known_customers.json`; `SCORING_MATH_VERSION` bumped).  Only items 4 (Platform-Foundation rewrite) and 6 (Build 2) remain.  Details below:

#### Remaining Item A — Rewrite `docs/Platform-Foundation.md` → ACV Potential Model section

**Current state of that section:** Has a prominent "⚠ 2026-04-17 — Architecture alignment in progress" header at the top pointing to decision-log + next-session-todo.  The rest of the section describes the PRE-alignment model (Claude holistic call, calibration block, hard cap) which is now fully retired in code but still exists as doc content.

**What to do:**
1. Read the existing section (Platform-Foundation.md lines ~1184 through ~1600 — the entire "ACV Potential Model" section).
2. Delete the "⚠ 2026-04-17" header block at the top (no longer "in progress" — the architecture is shipped).
3. Rewrite the section with best current thinking.  The new content should describe:
   - **The universal unit** (lab hours consumed = audience × adoption × hours × rate) — KEEP this framing, it's still correct.
   - **The five consumption motions** table — KEEP, unchanged.
   - **Company-level audience allocation (NEW — this is the 2026-04-17 architecture):**
     - Every product has one `estimated_user_base` field = humans who'd take training for this product (universal definition across org types).
     - `compute_company_total_audience(discovery)` produces a single company-level trainable audience using org-type-aware Python formula.  Document the four cases:
       - SHARED_ADMIN (software / enterprise software): `sum(max per archetype)` — enterprise_admin users overlap across Azure + Intune + Entra, but are distinct from developer_platform users.
       - DISTINCT_AUDIENCE (academic / LMS / TRAINING ORG): `sum(all capped)` — programs / catalogs are mostly different humans.
       - INDUSTRY_AUTHORITY: `sum(max per archetype)` — career-track-scoped overlap.
       - PARTIAL_OVERLAP (GSI / VAR / tech distributor / ILT training org): `0.70 × sum(max per archetype)` — cross-trained practitioners.
     - ILT was moved to PARTIAL_OVERLAP on 2026-04-17 late because `sum(all)` produced catastrophic inflation (LLPA $227M).
   - **Allocation to products** — company total × (raw_audience × archetype_multiplier) / sum_of_weights.  Archetype multiplier = IV_CEILING / 100.
   - **Per-product Motion 1 ACV** = allocated_share × adoption × hours × rate.
   - **Motions 2-5** remain per-product from fact drawers at Deep Dive time.
   - **Known-customer floor** — `max(framework, KNOWN_CUSTOMER_CURRENT_ACV[name])` so customers can't display below their actual ACV.
   - **Partnership-only** (Content Development firms) — delegates to `_build_partnership_acv_result` for partnership-shape output.
4. Delete the sections on "Discovery-Level ACV Estimation (Option 2 — Holistic)" — that describes the retired Claude call.
5. Delete references to `_HOLISTIC_ACV_PROMPT`, `HOLISTIC_ACV_COMPANY_HARD_CAP`, `HOLISTIC_ACV_MAX_RANGE_RATIO`, `HOLISTIC_ACV_PER_USER_CEILING`, `KNOWN_CUSTOMER_STAGE_CEILING_MULT`, `_format_anonymized_calibration_block`, `estimate_holistic_acv`, `_scrub_customer_data`, `_build_known_customer_constraints` — all retired.
6. Delete the "Relationship to Mark's Labability Prompt" sub-section if it's no longer relevant (Mark's framework informed the motions — still relevant — but not the holistic Claude call).
7. Keep "How Adoption Patterns Vary by Organization Type" table — the org-type overrides (Academic 25%/15hrs, ILT 25%/18hrs, etc.) are still correct.
8. Also update `docs/Badging-and-Scoring-Reference.md` — remove references to the retired constants (lines ~1049-1078 have table entries about hard cap / range ratio / per-user ceiling / stage ceiling mult — delete those rows).
9. Commit with a message that explains what changed and that this replaces the "in progress" header.

**Existing helpful signposts for the rewrite:**
- `backend/acv_calculator.py` lines 1197 onward — the `compute_discovery_company_acv` function is heavily commented.  Read those comments; they describe the architecture cleanly in function-level docstring form.
- `decision-log.md` 2026-04-17 late entry — has the full DECIDED list with rationale.
- This file's §1 block — the Build 1 summary.

**Estimated time:** 45-90 min depending on how thorough the rewrite is.  Don't rush; this is the authoritative spec.

#### Remaining Item B — Build 2: ACV-specific dimension weights

**Why:**  The ACV gate (per-product multiplier applied to `raw_acv`) currently uses the standard Fit Score (composed of PL 50 / IV 20 / CF 30 with each pillar's standard dimension weights).  Frank's agreed design is that ACV should use ACV-specific dimension weights that reflect what actually predicts ACV:
  - **CF for ACV:** Training Commitment 40, **Delivery Capacity 60**, **Build Capacity 0**, Org DNA 0.  Partners / ProServ can BUILD labs — Build Capacity shouldn't drag ACV down.  Delivery Capacity (can they ship training at scale) is the real CF driver of ACV.
  - **IV for ACV:** **Market Demand 40-50**, Product Complexity 25, Mastery Stakes 25, **Lab Versatility 0**.  Market Demand (does anyone buy paid training for this?) dominates.  Lab Versatility is already handled by Product Labability — zero-weight here to avoid double-counting.
  - **PL for ACV:** unchanged from Fit Score — same dimension weights.
  - Pillar weights: PL 50 / IV 20 / CF 30 (same as Fit Score at pillar level).

**What to build:**
1. **New constants in `backend/scoring_config.py`:**
   ```python
   ACV_GATE_PILLAR_WEIGHTS = {"product_labability": 50, "instructional_value": 20, "customer_fit": 30}
   ACV_GATE_CF_DIMENSION_WEIGHTS = {"training_commitment": 40, "delivery_capacity": 60, "build_capacity": 0, "organizational_dna": 0}
   ACV_GATE_IV_DIMENSION_WEIGHTS = {"market_demand": 40, "product_complexity": 25, "mastery_stakes": 25, "lab_versatility": 0}
   # PL unchanged — uses existing PILLAR_1_DIMENSION_WEIGHTS
   ```
   Start with MD=40.  Can tune to 50 later based on validation.
2. **New composer function in `backend/acv_calculator.py`:**
   ```python
   def compose_acv_gate_score(product, company_analysis) -> int:
       """Compose the ACV gate score (0-100) from the three pillars using ACV-specific dimension weights."""
       # PL — use product.fit_score.product_labability.score (already uses Fit-Score dimension weights; unchanged)
       # IV — recompute from product.fit_score.instructional_value.dimensions using ACV_GATE_IV_DIMENSION_WEIGHTS
       # CF — recompute from product.fit_score.customer_fit.dimensions using ACV_GATE_CF_DIMENSION_WEIGHTS
       # Compose: PL * 0.50 + IV * 0.20 * tech_fit_multiplier + CF * 0.30 * tech_fit_multiplier
       # Return 0-100 integer, clamped
   ```
3. **Replace Fit Score gate in `compute_acv_potential` (dict path) and `compute_acv_on_product` (dataclass path):**
   ```python
   # OLD:
   fit_score = fs.total_override or fs.total or 0
   if fit_score > 0:
       fit_factor = fit_score / 100
       acv_low_dollars *= fit_factor
       acv_high_dollars *= fit_factor
   
   # NEW:
   acv_gate_score = compose_acv_gate_score(product, company_analysis)
   if acv_gate_score > 0:
       acv_factor = acv_gate_score / 100
       acv_low_dollars *= acv_factor
       acv_high_dollars *= acv_factor
   # Also persist acv.acv_gate_score = acv_gate_score for transparency.
   ```
4. **Rough ACV gate at discovery time.**  For products without fact drawers, compute rough dimension values from discovery signals.  Same spirit as `intelligence._compute_rough_iv_score` (which composes a rough IV from category / api_surface / cert).  You'll need rough versions for each dimension the ACV gate needs:
   - Rough IV dimensions: `rough_market_demand`, `rough_product_complexity`, `rough_mastery_stakes`, `rough_lab_versatility` (zero-weight, skip).
   - Rough CF dimensions: `rough_training_commitment`, `rough_delivery_capacity`, `rough_build_capacity` (zero-weight, skip), `rough_organizational_dna` (zero-weight, skip).
   - CF dimensions come from COMPANY-level signals (`company_signals.atp_program`, `company_signals.training_programs`, etc.) — same signals the existing rough-CF composition uses.
5. **Wire the rough ACV gate into `compute_discovery_company_acv`** so per-product discovery-time ACV also gets the gate applied.  This is what will make the discovery-time Motion-1-only number MORE useful — gate reduces the number where PL / IV / CF rough values signal weak fit.
6. **Update `SCORING_MATH_VERSION`** again after Build 2 lands.
7. **Validate against anchors** — Microsoft / Trellix / Skillsoft / Pluralsight / ASU.  Should tighten numbers slightly (gate reduces) — known-customer floor will still protect customers.
8. **Docs — update Platform-Foundation ACV section** with the ACV gate description (separate from the allocation architecture).  The gate is its own bullet: "ACV scales linearly with ACV gate score; ACV gate is composed from ACV-specific dimension weights that differ from Fit Score weights."
9. **Commit separately from Build 1 docs rewrite** — two commits for two conceptual changes.

**Files to touch for Build 2:**
- `backend/scoring_config.py` — new constants
- `backend/acv_calculator.py` — `compose_acv_gate_score` function, call sites in `compute_acv_potential` + `compute_acv_on_product` + `compute_discovery_company_acv`
- `backend/intelligence.py` — may need rough CF signal composition if not already present
- `docs/Platform-Foundation.md` — ACV gate section (after the Build 1 rewrite lands)
- `docs/decision-log.md` — DECIDED entry for Build 2

**Estimated time:** 60-90 min if the existing dimension-scoring signatures are clean; more if there's refactoring needed.

### Remaining Build 1 defect — Non-customer numbers feel low

After tonight's full retrofit, some non-customer prospects show smaller-than-intuitive numbers:
  - Workday $66K (major HR SaaS, real opportunity is bigger)
  - Anaplan $115K (enterprise planning, real is bigger)
  - Adobe $941K (multi-product creative company)

**Reason:** discovery-time ACV is Motion-1-only (Customer Training).  Motions 2-5 (Partner, Employee, Cert, Events) only activate when products are Deep-Dived.  A large software company's Motion-1-only number systematically undersells them.

**Potential fix (backlog):** add discovery-time rough estimates for Motions 2-5 from `company_signals` (partner count from atp_program, events from events signal, etc.).  More math, more accurate discovery-time numbers.  Not urgent — Deep Dive sharpens these — but worth backlogging as a V2 enhancement.

### Tonight's cautionary tale (lesson for next Claude)

The known-customer retrofit overwrote 47 cached discoveries before we caught the LLPA ILT inflation.  Files in `backend/data/company_intel/` are gitignored — not git-revertable.  Surgical recovery was done (13 bad ones zeroed), but any retrofit that writes to that directory is a live-data operation, not a code change.

**Rule for next session:** before running any retrofit at scale, dry-run and spot-check every org type against its anchor.  If ANY category looks off, fix the formula first, retrofit later.  The retrofit script has `--dry-run` and `--only` flags for exactly this.

### Read these first, in this order

1. **`docs/decision-log.md`** — the 2026-04-17 DECIDED entries at the top.  Nine decisions captured in full.  No interpretation required.
2. **`docs/Platform-Foundation.md` → ACV Potential Model section** — the rewritten authoritative spec with the full architecture (company total → allocate to products → per-product math × ACV-specific gate).  Read end to end.
3. **`docs/collaboration-with-frank.md`** — the standard startup pass, not skipped.

### What's been shipped already this session (do NOT redo)

| Commit | What |
|---|---|
| `1b23f94` | Capability wiring (Layer-2 `skillable_knowledge.py` + prompt-build-time rendering + scoped Pillar 1 context).  Unified rebalancing machinery across scored + unscored paths — `get_audience_tiers_for_archetype`, `get_scale_aware_adoption_ceiling`, `get_hours_for_archetype_motion`. |

These landed clean, tests pass, push confirmed.  **Do not touch these.  The remaining work builds on top of them.**

### What's in-memory and NOT yet committed

During the design conversation I made in-memory edits to `backend/acv_calculator.py` (added `compute_discovery_company_acv`), `backend/intelligence.py` (swapped the `estimate_holistic_acv` call), and created `scripts/retrofit_discovery_acv.py`.  These were design-exploration only and were built BEFORE the architecture was fully agreed.  **Revert these in-memory edits at session start** — they don't match the final agreed architecture and need to be rewritten cleanly from the spec.  `git diff` + `git checkout` to reset `backend/acv_calculator.py`, `backend/intelligence.py`, and delete `scripts/retrofit_discovery_acv.py`.

### What to build, in order

Two commits, in sequence.  Full spec in `docs/Platform-Foundation.md` → ACV Potential Model.  Decisions summarized here for quick reference.

#### BUILD 1 — Unified audience allocation + field consolidation + legacy cleanup + retrofit (one coherent commit)

**Goal:** replace the legacy Claude holistic shortcut with deterministic Python that computes company-level total trainable audience, allocates it across products, and runs per-product motion math.

**Scope:**

1. **Field consolidation.** Retire `annual_enrollments_estimate`.  `estimated_user_base` becomes the universal field for every org type, semantic = "humans who'd take training for this product."  Update researcher prompts (discovery + per-product fact extractors) to populate `estimated_user_base` with the right value per org type:
   - Software company → global user count (as today)
   - Wrapper org (Academic / ILT / ELP / GSI / VAR / Distributor / LMS / Industry Authority) → enrollments / students / class attendees / practitioners (the actual human count who'd take THIS product's training)
2. **Company total audience estimator** in `backend/acv_calculator.py`.  New function: `compute_company_total_audience(discovery: dict) -> int`.  Org-type-aware formulas:
   - **Hyperscaler / software_company:** `max(per-product capped audiences) + 0.15 × second-largest`.  Shared admin audience across products.
   - **enterprise_learning_platform / lms_company:** `sum(per-product audiences)`.  Catalogs are mostly distinct.
   - **academic_institution:** `sum(per-program audiences)`.  Programs mostly different students.
   - **ilt_training_organization:** `sum(per-class audiences)`.  Classes mostly different attendees.
   - **industry_authority:** `sum(per-cert audiences)`.  Different certs, different candidates.
   - **systems_integrator / professional_services:** `max(per-practice) + 0.30 × sum(others)`.  Consultants often cross-trained.
   - **var / technology_distributor:** `max(per-product) + 0.30 × sum(others)`.  Some cross-training.
   - **content_development:** partnership-only, skip.

   Per-product capped audiences use the existing `get_audience_tiers_for_archetype` — the archetype-aware caps that were validated on 2026-04-16.
3. **Allocation logic** in `backend/acv_calculator.py`.  New function: `allocate_audience_to_products(company_total, products) -> dict[str, int]`.  For each product:
   - `weight = raw_audience × archetype_multiplier`
   - `archetype_multiplier = IV_CEILINGS_BY_ARCHETYPE[archetype] / 100` (enterprise_admin = 1.0, creative_professional = 0.65, consumer_app = 0.25, etc.)
   - `product_share = company_total × (weight / sum_of_weights)`
4. **Per-product Motion 1 ACV uses `product_share` as audience.**  Motions 2-5 use existing sources (partner count, employee subset, cert sitters, events).  No change to the math — just the audience input to Motion 1 changes.
5. **Sum across products = company ACV.**  Bounded by construction.  Adding or removing products re-divides the same pie.
6. **Discovery-time company ACV function** in `backend/acv_calculator.py`.  New function: `compute_discovery_company_acv(discovery: dict) -> dict`.  Runs allocation + per-product math over discovery data.  Returns a dict matching the historical `_holistic_acv` shape (field name stays; content becomes the framework output).
7. **Wire into `intelligence.discover()`.**  Replace the `estimate_holistic_acv(...)` Claude call with `compute_discovery_company_acv(discovery)`.
8. **Legacy cleanup — exhaustive sweep.**  Delete:
   - `researcher.estimate_holistic_acv`
   - `researcher._HOLISTIC_ACV_PROMPT`
   - `researcher._format_anonymized_calibration_block`
   - `researcher._build_holistic_acv_context`
   - `scoring_config.HOLISTIC_ACV_COMPANY_HARD_CAP`, `HOLISTIC_ACV_MAX_RANGE_RATIO`, `HOLISTIC_ACV_PER_USER_CEILING`
   - Any helper only these referenced (`_scrub_customer_data`, `_build_partnership_acv_result`, etc. — audit before deleting)
   - Grep for `_raw_claude` — retire wherever the holistic call was the source.
   - `docs/unified-acv-model.md` — fold remaining useful content into Platform-Foundation, then delete the file.  One source of truth for the architecture.
   - Doc references: grep every doc for `holistic_acv`, `estimate_holistic_acv`, `_HOLISTIC_ACV_PROMPT`, `calibration_block`, `hard_cap`, etc.  Update or remove.
9. **Retrofit script** `scripts/retrofit_discovery_acv.py`.  Pure Python.  Walks every `discovery_*.json` under `backend/data/company_intel/`.  For each:
   - Migrate `annual_enrollments_estimate` → `estimated_user_base` for wrapper-org products (copy, don't delete — until validation passes).
   - Recompute `_holistic_acv` via `compute_discovery_company_acv`.
   - Save.
   - Flag any company with 0 contributing products (thin data — needs re-research; do NOT zero out their `_holistic_acv` in that case, leave legacy).
10. **Bump `SCORING_MATH_VERSION`** to `2026-04-17.audience-allocation-unified`.  Triggers pure-Python rescore on next page load for all cached analyses.
11. **Modal help text** in `scoring_config.py` — update the ACV modal content to describe the new architecture.  No separate commit; include in this one.
12. **Validation against anchors:**
    - Microsoft ~$42M
    - Trellix $750K current / $3M potential
    - Skillsoft ~$5M (known customer, is the floor)
    - Pluralsight — fair for a company larger than Skillsoft ($5-10M range)
    - ASU $2-4M
    - Spot-check 3 more: Workday, CompTIA, NVIDIA
13. **Docs aligned:**
    - Rewrite `docs/Platform-Foundation.md` → ACV Potential Model section with the unified architecture.  (Done in the spec-writing commit.)
    - DECIDED entry in `decision-log.md`.  (Done in the spec-writing commit.)
14. **Commit message** captures all of the above with rationale + anchor numbers produced.

**Build 1 produces:** one green commit with all the audience-allocation work + field consolidation + legacy cleanup + retrofit + docs + modal + validation.  Pushed.

#### BUILD 2 — ACV-specific dimension weights (separate commit right after Build 1)

**Goal:** the ACV gate (the multiplier applied to per-product raw ACV) currently uses the standard Fit Score (50% PL + 20% IV + 30% CF with standard dimension weights).  Replace with ACV-specific dimension weights.

**Scope:**

1. **New scoring_config constants:**
   ```
   ACV_GATE_PILLAR_WEIGHTS = {"product_labability": 50, "instructional_value": 20, "customer_fit": 30}  # same as Fit Score at pillar level
   ACV_GATE_CF_DIMENSION_WEIGHTS = {"training_commitment": 40, "delivery_capacity": 60, "build_capacity": 0, "organizational_dna": 0}
   ACV_GATE_IV_DIMENSION_WEIGHTS = {"market_demand": 40, "product_complexity": 25, "mastery_stakes": 25, "lab_versatility": 0}
   # PL unchanged (uses existing dimension weights)
   ```
   (Final MD weight 40 vs 50 — start at 40, tune if needed.)
2. **New composer function** `backend/acv_calculator.py::compose_acv_gate_score(product, company_analysis) -> int`.  Composes an ACV-specific 0-100 score from the three pillars using the weights above.  Returns the score; per-product ACV math multiplies by `acv_gate_score / 100`.
3. **Gate always applies.**  Uses real scores where we have them (Deep-Dived products), rough heuristic values where we don't (pre-Deep-Dive or partially-scored companies).  Quality tracks data quality.  Consistent logic throughout.
4. **Rough ACV gate at discovery.**  For products without fact drawers, compute rough dimension values from discovery signals (same spirit as `_compute_rough_iv_score` in intelligence.py).  One rough helper per dimension that needs it.
5. **Replace Fit Score gate with ACV gate** in `compute_acv_potential` and `compute_acv_on_product`.
6. **Retrofit** — same SCORING_MATH_VERSION bump triggers rescore.  If needed, add a new retrofit to propagate the gate change to cached analyses.
7. **Validate again** against the same 5+ anchors.  Numbers should tighten or stay the same — the ACV-specific gate weights what we think MATTERS for ACV (delivery + market demand) rather than the standard Fit Score.
8. **Commit + push.**

**Build 2 produces:** one additional commit for the gate-weight change, cleanly validated.

#### Definition of done (both commits together)

- All 5 anchors land in reasonable range of target
- Full retrofit runs clean across 600 discoveries (no exceptions)
- Prospector + Inspector both render correctly
- Platform-Foundation ACV section is best current thinking
- decision-log entries captured
- unified-acv-model.md retired
- Both commits pushed to main

---

## §2 — What was in-flight this session that didn't ship

| Item | State | Why parked |
|---|---|---|
| Holistic ACV retirement (the Build 1 above) | Design agreed, spec written, NOT built | End-of-session; needs fresh head |
| Accenture Cloud Practice $0 motion audiences | Parked | Deeper trace needed after Build 1 retrofits; the allocation fix may resolve this |
| Run-in-Background link + Toast | Design discussed | Separate UX change; after Build 1/2 ship |
| Pluralsight $18-30M holistic pinning | Rolls into Build 1 | New framework replaces the Claude pinning |

---

## §3 — Session context that shouldn't get lost

- **Frank's "best current thinking" principle is the highest-order rule.**  We synthesize and rewrite documentation, we don't append.  `unified-acv-model.md` is retired because it fragments the central doc (Platform-Foundation).  If any ACV content lives elsewhere after Build 1, something's wrong.
- **Frank's "one standard" rule.**  The unified architecture means all ACV views (Prospector list, Inspector hero, CSV export, modals) read from the same framework output.  No parallel paths, no special cases.
- **Layer discipline.**  Capability data is Layer 2 (`skillable_knowledge.py`), scoring is Layer 3 (pillar scorers, rubric grader, ACV calculator).  Don't mix.
- **Field consolidation was the outcome of a direct challenge from Frank.**  My first instinct was a helper function that reads both fields — Frank called that a hack.  The right answer is one field with correct semantic for each org type.  Keep that intuition: when something sounds like a workaround, ask if there's a single clean answer.
- **The ACV gate is NOT the Fit Score.**  Separate architectural concept with different dimension weights (Build 2).  Bundled because "Fit Score gates ACV" was the pattern Platform-Foundation claimed, which turned out to be wrong per Frank's memory.  The ACV gate uses ACV-specific weights (delivery-capacity-heavy, zero build-capacity, market-demand-heavy).  Build 2 makes this real.

---

## §4 — Completed backlog items (prior session reference)

Archived earlier items from `next-session-todo.md` pre-2026-04-17 have been folded into `docs/roadmap.md` as appropriate.  The 2026-04-15 worktree cleanup and 2026-04-14 file cleanup references are no longer actionable.
