# Skillable Intelligence Platform — Test Plan

This document defines the automated test strategy for the backend rebuild. Every test category traces to one or more Guiding Principles. Tests serve as both validation and living documentation — a developer reading the test files understands the rules the system must follow.

This document reflects best current thinking. As thinking evolves, this document evolves with it — fully synthesized, never appended.

---

## Test Infrastructure

| Aspect | Approach |
|---|---|
| **Language** | Python |
| **Framework** | pytest |
| **Location** | `backend/tests/` |
| **Organization** | One test file per category — file name matches category |
| **Naming** | Each test has a clear name and docstring explaining what it validates and why |
| **Running** | `pytest` from the backend directory — all tests pass or fail with clear messages |

---

## Category 1: Scoring Configuration Validation

**File:** `backend/tests/test_scoring_config.py`

**Guiding Principles:** GP4 (Self-Evident Design), Define-Once Principle

**Purpose:** Verify that `scoring_config.py` — the single source of truth for the entire scoring framework — is internally consistent. These are structural tests. The config either passes or it doesn't.

| Test | What it validates |
|---|---|
| Pillar weights sum to 100 | 40 + 30 + 30 = 100 |
| Dimension weights sum to 100 within each Pillar | e.g., Provisioning 35 + Lab Access 25 + Scoring 15 + Teardown 25 = 100 |
| Every badge has at least one color defined | No badge exists without green, gray, amber, or red criteria |
| Every badge has evidence requirements | GP3 — no badge renders without evidence |
| Locked vocabulary has no conflicts | No term appears in both "use this" and "not this" columns |
| Verdict grid covers all 15 score band x ACV tier combinations | No gaps in the 5x3 matrix |
| All canonical lists are non-empty | Lab platforms, LMS partners, organization types all populated |
| Score thresholds are in descending order | 80 > 65 > 45 > 25 |

---

## Category 2: Prompt Generation System

**File:** `backend/tests/test_prompt_generator.py`

**Guiding Principles:** Define-Once Principle, End-to-End Principle

**Purpose:** Verify that the three-layer Prompt Generation System works correctly — configuration flows into template, template produces a complete prompt, no gaps. Proves the Define-Once Principle works at the code level.

| Test | What it validates |
|---|---|
| Generated prompt has no unreplaced placeholders | Every `{PLACEHOLDER}` in the template was filled by the config |
| Generated prompt contains all Pillar names | Product Labability, Instructional Value, Customer Fit all appear |
| Generated prompt contains all 12 dimension names | All dimensions present |
| Generated prompt contains all badge names from config | Every badge defined in the config appears in the generated prompt |
| Generated prompt contains locked vocabulary | Correct terms present, forbidden terms absent |
| Template + config produces valid output | Generator runs without errors |
| Config changes propagate to generated prompt | Change a weight in config, verify the generated prompt reflects it — proves Define-Once works |

---

## Category 3: Data Model

**File:** `backend/tests/test_data_model.py`

**Guiding Principles:** GP4 (Self-Evident Design), GP3 (Explainably Trustworthy)

**Purpose:** Verify that the data model correctly represents the three-pillar hierarchy, evidence with confidence coding, and data domain separation.

| Test | What it validates |
|---|---|
| Fit Score model has exactly three Pillars | Product Labability, Instructional Value, Customer Fit — no more, no less |
| Each Pillar has exactly four Dimensions | Correct names, correct weights |
| Evidence carries confidence level and explanation | Every evidence object has claim, source, confidence level (confirmed/indicated/inferred), AND a short explanation of why that level was assigned |
| Evidence without confidence level and explanation is invalid | Both fields required — validation rejects incomplete evidence |
| Fit Score calculation matches expected math | Pillar scores out of 100, weighted to Fit Score — verified against hand-calculated examples |
| Product data model contains no company intelligence fields | Architectural separation — product objects never carry fit scores, contacts, ACV, buying signals |
| Company intelligence model contains no program data fields | Designer data never mixed with Inspector data |
| Field names match locked vocabulary | `fit_score` not `composite_score`, `customer_fit` not `organizational_readiness`, etc. |

---

## Category 4: Scoring Logic

**File:** `backend/tests/test_scoring_logic.py`

**Guiding Principles:** GP3 (Explainably Trustworthy)

**Purpose:** Verify that the scoring math produces correct results — dimension rollups, pillar weighting, Fit Score calculation, verdict assignment, and ACV calculation.

| Test | What it validates |
|---|---|
| Dimension scores roll up correctly to Pillar score | e.g., Provisioning 30 + Lab Access 20 + Scoring 12 + Teardown 22 = 84 for Product Labability |
| Pillar scores weight correctly to Fit Score | (85 x 0.40) + (88 x 0.30) + (72 x 0.30) = correct Fit Score |
| All 15 verdict grid cells produce correct verdicts | Every score band x ACV tier combination tested — Prime Target through Poor Fit |
| Penalty deductions don't push scores below zero | Floor of 0 on every dimension |
| Dimension scores don't exceed their max weight | Provisioning can't exceed 35, Lab Access can't exceed 25, etc. |
| ACV calculation follows the formula | Population x Adoption Rate x Hours x Rate — verified against hand-calculated examples |
| Adoption ceilings are enforced | Events max 0.80, all other motions max 0.20 |

---

## Category 5: Research and Evidence Quality

**File:** `backend/tests/test_research_quality.py`

**Guiding Principles:** GP3 (Explainably Trustworthy)

**Purpose:** Verify that research produces well-formed output — proper evidence structure, confidence coding, badge compliance, and domain-based lab platform detection.

| Test | What it validates |
|---|---|
| Every badge in scoring output exists in the canonical badge list | AI can't invent badge names that aren't in the config |
| Every badge has at least one evidence item | GP3 — no badge without evidence |
| Every evidence item has confidence level AND explanation | confirmed/indicated/inferred plus the short explanation |
| Badge colors match the config criteria | A badge named "Credit Card Required" must be red, not green |
| Domain-based detection finds known lab platform URLs | Given a page containing a link to labondemand.com, detection correctly identifies Skillable |
| Domain-based detection covers the full canonical list | Every lab platform domain in the config is scannable |
| Discovery produces valid product list | Products have name, category, deployment model at minimum |
| Evidence bullets follow the format standard | `[Badge Name] \| [Qualifier]: [Finding] — [Source]. [What it means.]` |
| Dimensions producing more than 5 badges generate a soft warning | Logged for review, not rejected — but flagged for attention |

---

## Category 6: Data Domain Separation

**File:** `backend/tests/test_data_domains.py`

**Guiding Principles:** GP1 (Right Information, Right Person)

**Purpose:** Verify the architectural wall between the three data domains. These tests enforce the Foundation's requirement that "the separation must be architectural, not just a permissions layer."

| Test | What it validates |
|---|---|
| Product data storage contains no company intelligence fields | No fit scores, contacts, ACV, buying signals in product storage |
| Company intelligence storage contains no program data fields | No Designer programs, outlines, instructions in company storage |
| Program data storage contains no company intelligence fields | Designer never touches fit scores, contacts, competitive signals |
| A simulated Designer request cannot access company intelligence | The hard wall — even if you try, the data isn't there |
| Product data is accessible from all three tools | Inspector, Prospector, and Designer can all read product data |
| Storage directories are physically separate | Three distinct locations, not fields within shared files |

---

## Category 7: Locked Vocabulary Enforcement

**File:** `backend/tests/test_vocabulary.py`

**Guiding Principles:** GP4 (Self-Evident Design)

**Purpose:** Verify that the codebase uses the correct terms everywhere. No legacy vocabulary. Self-evident design means the right words at every layer.

| Test | What it validates |
|---|---|
| No forbidden terms in data model field names | No `composite_score`, `organizational_readiness`, `market_readiness`, `technical_orchestrability` |
| No forbidden terms in generated prompt output | No `Market Fit`, `Workflow Complexity`, `Gate 1`, `yellow`, etc. |
| All API response field names use locked vocabulary | `fit_score` not `composite_score`, `customer_fit` not `organizational_readiness` |
| Config vocabulary table has no internal conflicts | No term appears on both sides of the use/don't-use list |
| Template variable names match config field names | What the template references is what the config defines |

---

## Category 8: Intelligence Compounds (GP5)

**File:** `backend/tests/test_intelligence_compounds.py`

**Guiding Principles:** GP5 (Intelligence Compounds — It Never Resets)

**Purpose:** Verify that the system builds on what it knows. Deeper research sharpens lighter data. Nothing is lost. Intelligence compounds over time.

| Test | What it validates |
|---|---|
| Full dossier research updates discovery-level data | Deeper research sharpens lighter data, never overwrites it with less |
| Cache stores research and scoring results separately | Research can be preserved even if scoring framework evolves |
| Re-scoring a company preserves existing research | GP5 — intelligence never resets |
| Newer evidence replaces older evidence for the same finding | Fresher data wins, but nothing is lost silently |
| Cache expiry triggers re-research, not deletion | After 45 days, data refreshes — doesn't disappear |

---

## Category 9: UX Consistency and Vocabulary

**File:** `backend/tests/test_ux_consistency.py`

**Guiding Principles:** GP4 (Self-Evident Design), GP1 (Right Information, Right Person)

**Purpose:** Verify that all templates use the correct vocabulary, colors, classification badges, and theme variables. No legacy terminology, no hardcoded colors, no inconsistency across pages.

| Test | What it validates |
|---|---|
| All templates use CSS theme variables only | No hardcoded hex values outside of `_theme.html` |
| Nav renders consistently across all pages | Same header on Inspector, Product Selection, Full Analysis, Prospector, Designer |
| Org type badges use correct color groups | Purple for software/enterprise, teal for training/academic, warm blue for channel/partners |
| Deployment model badges use correct colors and labels | Installable (green), Hybrid (gray), Cloud-Native (green), SaaS-Only (amber) |
| Deployment model data value is `installable` not `self-hosted` | GP4 — data matches display |
| Discovery tier labels match new vocabulary | Seems Promising, Likely, Uncertain, Unlikely — no legacy labels |
| Product selection limit is configurable | Not hardcoded — pulled from config |
| No forbidden page names in user-facing text | No "Seller Action Plan", "Dossier", "Caseboard" visible to users |
| All classification badges use group color, not scoring color | Classification colors (purple/teal/warm blue) never overlap with scoring colors (green/amber/red) |

---

## Category 10: Anti-Hardcoding (Pre-Release Strict Mode)

**File:** `backend/tests/test_no_hardcoding.py`

**Guiding Principles:** Define-Once Principle, GP4 (Self-Evident Design)

**Purpose:** Catch hardcoded values that should reference `scoring_config.py` or `_theme_new.html`. The principle is "no magic values in business logic" — colors, thresholds, badge names, dimension names, rate values, etc. all live in one canonical place. These tests are the safety net for moments when humans (or Claude) forget to reference the config and inline the value instead.

| Test | What it validates |
|---|---|
| No hex colors in active templates outside `:root` blocks of theme files | Templates must use `var(--sk-...)` exclusively. Theme files are the single source of truth for color literals. Excludes `_legacy_*` files. |
| No inline `style="color: #..."` or `style="background: #..."` attributes in markup | Inline hardcoded colors bypass the theme system entirely. Forces all colors through CSS variables. |
| No Python dict literals with color-name keys outside `scoring_config.py` | A dict like `{"green": ..., "amber": ..., "red": ...}` in `scoring_math.py` or `app_new.py` is almost always a duplicate of `BADGE_COLOR_POINTS` or `BADGE_COLOR_DISPLAY_PRIORITY`. Excludes test files. |
| No string literals in business-logic code that exactly match exported `scoring_config.py` constants | If `"Standard VM (1-3 VMs)"` appears as a literal anywhere outside `scoring_config.py`, it should reference `cfg.DEFAULT_RATE_TIER_NAME` instead. |
| No magic numbers in `scoring_math.py` or `app_new.py` normalizers | Any int/float literal other than `0`, `1`, `-1`, `100` should be a named config constant or carry a `# magic-allowed: <reason>` annotation. |

### ⚠ False-Positive Watch — Pre-Release Strict Mode

**Heads-up: this category is intentionally aggressive** during pre-release. We chose strictness because:

- The codebase is small and false positives are cheap to fix (annotation or refactor takes seconds).
- Pre-release is the cheapest moment to enforce a "no hardcoding" standard before external users start touching anything.
- Constraints are easier to relax than to add — once external users see the system, tightening gets harder.

**Expect false positives.** Watch for these patterns and decide whether to relax the rule or keep it:

1. **Test fixtures** that intentionally create color dicts to verify color logic — should be excluded by the `tests/` path filter, but verify before relaxing.
2. **Innocent string matches** — e.g., the string `"low"` happens to match the ACV tier name AND a color name AND probably other things. The cross-file constant scan may flag it incorrectly. Use the annotation system or narrow the scan.
3. **Magic numbers that genuinely should NOT be config** — array indices, format string positions, well-known constants like HTTP status codes. The test allows `0`, `1`, `-1`, `100` by default; everything else needs annotation or refactor.
4. **Designer + Prospector legacy templates** — currently included in scope deliberately to pressure the §6 migration. If migration is delayed and the failing test becomes annoying, scope it out via path filter (don't relax the rule for them in the long run).
5. **Annotation creep** — if `# magic-allowed: <reason>` annotations start accumulating without good reasons, the test signal degrades. Periodically audit annotations to remove stale ones.

**Decision protocol when a false positive bites:**

- **Real signal, fix it:** refactor to reference config. This is the desired outcome.
- **Genuinely non-applicable:** add `# magic-allowed: <reason>` with a clear rationale.
- **Pattern is too broad:** narrow the test rule itself, not the codebase. Document the narrowing in this section so we know what we relaxed and why.
- **Test is adding more friction than value:** disable the specific test (not the whole category) with a `pytest.skip` and a note here. Only as a last resort.

**Goal:** keep this category strict through first external release. After that, revisit and decide which rules graduate to "permanently strict" and which relax to "warning only."

---

## GP Traceability Matrix

| Category | GP1 | GP2 | GP3 | GP4 | GP5 | Define-Once | End-to-End |
|---|---|---|---|---|---|---|---|
| 1. Scoring Config | | | | X | | X | |
| 2. Prompt Generation | | | | | | X | X |
| 3. Data Model | | | X | X | | | |
| 4. Scoring Logic | | | X | | | | |
| 5. Research & Evidence | | | X | | | | |
| 6. Data Domain Separation | X | | | | | | |
| 7. Locked Vocabulary | | | | X | | | |
| 8. Intelligence Compounds | | | | | X | | |
| 9. UX Consistency | X | | | X | | | |
| 10. Anti-Hardcoding | | | | X | | X | |
