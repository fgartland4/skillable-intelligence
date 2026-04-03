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

### 4.1 Caseboard Layout (Revised)

**Design decisions:**
- Company Indicators box removed — moved to Dossier
- Training & Certification products removed from left tier list — shown in right panel
- Competitive Landscape moved from left column to right panel
- Product cards compact — name + category badge + tier badge only, no description
- Empty tiers (0 products) grayed out
- No sticky footer — Run Dossier button lives in header next to company name
- Selection counter: "4 of 7 products selected" in orange; when limit reached, changes to "6 of 6 — uncheck one to swap" + uncheckable cards dim
- Research time estimate displayed alongside selection counter — updates live as user selects/deselects products (see Est. Research Time logic below)
- Right panel label: "AT A GLANCE" (not "Product Labability")
- Breadcrumbs removed — navigation handled by shared nav, "← Search Different Company" link, and browser back

### Est. Research Time — Display Logic

**Label format:** `Est. Research Time: XX min, XX sec` — always zero-padded to two digits in both positions so the label width never changes and the layout does not shift as the user selects products.

**Displayed:** In the header area alongside the selection counter, updates in real time via JS as the user selects/deselects products. No page reload needed.

**Cache state:** Determined at Caseboard render time. Flask checks the score cache for every product in the discovery list before rendering. Each product card is tagged with a `data-cached="true|false"` attribute. JS reads these attributes to compute the estimate — no additional server calls needed.

**Time constants (approximate — tune based on observed actuals):**

| Product state | Estimated contribution |
|---|---|
| Cached (score already exists, <45 days) | 2 seconds |
| Uncached (needs research + scoring) | 35 seconds |

**Calculation:**
```
total_seconds = sum(2 for each cached selected product) +
                sum(35 for each uncached selected product)
display = "Est. Research Time: X min, XX sec"
```

**Example:**
- 3 cached selected → Est. Research Time: 00 min, 06 sec
- 2 cached + 1 uncached selected → Est. Research Time: 00 min, 39 sec
- 1 cached + 3 uncached selected → Est. Research Time: 01 min, 47 sec

**Important:** Do not promise "instant" or "<10 seconds" even for all-cached selections. Cached products still require a DB read and page render — show the honest estimate. Consistency of the label matters more than precision.

**Future improvement:** Track actual per-product scoring times in storage. Use a rolling average of recent actuals to replace the 35s constant with a data-driven estimate per product type or category.

```
+------------------------------------------------------------------+
| [Nav — Prospector | Inspector* | Designer]                       |
+------------------------------------------------------------------+
|                                                                  |
|  ← Search Different Company                                      |
|                                                                  |
|  [Company Name]  [Org Badge]    [Run Dossier →]                 |
|  [company description —         [View Previous →]               |
|   two or more lines]            4 of 7 products selected        |
|                                 Est. Research Time: 00 min, 39s |
|                                                                  |
+------------------------------------------------------------------+
|                                              |                   |
|  HIGHLY LIKELY ─────────────────────────    |  AT A GLANCE     |
|  ┌──────────────────────────────────────┐   |  ● Highly Likely N|
|  │ ✓  [Product Name]  [Category] [HL]  │   |  ● Likely        N|
|  └──────────────────────────────────────┘   |  ● Less Likely   N|
|  ┌──────────────────────────────────────┐   |  ● Not Likely    N|
|  │ ✓  [Product Name]  [Category] [HL]  │   |  ──────────────── |
|  └──────────────────────────────────────┘   |  Total           N|
|                                              |                   |
|  LIKELY ────────────────────────────────    |  TRAINING &      |
|  [compact cards...]                          |  CERTIFICATION   |
|                                              |  ● Trellix Edu.. |
|  LESS LIKELY  [grayed if 0 products]        |  ● Trellix Cert..|
|                                              |                   |
|  NOT LIKELY   [grayed if 0 products]        |  COMPETITIVE     |
|                                              |  LANDSCAPE       |
|                                              |  CrowdStrike —   |
|                                              |  Falcon Platform |
|                                              |  Microsoft —     |
|                                              |  Defender/Sentin.|
|                                              |                   |
+------------------------------------------------------------------+
```

### 4.1a Family Picker (Modal — triggers when >15 products discovered)

**Design decisions:**
- Lightbox/modal overlay on top of Home screen (no separate page)
- Simple radio list — one family selection, then Continue
- Optimized for 3–8 families (most common case); supports ~20 with internal scroll (overflow-y: auto on modal body, fixed header + footer)
- No family descriptions, no example products — just name + count
- Claude groups products into families during the discovery phase (see research_storage_improvement_plan.md § Family Grouping)

**Trigger logic:**
- `len(discovery.products) > 15` → Family Picker modal shown before navigating to Caseboard
- `len(discovery.products) <= 15` → navigate directly to Caseboard (no modal)
- Threshold is evaluated in the `/inspector/discover` route after `discover()` returns

**Data flow:**
```
POST /inspector/discover
  → discover() returns discovery dict with discovery.products (full list)
  → if len(products) > 15:
        discovery.product_families = [{ name, product_count, product_keys }]
        render home.html with modal visible + families data
  → else:
        redirect to /inspector/caseboard/<discovery_id>

User selects family → POST /inspector/caseboard/<discovery_id>?family=<family_name>
  → load_discovery(discovery_id)
  → filter discovery.products to only products in selected family
  → render caseboard.html with filtered product set
```

**Family data structure** (set by Claude during discovery, stored on discovery dict):
```json
"product_families": [
  { "name": "Cloud Infrastructure (OCI)", "product_count": 42, "product_keys": ["Oracle Compute", "Object Storage", ...] },
  { "name": "Database & Data Platform",   "product_count": 31, "product_keys": ["Oracle Database 23ai", ...] }
]
```

**Selection counter state machine (Caseboard — max 6 products):**

| State | Counter display | Card behavior |
|---|---|---|
| 0 selected | "0 of N products selected" (gray) | All selectable |
| 1–5 selected | "N of N products selected" (orange) | All selectable |
| 6 selected (limit) | "6 of 6 — uncheck one to swap" (orange) | Unselected cards dim, click does nothing |
| Back to <6 | Returns to normal "N of N products selected" | All cards selectable again |

Run Dossier button: disabled when 0 selected, enabled at 1+.

**Real-world validation — Oracle:**
Oracle has ~258 discoverable products that cleanly group into 7 families:
1. Cloud Infrastructure (OCI)
2. Database & Data Platform
3. Cloud ERP & Finance
4. Human Capital Management
5. Supply Chain & Manufacturing (SCM)
6. Customer Experience (CX)
7. Industry, Specialized & Legacy ← known catch-all (NetSuite, Oracle Health, PeopleSoft, JD Edwards, E-Business Suite, 13+ industry verticals)

Families 1–6 are crisp with clear boundaries. Family 7 is a deliberate catch-all; disambiguation happens at the Caseboard level. Three genuinely ambiguous products (Autonomous Database, Oracle Analytics Cloud, Oracle Middleware/Java) — Claude should resolve by primary use case, not secondary bundle.

```
+------------------------------------------------------------------+
|  [Home screen dimmed behind]                                     |
|  ┌────────────────────────────────────────────┐                 |
|  │  Oracle — 258 products found               │                 |
|  │  Select a product family to continue       │                 |
|  │  ─────────────────────────────────────     │                 |
|  │  [scrollable if >8 families]               │                 |
|  │  ○ Cloud Infrastructure (OCI)  42 products │                 |
|  │  ○ Database & Data Platform    31 products │                 |
|  │  ○ Cloud ERP & Finance         28 products │                 |
|  │  ○ Human Capital Management    19 products │                 |
|  │  ○ Supply Chain & Mfg (SCM)    22 products │                 |
|  │  ○ Customer Experience (CX)    18 products │                 |
|  │  ○ Industry, Specialized &     98 products │                 |
|  │    Legacy                                  │                 |
|  │  ─────────────────────────────────────     │                 |
|  │              [Continue →]                  │                 |
|  └────────────────────────────────────────────┘                 |
+------------------------------------------------------------------+
```
+------------------------------------------------------------------+
|  [sticky footer]  N/6 selected  [hint text]  [Run Dossier →]   |
+------------------------------------------------------------------+
```

### 4.2 Dossier Layout (Revised)

**Design decisions:**
- No box around the hero — open layout, two columns
- Hero left: composite score + verdict + ONE most consequential badge from each dimension (any color — most important signal wins, not most positive)
- Hero right: Estimated Annual Contract Value (right-aligned) + "Est. based on N of N products"
- Four dimension boxes below hero — each shows ALL badges for that dimension in color order (✅ first, ⚠️ second, 🚫 last)
- Dimension boxes are the "more context below" — hero badge click-through jumps to corresponding dimension box
- Next Steps: full-width below the four boxes — two sections: WHAT TO LEAD WITH + PREPARE FOR THESE RISKS
- Products section: per-product collapsible rows below Next Steps — SE/SC depth
- Progress bars removed — dimension score number is sufficient
- Good Points / Risks sections removed from product card — covered by Zone 1 dimension boxes
- Contacts removed from product card
- Delivery path shown as plain label (specific canonical method name) not a colored badge
- Potential Labs moved inside Instructional Value section of product card
- Potential Labs: 2-column grid, two lines per card, compelling action-oriented names

**Hero badge selection logic:**
The single badge shown per dimension in the hero is the most consequential signal — not necessarily the most positive. A 🚫 blocker surfaces in the hero over a ✅ strength. Priority: 🚫 blockers first, then ⚠️ cautions, then ✅ strengths. Within each color, pick the badge with the highest scoring impact.

**Delivery path label:**
Nine canonical methods only — Hyper-V, ESX, Container, Azure VM, AWS VM, Azure Cloud Slice, AWS Cloud Slice, Custom API/BYOC, Simulation. "Standard VM" is retired. Shown as plain text label on collapsed product row and inside Product Labability section. Not a colored badge.

**Next Steps structure:**
Two named sections within Next Steps:
1. WHAT TO LEAD WITH — most compelling strengths ranked and framed in seller language; conversation anchors, not feature bullets
2. PREPARE FOR THESE RISKS — specific prep for each blocker/caution; what it means in a customer conversation, what question it triggers, how SE should be ready to answer

**Product card — dimension section structure:**
Each dimension shows: score (e.g. 36 /40) → delivery path line (Product Labability only) → summary sentence → component subsections → each component has its own header and evidence bullets in **Bold Label | Qualifier:** format → RECOMMENDATIONS subsection at end of dimension

**Potential Labs — placement and format:**
Lives inside Instructional Value, after Mastery Matters component. Two-column grid. Each card: line 1 = compelling action-oriented name, line 2 = two-line scenario description (punchy, present tense, stakes clear). Max two lines total per card.

```
+------------------------------------------------------------------+
| [Nav — Prospector | Inspector* | Designer]                       |
+------------------------------------------------------------------+
| ← Back to Caseboard    Analyzed 2026-04-03 · 4 scored           |
| DOSSIER · SELLER & SE ACTION PLAN                                |
+------------------------------------------------------------------+
|                                                                  |
|  [Company Name]  [Org Badge]                                     |
|  [company description]                                           |
|                                                                  |
|  93  STRONG FIT                    ESTIMATED ANNUAL CONTRACT     |
|      [Top Labability badge  ✅]               VALUE             |
|      [Top Instructional badge ✅]    $166,752 – $412,248        |
|      [Top Org Readiness badge ⚠️]                               |
|      [Top Market badge      ✅]   Est. based on 4 of 10 products|
|                                                                  |
+------------------------------------------------------------------+
|  PRODUCT LABABILITY    |  INSTRUCTIONAL VALUE                    |
|  [Lifecycle APIs   ✅] |  [Workflow Complexity   ✅]            |
|  [Learner Isolation✅] |  [Certification Program ✅]            |
|  [Long Provisioning⚠️] |  [High-Stakes Skills    ✅]            |
|  [Anti-Automation  🚫] |  [Adoption & TTV Risk   ⚠️]            |
+------------------------------------------------------------------+
|  ORGANIZATIONAL READINESS |  MARKET READINESS                    |
|  [Dedicated Content ✅]   |  [↑ Growing        ✅]              |
|  [ATP Program       ✅]   |  [Global           ✅]              |
|  [Instruqt          ⚠️]   |  [~2M Annual Users ✅]              |
|  [LMS / LXP         ✅]   |  [Strategic GSIs   ✅]              |
+------------------------------------------------------------------+
|  NEXT STEPS                                                      |
|                                                                  |
|  WHAT TO LEAD WITH                                               |
|  • Certification is your opener — five active role-based certs  |
|    via Certiverse map directly to Skillable's PBT format.       |
|  • Expansion, not displacement — active Skillable customer.     |
|  • Clean VM story — MSI install, full CLI scoring surface.      |
|                                                                  |
|  PREPARE FOR THESE RISKS                                         |
|  • Long Provisioning — confirm with SE whether NFR/Community    |
|    Edition can be pre-activated in Hyper-V image before first   |
|    meeting. Pre-instancing may be required.                      |
|  • Studio Web dependency — don't promise single VM covers all   |
|    three products unless SE confirms hybrid approach.            |
+------------------------------------------------------------------+
|  PRODUCTS ───────────────────────────────────────────────────   |
|                                                                  |
|  [Product]  [Lab Highlight]           [STRONG FIT]  Hyper-V  93▼|
|  Category                                                        |
|  +----------------------------------------------------------+   |
|  | CONSUMPTION ESTIMATE                                     |   |
|  | MOTION         | POP    | ADOPT | HRS  | EST. HOURS      |   |
|  | Cust Onboard.  | 8K-12K |  3%   | 2-4h | 480–1,440      |   |
|  | Channel Enabmt | 500-800|  8%   | 3-5h | 120–320         |   |
|  | Annual Potential                      $33,264–$92,040    |   |
|  | [methodology note — italic gray]                          |   |
|  |                                                           |   |
|  | PRODUCT LABABILITY  36 /40                                |   |
|  | Hyper-V · Skillable Datacenter                           |   |
|  | Strong technical fit — ready to build                    |   |
|  |                                                           |   |
|  |   PROVISIONING                                           |   |
|  |   • Runs in Hyper-V | Strength: ...                     |   |
|  |   • Windows MSI Install | Strength: ...                 |   |
|  |   • Learner Isolation | Strength: ...                   |   |
|  |                                                           |   |
|  |   LICENSING & ACCOUNTS                                   |   |
|  |   • NFR License Path | Strength: ...                    |   |
|  |   • Anti-Automation Controls | Caution: ...             |   |
|  |                                                           |   |
|  |   SCORING                                                |   |
|  |   • Script Scorable | Strength: ...                     |   |
|  |   • Scoring APIs | Strength: ...                        |   |
|  |                                                           |   |
|  |   TEARDOWN                                               |   |
|  |   • Teardown APIs | Strength: ...                       |   |
|  |                                                           |   |
|  |   RECOMMENDATIONS                                        |   |
|  |   • Delivery Path: Hyper-V — [what + why]               |   |
|  |   • Scoring Approach: uipathcli — [what + why]          |   |
|  |                                                           |   |
|  | INSTRUCTIONAL VALUE  28 /30                               |   |
|  |                                                           |   |
|  |   DIFFICULT TO MASTER                                    |   |
|  |   • Workflow Complexity | Strength: ...                  |   |
|  |   • Configuration Complexity | Strength: ...            |   |
|  |                                                           |   |
|  |   MASTERY MATTERS                                        |   |
|  |   • Certification Program | Strength: ...               |   |
|  |   • High-Stakes Skills | Strength: ...                  |   |
|  |                                                           |   |
|  |   POTENTIAL LABS                                         |   |
|  |   +──────────────────────┐ ┌──────────────────────+     |   |
|  |   │ Break the Bot        │ │ Zero to Orchestrator  │     |   |
|  |   │ Debug a failing job  │ │ Deploy and run your   │     |   |
|  |   │ before it hits prod  │ │ first attended robot  │     |   |
|  |   +──────────────────────┘ └──────────────────────+     |   |
|  |                                                           |   |
|  |   RECOMMENDATIONS                                        |   |
|  |   • Program Fit: [what + why]                            |   |
|  |                                                           |   |
|  | ORGANIZATIONAL READINESS  19 /20                          |   |
|  |                                                           |   |
|  |   CONTENT DEVELOPMENT                                    |   |
|  |   • Dedicated Content Dept | Strength: ...              |   |
|  |                                                           |   |
|  |   CONTENT DELIVERY ECOSYSTEM                             |   |
|  |   • ATP / Learning Program | Strength: ...              |   |
|  |   • Instruqt | Caution: ...                             |   |
|  |                                                           |   |
|  | MARKET READINESS  10 /10                                  |   |
|  |                                                           |   |
|  |   PRODUCT POPULARITY                                     |   |
|  |   • ↑ Growing | Strength: ...                           |   |
|  |   • Global | Strength: ...                              |   |
|  +----------------------------------------------------------+   |
+------------------------------------------------------------------+
```
|  | • **Scoring Approach:** [what + why]                     |   |
|  |                                                           |   |
|  | INSTRUCTIONAL VALUE  28/30                                |   |
|  | 28 /30  ███████████████████░░░                           |   |
|  | • **Workflow Depth | Strength:** ...                     |   |
|  | • **Certification Program | Strength:** ...              |   |
|  |                                                           |   |
|  | ORGANIZATIONAL READINESS  19/20                           |   |
|  | • **Dedicated Content Dept | Strength:** ...             |   |
|  | • **Instruqt | Caution:** ...                            |   |
|  |                                                           |   |
|  | MARKET READINESS  10/10                                   |   |
|  | • **↑ Growing | Strength:** ...                          |   |
|  |                                                           |   |
|  | POTENTIAL LABS                                            |   |
|  | +--------------------+  +--------------------+           |   |
|  | | Build REFramework  |  | Use Autopilot in   |           |   |
|  | | automation — conf..|  | Studio Web to gen..|           |   |
|  | +--------------------+  +--------------------+           |   |
|  +----------------------------------------------------------+   |
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
