# Step 1 Synthesis
## Cross-cutting analysis, priorities, patterns, conflicts, and open questions

---

## 1. The Big Picture

Five audits produced findings across the research engine, display logic, Skillable reference knowledge, code quality, and competitive intelligence. The core scoring infrastructure is sound. The most impactful work is prompt additions — four confirmed decisions that are fully defined and have zero ambiguity about what to add. Behind those, several code quality improvements reduce fragility without changing scoring behavior, and a storage architecture decision enables the full two-stage flow.

---

## 2. Key Structural Changes Needed

### 2.1 Prompt — Four Confirmed Additions to product_scoring.txt (All High Priority)
These are fully defined decisions with no outstanding questions:

**a. Collaborative Lab Detection (STEP 7)**
Add both patterns (Parallel/Adversarial cyber range; Sequential/Assembly Line) with detection signals, ILT-only constraint, and additive framing. Source: `reference_skillable_delivery_patterns.md` and `project_intelligence_improvements.md`.

**b. Break/Fix Scenario Detection (STEP 7)**
Add as named lab type with detection signals (troubleshooting guides, high consequence-of-error, incident response training) and additive framing alongside guided labs. Source: `project_intelligence_improvements.md`.

**c. Simulated Attack Scenario Detection (STEP 7)**
Add both modes (single-person self-paced; collaborative ILT). Full detection signals and two-track program recommendation defined. Source: `project_intelligence_improvements.md`.

**d. SaaS Phase 2 Three-Path Evaluation (STEP 1)**
Add evaluation of Cloud Slice → Custom API (four lifecycle steps) → Credential Pool → Simulation. Include MFA blocker and DELETE endpoint requirement for Custom API. Source: `project_intelligence_improvements.md`.

These four additions can be made to `product_scoring.txt` without changing any Python code and will immediately improve output quality for all future analyses.

### 2.2 Research Engine — Five Targeted Improvements to researcher.py

**a. Source type classification + differentiated fetch depth**
Classify fetched URLs as marketing/documentation/api_reference. Apply different `max_chars` per type. Highest value-per-effort ratio in the research engine.

**b. OpenAPI/Swagger spec queries per product**
Add two targeted queries per product in `research_products()`. Low effort, directly improves Gate 1 API evidence.

**c. Lab platform competitor query expansion**
Add GoDeploy, ReadyTech, Appsembler, Vocareum, LODS/Learn on Demand Systems to the `lab_platform` query in `discover_products()`. Rename `compete_` queries to `labplatform_` in `research_products()` for clarity. Low effort.

**d. SaaS-specific research queries**
Conditional queries for sandbox API, DELETE endpoint, credential pool viability, and MFA model — fires only when `deployment_model == "saas_only"` in the discovery data. Requires discovery data to flow into `research_products()`.

**e. Collaborative lab / break/fix / simulated attack detection queries**
Three new query types per product. Low effort additions to the existing query set.

### 2.3 Code — Three Single-Source-of-Truth Fixes (models.py)

**a. Move CEILING_FLAGS to models.py**
Currently duplicated in `core.py` and `intelligence.py`. One change, two benefits.

**b. Add canonical ORCHESTRATION_METHODS constant**
Nine base methods with valid tier variants. Enables validation in `_parse_response_to_models()` and documents the canonical set.

**c. Add `_verdict(score) -> str` function**
Removes verdict logic from the dossier template into the models layer where it belongs.

### 2.4 Storage — Company Record Architecture (intelligence.py)
The two-stage Inspector flow requires a Company Record as a first-class entity. Currently, discovery and analysis are separate JSON records linked by ID. The Company Record would aggregate both and support incremental enrichment (Stage 1 creates it; Stage 2 appends to it). This is the largest structural change and should be designed carefully before implementation — it affects all three tools.

---

## 3. Patterns and Standards to Apply Everywhere

### 3.1 The Canonical Naming Contract
Every orchestration method string must start with one of the nine canonical prefixes. The `startswith()` check in `compute_labability_total()` is the scoring gate. If Claude returns "HyperV" instead of "Hyper-V", the score drops silently to 0.15x. Add validation logging at parse time. This pattern should be documented and enforced as a contract.

### 3.2 The Single-Source-of-Truth Principle (Already Established — Enforce It)
The codebase has multiple examples of logic defined twice:
- CEILING_FLAGS in core.py AND intelligence.py
- `_labable_tier()` in intelligence.py AND similar logic in `_attach_scores()` in core.py
- Score computation in `compute_product_score()` AND `ProductLababilityScore.total`

The principle is already stated in the codebase (e.g., `core.py`: "Single source of truth for all score computation"). Apply it consistently. Every constant, flag set, and computation function should have exactly one definition.

### 3.3 The Vocabulary Lock
`reference_scoring_model.md` defines locked vocabulary. The locked terms are correctly used in the prompt and models. The legacy compat keys (`technical_orchestrability`, `workflow_complexity`, `training_ecosystem`, `market_fit`) remain in the code for backward compatibility but should be deprecated with a clear EOL timeline.

### 3.4 Penalties Are Prompt-Dependent — Document This Explicitly
All six penalty deductions (GPU -5, MFA -3, etc.) are applied by Claude, not by Python code. This means penalty correctness cannot be verified in automated tests. Until code-side penalty validation is implemented, document this dependency explicitly in `scorer.py` with a comment explaining the trust model and the risk.

### 3.5 Display Rendering Contract
Evidence bullets must start with `**Label:**` and recommendation bullets must use the `| Risk` / `| Blocker` suffix convention. These conventions are defined in the prompt but not enforced in templates. Templates apply `| safe` and convert `**text**` to `<strong>`, but they don't distinguish `| Risk` (orange) from `| Blocker` (red) in recommendation bullets. Adding CSS class detection for these suffixes in the Jinja2 template is a small change with meaningful display fidelity improvement.

---

## 4. Conflicts and Gaps Found Across the Five Sub-Tasks

### Conflict 1: `candidate_paths` (discovery) vs. `orchestration_method` (analysis)
The caseboard template renders `p.candidate_paths` from discovery data. The `Product` dataclass in `models.py` has `orchestration_method` but not `candidate_paths`. These serve different purposes (discovery suggests candidate paths; analysis confirms a single method) but the relationship is undocumented. The transition from multiple `candidate_paths` to a single confirmed `orchestration_method` should be explicit in both the data model and the caseboard display spec.

**Resolution needed:** Define whether `candidate_paths` stays in discovery (ephemeral, not persisted on Product) or becomes a field on the Product model for display purposes.

### Conflict 2: `AppSimpler` (task description) vs. `Appsembler` (code and memory)
The original task description references "AppSimpler" as a known competitor. All memory files and code use "Appsembler." These appear to be the same company — "Appsembler" is the correct name. The `research_products()` query already uses "Appsembler." No code change needed, but verify this is not a separate entity.

### Conflict 3: AI signal scoring asymmetry (+4 Dim 2 vs. +5 Dim 4)
Dim 2.1 awards +4 for Learning AI-embedded features; Dim 4 awards +5 for the same signal. This is not inherently wrong — instructional need and market demand are different questions. But it is not explicitly documented as intentional in the prompt or memory. If both dimensions score the same product signal, the user will see different numbers in different places. Add a comment in the prompt explaining the rationale.

### Conflict 4: `partnership_signals.existing_lab_partner` nested path in caseboard
The caseboard template accesses `discovery.partnership_signals.existing_lab_partner` via a nested path. The discovery dict's `partnership_signals` key is populated by the Claude discovery response, not by `researcher.py`. If the Claude prompt doesn't instruct it to output a `partnership_signals` object with `existing_lab_partner`, this path silently returns nothing. The discovery prompt should be audited to confirm it outputs this structure.

### Conflict 5: Dim 2.1 phase names are correct in prompt but not validated in code
The five workflow phase names (Design & Architecture, Configuration & Tuning, Deployment & Provisioning, Support Scenarios, Troubleshooting) are correctly defined in the prompt. Claude's response for Dim 2.1 includes a score and evidence bullets but the code does not parse which phases were "hit." The consumption potential and program sizing logic in STEP 8 could benefit from knowing which phases scored — currently this relationship is implicit.

### Gap 1: SaaS deployment model not available during research phase
`research_products()` does not receive `deployment_model` from the discovery output. SaaS-specific queries (see 2.2d above) cannot fire without this. Fix requires passing discovery-phase product metadata into the research function signature.

### Gap 2: No discovery audit trail
When `_detect_and_patch_discrepancies()` patches `likely_labable` in the discovery record, the original discovery-tier value is lost. For analysis purposes, knowing how much the discovery tier changed would be useful for prompt calibration. Consider logging or storing both the original and patched values.

### Gap 3: LODS/Learn on Demand as existing customer signal
The competitor detection query should handle "LODS" and "Learn on Demand Systems" differently from competitor platforms — these are Skillable's own former names and indicate an existing or former customer relationship (expansion opportunity), not a competitive displacement scenario. This distinction is missing from both the research query and the scoring prompt.

---

## 5. Prioritized Action List

### Tier 1 — Do First (Highest Impact, Low-to-Medium Effort)
All prompt additions; no code risk; immediate quality improvement:

1. Add Collaborative Lab detection to `product_scoring.txt` STEP 7
2. Add Break/Fix detection to `product_scoring.txt` STEP 7
3. Add Simulated Attack detection to `product_scoring.txt` STEP 7
4. Add SaaS Phase 2 three-path evaluation to `product_scoring.txt` STEP 1
5. Expand lab platform detection query in `researcher.py` (add GoDeploy, ReadyTech, Vocareum, LODS)

### Tier 2 — Do Second (Code Quality, No Logic Change)
Reduce fragility; establish single sources of truth:

6. Move CEILING_FLAGS to `models.py` as module-level constant
7. Add ORCHESTRATION_METHODS canonical constant to `models.py`
8. Add `_verdict(score)` function to `models.py`
9. Rename `_datacenter_prefixes` in `compute_labability_total()`
10. Add validation log when `orchestration_method` doesn't match expected prefix
11. Add Risk vs. Blocker CSS class distinction in dossier recommendation rendering

### Tier 3 — Do Third (Research Engine Improvements)
Improves evidence quality for all future analyses:

12. Source type classification + differentiated fetch depth in `researcher.py`
13. OpenAPI/Swagger spec queries per product
14. Collaborative lab / break/fix / simulated attack detection queries
15. Documentation breadth cataloging in `researcher.py` + `product_scoring.txt`

### Tier 4 — Do Fourth (Architecture Changes)
Requires careful design before implementation:

16. Pass `deployment_model` from discovery into `research_products()` (enables SaaS-specific queries)
17. SaaS-specific research queries conditional on deployment model
18. Company Record as first-class storage entity (enables two-stage flow)
19. `competitive_pairings` and `company_fit_score` fields in discovery dict

### Tier 5 — Do Later (Reliability and Monitoring)
Polish and auditability:

20. Code-side penalty enforcement (Option A: structured penalty field from Claude)
21. Discovery audit trail for discrepancy detection (store original + patched values)
22. Deprecation comments on legacy key aliases with EOL timeline
23. Document `_legacy_path()` as deprecated
24. Resolve `candidate_paths` vs. `orchestration_method` field ownership decision

---

## 6. Open Questions for Frank

### Q1: AppSimpler vs. Appsembler
The task description lists "AppSimpler" as a known competitor. All memory files and code use "Appsembler." Are these the same company? If so, which spelling is canonical? If different, what is AppSimpler and where did the name come from?

### Q2: AI signal asymmetry in Dim 2 vs. Dim 4
Dim 2.1 awards +4 for Learning AI-embedded features; Dim 4 awards +5 for the same signal. Is this asymmetry intentional? If yes, what's the rationale? If not, should both be +5 (match) or +4 (more conservative)?

### Q3: `candidate_paths` field ownership
Caseboard renders `p.candidate_paths` from discovery data. This field is not on the `Product` dataclass. Should it be? Or is it intentionally ephemeral (discovery-only, replaced by `orchestration_method` after scoring)? This affects both the data model and the caseboard display spec.

### Q4: `partnership_signals.existing_lab_partner` discovery structure
The caseboard expects a nested `discovery.partnership_signals.existing_lab_partner` structure. Is the discovery prompt currently producing this? Or is this an intended field that isn't yet being populated? If it's not in the current discovery prompt output, the "Lab Competitors" column in Company Indicators always shows "None detected."

### Q5: LODS / Learn on Demand Systems as existing customer signal
When research surfaces "LODS labs" or "Learn on Demand" for a prospect, this signals an existing or former Skillable customer (expansion opportunity), not a competitive displacement. Should Inspector output distinguish "existing Skillable customer — expand" from "competitor platform — displace"? If yes, this needs both a query and a display element in the caseboard/dossier.

### Q6: Company Record architecture — migration strategy
The proposed Company Record as a first-class storage entity would replace the current separate discovery + analysis JSON files. What's the right migration strategy? Options: (a) write new records in the Company Record format while reading both old and new formats; (b) lazy migration on read (upgrade on first access); (c) explicit migration script run once. Which approach fits the deployment model (Render, single instance)?

### Q7: Code-side penalty enforcement — Option A vs. B
For enforcing penalty correctness, the code review proposes Option A (Claude returns both raw score + applied penalties, Python computes final). This requires a prompt change that would invalidate all cached analyses until they expire. Is this change worth the cache invalidation cost? Or should we start with Option B (post-parse validation warning only) and move to Option A later?

### Q8: SaaS Phase 2 research query timing
SaaS-specific research queries require `deployment_model` from discovery to be available when `research_products()` fires. Currently, the two phases are sequential but the product metadata from discovery is not systematically passed to the research phase. Is the right fix: (a) pass product list including `deployment_model` explicitly to `research_products()`, or (b) have `research_products()` look up the discovery record directly from storage? Option (a) seems cleaner but requires an API change.

### Q9: Documentation breadth cataloging — pre-processor approach
For the documentation breadth cataloging improvement, the research plan proposes a lightweight pre-processor that extracts nav/sidebar structure from doc sites before passing to Claude. This pre-processor needs heuristics for common doc frameworks (ReadTheDocs, Docusaurus, GitBook, MkDocs, custom). How much investment should go into this pre-processor vs. just increasing the fetch depth and letting Claude extract structure from the raw text?

### Q10: Competitive pairing as a research query or a Claude inference task?
The Stage 1 competitive pairing decision (pair each product to its market competitors) could be implemented as: (a) a dedicated search query per product (`{product} competitors alternatives versus comparison`) feeding Claude, or (b) an inference task in the discovery Claude call (Claude infers competitors from its training knowledge without a research query). Option (a) is more reliable but adds queries. Option (b) is simpler but Claude's knowledge of specific competitive landscapes may be stale or wrong. Which approach is preferred?
