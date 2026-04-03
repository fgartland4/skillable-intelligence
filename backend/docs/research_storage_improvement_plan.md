# Research + Storage Improvement Plan
## Step 1.3 — Audit of researcher.py and intelligence.py against session decisions

---

## 1. What the Current Research Logic Does

### researcher.py

`researcher.py` provides two functions called in sequence during a full Inspector run:

**`discover_products(company_name, known_products)`**
Runs 12 parallel search queries covering: product discovery, training programs, ATP signals, training catalog, partner program/portal, customer success, LMS, and lab platform competitor signal. Also runs two LinkedIn org queries (VP-and-above across education/certification, and Director-level). Fetches up to 6 pages in parallel: company homepage, two product pages, training page, ATP page, partner portal page. All pages are fetched at `max_chars=4000`.

**`research_products(company_name, selected_products)`**
For each selected product, fires 9 queries: tech/deploy docs, training/certification, REST API/CLI/developer docs, AI features, Azure/AWS Marketplace, Docker, NFR/developer license, deployment guide, and competitor signal (CloudShare/Instruqt/Appsembler). Fetches up to 3 pages per product at `max_chars=3500`: top tech/doc page, training page, API page.

### intelligence.py

Orchestrates the two-phase flow:
- `discover()` — runs `discover_products()` then `discover_products_with_claude()`, saves, returns discovery dict with a `discovery_id`.
- `score()` — runs `research_products()` via `score_selected_products()`, attaches scores, detects discrepancies, logs competitor candidates.
- Caches are keyed by company name via JSON files; cache TTL is 45 days.
- Discrepancy detection compares discovery-tier `likely_labable` vs. post-scoring `_labable_tier()` and patches the discovery record.

### storage.py (inferred from imports)
JSON file-based storage. Keys: `analysis_id`, `discovery_id`. Functions: `save_analysis`, `load_analysis`, `save_discovery`, `load_discovery`, `find_analysis_by_company_name`, `find_discovery_by_company_name`, `find_analysis_by_discovery_id`, `save_competitor_candidates`.

---

## 2. What It Should Do Per New Decisions

### 2.1 Nine Orchestration Methods with Named Tiers

**Current state:** The nine orchestration methods (Hyper-V, ESX, Container, Azure VM, AWS VM, Azure Cloud Slice, AWS Cloud Slice, Custom API/BYOC, Simulation) are defined in the scoring prompt and reflected in `models.py` as free-text `orchestration_method` strings. There is no canonical enum or validation set.

**Gap:** No structured validation that the string returned by Claude matches one of the nine accepted methods. No lookup table for tier names per method. The `_legacy_path()` function in `scorer.py` handles backward compatibility but the canonical set is only implicit.

**Required improvement:** Define a canonical `ORCHESTRATION_METHODS` dict in `models.py` or a dedicated constants module, listing the nine methods and their valid tier names. Use this for validation on parse, not just in the prompt.

### 2.2 Negative/Penalty Scoring (GPU -5, MFA -3, Provisioning >30min -3, GUI-only -2, No NFR -2, Socket-based -2)

**Current state:** The penalty system is defined in `product_scoring.txt` (Step 4, Penalty Deductions section) and the poor_match_flags list. The prompt instructs Claude to apply penalties and add flags. The `compute_labability_total()` function in `models.py` only takes `tech`, `other`, and `orchestration_method` — it does NOT accept or apply penalties. Penalties are expected to already be reflected in the raw `product_labability` score Claude returns.

**Gap:** Penalty application is entirely prompt-dependent. If Claude forgets a penalty or under-applies it, there is no code-side enforcement. The penalty values are not validated in the code layer. `compute_product_score()` trusts Claude's penalty-adjusted score.

**Required improvement:** Either (a) parse poor_match_flags after scoring and apply penalties in Python to the raw `product_labability` score before final computation, or (b) have Claude return both the raw score and the applied penalties as structured fields. Option (a) is more reliable. Document that penalties stack freely with no floor.

### 2.3 Source Type Classification and Differentiated Fetch Depth

**Current state:** All pages are fetched at near-uniform depth: `max_chars=4000` in `discover_products()` and `max_chars=3500` in `research_products()`. API reference pages, marketing pages, and documentation sites are treated identically.

**Gap:** This is explicitly called out as a decision to implement. API reference pages may be truncated, causing Claude to miss DELETE endpoints, auth details, and rate limits critical for Gate 1. Marketing pages could be fetched at lower budget, freeing tokens for docs and API refs.

**Required improvement in researcher.py:**
```
def _classify_page_type(url: str) -> str:
    # Returns: "marketing" | "documentation" | "api_reference"
    # Heuristics: /docs/, /api/, /reference/, openapi, swagger → api_reference
    # /docs/, /guide/, /manual/, /learn/ → documentation
    # All others → marketing
```

Apply per-type fetch limits:
- marketing: `max_chars=2500`
- documentation: `max_chars=6000`
- api_reference: `max_chars=10000`

### 2.4 Targeted OpenAPI/Swagger Spec Queries

**Current state:** The `api_{name}` query in `research_products()` searches for `REST API CLI PowerShell automation developer documentation`. This is broad and may not surface OpenAPI/Swagger specs specifically.

**Gap:** OpenAPI/Swagger specs are often indexed separately and contain the most structured evidence for lifecycle coverage. No dedicated query targets them.

**Required addition to research_products() query set per product:**
```python
queries.append((f"openapi_{name}", f"{name} openapi spec swagger.json api reference site:github.com OR site:swaggerhub.com"))
queries.append((f"spec_{name}",    f"{company_name} {name} API reference openapi swagger lifecycle provision delete"))
```

Also: add a `_fetch_page_text()` call for OpenAPI JSON/YAML pages if found, with `max_chars=12000` (they are dense and structured).

### 2.5 Documentation Breadth Cataloging

**Current state:** `research_products()` fetches the top tech/doc page for each product at `max_chars=3500`. There is no explicit instruction to extract structural complexity signals (modules, features per module, options/steps per feature, interoperability count).

**Gap:** The page content is passed to Claude without any pre-processing to identify navigation structure. Claude cannot reliably count documentation modules from a page fetch of 3500 chars — it usually gets a partial view of the page.

**Required improvement:**
1. In `researcher.py`, add a dedicated doc-structure extraction pass. When a documentation site is detected (URL heuristic), fetch with `max_chars=6000` and pass to a lightweight pre-processor that attempts to extract nav/sidebar structure.
2. Add to the per-product query set:
   ```python
   queries.append((f"docnav_{name}", f"site:{vendor_doc_domain} {name} documentation modules features configuration"))
   ```
3. Pass extracted structure as a distinct field in the research context sent to Claude, separate from raw page content.

### 2.6 Two-Stage Inspector Flow

**Current state:** The flow is effectively single-pass. `discover_products()` runs a broad scan and Claude produces a discovery dict. `research_products()` runs product-specific queries for selected products. Both phases exist, but they are not clearly architected as separate stages with stage-level data contracts.

**Gap:** The two-stage model decision calls for Stage 1 to produce a Company Report (overall fit, ranked product list with signals, competitor pairings) and Stage 2 to produce a per-product deep dive. Currently, Stage 1 output is a raw discovery dict and Stage 2 output is a CompanyAnalysis. There is no Company Report as a first-class entity.

**Required improvement in intelligence.py:**
- Define `discover()` return as the Company Report entity (add `company_fit_score`, `ranked_products`, `competitor_pairings` fields).
- Stage 2 (`score()`) appends to the Company Report rather than replacing it.
- Storage must support this: save a single company record that gets incrementally enriched.

### 2.7 SaaS Three-Path Evaluation

**Current state:** The SaaS Isolation Pre-Screen is implemented in the prompt (Step 1) and in `_labable_tier()` / `_attach_scores()` via CEILING_FLAGS. Phase 1 of SaaS isolation gate is done. Phase 2 (three-path evaluation) is pending.

**Gap:** No SaaS-specific research queries. When a product is identified as SaaS-only in discovery, `research_products()` fires the same generic queries as for VM-installable products. The Sandbox API query, DELETE endpoint query, and credential pool viability query are absent.

**Required per-product SaaS path queries (add conditionally when `deployment_model == "saas_only"`):**
```python
queries.append((f"sandbox_{name}",    f"{company_name} {name} sandbox API trial account developer"))
queries.append((f"teardown_{name}",   f"{company_name} {name} API delete endpoint deprovision teardown"))
queries.append((f"credpool_{name}",   f"{company_name} {name} training account partner program sandbox credentials"))
queries.append((f"mfa_{name}",        f"{company_name} {name} API authentication MFA TOTP OAuth"))
```

This requires the discovery data to be available when building product-level queries — which it currently is not. The `deployment_model` from discovery needs to be passed into `research_products()`.

### 2.8 Collaborative Lab Detection

**Current state:** Not implemented in researcher.py. The prompt does not yet include Collaborative Lab detection signals. The `reference_skillable_delivery_patterns.md` defines both patterns (Parallel/Adversarial, Sequential/Assembly Line) with detection signals.

**Gap:** No research queries fire for collaborative lab signals. Claude cannot flag this without data.

**Required queries for collaborative lab detection (in `research_products()`):**
```python
queries.append((f"collab_{name}", f"{company_name} {name} red team blue team SOC cyber range OR \"data pipeline\" OR \"multi-role\" OR \"handoff\" training"))
```

### 2.9 Break/Fix and Simulated Attack Detection

**Current state:** Not implemented as distinct query types. May surface incidentally from `train_{name}` queries.

**Required queries:**
```python
queries.append((f"troubleshoot_{name}", f"{company_name} {name} troubleshooting guide fault recovery incident lab"))
queries.append((f"attack_{name}",       f"{company_name} {name} attack simulation threat detection incident response"))
```

### 2.10 Dim 2.1 Workflow Phase Names

**Current state:** The five workflow phases (Design & Architecture, Configuration & Tuning, Deployment & Provisioning, Support Scenarios, Troubleshooting) are defined in the scoring prompt. No issue in researcher.py for this — this is prompt-only.

**Gap:** No code-side mapping or validation. When Claude returns Instructional Value evidence referencing workflow phases, there is no structured parsing that identifies which phases were hit.

### 2.11 Dim 4 Category Priors Restructuring

**Current state:** The Dim 4 scoring rubric in `product_scoring.txt` (Step 4, Market Readiness) defines High (+5), Moderate (+2), and Low (+0) tiers. Categories defined: High demand = Cybersecurity, Cloud Infrastructure, Networking/SDN, Data Science & Engineering, Data & Analytics, DevOps. This matches the decision.

**Status:** Appears correctly implemented in the prompt. No researcher.py changes needed for this.

---

## 3. Storage Patterns That Need to Change

### 3.1 Company Record as First-Class Entity

**Current:** Two separate records — `discovery` (keyed by `discovery_id`) and `analysis` (keyed by `analysis_id`). They are linked via `discovery_id` on the analysis. The company name is the lookup key for both.

**Needed:** A single Company Record that aggregates both. Stage 1 (discover) creates the Company Record. Stage 2 (score) appends product deep-dive data to it. The Company Record is the unit of cache — not the discovery or analysis separately.

**Migration path:** Create a `company_record` storage tier. On first access, create from existing discovery + analysis. Going forward, write directly to the Company Record. Preserve backward compat with old discovery/analysis JSON files.

### 3.2 Research Cache Storage

**Current:** The research cache from `research_products()` is embedded in the discovery record via `_research_cache` key. This is not well-documented and the key is accessed only defensively.

**Needed:** Explicit research cache storage with clear schema. Cache should be keyed by `(company_name, product_name, stage)` so individual product research can be refreshed without re-running everything.

### 3.3 SaaS Deployment Model Flag in Discovery

**Current:** `deployment_model` comes from the Claude discovery response and is not explicitly stored at the company level — only on individual products.

**Needed:** A company-level `has_saas_products` boolean and list of `saas_product_names` in the discovery/company record, so downstream functions (research, scoring) can conditionally apply SaaS-specific logic without re-parsing.

### 3.4 Competitor Candidates Storage

**Current:** `save_competitor_candidates()` is called in `intelligence.py` after scoring. The storage function exists but the format of competitor candidates is not audited here.

**Needed:** Verify that competitor candidates include product-level competitor pairings (not just company-level). This feeds the Stage 1 competitive pairing feature.

---

## 4. New Query Sets Needed Per Product Type

### 4.1 SaaS Products (conditional on deployment_model)
- Sandbox/trial API documentation
- DELETE/deprovision endpoint
- Credential pool / training account program
- MFA on API authentication
- Partner portal for training accounts

### 4.2 Networking/SDN Products
- CLI configuration guide
- Multi-VM topology requirements
- Hardware virtualization compatibility
- License model (socket-based, per-device, etc.)

### 4.3 Security/Cybersecurity Products
- Threat detection lab scenarios
- Red Team / Blue Team training content
- SOC operations training
- Incident response scenarios
- EDR/SIEM specific: attack simulation documentation

### 4.4 Data Science / ML Products
- GPU requirements
- Training data size/cost
- Pipeline multi-stage workflow
- Collaborative lab signals (data engineer → data scientist → analyst handoff)

### 4.5 All Products (currently missing)
- OpenAPI/Swagger spec query (see 2.4)
- Documentation breadth/nav query (see 2.5)
- Collaborative lab detection (see 2.8)
- Break/fix and troubleshooting (see 2.9)

---

## 5. Gaps and Inconsistencies Found

### Gap 1: deployment_model not available during research phase
`research_products()` takes `selected_products` as a list of dicts from the discovery output. These include `name` but the availability of `deployment_model` (SaaS vs. installable) depends on what Claude's discovery response includes. If Claude omits `deployment_model` at discovery, the research phase has no way to apply SaaS-specific queries. Fix: require `deployment_model` in the discovery product schema and default to `"unknown"` with a fallback.

### Gap 2: Page fetch depth is uniform but token usage is not
Discovery pages are fetched at 4000 chars, product pages at 3500 chars. Both are passed to Claude who has a single `max_tokens=7500` budget per product. The page content often dominates the context, leaving little room for the prompt's scoring instructions. A differentiated fetch strategy (lower for marketing, higher for API docs) would improve Claude's evidence quality without increasing total token usage.

### Gap 3: No pre-processing of page content before passing to Claude
`_build_product_context()` in `scorer.py` concatenates raw page text. No filtering of navigation bars, cookie consent text, advertising copy, or repetitive header/footer content. The `_fetch_page_text()` function strips `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>` tags — this is helpful but not sufficient for doc sites that use div-based navigation or repeated sidebar elements.

### Gap 4: Nine orchestration methods partially named
The prompt uses all nine method names. The `_legacy_path()` function maps old path codes to five of them (Hyper-V, Azure Cloud Slice, AWS Cloud Slice, Custom API, Simulation). Azure VM, AWS VM, ESX, and Container are not in the legacy mapping. This is not a bug for new analyses (which have `orchestration_method` directly) but creates a documentation gap — the canonical set of nine methods is nowhere defined as a single authoritative list in the code.

### Gap 5: Competitor signal query fires for all products regardless of category
The `compete_{name}` query in `research_products()` always searches for CloudShare/Instruqt/Appsembler. This is appropriate but should also include Skytap and GoDeploy. More importantly, it should not be labeled `compete_` (which sounds like competitor product research) — it should be `labplatform_{name}` to be clear it is searching for existing lab platform usage.

### Gap 6: Missing `lab_platform` query in product research
`discover_products()` fires a `lab_platform` query at the company level. `research_products()` does NOT fire an equivalent product-level query. The product-level `compete_{name}` query is similar but targets general competitors, not specifically existing lab platform deployments for that product. These should be unified and consistent.

### Gap 7: Research cache from research_products() not reliably stored
The `_research_cache` key on discovery records is set only in some code paths. If `score()` is called with `research_cache=None` and the discovery record has no `_research_cache`, the research phase re-runs. This is not a bug but is a performance issue for the refresh and expand operations.

---

## 7. Navigation and Cache Usability — Required Logic Improvements

### 7.1 Problem: Discovery Cache Skips Caseboard

**Current behavior:** When a company has been run before and is in cache, the route bypasses Caseboard and navigates directly to the most recent Dossier.

**Required behavior:** Cache state must never skip Caseboard. Discovery cache is used to populate the Caseboard fast — but the user always lands on Caseboard first and makes a fresh product selection. This is intentional: the user may want to explore different products than last time.

**Rule:** `/inspector/discover` always redirects to `/inspector/caseboard/<discovery_id>`. Never to `/inspector/results/<analysis_id>`. The existing analysis is surfaced on the Caseboard via the "View Previous →" button.

### 7.2 Problem: Per-Product Scoring Should Be Additive

**Current behavior:** Scoring re-runs all selected products every time.

**Required behavior:** Per-product scores are cached individually. When the user selects products on the Caseboard:
- Products with a cached score → served instantly from cache (no re-score)
- Products without a cached score → researched and scored, then added to cache

Over multiple sessions with different product selections, the cache grows. Six products scored across two sessions → all six cached. The user never waits for a product they've already scored.

**Cache invalidation rules (per product):**
| Condition | Action |
|---|---|
| Cached score <45 days old | Serve from cache |
| Cached score ≥45 days old | Re-score automatically |
| User checked "Refresh Cache" | Re-score all selected products regardless of age |
| Product never scored before | Score and cache |

**Note:** "Refresh Cache" re-scores ALL selected products, not just stale ones. It is a deliberate full refresh, not a selective one.

### 7.3 Problem: Back Button Loses Caseboard State

**Required behavior:** Dossier → Back must return to the same Caseboard in the same state. Caseboard is always re-renderable from the cached discovery record — no re-discovery needed. The back navigation should be a standard browser back or an explicit `← Back to Caseboard` link pointing to `/inspector/caseboard/<discovery_id>`.

Dossier is also cached — if the user returns to Caseboard and re-selects the same products, the existing Dossier should be served immediately (no re-score), subject to the same 45-day / Refresh Cache rules above.

### 7.4 Mental Model for Implementation

```
Home → POST /inspector/discover
  → if cached discovery (<45 days, no refresh): load from cache
  → else: run discovery, cache result
  → ALWAYS redirect to /inspector/caseboard/<discovery_id>

Caseboard → user selects products → POST /inspector/score
  → for each selected product:
      if cached score exists and <45 days and not force_refresh:
          load from cache
      else:
          research + score, write to cache
  → redirect to /inspector/results/<analysis_id>

Dossier → "← Back to Caseboard" link → GET /inspector/caseboard/<discovery_id>
  → load from cache (always available) → render Caseboard
  → user re-selects same products → existing analysis served from cache
```

---

## 8. Family Grouping — Large Company Discovery Logic

### 7.1 Trigger Condition

When `discover_products_with_claude()` returns a product list with more than 15 products, the discovery response must also include a `product_families` field. The Flask route checks `len(discovery.products) > 15` and shows the Family Picker modal if true.

### 7.2 What Claude Must Return

The discovery prompt must instruct Claude to group products into families whenever the total product count exceeds 15. The `product_families` field must be part of the structured JSON response:

```json
"product_families": [
  {
    "name": "Cloud Infrastructure (OCI)",
    "product_count": 42,
    "product_keys": ["Oracle Compute", "Oracle Object Storage", "Oracle Networking", ...]
  },
  {
    "name": "Database & Data Platform",
    "product_count": 31,
    "product_keys": ["Oracle Database 23ai", "MySQL", "Oracle NoSQL", ...]
  }
]
```

`product_keys` must exactly match the `name` field of products in the `products` list — this is the join key used to filter the Caseboard.

### 7.3 Prompt Instructions for Family Grouping

Add to `discover_products_with_claude()` prompt when product count is anticipated to be large (include for all companies — Claude skips if ≤15 products and returns `product_families: []`):

```
If you discover more than 15 products, group them into product families.
Rules:
- Use the company's own published product pillar/family names where they exist (e.g., Oracle uses Fusion ERP, OCI, etc.)
- Target 3–8 families. Never more than 12.
- Every product must belong to exactly one family. Resolve ambiguity by primary use case, not secondary bundling.
- product_keys values must exactly match the name field of products in the products list.
- If 15 or fewer products, return product_families as an empty list [].
```

### 7.4 Ambiguity Resolution Rules

When a product could belong to multiple families, use this priority order:
1. The family the company's own sales/marketing motion assigns it to
2. The primary technical function of the product (not a bundled secondary capability)
3. The most specific family over the most general (e.g., "Database & Data Platform" over "Cloud Infrastructure" for Autonomous Database)

**Known ambiguous Oracle products and their resolved families:**
- Autonomous Database → Database & Data Platform (primary function is database; OCI is the delivery mechanism)
- Oracle Analytics Cloud → assign to the Fusion pillar it is most often bundled with, or create a standalone Analytics family if count justifies it
- Oracle Middleware / Java / Integration Cloud → Industry, Specialized & Legacy (platform technology, not a primary Fusion pillar)

### 7.5 Storage

`product_families` is stored on the discovery record alongside `products`. It is never re-computed after initial discovery — it is part of the discovery cache. A force-refresh re-runs discovery and regenerates families.

---

## 6. Priority Order for Implementation

1. **SaaS-specific research queries** — Phase 2 of SaaS isolation gate; highest impact on score accuracy for SaaS products.
2. **Source type classification and differentiated fetch depth** — directly improves API ref coverage; moderate implementation effort.
3. **OpenAPI/Swagger spec queries** — targeted addition to existing query set; low effort, high value for Gate 1.
4. **Documentation breadth cataloging** — feeds Dim 2 and consumption estimates; moderate effort.
5. **Collaborative lab and break/fix detection queries** — additive query additions; low effort.
6. **Company Record as first-class storage entity** — enables two-stage flow architecture; higher effort, required for Stage 1 Company Report feature.
7. **Code-side penalty validation** — validates Claude's penalty application; moderate effort, improves reliability.
8. **Research cache storage formalization** — quality improvement; low-medium effort.

