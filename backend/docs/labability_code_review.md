# Product Labability Code Review
## Step 1.6 — Audit of scorer.py, core.py, models.py, product_scoring.txt, intelligence.py against all session decisions

---

## 1. Summary Assessment

Overall, the core scoring infrastructure is well-implemented. The 40/30/20/10 model, multiplier logic, ceiling flags, and SaaS isolation gate (Phase 1) are correctly coded. The major gaps are in the scoring prompt's pending items (collaborative labs, break/fix, simulated attack, doc breadth cataloging, SaaS Phase 2) and in code-side penalty enforcement. Several inconsistencies exist between the prompt vocabulary and the code.

---

## 2. What Is Correctly Implemented

### 2.1 40/30/20/10 Scoring Model (models.py)
`compute_labability_total()` in `models.py` correctly implements the 40/30/20/10 weighting:
- `tech` (product_labability) on a 0-40 scale
- `other` = sum of instructional_value (0-30) + organizational_readiness (0-20) + market_readiness (0-10) = 0-60
- Returns `min(100, tech + round(other * multiplier))`

The formula is correct. The `ProductLababilityScore.total` property correctly delegates to `compute_labability_total()`. `compute_product_score()` correctly aggregates scores from the JSON storage dict.

**Status: Correct.**

### 2.2 Multiplier Logic (models.py)
`compute_labability_total()` implements multiplier logic as follows:
```python
_datacenter_prefixes = ("Hyper-V", "ESX", "Container", "Azure VM", "AWS VM")
if tech >= 32:
    multiplier = 1.0
elif tech >= 24 and any(orchestration_method.startswith(m) for m in _datacenter_prefixes):
    multiplier = 1.0
elif tech >= 19:
    multiplier = 0.75
elif tech >= 10:
    multiplier = 0.40
else:
    multiplier = 0.15
```

This correctly implements: Hyper-V/ESX/Container ≥24 → 1.0x; any method ≥32 → 1.0x; 19-31 non-datacenter → 0.75x; 10-18 → 0.40x; <10 → 0.15x.

**Minor gap:** "Azure VM" and "AWS VM" are datacenter prefixes in this logic, meaning Azure VM ≥24 also gets 1.0x. This is correct per the decision (Azure VM is a cloud VM but is treated like a datacenter path for multiplier purposes). However, the `_datacenter_prefixes` tuple name is misleading — Azure VM and AWS VM are not Skillable datacenters. Rename for clarity.

**Also note:** `orchestration_method.startswith(m)` works correctly because the orchestration method strings use the method name as a prefix (e.g., "Hyper-V: Standard" starts with "Hyper-V"). This is a dependency on the naming convention — must be maintained.

**Status: Correct, with minor naming clarity issue.**

### 2.3 Ceiling Flags (core.py, intelligence.py)
`_attach_scores()` in `core.py` and `_labable_tier()` in `intelligence.py` both implement CEILING_FLAGS:
```python
CEILING_FLAGS = {"bare_metal_required", "no_api_automation", "saas_only", "multi_tenant_only"}
```

Both check `flags & CEILING_FLAGS` and cap at `less_likely` (score ≥ 20) or `not_likely` (score < 20). Both are consistent. The logic is duplicated across two functions — this is a maintenance risk.

**Status: Correct, but duplicated. Single source of truth needed.**

### 2.4 Orchestration Method Field Migration (scorer.py)
`_parse_response_to_models()` in `scorer.py` correctly:
- Reads `orchestration_method` from new analyses
- Falls back to `_legacy_path(p)` for cached analyses that have the old `skillable_path`/`path_tier` fields
- Sets `_orchestration_method` on both the `Product` and `ProductLababilityScore` objects

`_legacy_path()` maps old path codes to orchestration methods for backward compatibility.

**Status: Correct for migration. Minor gap: `_legacy_path()` only maps 5 of the 9 methods (Hyper-V, Azure Cloud Slice, AWS Cloud Slice, Custom API, Simulation). ESX, Container, Azure VM, AWS VM have no legacy mapping. This is acceptable since they are new — old analyses won't have these — but should be documented.**

### 2.5 Dim 2.1 Workflow Phase Names (product_scoring.txt)
The five workflow phase names are correctly defined in STEP 4 Instructional Value section:
- Design & Architecture topics (+5)
- Configuration & Tuning topics (+5)
- Deployment & Provisioning topics (+5)
- Support Scenarios (+5)
- Troubleshooting topics (+5)

These match the session decisions exactly.

**Status: Correct in prompt. No code-side enforcement needed (prompt-only).**

### 2.6 Dim 4 Category Priors (product_scoring.txt)
STEP 4 Market Readiness correctly defines:
- High demand (+5): Cybersecurity, Cloud Infrastructure, Networking/SDN, Data Science & Engineering, Data & Analytics, DevOps
- Moderate demand (+2): Data Protection, Infrastructure/Virtualization, Application Development, ERP/CRM, Healthcare IT, FinTech, Collaboration, Content Management, Legal Tech, Industrial/OT
- Low/no demand (+0): Simple SaaS, Consumer
- AI signals (additive, separate): Creating AI +5, Learning AI-embedded features +5
- Other additive: Large/growing install base +2, Growing category +1, Limited competitor labs +1. Cap 10.

**Status: Correct.**

### 2.7 AI Signals in Dim 2 and Dim 4 (product_scoring.txt)
Both dimensions include AI signals:
- Dim 2.1 (Difficult to Master): Creating AI +5, Learning AI-embedded features +4
- Dim 4 (Market Readiness): Creating AI +5, Learning AI-embedded features +5

Note the asymmetry: Dim 2 awards +4 for embedded AI features, Dim 4 awards +5 for the same. This is intentional per the prompt structure (market demand ≠ instructional need), but should be confirmed.

**Status: Implemented. Confirm the +4 vs +5 asymmetry is intentional.**

### 2.8 SaaS Isolation Gate (intelligence.py, core.py, product_scoring.txt)
Phase 1 of the SaaS isolation gate is correctly implemented:
- Prompt: SaaS Isolation Pre-Screen in Step 1; Azure Cloud Slice SaaS warning in Step 3
- Code: CEILING_FLAGS in both `_labable_tier()` and `_attach_scores()`
- Template: `flag_label_filter` in `app.py` has display labels for `saas_only`, `multi_tenant_only`, `no_provisioning_api`

**Status: Phase 1 correct. Phase 2 (three-path evaluation) pending — not yet in prompt or code.**

### 2.9 Negative/Penalty Scoring (product_scoring.txt)
The penalty deductions are correctly defined in the prompt (Step 4, after tier scoring):
- GPU required: -5
- MFA on admin accounts: -3
- Provisioning time >30 min: -3
- GUI-only setup: -2
- No NFR/dev license: -2
- Socket-based licensing (ESX, additional): -2

Penalties stack freely with no floor. Triggered penalties are added to `poor_match_flags`.

**Status: Correct in prompt. Gap: penalties are prompt-dependent only — no code-side enforcement (see Section 3.1).**

---

## 3. What Is Missing or Inconsistent

### 3.1 Code-Side Penalty Enforcement (models.py, scorer.py)
**Gap:** `compute_product_score()` and `compute_labability_total()` trust the `product_labability.score` that Claude returns. Penalties are expected to already be applied by Claude. If Claude returns a pre-penalty score and separately lists `poor_match_flags`, the code cannot verify whether the penalties were correctly applied.

**Required change:** Two options:
- Option A: Have Claude return a `raw_product_labability_score` (pre-penalty) plus a list of applied penalties. Code computes the final score: `final = raw - sum(penalties)`. This makes penalty application auditable and reproducible.
- Option B: Add a post-parse validation pass in `_parse_response_to_models()`: check the `poor_match_flags` and verify the score is consistent with known penalty values. Log a warning if it appears Claude missed a penalty.

Option A is cleaner and is recommended.

**Priority: High — affects scoring accuracy for all products with applicable flags.**

### 3.2 CEILING_FLAGS Duplication (core.py vs. intelligence.py)
**Gap:** The CEILING_FLAGS set is defined independently in two places:
- `_attach_scores()` in `core.py`: inline set `{"bare_metal_required", "no_api_automation", "saas_only", "multi_tenant_only"}`
- `_labable_tier()` in `intelligence.py`: inline set named `CEILING_FLAGS`

Both must be kept in sync. A flag added to one but not the other creates a silent inconsistency.

**Required change:** Move CEILING_FLAGS to `models.py` as a module-level constant. Import it in both `core.py` and `intelligence.py`. Single source of truth.

**Priority: Medium — maintenance risk, not currently a bug.**

### 3.3 Vocabulary Inconsistency: Dimension Names (models.py vs. prompt vs. JSON)
**Gap:** The scoring model uses these names in different places:

| Where | Dim 1 name | Dim 2 name | Dim 3 name | Dim 4 name |
|---|---|---|---|---|
| `models.py` field name | `product_labability` | `instructional_value` | `organizational_readiness` | `market_readiness` |
| Prompt | "Product Labability" | "Instructional Value" | "Organizational Readiness" | "Market Readiness" |
| JSON output key | `product_labability` | `instructional_value` | `organizational_readiness` | `market_readiness` |
| Legacy compat keys | `technical_orchestrability` | `workflow_complexity` | `training_ecosystem` | `market_fit` |

The locked vocabulary in `reference_scoring_model.md` confirms the current names are correct. The legacy compat keys (`technical_orchestrability` etc.) are handled in `compute_product_score()` and `_parse_response_to_models()`.

**Status: Correct, but the legacy compat code creates two access paths that must both be maintained. Document them explicitly and add a deprecation comment.**

### 3.4 Missing: Collaborative Lab Detection (product_scoring.txt)
**Gap:** The prompt has no section for Collaborative Lab detection or recommendation. The `reference_skillable_delivery_patterns.md` fully defines both patterns (Parallel/Adversarial, Sequential/Assembly Line) with detection signals and recommendation framing.

**Required addition to product_scoring.txt (in STEP 7):**
- Add "Collaborative Lab" as an optional recommendation label under Delivery Path
- Define detection signals for Pattern A (cyber range) and Pattern B (assembly line)
- Add ILT-only constraint
- Specify additive framing (alongside standard VM labs, not instead)

**Priority: High — this is a confirmed decision, fully defined, zero ambiguity.**

### 3.5 Missing: Break/Fix Scenario Detection (product_scoring.txt)
**Gap:** The prompt has no instruction to detect or recommend break/fix scenarios.

**Required addition to product_scoring.txt (in STEP 7):**
- Add "Break/Fix Scenarios" as a named lab type option
- Detection signals: troubleshooting guides, advanced certification testing diagnostic skills, high consequence-of-error Gate 2 products, incident response training
- Additive framing: guided labs for initial skill-building + break/fix for advanced learners and cert prep

**Priority: High — confirmed decision.**

### 3.6 Missing: Simulated Attack Scenario Detection (product_scoring.txt)
**Gap:** No simulated attack scenario guidance in the prompt.

**Required addition to product_scoring.txt (in STEP 7):**
- Add "Simulated Attack" as a named delivery option for cybersecurity products
- Two modes: single-person (solo Blue Team, self-paced) and Collaborative Lab (live Red Team, ILT)
- Detection signals: SIEM, EDR, identity protection, threat detection, network security, incident response, threat hunting, penetration testing, SOC operations
- Program recommendation when signals present: self-paced (guided + break/fix + simulated attack) + ILT (cyber range with live Red/Blue Team)

**Priority: High — confirmed decision.**

### 3.7 Missing: SaaS Phase 2 Three-Path Evaluation (product_scoring.txt)
**Gap:** The prompt handles SaaS isolation (caps score, flags `saas_only`) but does not evaluate or recommend among the three paths: Cloud Slice → Custom API → Credential Pool → Simulation. It does not instruct Claude to research sandbox API availability, DELETE endpoint, or credential pool viability.

**Required prompt addition:** After the SaaS Isolation Pre-Screen, add a three-path evaluation block that instructs Claude to assess:
1. Cloud Slice viability (Marketplace listing, supported services, Entra SSO)
2. Custom API viability (four lifecycle steps: provision/configure/validate/DELETE; MFA blocker; provisioning latency)
3. Credential Pool viability (sandbox accounts, reset API, partner program)
4. Simulation as fallback (when none of the above is viable)

**Priority: High — Phase 2 of a partially implemented decision.**

### 3.8 Missing: Documentation Breadth as Gate 2 Input (product_scoring.txt)
**Gap:** Dim 2 (Instructional Value) scores workflow phases based on Claude's general judgment. The prompt does not instruct Claude to use documentation structure (modules, features per module, steps per feature, interoperability count) as explicit, structured evidence.

**Required prompt update:** In STEP 4 Instructional Value section, add instruction to:
1. Count modules from documentation nav (if available in research)
2. Assess feature depth within modules
3. Count distinct integration targets as separate lab scenarios
4. Map this directly to program scope in the evidence bullets

**Priority: Medium — improves evidence quality and program sizing.**

### 3.9 Missing: Delivery Path Rationale Enforcement for VMware → Hyper-V (product_scoring.txt)
**Gap:** The prompt instructs Hyper-V as default over ESX and gives cost rationale, but does not explicitly require this rationale to appear in the Delivery Path bullet. The step-7 instructions say "be decisive" and give good examples, but the Broadcom cost rationale could be stronger.

**Required addition:** In STEP 7 Delivery Path instructions, add explicit rule: "When recommending Hyper-V over ESX, always include the Broadcom pricing rationale in the bullet — this is a business case point, not a footnote."

**Priority: Low-Medium — already partially addressed in the prompt.**

### 3.10 Missing: Azure/AWS Consumption Cost Note (product_scoring.txt)
**Gap:** The consumption potential section notes that Cloud Slice rate is "$6/hr — platform rate only." The `vm_rate_estimate` field instructions do call out "this is Skillable's platform rate only — Azure and AWS service consumption costs are billed separately." However, the recommendation for Cloud Slice products should also surface this in the Program Fit or Blockers bullet.

**Required addition:** In STEP 7, when recommending Azure Cloud Slice or AWS Cloud Slice as delivery path, add a rule to note the cloud service cost separation in the recommendation.

**Priority: Low — already partially addressed in the prompt's consumption section.**

---

## 4. Specific Changes Needed, File by File

### models.py
1. **Add CEILING_FLAGS as a module-level constant** (set of strings). Remove from inline definitions in core.py and intelligence.py. Import in both.
2. **Add canonical ORCHESTRATION_METHODS dict** listing all 9 base methods and their valid tier variants, as a module-level constant. This documents the canonical set and enables validation in `_parse_response_to_models()`.
3. **Rename `_datacenter_prefixes` in `compute_labability_total()`** to `_full_multiplier_prefixes` or `_1x_at_24_prefixes` to accurately reflect that Azure VM and AWS VM are included (they're not Skillable datacenters).
4. **Add `_verdict(composite_score: int) -> str`** as a module-level function returning "Strong Fit" / "Pursue" / "Monitor" / "Pass" based on score thresholds. Currently this logic is in the dossier template.

### core.py
1. **Import CEILING_FLAGS from models.py** instead of defining inline.
2. **Consider adding `_labable_tier(p: dict) -> str`** to `core.py` as a shared helper, eliminating the duplicate in `intelligence.py`. Or keep it in `intelligence.py` and import in `core.py`. Either way, one definition.

### intelligence.py
1. **Import CEILING_FLAGS from models.py** instead of defining inline in `_labable_tier()`.
2. **Import `_labable_tier` or equivalent from `core.py`** rather than defining separately.
3. **Add `company_fit_score` and `competitive_pairings` fields to the discovery dict** returned by `discover()`. These are Stage 1 Company Report fields.

### scorer.py
1. **Document `_legacy_path()` as deprecated** with a comment noting which analysis versions may still use it and when it can be removed (when all cached analyses are refreshed or expired).
2. **If Option A for penalty enforcement is adopted**: update `_parse_response_to_models()` to read `raw_product_labability_score` from Claude's response and apply penalties from `poor_match_flags` to compute the final score.
3. **Alias comment**: add a comment on the legacy key aliases (`technical_orchestrability`, `workflow_complexity`, etc.) explaining they are for backward compatibility with analyses scored before the vocabulary change, and listing the expected EOL date (45-day cache TTL means they'll all expire naturally).

### product_scoring.txt
1. **Add Collaborative Lab detection and recommendation** to STEP 7 (Delivery Path options). High priority.
2. **Add Break/Fix scenario detection and recommendation** to STEP 7. High priority.
3. **Add Simulated Attack scenario detection and recommendation** to STEP 7. High priority.
4. **Add SaaS Phase 2 three-path evaluation block** in STEP 1 (after SaaS Isolation Pre-Screen). High priority.
5. **Add documentation breadth cataloging instruction** to STEP 4 Dim 2.1 section. Medium priority.
6. **Tighten Delivery Path WHY rule for Hyper-V over ESX** — require explicit Broadcom rationale in the bullet. Low-Medium priority.
7. **Add Cloud Slice cost separation note** to STEP 7 recommendation for Cloud Slice products. Low priority.
8. **Confirm or document the +4 vs +5 AI signal asymmetry** between Dim 2.1 and Dim 4. If intentional, add a brief rationale comment in the prompt.

---

## 5. Priority Order for Implementation

### Priority 1 — Prompt additions (no code risk, immediate quality improvement)
1. Collaborative Lab detection → product_scoring.txt STEP 7
2. Break/Fix detection → product_scoring.txt STEP 7
3. Simulated Attack detection → product_scoring.txt STEP 7
4. SaaS Phase 2 three-path evaluation → product_scoring.txt STEP 1
5. Documentation breadth cataloging → product_scoring.txt STEP 4

### Priority 2 — Code quality (refactors, no logic change)
6. Move CEILING_FLAGS to models.py (single source of truth)
7. Add ORCHESTRATION_METHODS canonical constant to models.py
8. Add `_verdict()` function to models.py
9. Rename `_datacenter_prefixes` to more accurate name
10. Add deprecation comment to `_legacy_path()`

### Priority 3 — Code logic (changes to scoring behavior)
11. Code-side penalty enforcement (Option A — structured penalty field from Claude)
12. Add `company_fit_score` and `competitive_pairings` to discovery dict (Stage 1 Company Report)

### Priority 4 — Cleanup
13. Document legacy key aliases with EOL timeline
14. Confirm AI signal asymmetry (+4 vs +5) and document

---

## 6. The One Thing Most Likely to Cause a Bug

The `orchestration_method.startswith(m)` check in `compute_labability_total()` silently gives multiplier 0.15x to any product whose orchestration_method string is empty, `"Unknown"`, or doesn't match any expected prefix. If Claude returns an orchestration method that is spelled slightly differently from the canonical prefix (e.g., "Hyper V" instead of "Hyper-V"), the multiplier falls to 0.15x and the score drops substantially. This is the most likely source of unexpectedly low scores that are hard to debug. Add a validation step or a warning log when `orchestration_method` doesn't match any expected prefix.
