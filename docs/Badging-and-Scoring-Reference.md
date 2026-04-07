# Skillable Intelligence — Badging and Scoring Reference

This document is the operational reference for all badge names, color criteria, scoring signals, point values, and display standards across Skillable Intelligence tools. It implements the strategic framework defined in **Platform-Foundation.md**, which is the authoritative source for Pillar definitions, Guiding Principles, and platform architecture.

This document also serves as the **in-app explainability layer** (GP3). Each section can be linked from the UX so users can see exactly how any part of the framework works — one source of truth, one click, digestible.

This document reflects best current thinking. As thinking evolves, this document evolves with it — fully synthesized, never appended.

---

## Scoring Hierarchy

- **Fit Score** — composite of three Pillars
  - **Pillars** — weighted components (Product Labability 40%, Instructional Value 30%, Customer Fit 30%)
    - **Dimensions** — four specific areas within each Pillar. Dimension weights within a Pillar always add up to 100 (e.g., Provisioning 35 + Lab Access 25 + Scoring 15 + Teardown 25 = 100).
      - **Requirements** — what the AI researches and evaluates; surface as badges in the UX

Each Pillar scores out of 100 internally (the sum of its dimension scores), then gets weighted to its share of the Fit Score. A Product Labability score of 85/100 contributes 85 x 0.40 = 34 points to the Fit Score.

**The 70/30 Split:** 70% of the Fit Score is about the product (Product Labability + Instructional Value). 30% is about the organization (Customer Fit). The product is the center of everything.

---

## Badge System

### Four Badge Colors

| Color | Meaning | Qualifier label |
|---|---|---|
| **Green** | Strength / Opportunity | `| Strength:` or `| Opportunity:` |
| **Gray** | Neutral / Context | `| Context:` |
| **Amber** | Risk / Caution | `| Risk:` |
| **Red** | Blocker | `| Blocker:` |

### Purple Classification Badges

Purple is used for classification, not scoring. Product subcategory badges and company classification badges all render in purple. This provides a consistent visual signal that a badge is categorizing, not assessing.

### Badge Evidence on Hover

Every badge MUST carry an evidence payload — no badge renders without evidence. Hovering over any badge for 1.5 seconds triggers a modal displaying:

- Evidence bullets (specific findings)
- Source (where the evidence came from)
- Confidence level (confirmed, indicated, or inferred)

This is the primary mechanism for GP3 (Explainably Trustworthy) at the badge level.

### Evidence Format

`**[Badge Name] | [Qualifier]:** [Specific finding] — [source title]. [What it means for lab delivery.]`

Badge order within each dimension: Strengths/Opportunities first, then Context, then Risks, then Blockers.

### Evidence Confidence Language

Confidence is core logic in the codebase — every finding carries a confidence level as a stored field. It influences badge color assignment and surfaces in evidence language.

| Level | Meaning | Example |
|---|---|---|
| **Confirmed** | Direct evidence from primary source | "REST API **confirmed** — OpenAPI spec at docs.vendor.com" |
| **Indicated** | Strong indirect evidence | "VM deployment **indicated** — installation guide references Windows Server" |
| **Inferred** | AI assumption from patterns or limited signals | "Troubleshooting lab potential **inferred** from category norms" |

For high-risk areas (contacts, consumption estimates): rationale must be explicit ("Estimated based on..." or "Contact identified from LinkedIn search results — may be out of date").

### Badge Naming Principles

- Name the **solution**, not the problem, when the recommendation is clear
- Use variable-driven badge text when the specific finding IS the answer (LMS name, competitor name, user count, region)
- If green and unremarkable, don't surface — only show what matters
- No dimension should need more than three to five badges — detail belongs in evidence bullets
- Keep badge text short — clear and concise above all

### Badge Display by Tool

| Tool | What appears |
|---|---|
| **Prospector** | Color + HubSpot ICP Context (1-2 sentence synthesis — why this score) |
| **Inspector Caseboard** | Color + badge name (no rationale) |
| **Inspector Dossier hero** | Color + badge name; hover for evidence (1.5s delay modal) |
| **Inspector Dossier drill-down** | Full evidence bullet with source and rationale |
| **Designer** | Green signals become program design inputs; badges not shown |

**HubSpot Integration** (data sent, not UX controlled): Fit Score, ACV Potential, HubSpot ICP Context, key badges, product list, contacts. HubSpot ICP Context is regenerated from best current intelligence every time data is sent (GP5).

---

## Two Hero Metrics

| Metric | What it answers | How it's determined |
|---|---|---|
| **Fit Score** | Should we pursue this? | Composite of three Pillars |
| **ACV Potential** | How big is this if we win? | Calculated: population x adoption x hours x rate |

ACV values use lowercase k for thousands and uppercase M for millions (e.g., 250k, 1.2M).

### Verdict Grid

The verdict combines Fit Score and ACV Potential into a single action-oriented label. It tells the seller what the opportunity looks like and what action makes sense — without predicting customer behavior or dictating effort.

**Score color spectrum:**

| Score range | Color |
|---|---|
| >=80 | Dark Green |
| 65-79 | Green |
| 45-64 | Light Amber |
| 25-44 | Amber |
| <25 | Red |

**ACV tiers:** High, Medium, Low.

**Verdict grid:**

| Score | High ACV | Medium ACV | Low ACV |
|:---:|:---:|:---:|:---:|
| **>=80** | Prime Target | Strong Prospect | Good Fit |
| | Dark Green | Dark Green | Dark Green |
| **65-79** | High Potential | Worth Pursuing | Solid Prospect |
| | Green | Green | Green |
| **45-64** | High Potential | Worth Pursuing | Solid Prospect |
| | Light Amber | Light Amber | Light Amber |
| **25-44** | Assess First | Keep Watch | Deprioritize |
| | Amber | Amber | Amber |
| **<25** | Keep Watch | Poor Fit | Poor Fit |
| | Red | Red | Red |

**Verdict definitions:**

| Verdict | What it communicates |
|---|---|
| **Prime Target** | Best possible combination. Build a strategy, align the team. |
| **Strong Prospect** | Great fit, meaningful opportunity. Pursue with confidence. |
| **Good Fit** | The fit is real. Worth your time. |
| **High Potential** | Gaps to work through but significant upside justifies the investment. |
| **Worth Pursuing** | Good fundamentals all around. Give it attention. |
| **Solid Prospect** | Decent fit, modest opportunity. Steady. |
| **Assess First** | Low fit today, but the opportunity is big. Do the homework before deciding. |
| **Keep Watch** | Not ready today. Opportunity is big enough to stay close and revisit when conditions change. |
| **Deprioritize** | Low fit, small opportunity. Focus elsewhere. |
| **Poor Fit** | Products don't align. Be honest about it. |

---

## Discovery-Stage Badges

These appear on the Caseboard after discovery research, before the full scoring run. They give early context, not scores.

### Company Classification

Displayed as a **purple badge** in the page header, right of company name. All labels uppercase. Purple signals classification, not assessment.

**Software companies:** Format is `{CATEGORY} SOFTWARE`

| Rule | Display | Example |
|---|---|---|
| Products span 3+ categories | **ENTERPRISE SOFTWARE** | Microsoft |
| Products span 1-2 categories | **{CATEGORY} SOFTWARE** | Trellix -> CYBERSECURITY SOFTWARE |

**All other organization types:**

| Data value | Display |
|---|---|
| `training_organization` | **TRAINING ORG** |
| `academic_institution` | **ACADEMIC** |
| `systems_integrator` | **SYSTEMS INTEGRATOR** |
| `technology_distributor` | **TECH DISTRIBUTOR** |
| `professional_services` | **PROFESSIONAL SERVICES** |
| `content_development` | **CONTENT DEVELOPMENT** |
| `lms_company` | **LMS PROVIDER** |

### Product Subcategory

Displayed as a **purple badge** on each product row — consistent color for all classification badges. AI-generated during discovery.

| Top-Level Category | Subcategory examples |
|---|---|
| Cybersecurity | Endpoint Protection, Detection & Response, Data Protection, Network Security, Email Security, Threat Intelligence, SIEM/SOAR, Identity & Access |
| Cloud Infrastructure | Compute, Networking, Storage, Containers & Kubernetes, Serverless, Database, Identity & Access |
| Data Protection | Backup & Recovery, Disaster Recovery, Data Management, Archive & Compliance |
| DevOps | CI/CD, Infrastructure as Code, Monitoring & Observability, Configuration Management |
| ERP/CRM | Financial Management, HR & HCM, Supply Chain, Sales & Marketing, Customer Service |

### Deployment Model

| Data Value | Display | Color | Description |
|---|---|---|---|
| `installable` | **Installable** | Green (muted) | Downloadable installer, container image, or VM image |
| `hybrid` | **Hybrid** | Gray | Available as both installable and cloud/SaaS |
| `cloud` | **Cloud-Native** | Green (muted) | Deployed on customer-controlled cloud infrastructure |
| `saas-only` | **SaaS-Only** | Amber | Vendor-managed only — learner isolation and API questions ahead |

---

## Pillar 1 — Product Labability (40%)

*How labable is this product? Can Skillable deliver a complete lab lifecycle?*

The gatekeeper. If this fails, nothing else matters. Provisioning determines difficulty for everything else — when a product runs in Skillable's infrastructure (VM, container, Cloud Slice), the other dimensions are largely within Skillable's control. When a product runs in the vendor's own cloud, every dimension depends on the vendor's APIs.

| Dimension | Weight | Question |
|---|---|---|
| PROVISIONING | 35 | How do we get this product into Skillable? |
| LAB ACCESS | 25 | Can we get people in with their own identity, reliably, at scale? |
| SCORING | 15 | Can we assess what they did, and how granularly? |
| TEARDOWN | 25 | Can we clean it up when it's over? |

### Meta-Principle for Pillar 1 Badging

**Badge name = canonical vocabulary entry. Product-specific details (vendor names, REST API URLs, license terms, install paths) live in the evidence payload on hover, NEVER in the badge name itself.**

Universal rules that apply to every Pillar 1 dimension:

| Rule | What it means |
|---|---|
| **No product names in badge names** | `ePO Admin Credential` → wrong. `Cred Recycling` → right (with ePO details in evidence). |
| **No topic labels as badge names** | `Deployment Model`, `REST API Surface` → wrong. The badge is the *finding*, not the *category*. |
| **No invented badge names** | Stay strictly within the canonical vocabulary listed below. |
| **No positive canonical for negative finding** | `Runs in Azure \| Risk: No Marketplace Listing` is a polarity error. Negative findings need negative-named badges. |
| **One badge per finding — never duplicate canonical names** | Two distinct findings about the same topic use two distinct canonicals (e.g., `Runs in Hyper-V` + `Pre-Instancing` for "clean install + slow init"). Same name twice is never the answer. |
| **Flat-tier scoring** | No `Hyper-V: Standard` / `Moderate` / `Weak` modifiers. Each canonical earns its full base credit when emitted green. Friction is expressed via separate friction badges. |

### 1.1 Provisioning (35 pts)

*How do we get this product into Skillable?*

#### Path Priority Order

Walk in sequence. The priority IS the score order — pick the FIRST viable path, not the highest-scoring.

| Priority | Path | When | Canonical |
|---|---|---|---|
| 1 | **VM fabric** | Installable on Windows / Linux | `Runs in Hyper-V` (default), `Runs in Container` (singular), `ESX Required` (4-pt discount) |
| 2 | **Cloud Slice fabric** | Product IS an Azure or AWS native managed service | `Runs in Azure` or `Runs in AWS` |
| 3 | **Sandbox API** (Custom API / BYOC) | SaaS but vendor exposes provisioning API for per-learner environments | `Sandbox API` (green) |
| 4 | **Simulation** | Nothing else viable. NOT a fallback — a real fabric. | `Simulation` (gray Context, base credit) |

**Cloud disambiguation:** `Runs in Azure` / `Runs in AWS` mean the product IS that cloud's native managed service, NOT "hostable on a VM in that cloud." For installable products that happen to run on cloud VMs, use `Runs in Hyper-V`.

**Cloud preference:** When a product runs natively on Azure AND AWS, detect vendor preference signals (marketing emphasis, docs priority, partnerships). When no preference signal exists, default to Azure.

**Native fabric beats manual API wiring.** A SaaS product native to Azure or AWS uses Cloud Slice (Path 2), not Sandbox API (Path 3) — even if both are technically viable.

#### Provisioning Canonical Badges

| Badge | Green | Amber | Red |
|---|---|---|---|
| **Runs in Hyper-V** | Clean VM install confirmed | Installs with complexity | — |
| **Runs in Azure** | Azure-native managed service | Azure path with friction | — |
| **Runs in AWS** | AWS-native managed service | AWS path with friction | — |
| **Runs in Container** (singular) | Container-native confirmed, no disqualifiers | Image exists but disqualifiers OR research uncertain | — |
| **ESX Required** | — | Nested virt or socket licensing forces ESX (details in evidence) | — |
| **Simulation** | — | — (gray Context when chosen path) | — |
| **Sandbox API** (gatekeeper) | Vendor has rich provisioning / sandbox / management API for per-learner environments | API exists but coverage uncertain or partial | No provisioning API confirmed |
| **Pre-Instancing** | Slow first-launch mitigated by Skillable Pre-Instancing — feature opportunity | — | — |
| **Multi-VM Lab** | Multiple VMs working together — Skillable strength | — | — |
| **Complex Topology** | Real network complexity (routers / switches / firewalls / segmentation) — networking AND cybersecurity | — | — |
| **Large Lab** | Single environment with big footprint (RAM, CPU, GPU, datasets) | — | — |
| **GPU Required** | — | Forces cloud VM with GPU instance — slower, more expensive | — |
| **Bare Metal Required** | — | — | Physical hardware required |
| **No Deployment Method** | — | — | Ultimate dead end — neither real provisioning NOR Simulation viable |
| **Requires GCP** | — | No native Skillable GCP path | — |

**Flat-tier scoring:** each canonical badge earns its full base credit when emitted green. The math layer is color-aware — amber gives half credit, red falls back to color points (negative).

| Canonical | Green base credit |
|---|---|
| `Runs in Hyper-V`, `Runs in Azure`, `Runs in AWS`, `Runs in Container` | +30 |
| `ESX Required` | +26 (4-pt discount for Broadcom licensing operational cost) |
| `Sandbox API` | +22 |
| `Simulation` | +12 |
| `Multi-VM Lab`, `Complex Topology`, `Large Lab`, `Pre-Instancing` | +0 (drives ACV rate tier upward) |

**Mutually exclusive:** `Multi-VM Lab` and `Large Lab` describe overlapping ideas — pick whichever better describes the primary nature of the scale, not both. Max 2 of the three strength badges (`Multi-VM Lab`, `Complex Topology`, `Large Lab`) per product.

#### Provisioning Friction Penalties

| Penalty | Deduction |
|---|---|
| `GPU Required` | -5 |
| `Socket licensing (ESX) >24 vCPUs` | -2 (surfaces as evidence on the `ESX Required` badge) |

Penalties retired in the 2026-04-06 sharpening: `GUI-only setup` (once the image is built, the learner doesn't experience the GUI install — not friction worth surfacing), `Provisioning time over 30 min` (replaced by the green `Pre-Instancing` opportunity badge), `No NFR / dev license` (moved to Lab Access via `Training License`).

#### Ceiling Flags (Provisioning)

| Flag | Effect |
|---|---|
| `bare_metal_required` | Hard cap: Product Labability ≤ 5 |
| `no_api_automation` | Hard cap: Product Labability ≤ 5 |
| `saas_only` | Classification metadata only — does NOT cap. The `Sandbox API` canonical badge (red) drives any actual cap. |
| `multi_tenant_only` | Classification metadata only — does NOT cap. |

---

### 1.2 Lab Access (25 pts)

*Can we get people in with their own identity, reliably, at scale?*

#### Lab Access Canonical Badges

| Badge | Green | Amber | Red |
|---|---|---|---|
| **Full Lifecycle API** | Complete API for user provisioning and management | — | — |
| **Identity API** | Vendor API can create users and assign roles per learner | API exists but coverage uncertain | — |
| **Entra ID SSO** | App pre-configured to use Entra ID tenant — zero credential management. **Azure-native applications only.** Preempts `Identity API` for Azure products. | — | — |
| **Cred Recycling** | Customer credentials can be reset and recycled between learners — low operational overhead | Recycling exists but coverage uncertain | — |
| **Credential Pool** | Pre-provisioned consumable credential pool — operationally painful but works (distinct from `Cred Recycling`) | — | — |
| **Training License** (consolidated) | NFR / training / eval / dev license path confirmed, low friction | License exists with friction (sales call, cost, short trial, enterprise-only) | License is effectively blocked (credit card + high cost + no negotiation path) |
| **Learner Isolation** (gatekeeper, always emit) | Per-user / per-tenant isolation confirmed via API evidence | Research can't confirm either way | Explicitly absent — confirmed shared multi-tenant with no isolation mechanism |
| **Manual SSO** | — | Azure SSO but requires manual learner login (distinct from `Identity API`) | — |
| **MFA Required** | — | — | Multi-factor authentication blocks automated provisioning |
| **Anti-Automation Controls** | — | — | Platform actively blocks automated account creation (CAPTCHA, bot detection) |
| **Rate Limits** | — | — | API rate limits constrain concurrent learner provisioning |

**Training License consolidation note:** The consolidated `Training License` canonical replaces the historical `NFR Accounts Available`, `Trial Account`, `Credit Card Required`, `High License Cost` badges. One canonical, three states, one source of truth.

**Cred Recycling vs Credential Pool:** Two distinct canonicals.
- **`Credential Pool`** = Customer hands over a batch of credentials, we deplete the pool, when we run low we ask for more. Operationally painful.
- **`Cred Recycling`** = Customer hands over one set, we clean up after each learner and put it back in the pool. Self-sustaining.

#### Lab Access Scoring

| Canonical | Green base credit |
|---|---|
| `Full Lifecycle API` | +23 |
| `Entra ID SSO` | +20 |
| `Identity API` | +19 |
| `Cred Recycling` | +18 |
| `Credential Pool`, `Training License` | +16 |
| `Manual SSO` | +12 |
| `MFA Required`, `Rate Limits` (penalties) | -10, -5 |
| `Anti-Automation Controls` | -5 |

#### Lab Access Floor: 0

---

### 1.3 Scoring (15 pts)

*Can we assess what they did, and how granularly?*

| Canonical | Green | Amber | Notes |
|---|---|---|---|
| **Scoring API** | Vendor REST API for state validation — rich coverage | API exists but coverage uncertain or partial | Replaces historical `API Scorable (rich/partial)`. Product-specific REST API details (vendor URLs, OpenAPI specs) live in evidence on hover. |
| **Script Scoring** | PowerShell / CLI / Bash scripts can validate config state comprehensively | Scriptable surface exists but with gaps | Two states (Frank: don't flatten this one). |
| **AI Vision** | GUI-driven product where state is visually evident — AI Vision is the right tool. **Peer to API/Script, NOT a fallback.** | AI Vision usable but visual state ambiguous | Renamed from `AI Vision Scorable`. The "fallback" framing has been retired everywhere. |
| **Simulation Scorable** | — | Simulation environment supports scoring via guided interaction | SE clarification pending: when can/can't we score in a simulation; should this ever be red? |
| **MCQ Scoring** | — | No programmatic surface — knowledge-check questions only | The genuine fallback. Used when no environment state is available to validate. |

#### Scoring Base Credits

| Canonical | Green base credit |
|---|---|
| `Scoring API` | +14 |
| `Script Scoring` | +12 |
| `AI Vision` | +11 |
| `Simulation Scorable` | +8 |
| `MCQ Scoring` | +4 |

**Routing rule for Scoring:** the Scoring dimension is about HOW we assess (API / Script / AI Vision / MCQ). Subject matter / what's being learned (governance, security topics, eDiscovery workflows) belongs in **Instructional Value (Pillar 2)**, NOT Scoring.

#### Management API Decomposition

When research surfaces a vendor "Management API" or "Full Lifecycle API," it decomposes into FOUR dimension-specific badges. Verify each stage's coverage independently — don't assume green across all four from a single signal.

| Stage | Dimension | Badge |
|---|---|---|
| Environment provisioning | Provisioning | `Sandbox API` |
| User / role creation | Lab Access | `Identity API` (or `Entra ID SSO` if Azure-native) |
| State validation | Scoring | `Scoring API` |
| Environment cleanup | Teardown | `Teardown API` |

---

### 1.4 Teardown (25 pts)

*Can we clean it up when it's over?*

For Skillable-hosted labs (Hyper-V / Container / ESX / Simulation), teardown is automatic and scores full marks. Badges only surface when there's a finding.

| Canonical | Green | Amber | Red |
|---|---|---|---|
| **Datacenter** | Skillable hosts the environment (Hyper-V, ESX, Container, OR Simulation) — teardown is automatic via snapshot revert or platform cleanup | — | — |
| **Teardown API** | Vendor API covers environment cleanup and deprovisioning | Some teardown API coverage but gaps remain | — |
| **Manual Teardown** | — | — | No teardown mechanism — manual cleanup required between learners |
| **Orphan Risk** | — | Incomplete teardown may leave orphaned resources / accounts even when API exists | — |

#### Teardown Base Credits

| Canonical | Green base credit |
|---|---|
| `Datacenter` | +25 (full marks) |
| `Teardown API` | +22 |
| `Manual Teardown` | -10 (penalty) |
| `Orphan Risk` | -5 (penalty) |

**Datacenter rule:** fires green for ANY Skillable-hosted path including Simulation. Simulation runs in our infra so teardown is automatic there too.

**Distinct from Manual Teardown:** `Orphan Risk` fires alongside `Teardown API` amber when there's API coverage but with gaps that could leave residue. Both can fire on the same product.

#### Teardown Floor: 0

### Risk Cap Reduction (applies to ALL Pillar 1 dimensions)

A Pillar 1 dimension can never be at full cap when there's a known risk badge. Even if the green canonical badges overflow the cap, an amber Risk or red Blocker visibly reduces the dimension score so the user sees the friction. **Per Frank's directive 2026-04-07** after reviewing Trellix Endpoint Security · Lab Access at 25/25 with a Training License Risk badge — the perfect score hid a real concern.

| Risk type | Cap reduction per badge | Rationale |
|---|---|---|
| **Amber Risk** | **-3 from cap** | "Strong with friction to manage." A dimension with one amber risk still reads well above 50%. |
| **Red Blocker** | **-8 from cap** | "Must be resolved before we can ship." A dimension with one red lands in mid-amber verdict territory — can't be ignored. |

**How it works:**
1. Compute `raw_total` normally (canonical signals + penalties + color contributions). Amber half-credit and red color-fallback already apply at this stage.
2. Count visible risk badges in the dimension: `amber_count` (badges with color amber), `red_count` (badges with color red).
3. Compute the knockdown: `(amber_count × 3) + (red_count × 8)`.
4. `effective_cap = max(dim.weight - knockdown, dim.floor or 0)`.
5. `score = min(raw_total, effective_cap)`.

**This is a CAP REDUCTION, not a deduction.** If `raw_total` is already below the lowered cap, the knockdown has no further effect — there's no double-counting with the half-credit and color-fallback rules that apply at the raw stage.

**Linear compounding.** Each risk knocks more off. Two ambers = -6, three reds = -24. Hard floor at the dimension's existing floor (0 for most) prevents pathological negatives.

**Worked example — Trellix Endpoint Security · Lab Access:**

| Badge | Color | Math credit |
|---|---|---|
| Identity API | green | +19 (full canonical credit) |
| Cred Recycling | green | +18 (full canonical credit) |
| Training License | amber | +8 (half-credit per amber rule) |
| **Raw total** | | **45** |
| Original cap | | 25 |
| Risk knockdown | | -3 (one amber) |
| **Effective cap** | | **22** |
| **Score** | | **22/25** |

Without the risk cap reduction, the score would be capped at 25/25 and the Training License Risk badge would have no visible impact. With the rule, the dimension reads "strong but with one risk to manage" — accurate.

**Does NOT apply to the rubric model (Pillar 2 / Pillar 3).** Strength tiers (`strong` / `moderate` / `weak`) already encode friction in the rubric model. Adding a cap reduction there would double-count what the strength grading already captures.

### Technical Fit Multiplier

Applied after scoring Product Labability:

| Product Labability Score | Method | Multiplier |
|---|---|---|
| >=32 | Any | 1.0x |
| 24-31 | Datacenter | 1.0x |
| 19-31 | Non-datacenter | 0.75x |
| 10-18 | Any | 0.40x |
| 0-9 | Any | 0.15x |

---

## Two Architectures Across Pillars — read this first

The three Pillars use **two different scoring architectures** because the three Pillars measure fundamentally different kinds of things. This is intentional. Future maintainers: do not collapse them into one model.

| Pillar | Nature | Architecture | Why |
|---|---|---|---|
| **1 — Product Labability** | Technical fact-finding. Hyper-V either supports the install or it doesn't. APIs exist or they don't. **Concrete and binary.** | **Canonical model.** Fixed badge vocabulary. Math credits points by name-matched signal lookup. Color-aware (green = full, amber = half, red = color fallback). | The technical fabric concepts are universal — `Runs in Hyper-V`, `Sandbox API`, `Datacenter` mean the same thing across every product. Canonical names work cleanly. |
| **2 — Instructional Value** | Domain-specific judgment. Subject matter complexity for legal, cybersecurity, banking, healthcare etc. is genuinely different. **Subjective and contextual.** | **Rubric model.** Variable, AI-synthesized badge names. Math credits points by `(dimension, strength)` lookup against a per-dimension rubric. Each badge carries a `signal_category` tag for cross-product analytics. | Forcing canonical names here loses the domain-specific terminology that makes badges useful to the seller. The rubric grades evidence strength so the math is still deterministic. |
| **3 — Customer Fit** | Organizational pattern recognition. Mostly universal concepts but the specific evidence varies (counts, platforms, conferences). **Mostly universal, somewhat interpretive.** | **Rubric model.** Same as Pillar 2. Variable badge names with concrete data + rubric grading. | Per-product specifics like `~500 ATPs` or `Skillable` or `Cohesity Connect 5K` are exactly what makes the chip useful — generic names like `Partner Ecosystem` are abstract. Rubric handles the strength grading. |

**The two-architecture decision was made deliberately on 2026-04-06** after walking the Pillar 1 implementation and discovering that the same approach didn't fit Pillars 2 and 3. See decision log for the full rationale.

---

## Pillar 2 — Instructional Value (30%)

*Does this product have instructional value for hands-on training?*

The commercial case. Measures whether this product genuinely warrants hands-on lab experiences. Combined with Product Labability, these two product-level pillars represent 70% of the Fit Score.

Pillar 2 uses the **rubric model**. Each badge the AI emits carries:
- `name` — variable, AI-synthesized, domain-specific (the visible chip)
- `strength` — `strong` / `moderate` / `weak` — REQUIRED, drives the math
- `signal_category` — one of the dimension's fixed category list — REQUIRED, hidden, for analytics
- `color` — green / amber / red (mirrors strength; red is reserved for hard negatives only)
- `evidence` — sentence-level context (existing field, hover popover)

| Dimension | Weight | Question |
|---|---|---|
| PRODUCT COMPLEXITY | 40 | Is this product hard enough to require hands-on practice? |
| MASTERY STAKES | 25 | How much does competence matter? |
| LAB VERSATILITY | 15 | What kinds of hands-on experiences can we build? |
| MARKET DEMAND | 20 | Does the broader market validate the need? |

### 2.1 Product Complexity (cap 40)

*Is this product hard enough to require hands-on practice?*

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +6 | Deep multi-system, multi-phase workflows; multiple distinct admin/operator roles; rich troubleshooting paths; OR genuine AI requiring iterative practice |
| **moderate** | +3 | Some depth or some complexity but limited scope — single-phase, narrow role set, light troubleshooting |
| **weak** | don't emit | Thin documentation, mostly straightforward, single-stage workflow |

**signal_category list** (the AI picks ONE per badge): `deep_configuration` · `multi_phase_workflow` · `role_diversity` · `troubleshooting_depth` · `complex_networking` · `integration_complexity` · `ai_practice_required` · `consumer_grade` (red) · `simple_ux` (red)

**Hard negatives (red — fall back to color points):** `Consumer Grade` · `Simple UX` — fire only when the product is genuinely too trivial for labs.

**Typical spread:** 6 strong = 36/40. Moderate complexity → 3-5 moderate → 9-15.

---

### 2.2 Mastery Stakes (cap 25)

*How much does competence matter? What happens if they get it wrong?*

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +9 | Misconfiguration causes breach, data loss, compliance failure, sanctions, malpractice, downtime — real and consequential harm |
| **moderate** | +5 | Errors are visible and create rework / reputation cost but are recoverable |
| **weak** | don't emit | Mostly inconvenience — easily fixed, no lasting consequences |

**signal_category list:** `harm_severity` · `learning_curve` · `adoption_risk` · `compliance_consequences`

**Typical spread:** 3 strong = 27 → capped at 25 (max). 2 strong + 1 moderate = 23. Mostly moderate = 10.

---

### 2.3 Lab Versatility (cap 15)

*What kinds of high-value, hands-on experiences can we build for this product?*

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +5 | Clear high-value lab type fits naturally — Cyber Range, Red vs Blue, Performance Tuning, Migration Lab, Compliance Audit, Incident Response, etc. |
| **moderate** | +3 | Lab type is adaptable to the product but requires some shoehorning |
| **weak** | don't emit | Lab type doesn't fit — most simple products get nothing in this dimension |

**signal_category list:** `adversarial_scenario` · `incident_response` · `break_fix` · `team_handoff` · `cyber_range` · `performance_tuning` · `migration_lab` · `architecture_challenge` · `compliance_audit` · `disaster_recovery` · `bug_bounty`

**Typical spread:** 3 strong = 15 (max). Most products get 1-2 entries. Dual purpose: conversational competence in Inspector, program recommendations in Designer.

---

### 2.4 Market Demand (cap 20)

*Does the broader market validate the need for hands-on training on this product?*

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +5 | Clear scale signal — large install base, active certification ecosystem, AI platform, enterprise validation at scale, high-demand category, IPO/major funding |
| **moderate** | +3 | Moderate signal — growing category, mid-size install base, emerging certification, regional presence |
| **weak** | don't emit | Thin signal — small install base, niche category, no certification |

**signal_category list:** `install_base_scale` · `geographic_reach` · `cert_ecosystem` · `funding_growth` · `category_demand` · `competitor_labs` · `ai_signal` · `enterprise_validation`

**Variable badge name examples:** `~2M Users` · `Series D $200M` · `IPO 2024` · `Cisco Live 30K` · `Active Cert Exam` · `~500 ATPs` · `Global` · `AI Platform` · `Fortune 100 Clients`

**Typical spread:** 4 strong = 20 (max). Mostly moderate = 9-12.

---

## Variable badge name rules (Pillar 2)

| Rule | |
|---|---|
| **2-3 words preferred, 4 words absolute max** | Only 4 if every word is short |
| **Use abbreviations and numerals aggressively** | `Cert` (not Certification), `Config` (not Configuration), `Admin` (not Administrator), `Ops` (not Operations), `Dev` (not Development), `Auth` (not Authentication), `Docs`, `Repo`, `Perf`, `Env`, `Prod`, `App` |
| **Standard industry acronyms — never spell out** | API, CLI, GUI, AI, MFA, NFR, ATP, LMS, RBAC, IDP, IPO, PBT, MCQ, SSO |
| **Subject matter terminology is encouraged** | The whole point of Pillar 2 variable names is to capture domain-specific concepts — `Outside Counsel Dependency`, `Lateral Movement Detection`, `Settlement Reconciliation` |
| **NO product names of the company being scored** | The dossier header has the company name — don't repeat it in badges |

---

## Pillar 3 — Customer Fit (30%)

*Is this organization a good match for Skillable?*

Everything about the organization in one Pillar. Combines training commitment, build capacity, delivery capacity, and organizational DNA. 30% of the Fit Score — meaningful but never overriding the product truth.

Pillar 3 uses the **rubric model**, same architecture as Pillar 2.

### Customer Fit is the same for every product in a company

**Customer Fit measures the organization, not the product.** Every product from the same company shows the same Pillar 3 reading. The Trellix Customer Fit is the Trellix Customer Fit — it does not change when you switch from Trellix Endpoint Security to Trellix Threat Intelligence Exchange in the dossier dropdown.

The unification is enforced in the Intelligence layer by two helpers in `intelligence.py`:

- `_build_unified_customer_fit(products)` — pure function, returns the unified Customer Fit dict from a list of per-product CF blocks
- `_apply_customer_fit_to_products(products, customer_fit)` — broadcasts the unified block onto every product (deep-copied so the per-product math loop has independent refs)

Both are called at the start of every `intelligence.recompute_analysis()` call so the per-product math runs against the unified data and produces identical Pillar 3 scores across products. The unification is a post-processing merge of existing AI output (no new Claude calls) — Claude scores per-product as it always has, but the merged result becomes the canonical company-level Customer Fit.

**Merge rule** — per `signal_category` (the rubric-model "what this measures" tag), pick the best badge across all products using "best showing wins" priority:

1. **Strongest strength tier wins.** `strong` > `moderate` > `weak`. If one product's research found a strong-tier badge for a signal_category and another found moderate, the strong wins.
2. **Within the same strength tier, prefer the most-positive color.** Sourced from `cfg.BADGE_COLOR_POINTS` — higher numeric value means more positive (`green` > `gray` > `amber` > `red`). Define-Once: no hardcoded color order anywhere in the merge logic.
3. **Tiebreak by evidence length.** Within the same strength and color, the badge with longer evidence text wins (more grounding = better evidence).

**The rationale:** Customer Fit is the company-level "best evidence we have" reading. If one product's research dug deeper and surfaced stronger/more-positive evidence about an organizational signal, that evidence is the most accurate read of the company. Per Frank's directive: "apply the best of the best and make the best showing for customer fit possible." This trades off some risk-signal preservation for consistency and a generous read of the company.

**Why this exists:** Frank reviewed Trellix Threat Intelligence Exchange and Trellix Endpoint Security on 2026-04-07 and saw Customer Fit drift between them — Partner Ecosystem amber on one, green on the other; Content Dev Team different across products. The organization is the organization. One source of truth.

**Pillar 1 and Pillar 2 stay per-product.** Product Labability is genuinely about the product. Most of Instructional Value (Product Complexity, Mastery Stakes, Lab Versatility) is also per-product. Only Pillar 3 is fully organizational.

#### In progress: store the unified CF on the discovery (next architectural step)

The current implementation merges per-product CF blocks at render time. The next step is to store the unified Customer Fit ONCE on the parent discovery as `discovery["_customer_fit"]` so Inspector, Prospector, and Designer can read it from a single source without needing an analysis. The new helper `intelligence.aggregate_customer_fit_to_discovery(analysis)` is in place; wiring it into `intelligence.score()` and switching `recompute_analysis()` to read from the discovery first is the remaining work.

### Dimension order (chronological reading order)

The dimensions are presented in chronological reading order — how a seller naturally thinks about a customer's training maturity:

| Order | Dimension | Weight | Question |
|---|---|---|---|
| 1 | **Training Commitment** | 25 | Have they invested in training? |
| 2 | **Build Capacity** | 20 | Can they create the labs? |
| 3 | **Delivery Capacity** | 30 | Can they get labs to learners at scale? |
| 4 | **Organizational DNA** | 25 | Are they the kind of company that partners? |

This order is the **single source of truth** — defined once in `scoring_config.py` PILLAR_CUSTOMER_FIT.dimensions tuple, propagates to the docs (this section), the AI prompt template, and the dossier UX rendering.

### 3.1 Training Commitment (cap 25)

*Have they invested in training? What's the evidence?*

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +6 | **Explicit hands-on / lab / interactive / scenario-based language** in published programs · Active cert with tested exam pass rates · Major flagship training events · Senior training leadership with mandate (level only — never name the person) · Strong regulated-industry compliance training |
| **moderate** | +3 | Catalog of training exists but mostly content-only · Documented programs without scale evidence · Director-level training leader · Some compliance training |
| **weak** | don't emit | Single training mention with no detail |

**signal_category list:** `hands_on_commitment` · `cert_exam_active` · `training_catalog` · `training_leadership_level` · `compliance_program` · `training_events` · `product_training_partnership`

**The hands-on / lab / interactive language pattern is the strongest single signal.** When the AI finds explicit references to hands-on labs, interactive exercises, scenario-based training in the vendor's published programs, that's the highest-value Training Commitment finding — credit it as strong.

**Example badge names:** `Hands-on Lab Commitment` · `Active Cert Exam` · `Cohesity Connect 5K` · `Compliance Training Mandate` · `VP-Level Training` · `~200 Course Catalog`

---

### 3.2 Build Capacity (cap 20)

*Can they create the labs?*

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +5 | Named education / curriculum / content team explicitly responsible for content creation · IDs, Lab Authors, Tech Writers / Editors documented · Product-Training partnership documented as collaborative content development · Strong DIY lab evidence · Documented content development partnerships |
| **moderate** | +3 | SME participation in content development mentioned · Named training department with some authoring signals · Third-party content firm engagement · Instructors with **explicit dual-role** authoring evidence |
| **weak** | don't emit | Just "training department exists" with no creation evidence · Plain instructor headcount (those route to Delivery Capacity) · SMEs whose role is review/accuracy only |

**signal_category list:** `content_team_named` · `instructional_designers` · `lab_authors` · `tech_writers` · `product_training_partnership` · `content_partnership` · `diy_labs` · `instructor_authors_dual_role`

**CRITICAL distinction — Build Capacity is about CREATE roles, not delivery:**

| ✅ Build Capacity | ❌ NOT Build Capacity |
|---|---|
| Instructional Designers (IDs) | Pure delivery instructors / trainers / workshop leaders |
| Content Developers | Generic "training department" without creation evidence |
| Lab Authors | Lab infrastructure (that's Delivery Capacity) |
| Tech Writers / Editors | Training catalog SIZE (that's Training Commitment) |
| SMEs **explicitly paired with content authoring** | SMEs whose role is review or accuracy only |
| Instructors **with explicit dual-role authoring evidence** | Plain instructor headcount |

**Default routing for instructors:** Delivery Capacity. Build Capacity only fires when the AI finds explicit dual-role evidence (instructor as lab author, tech writer, content developer, etc.).

**Example badge names:** `Workday Education Team` · `~30 Lab Authors` · `IDs On Staff` · `Tech Writer Team` · `Content Co-Authoring` · `DIY Lab Authoring` · `University Content Partnership`

---

### 3.3 Delivery Capacity (cap 30)

*Can they get labs to learners at scale?*

Weighted highest within Customer Fit because having labs = cost, delivering labs = value. Without delivery channels, labs never reach learners.

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +8 | Existing lab platform (Skillable = expansion, competitor name = displacement) · Large ATP / learning partner network at scale · Skillable-partner LMS already in place (Docebo, Cornerstone) · Major flagship events with hands-on tracks at scale · Instructor-led delivery network at scale |
| **moderate** | +4 | `No Lab Platform` (greenfield — opportunity, NOT deficiency) · `DIY Lab Platform` (replacement opportunity) · Limited ATP network · Other LMS in place · Moderate instructor delivery network · Smaller events |
| **weak** | don't emit | Plain "they offer training" with no delivery infrastructure named |

**signal_category list:** `lab_platform` (variable) · `atp_network` · `lms_partner` · `lms_other` · `instructor_delivery_network` · `training_events_scale` · `gray_market`

#### Lab Platform naming convention

The lab platform badge IS the platform name. **No `Lab Platform:` prefix.**

| State | Badge name | Color | Strength |
|---|---|---|---|
| Skillable customer (expansion) | `Skillable` | green | strong |
| Competitor (displacement) | `CloudShare`, `Instruqt`, `Skytap`, `Kyndryl`, `ReadyTech`, etc. | amber | strong |
| Greenfield (no platform yet) | `No Lab Platform` | gray Context | moderate |
| Built their own | `DIY Lab Platform` | gray Context | moderate |

**`No Lab Platform` is moderate, not weak.** From a Skillable seller's perspective, no incumbent means greenfield opportunity — no competitor to displace, just need to sell the hands-on premise.

**Example badge names:** `Skillable` · `CloudShare` · `No Lab Platform` · `~500 ATPs` · `Docebo Public` · `Cohesity Connect 5K` · `~200 Trainers`

---

### 3.4 Organizational DNA (cap 25)

*Are they the kind of company that partners and builds training programs?*

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +6 | Strong partner ecosystem (e.g., `~500 ATPs`, formal channel program with technical certification) · Platform Buyer culture (uses external platforms vs builds in-house) · Accessible / partner-friendly engagement |
| **moderate** | +3 | Mixed approach — some partner, some build in-house · Moderate partner engagement · Some channel structure · Larger but workable |
| **weak** | don't emit | Generic "they're an organization" with no specific patterns |

**Hard negative (red — fall back to color points):** `Hard to Engage` — fires only when documented evidence shows the org is bureaucratic, slow, or hostile to partners.

**signal_category list:** `partner_pattern` · `build_vs_buy_culture` · `engagement_ease` · `channel_structure`

#### Organizational DNA IS / IS NOT — read carefully (this dimension has a routing failure history)

| ✅ Organizational DNA IS about | ❌ Organizational DNA is NOT about |
|---|---|
| How the COMPANY operates as a business | The technical architecture of their products (Pillar 1) |
| Partnership patterns and ecosystem strength | API openness, platform extensibility, integration maturity (Pillar 1) |
| Build-in-house vs buy-from-outside culture | Whether their software is technically modular (Pillar 1) |
| Ease of doing business — accessible vs hard to engage | Cloud-native vs on-prem deployment shape (classification) |
| Cultural patterns — bureaucratic vs nimble | Their product line structure (this is about the ORG, not products) |
| Channel program structure | "Open Platform Architecture" — mis-routing pattern caught on Trellix |

**Example badge names:** `~500 ATPs` · `Strong Channel` · `Platform Buyer` · `Partner-Friendly` · `Mixed Build/Buy` · `Hard to Engage` (red)

---

## Pillar 3 variable badge name rules (in addition to Pillar 2 rules above)

| ✅ OK in Pillar 3 badge names | ❌ NOT OK in Pillar 3 badge names |
|---|---|
| Counts and scale (`~500 ATPs`, `~30 Lab Authors`, `30K Attendees`) | **Person titles or names** (`VP of Customer Education`, `Jane Smith`) — too individual |
| Platform names (`Skillable`, `CloudShare`, `Docebo Public`, `Cornerstone Internal`) | The company name of the org being scored (redundant with the dossier header) |
| Conference names (`Cohesity Connect`, `Cisco Live`) | Generic categories (`Lab Platform`, `Training Department`) |
| Funding signals (`Series D $200M`, `IPO 2024`) | Long descriptive phrases |
| Geographic reach (`Global`, `NAMER+EMEA`) | |

---

## ACV Potential

Calculated, not scored. Estimated annual contract value if the customer standardized on Skillable.

**ACV = Population x Adoption Rate x Hours per Learner x Rate**

ACV values use lowercase k for thousands and uppercase M for millions (e.g., 250k, 1.2M).

### Rate by Delivery Path

| Path | Rate |
|---|---|
| Azure/AWS Cloud Slice, Custom API | $6/hr (platform; cloud consumption separate) |
| Container | $6-12/hr |
| Standard VM (1-3 VMs) | $12-15/hr |
| Large/complex VM | $45-55/hr |
| Simulation | $5/hr |

### Six Consumption Motions

| Motion | Typical adoption ceiling |
|---|---|
| Customer Onboarding & Enablement | 0.02-0.08 |
| ATP & Channel Enablement | 0.05-0.15 |
| General Practice & Skilling | 0.02-0.08 |
| Certification / PBT | 0.02-0.10 |
| Employee Technical Enablement | 0.05-0.15 |
| Events & Conferences | 0.30-0.70 |

Never exceed 0.80 (Events only). Never exceed 0.20 for all other motions.

---

## Seller Briefcase

Below the three Pillar cards, each Pillar contributes a briefcase section — 2-3 sharp, actionable bullets that arm the seller for conversations. Each section has an info icon linking to the relevant framework documentation.

**Per-product, not per-analysis.** Each scored product has its own Seller Briefcase. When the user switches products in the dropdown, the briefcase swaps to that product's briefcase.

**Three sections, three AI calls, three different models.** Each section is generated by its own focused Claude call, on the model best suited to its purpose. All three calls per product run in parallel; across N products that's 3N parallel calls.

| Section | Model | Why this model | Max tokens |
|---|---|---|---|
| **Key Technical Questions** | Opus 4.6 | Sales-critical synthesis — questions go to a technical champion and must be sharp and answerable | ~800 |
| **Conversation Starters** | Haiku 4.5 | Fast pattern-matching — product-specific talking points the seller can use credibly | ~500 |
| **Account Intelligence** | Haiku 4.5 | Fast surfacing of organizational signals from existing scoring data | ~500 |

Each call receives the same per-product scoring context (all pillar scores, dimensions, badges, evidence, deployment model, verdict, contacts) so it synthesizes from what's already known instead of doing fresh research. Total time per product is gated by the slowest call (Opus KTQ ~20 seconds). Cached products keep their cached briefcase — only newly scored products trigger fresh briefcase generation.

| Section | Under which Pillar | What it gives the seller |
|---|---|---|
| **Key Technical Questions** | Product Labability | Who to find at the customer, what department, and the specific technical questions that unblock the lab build. Includes a verbatim question the champion can send. |
| **Conversation Starters** | Instructional Value | Product-specific talking points about why hands-on training matters. Makes the seller credible without being technical. |
| **Account Intelligence** | Customer Fit | Organizational signals — training leadership, org complexity, LMS platform, competitive signals, news. Shows the seller has done their homework. |

---

## Vocabulary — Locked Terms

| Use this | Not this |
|---|---|
| Fit Score | Composite Score / Lab Score |
| Pillar | Dimension (as top-level component) |
| Product Labability | Technical Orchestrability |
| Instructional Value | Product Demand / Workflow Complexity |
| Customer Fit | Customer Motivation / Organizational Readiness (as separate pillars) |
| Provisioning | Orchestration Method / Gate 1 |
| Lab Access | Licensing & Accounts / Gate 2 / Configure |
| Scoring | Gate 3 |
| Teardown | Gate 4 |
| Product Complexity | Difficult to Master |
| Mastery Stakes | Mastery Matters / Consequence of Failure |
| Lab Versatility | Lab Format Opportunities |
| Market Demand | Market Fit / Market Readiness / Strategic Fit |
| Training Commitment | Training Motivation |
| Organizational DNA | (no prior term) |
| Delivery Capacity | Content Delivery Ecosystem |
| Build Capacity | Content Development Capabilities |
| Content Dev Team | Dedicated Content Dept |
| Content Outsourcing | Outsourced Content Creation |
| DIY Labs | DIY |
| Green / Gray / Amber / Red | Pass / Partial / Fail / Yellow |
| Blocker | Red (in badge context) |
| HubSpot ICP Context | Notes / Generic notes field |

---

## Items Requiring Calibration

These need validation against real company data (Trellix, CompTIA, Microsoft, etc.):

| Item | Question |
|---|---|
| **Pillar weights (40/30/30)** | Do these produce the right Fit Scores for known companies? |
| **Dimension weights within Pillars** | Do the internal weights rank dimensions correctly? |
| **Score thresholds (80/65/45/25)** | Do these produce the right verdict distribution? |
| **ACV thresholds (High/Medium/Low)** | What dollar amounts define the ACV tiers? |
| **Penalty values** | Are -10 (Credit Card, MFA) and -5 (Rate Limits, etc.) proportional? |
| **Technical Fit Multiplier** | Does this still apply correctly with the new Pillar structure? |
| **Lab Versatility scoring** | Is +5 per badge the right granularity for a 15-point dimension? |
| **Organizational DNA scoring** | How do we score a dimension built on mostly inferred signals? |
