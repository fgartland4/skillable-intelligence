# Next Session — Todo List

**Last updated:** 2026-04-17 (ACV architecture alignment session)

---

## §1 — START HERE NEXT SESSION

**Build the unified ACV architecture.** Full spec written.  Decisions made.  Every detail captured.  A new Claude picks this up cold and executes.

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
