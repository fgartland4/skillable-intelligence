# Caseboard + Dossier Display and Parsing Spec
## Step 1.4 — Data field mapping, parsing contract, and layout wireframes

---

## 1. Data Field Map — Caseboard

The Caseboard is the Stage 1 output view. It renders from a `discovery` dict passed by Flask.

### 1.1 Top-Level Discovery Fields Used

| Field | Source | UI Element | Notes |
|---|---|---|---|
| `discovery.company_name` | Claude discovery response | Page title, breadcrumb, header h1, nav | Required |
| `discovery.organization_type` | Claude discovery response | Org badge next to company name | Enum: software_company / academic_institution / training_organization / systems_integrator / technology_distributor / professional_services |
| `discovery.company_description` | Claude discovery response | Header subtitle text | Optional; rendered as-is |
| `discovery.company_url` | Claude discovery response | Not currently rendered on caseboard | Available in data |
| `discovery.discovery_id` | Generated in intelligence.py | Hidden form field `<input name="discovery_id">` | Used to link to scoring |
| `discovery.products` | Claude discovery response | Product card grid, tier counts | List of product dicts |
| `discovery.atp_signals` | researcher.py (search results) | "Partner Program" badge in Company Indicators | Boolean presence check |
| `discovery.training_programs` | researcher.py (search results) | "Training Programs" badge + count in Company Indicators | Presence + length check |
| `discovery.partnership_signals.existing_lab_partner` | Claude discovery response | "Lab Competitors" column in Company Indicators | Iterable or string |

### 1.2 Product Card Fields (per product in `discovery.products`)

| Field | UI Element | Display logic |
|---|---|---|
| `p.name` | Card title text | Required |
| `p.category` | Category badge (purple) | Optional; shown if present |
| `p.deployment_model` | Deployment badge (gray) or SaaS badge (amber) | `saas-only` / `saas_only` → amber "SaaS Only"; others → gray with normalized label |
| `p.likely_labable` | Tier section membership + left-border color | Enum: highly_likely (green) / likely (teal) / less_likely (amber, dimmed) / not_likely (red, more dimmed) |
| `p.poor_match_flags` | SaaS/No API/Hardware/Multi-Tenant warning badges in Company Indicators box | Aggregated across all products |
| `p.candidate_paths` | Path badges (small, dark-bordered) on card | First 2 paths shown |
| `p.description` | Card body text | Optional; shown if present |
| `p.priority` | Sort order within tier | Used for `sort(attribute='priority')` |

### 1.3 Intel Panel Fields (right column)

| Field | UI Element |
|---|---|
| `discovery.products` filtered by `likely_labable` | Tier summary dots + counts |
| Org Readiness computed from `organization_type`, `atp_signals`, `training_programs`, product `category=='Training & Certification'` | Maturity slider (Nascent / Emerging / Established / Mature) with fill percentage |
| `discovery.org_contacts` (search results) | Contact cards in Intel panel |

### 1.4 Company Indicators Box — Computed Fields

The Company Indicators box is a computed view built entirely from discovery-layer data. No analysis data is used here.

| Computed signal | Source fields | Display |
|---|---|---|
| "Partner Program" | `discovery.atp_signals` truthy | Green badge |
| "Training Programs" | `discovery.training_programs` truthy | Green badge |
| "Training & Cert Org" | Any product with `category=='Training & Certification'` | Teal badge |
| "All SaaS — Low Fit" | All products have `saas_only` flag | Red badge |
| "N SaaS-Only" | Count of products with `saas_only` flag | Amber badge with count |
| "No API Automation" | Any product has `no_api_automation` flag | Amber badge |
| "Hardware Required" | Any product has `bare_metal_required` flag | Red badge |
| "Multi-Tenant Only" | Any product has `multi_tenant_only` flag | Amber badge |
| Org Readiness level | org_type + atp_signals + training_programs + TC products | Score 0-7 → Nascent/Emerging/Established/Mature |
| Products Discovered count | `len(discovery.products)` | Text |
| Training Programs count | `len(discovery.training_programs)` | Text |
| Lab Competitors | `discovery.partnership_signals.existing_lab_partner` | Text, amber color if present |

### 1.5 Footer Bar Fields

| Field | UI Element |
|---|---|
| JS-computed selection count | "N/6 selected" counter |
| Form submit state | "Run Dossier" button (disabled if 0 selected) |
| `existing_analysis.analysis_id` | "View Previous" button (shown if previous analysis exists) |

---

## 2. Data Field Map — Dossier

The Dossier renders from an `analysis` dict (the full scored analysis + computed score fields).

### 2.1 Zone 1 — Seller Summary Card

| Field | Source | UI Element |
|---|---|---|
| `data.company_name` | analysis | Page title, Zone 1 heading |
| `data.organization_type` | analysis | Org badge |
| `data.company_description` | analysis | Subtitle under company name |
| `data._composite_score` | Computed by `_attach_scores()` | Verdict badge logic + score display |
| Verdict | Derived from `_composite_score` | "Strong Fit" / "Pursue" / "Monitor" / "Pass" |
| Blockers | Products with CEILING_FLAGS or poor_match_flags | Hero blocker badges (red) |
| Top product name + labability | `data.products[0]` after sort | Labability badge in seller grid |
| Contacts | First product's `contacts` list | Contact name/title/LinkedIn in seller grid |
| Consumption estimate | `consumption_potential.annual_hours_low/high` × `vm_rate_estimate` | ACV estimate (seller hero, large number) |
| Next steps / recommendations | `products[0].recommendation` list | Bullet list in Zone 1 bottom |

### 2.2 Zone 2 — SE Technical Detail (per product, collapsible)

Each product renders as a `<details>` element. Fields per product:

| Field | UI Element |
|---|---|
| `p.name` | Summary heading |
| `p.category` | Category badge in summary |
| `p._total_score` | Large score number (color: green ≥70, amber 45-69, red <45) |
| `p.orchestration_method` | Path badge in summary row |
| `p.lab_highlight` | Small green badge in summary |
| `p.labability_score.product_labability.score` (0-40) | Dimension score display + bar |
| `p.labability_score.product_labability.summary` | Summary paragraph |
| `p.labability_score.product_labability.evidence` | Bullet list (claim + optional source link) |
| `p.labability_score.instructional_value.score` (0-30) | Dimension score + bar |
| `p.labability_score.instructional_value.summary` | Summary paragraph |
| `p.labability_score.instructional_value.evidence` | Bullet list |
| `p.labability_score.organizational_readiness.score` (0-20) | Dimension score + bar |
| `p.labability_score.organizational_readiness.summary` | Summary |
| `p.labability_score.organizational_readiness.evidence` | Bullet list |
| `p.labability_score.market_readiness.score` (0-10) | Dimension score + bar |
| `p.labability_score.market_readiness.summary` | Summary |
| `p.labability_score.market_readiness.evidence` | Bullet list |
| `p.poor_match_flags` | Flag badges (red) under product name |
| `p.recommendation` | Recommendation bullet list (Delivery Path, Scoring Approach, etc.) |
| `p.lab_concepts` | Lab concept chips (purple, 2-column grid) |
| `p.consumption_potential.motions` | Consumption table (motion rows) |
| `p.consumption_potential.annual_hours_low/high` | Total row |
| `p.consumption_potential.vm_rate_estimate` | Rate column |
| `p.consumption_potential.methodology_note` | Caveat text |
| `p.owning_org.name/type/description` | Owning Org section |
| `p.contacts` | Contact rows with LinkedIn links |

---

## 3. Parsing Contract

### 3.1 Route → Template Data Flow

```
GET /inspector/caseboard/<discovery_id>
    → load_discovery(discovery_id)
    → find_analysis_by_discovery_id(discovery_id) (optional)
    → render_template('caseboard.html',
          discovery=discovery_dict,
          existing_analysis=analysis_or_None)

POST /inspector/score  (form submit from caseboard)
    → selected products from form checkboxes (name="products", multiple)
    → discovery_id from hidden field
    → intelligence.score(company_name, selected_products, discovery_id)
    → redirect to /inspector/results/<analysis_id>

GET /inspector/results/<analysis_id>   (redirects to dossier)
    → load_analysis(analysis_id)
    → _attach_scores(data)    # sets _total_score, likely_labable, _composite_score
    → render_template('dossier.html', data=data)
```

### 3.2 Evidence Rendering Contract

Evidence bullets use the `**Label | Suffix:**` convention from the prompt. The templates render these as HTML by applying Jinja2's `| safe` filter after the claim string is parsed for markdown bold syntax.

Current parsing: evidence `claim` strings are passed through a Jinja2 filter that converts `**text**` → `<strong>text</strong>`. Source URLs are rendered inline as `<a>` tags using `evidence.source_url` + `evidence.source_title`.

**Contract:** Every evidence item must have a `claim` string starting with `**Label:**`. Optional `source_url` and `source_title` fields produce a hyperlink after the claim. Evidence items without a source URL render claim text only.

### 3.3 Recommendation Rendering Contract

`p.recommendation` is a list of strings. Each string must start with `**Label:**` for correct rendering. The dossier renders these as a `<ul>` with `| safe` applied per item. Labels with `| Risk:` suffix render with `.step-risk` CSS class (red color). Labels with `| Blocker:` suffix render with `.step-risk` class (also red currently — may need a separate class for orange vs. red per the badge convention).

**Gap:** The templates currently do not distinguish `| Risk` (orange) from `| Blocker` (red) in recommendation bullets. Both render red. The scoring prompt defines different colors for these. This is a display inconsistency to resolve.

### 3.4 Score Field Validation

`_attach_scores()` is the single source of truth for score computation. It must be called before rendering any dossier. The following computed fields must be present on the data dict before rendering:

- `p._total_score` (int, 0-100) — set by `compute_product_score(p)`
- `p.likely_labable` (str) — set by `_attach_scores()` tier logic
- `data._composite_score` (int) — top product score
- `data._composite_gated` (bool) — True if composite < 30

---

## 4. ASCII Wireframes

### 4.1 Caseboard Layout

```
+------------------------------------------------------------------+
| [Skillable logo]  Inspector  /  [company]          [nav back]   |
+------------------------------------------------------------------+
| Start / Inspector / [Company Name]  (breadcrumb)                 |
+------------------------------------------------------------------+
|                                                                  |
|  [← Search Different Company]                                    |
|  INSPECTOR CASEBOARD                                             |
|  [Company Name]  [Org Type Badge]         [Run Dossier →]       |
|  [company description]                    [View Previous →]      |
|                                           [N selected status]   |
+------------------------------------------------------------------+
|  COMPANY INDICATORS BOX                                          |
|  +---------------------------+  +---------------------------+   |
|  |  [Partner Program] [Trng]  |  |  ORG READINESS           |   |
|  |  [Training & Cert]         |  |  [=====●         ]       |   |
|  |  [N SaaS-Only] [No API]   |  |  Nascent Emerging Est. M  |   |
|  +---------------------------+  +---------------------------+   |
|  PRODUCTS DISCOVERED: N  |  TRAINING PROGRAMS: N  |  LAB COMP  |
+------------------------------------------------------------------+
|                                              |                   |
|  [form#scoreForm]                            |  INTEL PANEL     |
|                                              |  (sticky right)  |
|  HIGHLY LIKELY ─────────────────────────    |  +-------------+ |
|  ┌──────────────────────────────────────┐   |  | Tier Summary| |
|  │ ✓  [Product Name]                    │   |  | ● HL:  N    | |
|  │     [Category] [Deploy] [highly lkly]│   |  | ● L:   N    | |
|  │     product description text...      │   |  | ● LL:  N    | |
|  └──────────────────────────────────────┘   |  | ● NL:  N    | |
|  ┌──────────────────────────────────────┐   |  +-------------+ |
|  │ ✓  [Product Name]  ...               │   |                  |
|  └──────────────────────────────────────┘   |  +-------------+ |
|                                              |  | Contacts    | |
|  LIKELY ────────────────────────────────    |  | Name        | |
|  ┌──────────────────────────────────────┐   |  | Title       | |
|  │ ✓  [Product Name]  ...               │   |  | LinkedIn    | |
|  └──────────────────────────────────────┘   |  +-------------+ |
|                                              |                  |
|  LESS LIKELY ───────────────────────────    |                  |
|  [dimmed cards, uncheckable]                 |                  |
|                                              |                  |
|  NOT LIKELY ────────────────────────────    |                  |
|  [more dimmed cards]                         |                  |
|                                              |                  |
|  TRAINING & CERT ───────────────────────    |                  |
|  [non-selectable cards]                      |                  |
|                                              |                  |
+------------------------------------------------------------------+
|  [sticky footer]  N/6 selected  [hint text]  [Run Dossier →]   |
+------------------------------------------------------------------+
```

### 4.2 Dossier Layout

```
+------------------------------------------------------------------+
| [Skillable logo]  [nav]                                          |
+------------------------------------------------------------------+
| ← Back to caseboard                                              |
+------------------------------------------------------------------+
|  [cache banner: "Analysis from [date]" | Re-run button]          |
+------------------------------------------------------------------+
|                                                                  |
|  ZONE 1 — SELLER SUMMARY  (highlighted card)                    |
|  +------------------------------------------------------------+  |
|  |  [Company Name]  [Org Badge]                               |  |
|  |  company description                                        |  |
|  |                                                             |  |
|  |  [VERDICT BADGE]  |  $XXX,XXX ACV range  |  [BLOCKERS]    |  |
|  |                   |  Estimated annual     |  [red badges]  |  |
|  |                                                             |  |
|  |  +------------------+  +------------------+               |  |
|  |  | PRODUCT LABABILITY|  | CONTACTS         |              |  |
|  |  | [Product] [badge] |  | [Name]           |              |  |
|  |  | [Product] [badge] |  | [Title]          |              |  |
|  |  +------------------+  | [LinkedIn]        |              |  |
|  |  +------------------+  +------------------+               |  |
|  |  | DELIVERY PATH    |  | TOP PRODUCT       |              |  |
|  |  | [text]           |  | [Name] [score]    |              |  |
|  |  +------------------+  +------------------+               |  |
|  |                                                             |  |
|  |  NEXT STEPS                                                |  |
|  |  • [Delivery Path]: text                                   |  |
|  |  • [Scoring Approach]: text                                |  |
|  |  • [Program Fit]: text                                     |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  SE / SC TECHNICAL DETAIL ─────────────────────────────────    |
|                                                                  |
|  ▶ [Product Name]  [Category]  [Orchestration Path]  [88]      |
|    (collapsed by default)                                        |
|                                                                  |
|  ▼ [Product Name]  [Category]  [Orchestration Path]  [72]      |
|    (expanded)                                                    |
|    +----------------------------------------------------------+  |
|    | PRODUCT LABABILITY  32/40  ══════════════░░             |  |
|    | summary text...                                          |  |
|    | • **Windows Install:** ...                               |  |
|    | • **REST API | Strength:** ...                           |  |
|    |                                                          |  |
|    | INSTRUCTIONAL VALUE  24/30  ══════════░░░░              |  |
|    | summary text...                                          |  |
|    | • **Workflow Depth:** ...                                |  |
|    |                                                          |  |
|    | ORGANIZATIONAL READINESS  15/20  ══════░░░░             |  |
|    | • **Training Org:** ...                                  |  |
|    |                                                          |  |
|    | MARKET READINESS  8/10  ══════════░░                    |  |
|    | • **Category Fit | Strength:** ...                       |  |
|    |                                                          |  |
|    | POOR MATCH FLAGS                                         |  |
|    | [flag badge] [flag badge]                                |  |
|    |                                                          |  |
|    | LAB CONCEPTS                                             |  |
|    | [concept chip] [concept chip]                            |  |
|    | [concept chip] [concept chip]                            |  |
|    |                                                          |  |
|    | CONSUMPTION POTENTIAL                                    |  |
|    | Motion          | Pop Range | Hrs | Adopt | Annual Hrs  |  |
|    | [motion label]  | N–N       | N   | N%    | N–N hrs     |  |
|    | TOTAL                               N–N hrs / $N–N ACV  |  |
|    |                                                          |  |
|    | CONTACTS  /  OWNING ORG                                  |  |
|    | [contact name + title + linkedin]                        |  |
|    +----------------------------------------------------------+  |
|                                                                  |
+------------------------------------------------------------------+
```

---

## 5. Gaps in Current Parsing

### 5.1 Verdict derivation
The dossier template derives a verdict from `_composite_score` but the exact cutoffs are in the template logic, not in a shared constant. This should be in `core.py` or `models.py` as a named function `_verdict(score)`.

Current (inferred from template):
- score >= 70 → "Strong Fit"
- score >= 45 → "Pursue"
- score >= 20 → "Monitor"
- else → "Pass"

### 5.2 Risk vs. Blocker rendering in recommendations
The `| Risk` and `| Blocker` suffixes both use `.step-risk` (red). Per the badge convention, `| Risk` should render orange and `| Blocker` should render red. The template needs a Jinja2 filter or conditional logic to distinguish these.

### 5.3 Missing fields for new decisions

The following data fields are referenced by decisions but not yet present in the templates or data model:

| New field needed | Where | Why |
|---|---|---|
| `competitive_pairings` | Caseboard Company Indicators + Stage 1 output | Competitor pairing decision |
| `company_fit_score` | Caseboard Intel Panel / Stage 1 Company Report | Two-stage flow Stage 1 output |
| `collaborative_lab_signals` | Dossier Delivery Path section | Collaborative lab detection |
| `break_fix_signals` | Dossier Delivery Path section | Break/fix detection |
| `simulated_attack_signals` | Dossier Delivery Path section | Attack simulation detection |
| `doc_breadth_map` | Dossier Instructional Value section | Documentation breadth cataloging |
| Dim 2.1 phase hit list | Dossier Instructional Value evidence | Named phases scored |

### 5.4 Caseboard competitor display
The `Lab Competitors` column reads `discovery.partnership_signals.existing_lab_partner` — a nested path that requires `partnership_signals` to be a dict with an `existing_lab_partner` key. If the discovery response uses a flat structure (no `partnership_signals` wrapper), this path fails silently. Verify the Claude discovery prompt produces this nested structure or flatten the access path.

### 5.5 `candidate_paths` field
Caseboard cards render `p.candidate_paths` (first 2) as path badges. This field is not in the `Product` dataclass in `models.py` — it appears to be a discovery-phase-only field returned by the discovery Claude call. It is not persisted on the scored Product model. This creates a display difference: caseboard shows candidate_paths; dossier shows `orchestration_method`. The relationship between `candidate_paths` (discovery) and `orchestration_method` (scored) should be documented and the transition should be explicit.
