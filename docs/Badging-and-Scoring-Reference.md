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

**Fit Score formula (updated 2026-04-07):** pure weighted sum of three pillars, with the Technical Fit Multiplier scaling down the IV+CF contribution when Pillar 1 is weak:

```
fit = PL × 0.40 + IV × 0.30 × multiplier + CF × 0.30 × multiplier
```

The previous version had a `max(weighted_sum, PL)` floor — Pillars 2/3 could only LIFT the score above PL, never drag it below. That floor was removed after Frank's Diligent review surfaced the case where Diligent Boards had PL=66 (technically labable) but IV=33 (thin instructional case) and CF=23 (no training maturity), and the floor pinned the Fit Score at 66 (Solid Prospect) instead of 43 (Keep Watch — the honest signal). The framework's 70/30 product/org weighting is the right formula; the floor was fighting the framework.

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

The Scoring dimension uses a special **"Grand Slam" breadth rule** on top of the normal signal point lookup. Per Frank 2026-04-07 ("Scoring is about OPTIONS"): full marks (15/15) require **AI Vision PLUS at least one programmatic method** — Script Scoring for VM context OR Scoring API for cloud context. Single-method-alone caps below 15.

The dichotomy: **Script Scoring** is what you write when you have shell access to a VM (Bash/PowerShell that runs INSIDE the VM). **Scoring API** is what cloud products require — cloud services don't give you shell access, so you need an API to invoke validation work remotely. They're the same kind of work (writing a state validation script) in different orchestration contexts.

| Canonical | Green | Amber | Notes |
|---|---|---|---|
| **Scoring API** | Vendor REST API for state validation — rich coverage | API exists but coverage uncertain or partial | Cloud products use this. Replaces historical `API Scorable (rich/partial)`. Product-specific REST API details live in evidence on hover. |
| **Script Scoring** | Bash/PowerShell scripts can validate config state comprehensively | Scriptable surface exists but with gaps | VM products use this. Direct shell access = anything goes. Two states (Frank: don't flatten this one). |
| **AI Vision** | GUI-driven product where state is visually evident — AI Vision is the right tool. **Peer to API/Script, NOT a fallback.** Real Skillable differentiator (rare in lab platform space, only ~1 year old). | AI Vision usable but visual state ambiguous | Renamed from `AI Vision Scorable`. The "fallback" framing has been retired everywhere. |
| **Simulation Scorable** | — | Simulation environment supports scoring via guided interaction | SE clarification pending: when can/can't we score in a simulation; should this ever be red? |
| **MCQ Scoring** | — (display only) | No programmatic surface — knowledge-check questions only | **0 points** (Frank 2026-04-07: anyone can do MCQs, it's not lab work). Display as gray Context so the seller sees the option, but earns nothing. |

#### Scoring Base Credits (recalibrated 2026-04-07)

| Canonical | Standalone cap | Notes |
|---|---|---|
| `Scoring API` | **+12 (alone)** | Sparse APIs cap below 12. Rich suite needed for the standalone ceiling. Pairs with AI Vision to hit Grand Slam (15). |
| `Script Scoring` | **+15 (alone)** | VM context = anything goes. Standalone full marks possible. |
| `AI Vision` | **+10 (alone)** | Strong but not enough for high-stakes scoring (cert exams need more rigor). Pairs with Script or API to hit Grand Slam (15). |
| `Simulation Scorable` | +8 | (Existing — pending SE-3 clarification) |
| `MCQ Scoring` | **0** | Display only. No credit. |

**The Grand Slam rule (enforced in `scoring_math._compute_signal_penalty_dimension`):**

| Methods present (excluding MCQ) | Effective cap |
|---|---|
| AI Vision + Script Scoring | **15** (Grand Slam, VM) |
| AI Vision + Scoring API | **15** (Grand Slam, cloud) |
| Script Scoring alone | **15** (VM context) |
| Scoring API alone | **12** (sourced from `cfg.SCORING_API_ALONE_CAP`) |
| AI Vision alone | **10** (sourced from `cfg.SCORING_AI_VISION_ALONE_CAP`) |
| Nothing (only MCQ or zero methods) | **0** |

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

For real Skillable-hosted environments (Hyper-V / Container / ESX), teardown is automatic and scores full marks via the Datacenter badge. **Simulation paths use a separate Simulation Reset badge worth ZERO points** — a Simulation lab for a SaaS web app doesn't have anything to "tear down" in the operational sense, so the historical "Datacenter green for Simulation" rule was misleading and earned 25/25 for teardown work that didn't happen.

| Canonical | Green | Amber | Red |
|---|---|---|---|
| **Datacenter** | Skillable hosts a REAL environment (Hyper-V, ESX, OR Container) — teardown is automatic via snapshot revert or container destroy. **Does NOT apply to Simulation.** | — | — |
| **Simulation Reset** | (gray Context only) — Simulation session ends with the user session. No teardown work. **Earns ZERO Teardown points** (Frank 2026-04-07). | — | — |
| **Teardown API** | Vendor API covers environment cleanup and deprovisioning | Some teardown API coverage but gaps remain | — |
| **Manual Teardown** | — | — | No teardown mechanism — manual cleanup required between learners |
| **Orphan Risk** | — | Incomplete teardown may leave orphaned resources / accounts even when API exists | — |

#### Teardown Base Credits

| Canonical | Green base credit |
|---|---|
| `Datacenter` | +25 (full marks) — VM/ESX/Container ONLY |
| `Simulation Reset` | **0** — display-only |
| `Teardown API` | +22 |
| `Manual Teardown` | -10 (penalty) |
| `Orphan Risk` | -5 (penalty) |

**Datacenter rule (updated 2026-04-07):** fires green for VM-fabric, ESX, or Container paths only. **Simulation paths use Simulation Reset instead** — a SaaS Sim lab has no operational teardown work, and earning the full 25 was misleading. The seller should see Teardown was considered (via the gray Simulation Reset badge) but not earn credit for work that doesn't happen.

**Distinct from Manual Teardown:** `Orphan Risk` fires alongside `Teardown API` amber when there's API coverage but with gaps that could leave residue. Both can fire on the same product.

#### Teardown Floor: 0

### Sandbox API Red Pillar 1 Cap (SE-4)

When a product has **no real provisioning path** (no Runs in Hyper-V / Azure / AWS / Container / ESX) AND its Sandbox API badge is red, the entire Pillar 1 is capped low. The other dimensions (Lab Access, Scoring, Teardown) can't independently rack up points on a product that essentially can't be provisioned. Per Frank 2026-04-07 after Diligent review.

| Condition | Pillar 1 cap | Why |
|---|---|---|
| Sandbox API red + Simulation viable | **25** (`cfg.SANDBOX_API_RED_CAP_SIM_VIABLE`) | Simulation is the only viable lab delivery — capped at 25 to reflect that real provisioning isn't there |
| Sandbox API red + nothing viable | **5** (`cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE`) | The product cannot be labbed at all — capped at 5 (Workday-style dead end) |

Detection lives in `scoring_math.detect_sandbox_api_red_cap()`. Applied in `compute_all()` before the existing ceiling flag pass. Surfaces in the dossier's `ceilings_applied` list as `sandbox_api_red`.

**Why this matters:** before this rule shipped, Diligent Boards (SaaS, Sandbox API red, Simulation gray) scored 9/35 Provisioning + 17/25 Lab Access + 15/15 Scoring + 25/25 Teardown = 66/100 Pillar 1. The 17, 15, and 25 were essentially fictional — they were dimension scores for things that don't really exist on a SaaS web app with no per-learner provisioning. Now Pillar 1 caps at 25, the seller sees the cap with the reason `sandbox_api_red` in the audit trail, and the Fit Score honestly reflects "this product can't be labbed."

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

## Three Architectural Properties Across Pillars — read this first

The three Pillars differ along **three orthogonal architectural properties**. Each combination is intentional and reflects what the pillar actually measures. Future maintainers: do not collapse them into one model.

| Pillar | Scoring model | Scoring scope | Nature of measurement |
|---|---|---|---|
| **1 — Product Labability** | **Canonical model.** Fixed badge vocabulary. Math credits points by name-matched signal lookup. Color-aware (green = full, amber = half, red = color fallback). | **Per-product.** Each product has its own Pillar 1 reading because each product has its own technical fabric. | Technical fact-finding. Hyper-V either supports the install or it doesn't. APIs exist or they don't. **Concrete and binary.** |
| **2 — Instructional Value** | **Rubric model.** Variable, AI-synthesized badge names. Math credits points by `(dimension, strength)` lookup against a per-dimension rubric. Each badge carries a `signal_category` tag for cross-product analytics. | **Per-product.** Product complexity, mastery stakes, lab versatility, and market demand are all properties of THIS product. | Domain-specific judgment. Subject matter complexity for legal, cybersecurity, banking, healthcare etc. is genuinely different. **Subjective and contextual.** |
| **3 — Customer Fit** | **Rubric model.** Same as Pillar 2 — variable badge names with concrete data + rubric grading. | **Per-COMPANY.** Customer Fit measures the ORGANIZATION, not the product. Every product from the same company gets the same Pillar 3 reading. The Trellix Customer Fit is the Trellix Customer Fit — it does not change when you switch from Trellix Endpoint Security to Trellix Threat Intelligence Exchange in the dossier dropdown. | Organizational pattern recognition. Training maturity, build capacity, delivery channels, partner culture — these are properties of the COMPANY, not any single product. |

**Key takeaways:**

1. **Two scoring models, not one.** Canonical (Pillar 1) and Rubric (Pillars 2 + 3) are intentionally different because they measure different kinds of things. Don't unify them.
2. **Two scoring scopes, not one.** Per-product (Pillars 1 + 2) and per-company (Pillar 3) reflect the distinction between product properties and organizational properties. The company-level scope for Pillar 3 is enforced via the unification helpers documented in the Pillar 3 section below.
3. **Pillar 3 is the only fully-organizational pillar.** Even Pillar 2 Market Demand has product-specific aspects. Only Pillar 3 is purely about the company.

**Decision history:** the two-scoring-model architecture was decided on 2026-04-06 after walking the Pillar 1 implementation and discovering the same approach didn't fit Pillars 2 and 3. The company-level scope for Pillar 3 was decided on 2026-04-07 after Frank reviewed Trellix and saw Customer Fit drift between products of the same company. Both are in the decision log.

---

## Pillar 2 — Instructional Value (30%)

*Does this product have instructional value for hands-on training?*

The commercial case. Measures whether this product genuinely warrants hands-on lab experiences. Combined with Product Labability, these two product-level pillars represent 70% of the Fit Score.

### The Posture — Default-Positive, Not Prove-It

**Most software has instructional value for the right audience.** Microsoft Excel has instructional value for financial analysts. Outlook has instructional value for power users. Cybersecurity, data science, cloud, DevOps, networking, specialist business software — for the right learner, hands-on practice is almost always valuable. The framework used to start at zero and ask the AI to *earn* Instructional Value through evidence; that produced absurd results where a multi-VM cybersecurity platform would score 41/100 because positive signals couldn't overcome a pessimistic default.

**The new posture is realistic by default.** Every Instructional Value dimension starts from a baseline derived from the product's category — most categories start above the median, reflecting the reality that most real software warrants hands-on practice. Findings move the score up (specific positive signals) or down (explicit negatives like consumer-grade). Missing evidence means "baseline," not "zero."

**The question shifts from** *"is there evidence of instructional value?"* **to** *"is there any reason this product would NOT have instructional value?"*

### CRITICAL — Every badge is an ANSWER, never a question or topic

**This rule applies to EVERY badge in EVERY Pillar 2 and Pillar 3 dimension.** A badge label must be a finding the seller can read out loud and understand without context. If it's a question or a topic, it fails.

**The four kinds of answers** — every badge is exactly one of these:

| Kind | Strength | Example |
|---|---|---|
| **Good answer** — positive finding | `strong` (green) | `Platform Buyer`, `~500 ATPs`, `Multi-VM Architecture`, `Active Cert Exam` |
| **Pause answer** — concerning finding, dig deeper | `moderate` (amber) | `Long RFP Process`, `Regional Partner Network`, `Slide-Deck Only Training` |
| **Warning answer** — major red flag | (red, hard negative) | `Hard to Engage`, `No Training Partners`, `No Classroom Delivery`, `Consumer Grade` |
| **Context answer** — informational, no scoring impact | `informational` (gray) | `Recent VP Hire`, `Parent Company: SoftBank`, `Niche Specialty` |

**The "read it out loud" test** — if you cannot read the badge label as a statement about the customer and have it make sense, it's wrong:

| ❌ Question / topic (FAIL) | ✓ Answer (PASS) |
|---|---|
| `Build vs Buy` (question) | `Platform Buyer` OR `Builds Everything` |
| `Partner Ecosystem` (topic) | `Multi-Type Partnerships` OR `~500 ATPs` OR `Thin Channel` |
| `Integration Maturity` (topic) | `Open Platform Culture` OR `Closed Platform` |
| `Ease of Engagement` (topic) | `Partner-Friendly` OR `Long RFP Process` OR `Hard to Engage` |
| `Training Culture` (topic) | `Hands-On Training Culture` OR `Slide-Deck Only Training` |
| `Training Catalog` (topic) | `200+ Courses` OR `Thin Catalog` OR `Compliance-Only Catalog` |
| `Deep Configuration` (topic) | `Deeply Configurable` OR `180+ Detection Rules` |
| `Multi-Phase Workflow` (topic) | `Design → Deploy → Tune → Troubleshoot` |
| `High-Stakes Skills` (topic) | `Breach Exposure` OR `HIPAA Audit Risk` OR `Patient Safety Critical` |

**If you cannot produce an answer for a finding, don't emit the badge.** A question / topic label produces NO information for the seller — it just labels that the AI noticed something. The seller needs to know what the AI FOUND.

### Rubric Model Architecture

Pillar 2 uses the **rubric model** (intentionally different from Pillar 1's canonical model — see "Three Architectural Properties Across Pillars" above). Each badge the AI emits carries:
- `name` — variable, AI-synthesized, domain-specific (the visible chip) — **the name IS the finding (an ANSWER), never a topic label or a question**
- `strength` — `strong` / `moderate` / `informational` / `weak` — REQUIRED, drives the math. `informational` is 0 points (context-only).
- `signal_category` — one of the dimension's fixed category list — REQUIRED, hidden, for analytics
- `color` — green / amber / red / gray (mirrors strength; red reserved for hard negatives; gray for informational)
- `evidence` — sentence-level context (existing field, hover popover)

### Dimensions

| Dimension | Weight | Question |
|---|---|---|
| PRODUCT COMPLEXITY | 40 | Is this product hard enough that someone needs hands-on practice to become competent? |
| MASTERY STAKES | 25 | What are the consequences of getting it wrong? |
| LAB VERSATILITY | 15 | What kinds of high-value hands-on experiences can we build? |
| MARKET DEMAND | 20 | Is this a topic people actively want to learn? |

---

### 2.1 Product Complexity (cap 40)

*Is this product hard enough that someone needs **repeated hands-on practice** to become competent with it?*

#### What the Product Complexity Dimension Measures

Product Complexity asks a single question: **does becoming good at using this product require practice that can't be done by reading a manual or watching a video?** Complexity here is not about abstract sophistication — it's about whether hands-on repetition, experimentation, and real-environment interaction are the difference between someone who can use the product and someone who can't.

A product is complex in the sense this dimension measures when **any** of the following are true:

- It requires **configuring** multiple interrelated components where wrong choices cause cascading problems
- It has **multi-phase workflows** where each phase depends on the previous (design → deploy → operate → troubleshoot)
- It involves **multiple distinct personas** (admin vs operator vs end user vs developer) who each need different hands-on skills
- It requires **troubleshooting real failure scenarios** that can't be simulated in a static document
- It has **AI features that require iterative practice** — prompting, tuning, verifying — where watching is not enough
- It has **networking topology** that must be understood through manipulation, not description
- It has **integration complexity** where the product's real work happens through external systems

Complexity is measured **relative to the audience who would learn this product**, not absolutely. Enterprise software for insurance claims operations is "simple" to a software engineer but "genuinely complex" to the claims adjuster who needs to use it every day. The question is always: **for the people who would take a lab on this product, is the product hard enough that they need to practice?**

#### What This Dimension Does NOT Measure

| Not this | That belongs to... |
|---|---|
| Whether the product is **easy or hard to provision** | Pillar 1 Provisioning |
| Whether labs can be **scored** on this product | Pillar 1 Scoring |
| How much **mastery matters** — the consequences of getting it wrong | **Pillar 2 Mastery Stakes** |
| Whether there's a **market** of people who want to learn this | Pillar 2 Market Demand |
| Whether the company has **training infrastructure** | Pillar 3 |

Product Complexity is about the product's intrinsic difficulty. Mastery Stakes is about the cost of failure. Both can be high or low independently. A simple product with high stakes (don't press the big red button) is different from a complex product with low stakes (tuning a CI/CD pipeline where mistakes cost time but not money).

#### Category-Aware Baseline

Applied **before** any findings. The AI looks up the baseline by the product's top-level category (from `CATEGORY_PRIORS` in `scoring_config.py`), adds strong/moderate finding credits, subtracts any explicit negative findings, caps at 40 / floors at 0.

| Category | Baseline | Rationale |
|---|---|---|
| **Cybersecurity** | **32 / 40 (80%)** | Multi-system, cross-role, deep configuration — cybersecurity products are almost always hands-on-appropriate |
| **Cloud Infrastructure** | **32 / 40 (80%)** | Compute, networking, storage, containers, serverless, databases — inherently multi-component |
| **Networking / SDN** | **32 / 40 (80%)** | Topology, routing, segmentation — impossible to learn without hands-on |
| **Data Science & Engineering** | **32 / 40 (80%)** | Pipelines, tuning, iteration — practice is the only way |
| **Data & Analytics** | **32 / 40 (80%)** | Modeling, query tuning, real datasets |
| **DevOps** | **32 / 40 (80%)** | CI/CD, IaC, monitoring, configuration management — hands-on by nature |
| **AI Platforms & Tooling** | **32 / 40 (80%)** | Anthropic, OpenAI, Hugging Face, LangChain, LlamaIndex, Pinecone, Weaviate, agent frameworks, LLMOps, fine-tuning platforms — iterative prompt + verify + tune cycles, multi-component pipelines |
| **Data Protection** | **30 / 40 (75%)** | Backup, DR, archive, data management — complex multi-layer systems with real operational depth |
| **ERP** | **28 / 40 (70%)** | Financial management, HR/HCM, supply chain — deep configuration, cross-module workflows, multi-role |
| **CRM** | **28 / 40 (70%)** | Salesforce, Dynamics, HubSpot — deep customization, workflow automation, integration depth |
| **Healthcare IT** | **28 / 40 (70%)** | EMR / EHR / clinical systems — regulated workflows, multi-role, real depth |
| **FinTech** | **28 / 40 (70%)** | Trading, settlement, reconciliation — real multi-phase workflows with depth |
| **Legal Tech** | **28 / 40 (70%)** | Matter management, e-discovery, document workflows — real depth and role diversity |
| **Industrial / OT** | **28 / 40 (70%)** | SCADA, control systems, PLC programming — real technical complexity |
| **Infrastructure / Virtualization** | **28 / 40 (70%)** | VMware, Hyper-V, container platforms — real operational depth |
| **App Development** | **28 / 40 (70%)** | Developer tools, SDKs, CI platforms, IDEs — meaningful depth, real hands-on value |
| **Collaboration** | **24 / 40 (60%)** | SharePoint, Microsoft 365, Teams — meaningful administrative and workflow depth, especially at the development / automation level, but less intense than core enterprise systems |
| **Content Management** | **24 / 40 (60%)** | Documentum, Alfresco, Box Enterprise — real workflow, permission, and metadata depth |
| **Social / Entertainment** *(e.g., Facebook, Instagram, TikTok, Netflix, Spotify)* | **4 / 40 (10%)** | No professional training market — these are personal / entertainment platforms, not content areas |
| **Unknown / uncategorized** | **22 / 40 (55%)** | Neutral fallback — findings drive the score |

**Note — "Simple SaaS" removed.** SaaS is a delivery mechanism, not a content area. Products are classified by what they *do* (cybersecurity, ERP, data protection, etc.), not by how they're delivered. There's no training market for "SaaS" as a category.

**Note — ERP and CRM are separate categories.** ERP (Financial, HR/HCM, Supply Chain) and CRM (Sales, Marketing, Customer Service) were historically bundled but are meaningfully different on both complexity and stakes. They're split throughout every Pillar 2 dimension.

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +6 | The finding **alone** could justify a hands-on lab — deep multi-system work, multi-phase workflows with real state transitions, genuine troubleshooting against realistic failure modes, AI requiring iterative practice, multi-VM or networking topology requirements, integration as the primary workflow |
| **moderate** | +3 | The finding **adds** to the case — some depth or complexity but limited scope, single-phase, narrower role set, meaningful but not dominant |
| **weak** | don't emit | Too thin to carry its own badge — not worth the noise |

**The baseline is doing most of the work.** Three strong badges (6×3=18) on top of a cybersecurity baseline (28) = 46, capped at 40. A finding-hungry prompt can safely emit 4-5 badges without blowing cap, and a thin product with few findings still reflects its real category baseline.

#### Signal Categories

The AI picks **one** `signal_category` per badge from this fixed list (hidden from UX, used for analytics and cross-product comparison):

| Signal category | What it means |
|---|---|
| `multi_vm_architecture` | Product requires multiple VMs working together — **cross-pillar with P1 Multi-VM Lab** |
| `deep_configuration` | Many interrelated settings with real consequences |
| `multi_phase_workflow` | Distinct lifecycle phases: design → build → deploy → operate → troubleshoot |
| `role_diversity` | Multiple personas each needing hands-on skills |
| `troubleshooting_depth` | Rich fault modes requiring practice against realistic broken states |
| `complex_networking` | VLANs, routing, multi-network topology — learned only by manipulation |
| `integration_complexity` | External systems ARE the primary workflow |
| `ai_practice_required` | AI features where prompting/tuning/verifying requires iteration |
| `state_persistence` | Stateful systems where wrong state cascades over time |
| `compliance_depth` | Regulated workflows (SOX, HIPAA, PCI) with audit implications |
| `consumer_grade` **(negative)** | Red — product is genuinely consumer-facing, not lab-appropriate |
| `simple_ux` **(negative)** | Red — intentionally simple interface, minimal lab value |
| `wizard_driven` **(negative)** | Amber/red — primary UX is a sequential wizard with few real decisions |

#### Cross-Pillar Evidence Compounding

Certain Product Complexity findings should **automatically be considered** based on Pillar 1 findings:

| If this fires in P1... | ...then this should fire in P2 Product Complexity |
|---|---|
| `Multi-VM Lab` (Provisioning) | `multi_vm_architecture` signal_category |
| `Complex Topology` (Provisioning) | `complex_networking` signal_category |
| `Large Lab` (Provisioning) | `deep_configuration` or `state_persistence` |

**This is a prompt instruction, not a math rule.** The AI is told to cross-reference Pillar 1 findings when evaluating Product Complexity. The same fact legitimately credits both pillars because they answer different questions about the same evidence.

#### Worked Examples

**Example 1 — Trellix Global Threat Intelligence (Cybersecurity):**

| Step | Value |
|---|---|
| Baseline (Cybersecurity) | **28** |
| `Multi-Correlation Engine` (strong, `deep_configuration`) | +6 |
| `IOC Pivoting Workflow` (strong, `multi_phase_workflow`) | +6 |
| `Analyst + Automation Split` (strong, `role_diversity`) | +6 |
| `SIEM + EDR + Ticketing Chain` (strong, `integration_complexity`) | +6 |
| Raw total | 52 |
| **Final score** | **40 / 40** (capped) |

**Example 2 — Diligent Boards (Content Management / Governance):**

| Step | Value |
|---|---|
| Baseline (Content Management) | **24** |
| `Agenda + Voting Workflow` (moderate, `multi_phase_workflow`) | +3 |
| `Committee Role Separation` (moderate, `role_diversity`) | +3 |
| `Document Permission Tree` (moderate, `deep_configuration`) | +3 |
| **Final score** | **33 / 40** |

**Example 3 — Microsoft Excel (Collaboration):**

| Step | Value |
|---|---|
| Baseline (Collaboration) | **24** |
| `Power Query Workflow` (strong, `multi_phase_workflow`) | +6 |
| `Formula + Pivot Modeling` (moderate, `deep_configuration`) | +3 |
| `Simple UX for basic tasks` (amber, `simple_ux`) | -3 |
| **Final score** | **30 / 40** |

**Example 4 — Instagram (Social / Entertainment):**

| Step | Value |
|---|---|
| Baseline (Social / Entertainment) | **4** |
| `Consumer Grade` (red, `consumer_grade`) | -4 |
| **Final score** | **0 / 40** |

#### Typical Spread

| Product type | Expected Product Complexity |
|---|---|
| Multi-system cybersecurity / cloud / DevOps / AI platforms with real depth | **36-40** |
| Data Protection, real enterprise software, regulated-industry platforms | **32-40** |
| ERP, CRM, Healthcare IT, FinTech, Legal Tech, Industrial/OT | **28-36** |
| Collaboration / Content Management | **24-32** |
| Social / Entertainment | **0-4** |

---

### 2.2 Mastery Stakes (cap 25)

*What are the consequences of getting it wrong? How much does competence matter?*

#### What the Mastery Stakes Dimension Measures

Mastery Stakes asks: **what are the consequences of getting it wrong?** The dimension measures the real-world cost of incompetence — breach, data loss, compliance failure, malpractice, downtime, reputation damage, regulatory sanction, physical harm. High stakes create a commercial case for hands-on training that goes beyond "it's hard to learn" — it becomes "they *must* be competent before they touch production."

High Mastery Stakes exist when the product operates in an environment where:

- **Security failures** expose data, credentials, or systems to attack
- **Compliance failures** trigger regulatory action, fines, or audit exposure (HIPAA, PCI, SOX, GDPR, SOC 2)
- **Data integrity failures** corrupt records, break reporting, or poison downstream systems
- **Business continuity failures** cause outages, missed SLAs, or customer-facing incidents
- **Safety failures** create physical, medical, or financial harm to end users
- **Legal failures** expose the organization to malpractice, privilege breaches, or liability
- **Reputational failures** are public, permanent, or cause customer churn

Mastery Stakes is NOT about how hard the product is. It's about the cost of failing to use it correctly.

#### What This Dimension Does NOT Measure

| Not this | That belongs to... |
|---|---|
| How hard the product is to learn | **Pillar 2 Product Complexity** |
| Whether labs can be scored | Pillar 1 Scoring |
| Whether the company runs compliance training programs | Pillar 3 Training Commitment |
| Whether the market cares about this skill | Pillar 2 Market Demand |

#### Posture: Default-Positive for Specialist Software

Most specialist software has real stakes — that's why it's specialist software. The old framework undercredited this by firing only one or two badges per product. The new framework starts from a category-aware baseline that reflects the reality that most serious software operates in environments where mistakes matter.

#### Category-Aware Baseline

| Category | Baseline | Rationale |
|---|---|---|
| **Cybersecurity** | **22 / 25 (88%)** | Breach = headlines. Stakes are definitional, not situational. |
| **Healthcare IT** | **22 / 25 (88%)** | Patient safety, HIPAA, clinical liability — definitional. |
| **FinTech** | **22 / 25 (88%)** | Money, SOX, PCI, AML, regulatory exposure — definitional. |
| **Legal Tech** | **22 / 25 (88%)** | Malpractice, privilege, documented liability — definitional. |
| **Data Science & Engineering** | **22 / 25 (88%)** | Snowflake, Databricks, data warehouses and pipelines — **garbage in, garbage out**. Millions in decisions ride on the data layer being correct. |
| **AI Platforms & Tooling** | **22 / 25 (88%)** | Model errors at scale compound — wrong outputs flow into every downstream decision or product experience. Stakes are definitional for production AI systems. |
| **ERP** | **20 / 25 (80%)** | Financial records, SOX audit, business continuity — top-of-business stakes |
| **Data Protection** | **20 / 25 (80%)** | Data loss, DR failures — often irreversible |
| **Industrial / OT** | **20 / 25 (80%)** | SCADA, physical safety, control systems |
| **Cloud Infrastructure** | **20 / 25 (80%)** | Downtime, data exposure, misconfigured security groups — real incidents at scale |
| **Networking / SDN** | **20 / 25 (80%)** | Routing and segmentation errors take down production or expose data |
| **DevOps** | **20 / 25 (80%)** | Production deploys, pipeline failures, config drift — high stakes in live systems |
| **Infrastructure / Virtualization** | **20 / 25 (80%)** | Host failures, VM sprawl, hypervisor misconfig — real operational stakes |
| **Data & Analytics** | **18 / 25 (72%)** | Tableau, Power BI, Looker, BI layers — business-skills layer. Dashboards drive decisions; mistakes mislead executives even when the underlying data is clean. |
| **CRM** | **16 / 25 (64%)** | Real consequences (pricing, contracts, GDPR/CCPA, revenue recognition), but fewer regulated-industry audits than ERP |
| **Content Management** | **16 / 25 (64%)** | Document workflow errors, permission gaps, records-retention mistakes — real but usually recoverable |
| **Collaboration** | **16 / 25 (64%)** | SharePoint, Teams, Microsoft 365 — administrative mistakes affect real business operations; development/automation layer raises the stakes further |
| **App Development** | **14 / 25 (56%)** | Stakes depend entirely on what's being built — neutral-moderate baseline |
| **Unknown / uncategorized** | **14 / 25 (56%)** | Neutral fallback — see "Unknown Classification Flag" below |
| **Social / Entertainment** *(e.g., Facebook, Instagram, TikTok, Netflix, Spotify)* | **2 / 25 (8%)** | No professional training market — no professional stakes |

**Unknown Classification Flag.** When a product lands in `Unknown / uncategorized`, the scorer sets a `classification_review_needed: true` flag on the product result, and the dossier + caseboard surface a small amber "Review Classification" indicator. This fires in two scenarios:

| Scenario | Example |
|---|---|
| **True unknown** — AI can't pick any existing category | Novel quantum compute platform, emerging AI agent framework |
| **Multi-category dominant** — multiple categories fit and the AI's pick is low-confidence | NVIDIA (networking + compute + AI), Cloudflare (networking + security + edge), Databricks (data sci + cloud infra) |

The flag is a signal for human review, not a scoring penalty. The neutral Unknown baselines (defined in `scoring_config.py` → `IV_CATEGORY_BASELINES[UNKNOWN_CLASSIFICATION]` and `CF_ORG_BASELINES[UNKNOWN_CLASSIFICATION]`) keep the score honest while the flag tells the user "verify this classification before trusting the numbers." Logs capture Unknown classifications so patterns (e.g., five hardware/compute products in a row) can trigger adding a new category to the taxonomy.

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +9 | Misconfiguration causes breach, data loss, compliance failure, sanctions, malpractice, material downtime, or physical harm — **real and consequential** |
| **moderate** | +5 | Errors are visible and create rework, reputation cost, or business friction but are recoverable |
| **weak** | don't emit | Mostly inconvenience — easily fixed, no lasting consequences |

#### Signal Categories

| Signal category | What it means |
|---|---|
| `breach_exposure` | Security mistakes cause data exposure, credential theft, or attack surface growth |
| `compliance_consequences` | Regulatory framework (HIPAA, PCI, SOX, GDPR, SOC 2, etc.) creates direct audit/fine exposure |
| `data_integrity` | Errors corrupt data, break reporting, poison downstream systems |
| `business_continuity` | Failures cause outages, SLA breaches, missed transactions |
| `safety_regulated` | Safety-critical environment — physical harm, patient safety, OT systems |
| `legal_liability` | Malpractice, privilege, contractual exposure, document handling errors |
| `reputation_damage` | Public-facing errors that cause customer churn or permanent reputation impact |
| `financial_impact` | Direct dollar impact from incorrect transactions, pricing errors, reconciliation failures |

#### Badge Naming — Finding-as-Name

| ✗ Wrong | ✓ Right |
|---|---|
| `High Stakes` | `HIPAA Exposure` |
| `Compliance Risk` | `PCI-DSS Audit` |
| `Data Loss Risk` | `Irreversible Data Loss` |
| `Breach Risk` | `Credential Theft Path` |
| `Harm Severity` | `Patient Safety Critical` |

Domain examples: `Ransomware Recovery`, `Material Financial Impact`, `Audit Trail Gap`, `Production Outage`, `Misrouted Patient Data`.

#### Worked Examples

**Trellix GTI (Cybersecurity):**

| Step | Value |
|---|---|
| Baseline (Cybersecurity) | **22** |
| `Breach Detection Gap` (strong, `breach_exposure`) | +9 |
| **Final score** | **25 / 25** (capped from 31) |

**Diligent Boards (Content Management / Governance):**

| Step | Value |
|---|---|
| Baseline (Content Management) | **16** |
| `Board Privilege Exposure` (strong, `legal_liability`) | +9 |
| **Final score** | **25 / 25** (capped from 25) |

**Microsoft Excel (Collaboration):**

| Step | Value |
|---|---|
| Baseline (Collaboration) | **16** |
| `Material Financial Impact` (moderate, `financial_impact`) — for analysts building models | +5 |
| **Final score** | **21 / 25** |

#### Typical Spread

| Product type | Expected Mastery Stakes |
|---|---|
| Cybersecurity, healthcare, fintech, legal, data science, AI platforms | **22-25** |
| ERP, data protection, industrial/OT, cloud, networking, DevOps, infra/virt | **20-25** |
| Data & analytics, CRM, content mgmt, collaboration, app dev | **14-22** |
| Social / Entertainment | **0-4** |

---

### 2.3 Lab Versatility (cap 15)

*What kinds of high-value hands-on skill development and skill validation experiences could be designed and delivered on Skillable for this product?*

#### What the Lab Versatility Dimension Measures

Lab Versatility asks: **what lab types could be designed and delivered on Skillable for this product?** This is about the *platform's capability* — what kinds of hands-on skill development and skill validation experiences could be created on Skillable for this product, regardless of *who* actually builds them (Skillable Professional Services, the customer's own team, or a content partner). It's the dimension that connects Inspector to Designer — the lab types identified here feed directly into Designer's program recommendations, and they give sellers specific conversational competence points about *what kinds of labs* are possible.

Lab Versatility is measured against the **Lab Type Menu** (defined in `scoring_config.py` as `LAB_TYPE_MENU`):

- **Red vs Blue** — adversarial team scenarios (cybersecurity EDR/SIEM/network security)
- **Simulated Attack** — realistic attack, learner responds (any defensive product)
- **Incident Response** — production down, diagnose under pressure (infrastructure, security, cloud, databases)
- **Break/Fix** — something's broken, figure it out (any product with complex failure modes)
- **Team Handoff** — multi-person sequential workflow (DevOps, data engineering, SDLC)
- **Bug Bounty** — find the flaws (development platforms, security)
- **Cyber Range** — full realistic network, live threats (network security, SOC ops)
- **Performance Tuning** — system works but needs optimization (databases, infrastructure, cloud, data)
- **Migration Lab** — move from A to B (enterprise software, cloud, infrastructure)
- **Architecture Challenge** — design under constraints
- **Compliance Audit** — walk through a regulatory check
- **Disaster Recovery** — practice the recovery plan
- **CTF (Capture The Flag)** — cybersecurity skill hunts

A product with Lab Versatility doesn't need to support ALL lab types — it needs to support **some lab type naturally**, where "naturally" means the lab type fits the product's real workflow without shoehorning.

#### What This Dimension Does NOT Measure

| Not this | That belongs to... |
|---|---|
| Whether the product is complex | **Pillar 2 Product Complexity** |
| Whether the lab can be scored | Pillar 1 Scoring |
| Whether Skillable can provision the product | Pillar 1 Provisioning |

#### Posture: Default-Positive for Most Real Software

Most real software supports at least one lab type naturally. The old framework used to return 0/15 for products where the AI couldn't identify a perfect match — that's the wrong read. Almost any serious product supports *some* hands-on learning experience, even if it's just "Break/Fix" or "Architecture Challenge." The new posture starts from a baseline reflecting what lab types are *typically* natural for each category.

#### Category-Aware Baseline

| Category | Baseline | Natural lab types |
|---|---|---|
| **Cybersecurity** | **14 / 15 (93%)** | Red vs Blue, Simulated Attack, Incident Response, Cyber Range, CTF, Break/Fix |
| **Cloud Infrastructure** | **14 / 15 (93%)** | Migration, Performance Tuning, Incident Response, Architecture Challenge, DR |
| **Networking / SDN** | **14 / 15 (93%)** | Cyber Range, Incident Response, Troubleshooting, Performance Tuning |
| **DevOps** | **14 / 15 (93%)** | CI/CD Team Handoff, Break/Fix, Architecture Challenge, Performance Tuning |
| **AI Platforms & Tooling** | **14 / 15 (93%)** | Prompt-tune-verify cycles, Bug Bounty on models, Architecture Challenge, Team Handoff |
| **Data Science & Engineering** | **13 / 15 (87%)** | Pipeline building, Performance Tuning, Architecture, Break/Fix |
| **Data Protection** | **12 / 15 (80%)** | DR, Compliance Audit, Break/Fix |
| **Industrial / OT** | **12 / 15 (80%)** | Incident Response, Break/Fix, Architecture |
| **Infrastructure / Virtualization** | **12 / 15 (80%)** | Break/Fix, Migration, Performance Tuning |
| **Data & Analytics** | **12 / 15 (80%)** | Performance Tuning, Modeling, Troubleshooting |
| **App Development** | **12 / 15 (80%)** | Architecture Challenge, Bug Bounty, Team Handoff |
| **ERP** | **12 / 15 (80%)** | Workflow, Migration, Configuration, Team Handoff |
| **Healthcare IT** | **12 / 15 (80%)** | Workflow, Compliance Audit, Incident Response |
| **FinTech** | **12 / 15 (80%)** | Workflow, Compliance Audit, Incident Response |
| **Legal Tech** | **11 / 15 (73%)** | Workflow, Compliance Audit |
| **CRM** | **11 / 15 (73%)** | Workflow, Migration, Configuration |
| **Collaboration** | **11 / 15 (73%)** | Workflow, Power-User, Team Handoff, Configuration |
| **Content Management** | **11 / 15 (73%)** | Workflow, Migration, Permission Modeling |
| **Unknown / uncategorized** | **11 / 15 (73%)** | Neutral fallback — flag for classification review |
| **Social / Entertainment** *(e.g., Facebook, Instagram, TikTok, Netflix, Spotify)* | **1 / 15 (7%)** | Rarely fits any lab type |

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +5 | A clear high-value lab type fits naturally — Red vs Blue, Cyber Range, Incident Response, Performance Tuning, Migration Lab, Compliance Audit, Break/Fix — and the product's real workflow supports it without shoehorning |
| **moderate** | +3 | A lab type is adaptable to the product but requires some shoehorning — workflows can be recreated but aren't the natural lab format |
| **weak** | don't emit | Lab type doesn't fit; the product doesn't support hands-on in any recognizable form |

#### Signal Categories

Maps directly to `LAB_TYPE_MENU` entries:

| Signal category | Lab type |
|---|---|
| `adversarial_scenario` | Red vs Blue |
| `simulated_attack` | Simulated Attack |
| `incident_response` | Incident Response |
| `break_fix` | Break/Fix |
| `team_handoff` | Team Handoff |
| `bug_bounty` | Bug Bounty |
| `cyber_range` | Cyber Range |
| `performance_tuning` | Performance Tuning |
| `migration_lab` | Migration Lab |
| `architecture_challenge` | Architecture Challenge |
| `compliance_audit` | Compliance Audit |
| `disaster_recovery` | Disaster Recovery |
| `ctf` | CTF / Capture The Flag |

#### Badge Naming — Finding-as-Name

The badge name should be the **specific lab type** applied to the product, not the category:

| ✗ Wrong | ✓ Right |
|---|---|
| `Lab Versatility` | `Red vs Blue` |
| `Adversarial Scenario` | `EDR Threat Hunting` |
| `Incident Response Type` | `SOC Alert Triage` |
| `Performance Tuning Type` | `Query Plan Optimization` |

#### Worked Example — Trellix GTI

| Step | Value |
|---|---|
| Baseline (Cybersecurity) | **14** |
| `SOC Alert Triage` (strong, `incident_response`) | +5 |
| **Final score** | **15 / 15** (capped from 19) |

#### Typical Spread

| Product type | Expected Lab Versatility |
|---|---|
| Cybersecurity, cloud, networking, DevOps, AI platforms, data science | **14-15** |
| Data platforms, infrastructure, business software with workflow depth | **12-15** |
| Collaboration, content management, CRM, legal tech | **11-14** |
| Social / Entertainment | **0-2** |

---

### 2.4 Market Demand (cap 20)

*How big is the worldwide population of people who need to learn this product at hands-on depth?*

#### What the Market Demand Dimension Measures

Market Demand asks: **how big is the worldwide population of people who need to learn this product at hands-on depth?** It's the intersection of three things:

1. **Is there something to learn?** (derived from Product Complexity)
2. **Do consequences drive employers to invest in training?** (derived from Mastery Stakes)
3. **How large is the specialist population** — how many people hold roles that actually need this skill at depth, not just casual end-user use?

**Important distinction — user population ≠ training population.** A product with 2 billion casual users and 200 administrators has a small Market Demand. A product with 5 million specialist professionals who all need deep skills has a massive Market Demand. Salesforce Trailhead exists because admins need training — but the admin population per company is tiny compared to cybersecurity professionals per company. Cybersecurity, cloud, networking, and DevOps dominate Market Demand because **the specialist population is large AND every person in it needs hands-on skills**. CRM, SharePoint, and ERP specialists are real populations, just smaller.

**Market Demand is naturally derivative of Product Complexity × Mastery Stakes × Specialist Population.** A simple popular product (Instagram) has near-zero Market Demand. A complex niche product has moderate Market Demand. Complex + high-stakes + large specialist population = maximum Market Demand.

Strong Market Demand signals:

- **Active certification ecosystem** — the product (or category) has recognized certs that people pursue for career advancement
- **ATP / training partner networks** — third parties exist who sell training for this product, which is definitional proof that demand exists (why would a partner exist without buyers?)
- **Scaled install base in a specialist context** — not raw user count, but *learner-eligible* user count
- **High-demand category** — cybersecurity, cloud, data science, AI are categories where people actively seek skills
- **Recognized skill in job markets** — the skill appears in job postings, LinkedIn searches, recruiter language
- **Conference and event presence** — the product has its own conference or hands-on tracks at major events
- **Growth and funding signals** — IPO, Series funding, enterprise adoption at scale

Market Demand is the **legitimacy check** — does the outside world validate that training on this product is worth delivering? If an ATP network exists, yes. If there's an active cert exam, yes. If the category is cybersecurity, yes almost by definition. If it's a niche internal tool for one bank, no.

#### What This Dimension Does NOT Measure

| Not this | That belongs to... |
|---|---|
| How many learners the CUSTOMER has — internal employees, customers, partners | That's the *company's* scale, not the market's appetite for the skill. Company scale is Pillar 3 considerations (Delivery Capacity, Org DNA). |
| Whether the product is complex | Pillar 2 Product Complexity |
| Whether the product has real stakes | Pillar 2 Mastery Stakes |
| Whether the company has an ATP network | That's **Delivery Capacity**, but the existence of an ATP network is also a cross-pillar signal that Market Demand is real (someone's buying training or they wouldn't be partners) |

#### Cross-Pillar Evidence Compounding

The **same fact** can legitimately credit both Delivery Capacity (Pillar 3) AND Market Demand (Pillar 2):

| Fact | Pillar 3 Delivery Capacity credits | Pillar 2 Market Demand credits |
|---|---|---|
| `~500 ATPs globally` | Strong Delivery Capacity — they can reach learners | Strong Market Demand — nobody becomes a partner for a product with no demand |
| `Active cert exam with published pass rates` | Moderate Delivery Capacity (indirectly — the exam creates demand for training) | Strong Market Demand — cert existence IS active skill demand |
| `Major flagship event (e.g., Cohesity Connect, Cisco Live)` | Strong Delivery Capacity — delivery channel at scale | Strong Market Demand — nobody attends a training-heavy conference if there's no appetite |

**The AI is instructed to emit cross-pillar badges for these facts** — a single piece of evidence can land in two pillars with appropriate strength tiers in each.

#### Posture: Default-Positive for Categories with Real Skill Demand

High-demand categories (cybersecurity, cloud, DevOps, data science, AI platforms) have near-universal Market Demand because the specialist population is large AND every person in it needs hands-on skills. Moderate categories (ERP, healthcare IT, fintech, legal tech) have real but narrower demand — the specialist population per company is smaller. Categories like CRM, collaboration, and content management have small per-company admin populations even when aggregate user counts are huge, which lowers Market Demand proportionally. Social / Entertainment has no professional training market at all.

#### Category-Aware Baseline

| Category | Baseline | Rationale |
|---|---|---|
| **Cybersecurity** | **14 / 20 (70%)** | Massive specialist population, but the CATEGORY baseline leaves room for product-specific differentiation. A Microsoft Defender or CrowdStrike lands near the top (18-20); a Trellix lands in the middle (16-17); a niche vendor lands lower. |
| **Cloud Infrastructure** | **14 / 20 (70%)** | Massive specialist population — AWS/Azure/GCP certs are career-defining, millions of cloud engineers globally. Room for per-product spread. |
| **AI Platforms & Tooling** | **14 / 20 (70%)** | Surging specialist population — prompt engineering, agent development, LLMOps, fine-tuning are the most-requested skills. |
| **Networking / SDN** | **13 / 20 (65%)** | Large specialist population — network engineers globally. Cisco, Juniper, etc. — long-established cert ecosystems. |
| **DevOps** | **13 / 20 (65%)** | Large specialist population — Kubernetes, Terraform, Docker, CI/CD engineers. |
| **Data Science & Engineering** | **12 / 20 (60%)** | Large specialist population — growing certs (Databricks, Snowflake, dbt), widespread job postings. |
| **Data & Analytics** | **11 / 20 (55%)** | Real specialist market (Tableau, Power BI) — broad but not as deep-hands-on as data engineering. |
| **App Development** | **11 / 20 (55%)** | Language and framework-specific skill markets — large but fragmented. |
| **ERP** | **10 / 20 (50%)** | SAP, Workday, Oracle, NetSuite — specialist consultant population worldwide, but smaller than cyber or cloud. |
| **Infrastructure / Virtualization** | **10 / 20 (50%)** | VMware VCP, Nutanix, Citrix — established but maturing. |
| **Healthcare IT** | **10 / 20 (50%)** | Specialist demand (Epic, Cerner, Meditech) — niche but highly valued. |
| **FinTech** | **10 / 20 (50%)** | Trading platforms, Bloomberg, banking systems — specialist, compliance-driven. |
| **Industrial / OT** | **10 / 20 (50%)** | Niche but real — PLC, SCADA, Rockwell, Siemens skills in specific industries. |
| **Data Protection** | **9 / 20 (45%)** | Vendor-specific cert programs — smaller specialist admin population per company. |
| **Legal Tech** | **9 / 20 (45%)** | Relativity Certified User, e-discovery platforms — niche professional demand. |
| **Unknown / uncategorized** | **9 / 20 (45%)** | Neutral fallback — flag for classification review |
| **CRM** | **8 / 20 (40%)** | Salesforce Trailhead is big in aggregate but the admin/developer population per company is small — 5,000 users, 3 admins. |
| **Collaboration** | **8 / 20 (40%)** | Microsoft 365 admin certs, SharePoint development — real but narrow admin population per company. |
| **Content Management** | **8 / 20 (40%)** | Documentum, Alfresco, Box — specialist admin population per company is small. |
| **Social / Entertainment** *(e.g., Facebook, Instagram, TikTok, Netflix, Spotify)* | **0 / 20 (0%)** | No professional training market |

**Why baselines are lower than they were (2026-04-07 recalibration):** the old baselines (17 for Cybersecurity) ate all the product-specific differentiation — Microsoft Defender and Trellix both capped at 20/20 despite 10x different install bases. New baselines leave room for the product-specific signals (`install_base_scale`, `cert_body_mentions`, `independent_training_market`) to create real spread. A Microsoft-scale product should land at ~18-19, a Trellix-scale product at ~15-16, a niche product at ~12-13.

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +5 | Clear scale signal — active certification ecosystem, ATP network at scale, AI platform at the product level, enterprise validation with named reference customers, high-demand category, major IPO/funding, flagship event at scale |
| **moderate** | +3 | Moderate signal — growing category, mid-size install base, emerging certification, regional training partner presence |
| **weak** | don't emit | Thin signal — small install base, niche category with no cert market, no training partner ecosystem |

#### Signal Categories

| Signal category | What it means |
|---|---|
| `install_base_scale` | Product-specific user population at hands-on depth — differentiates Microsoft Defender vs Trellix vs niche vendor |
| `enterprise_validation` | Named Fortune 500 / Global 2000 reference customers |
| `geographic_reach` | Global presence vs regional vs single country |
| `cert_body_mentions` | CompTIA, EC-Council, SANS, or ISC2 curriculum mentions THIS product — **cross-pillar with Delivery Capacity** (third-party delivered training signal) |
| `independent_training_market` | Coursera / Pluralsight / LinkedIn Learning / Udemy have courses on THIS product — **cross-pillar with Delivery Capacity** |
| `no_independent_training_market` | Cross-pillar penalty — fewer than 3 courses found on the open market |
| `cert_ecosystem` | Vendor's own certification program (not third-party) |
| `competitor_labs` | Other lab platforms sell training for this product — demand is proven |
| `funding_growth` | IPO, Series D, major enterprise momentum |
| `category_demand` | High-demand parent category (cybersecurity, cloud, data, DevOps, AI) |
| `ai_signal` | Product IS or heavily features AI — surging skill demand |

**Key insight (Frank 2026-04-07):** Market Demand is both **category demand** (baseline) AND **product-specific evidence**. The category tells you the ceiling; the product-specific evidence determines where THIS product lands within the category. Lots of people want cybersecurity training — not all of them care about Trellix specifically. Research CompTIA, EC-Council, SANS, ISC2 curricula for product mentions. Research Coursera, Pluralsight, LinkedIn Learning, Udemy for courses on THIS product. Count them and emit a specific answer badge.

#### Badge Naming — Finding-as-Name

| ✗ Wrong | ✓ Right |
|---|---|
| `Market Demand` | `~500 ATPs` |
| `Certification Ecosystem` | `Active Cert Exam` |
| `High Demand Category` | `Cybersecurity Skill` |
| `Install Base` | `~2M Users` |
| `Flagship Event` | `Cisco Live 30K` |
| `AI Platform` | `AI Training Platform` |

Domain examples: `Fortune 100 Clients`, `Series D $200M`, `IPO 2024`, `Global ATP Net`, `Azure Marketplace`, `Top 3 EDR`.

#### Worked Example — Trellix GTI

| Step | Value |
|---|---|
| Baseline (Cybersecurity) | **14** |
| `Top 5 Threat Intel` (strong, `install_base_scale`) | +5 |
| `Active Cert Track` (strong, `cert_ecosystem`) | +5 |
| `CompTIA Curriculum` (strong, `cert_body_mentions`) — cross-pillar with Delivery Capacity Layer 2 | +5 |
| **Final score** | **20 / 20** (capped from 29) |

*Note: Trellix does not have an Authorized Training Partner program, so `atp_alp_program` does NOT fire. But CompTIA does mention threat intelligence in its cybersecurity curriculum, and Coursera has courses on threat intel — those fire as third-party-delivered signals in both Market Demand AND Delivery Capacity Layer 2.*

#### Typical Spread

| Product type | Expected Market Demand |
|---|---|
| Cybersecurity, cloud, AI platforms | **17-20** |
| Networking / SDN, DevOps, data science | **16-20** |
| Data & Analytics | **14-18** |
| ERP, app development, infrastructure, healthcare IT, FinTech, industrial / OT | **12-17** |
| Data Protection, legal tech | **11-15** |
| CRM, collaboration, content management | **10-15** |
| Unknown (pending classification review) | **11 baseline** |
| Social / Entertainment | **0-3** |

---

## Variable badge name rules (Pillar 2)

| Rule | |
|---|---|
| **2-3 words preferred, 4 words absolute max** | Only 4 if every word is short |
| **The name IS the finding, never a topic label** | `SIEM + EDR Integration` (finding) ✓ · `Integration Complexity` (topic) ✗ |
| **Use abbreviations and numerals aggressively** | `Cert` (not Certification), `Config` (not Configuration), `Admin` (not Administrator), `Ops` (not Operations), `Dev` (not Development), `Auth` (not Authentication), `Docs`, `Repo`, `Perf`, `Env`, `Prod`, `App` |
| **Standard industry acronyms — never spell out** | API, CLI, GUI, AI, MFA, NFR, ATP, LMS, RBAC, IDP, IPO, PBT, MCQ, SSO, SIEM, EDR, SOC, PBT |
| **Subject matter terminology is encouraged** | The whole point of Pillar 2 variable names is to capture domain-specific concepts — `Outside Counsel Dependency`, `Lateral Movement Detection`, `Settlement Reconciliation` |
| **NO product names of the company being scored** | The dossier header has the company name — don't repeat it in badges |
| **NO signal_category names as badge names** | `deep_configuration` is the category, not the badge. The badge is `180+ Detection Rules` or similar — the *finding* that belongs in that category |

---

## Pillar 3 — Customer Fit (30%)

*Is this organization a good match for Skillable?*

Everything about the organization in one Pillar. Combines training commitment, build capacity, delivery capacity, and organizational DNA. 30% of the Fit Score — meaningful but never overriding the product truth.

### The Posture — Default-Realistic, Organization-Type Baselines

Customer Fit follows the same default-positive philosophy as Instructional Value: **most real organizations that reach the Inspector dossier are serious about training in some form**, so the framework starts from a reasonable baseline and sculpts up or down based on specific findings. The old framework started dimensions at zero and demanded the AI prove commitment from evidence — that produced pessimistic scores even for vendors with clearly mature training functions.

**The new posture is centered on organization type.** The discovery phase classifies every company into an organization type (ENTERPRISE SOFTWARE, SOFTWARE category-specific, TRAINING ORG, ACADEMIC, SYSTEMS INTEGRATOR, PROFESSIONAL SERVICES, CONTENT DEVELOPMENT, LMS PROVIDER, TECH DISTRIBUTOR). **Each Customer Fit dimension has an organization-type baseline** — a realistic starting point for a company of that type. Positive findings raise the score; negative findings (penalties) lower it. Missing evidence means baseline, not zero.

### Research Asymmetry — Critical for CF Dimensions

Not all Customer Fit dimensions are equally easy to research from outside the firewall. This asymmetry matters for how the AI should apply penalties:

| Dimension | Research difficulty | Penalty philosophy |
|---|---|---|
| **Training Commitment** | Moderate — customer-facing training is public, employee training is harder to see | Penalize when external training evidence is missing, be cautious about employee-only training |
| **Build Capacity** | Hard — internal authoring roles and content team structures are inward-facing | **Cautious penalties only.** Absence of public evidence ≠ evidence of absence. Only penalize when research finds *positive* evidence of outsourcing or confirmed absence of authoring roles. |
| **Delivery Capacity** | Easy — ATPs, events, course calendars, cert infrastructure are all public | **Penalize aggressively.** Absence of public evidence *is* strong evidence of absence. A software vendor with no visible partner network or training calendar really doesn't have one. |
| **Organizational DNA** | Moderate — partnerships are public, RFP processes and internal culture take more inference | Penalize with confidence on well-documented signals (IBM-style build-everything culture, heavy procurement), be cautious on inferred signals |

This asymmetry is baked into the penalty design for each dimension and explicitly taught to the AI in the prompt template.

Pillar 3 uses the **rubric model**, same architecture as Pillar 2. Each badge carries `name`, `strength`, `signal_category`, `color`, and `evidence`. Variable AI-synthesized badge names, fixed signal_category lists, finding-as-name discipline — nothing architectural changes from Pillar 2.

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

*Are you committed to helping your people become genuinely competent — not just checking a training box?*

#### What the Training Commitment Dimension Measures

Training Commitment asks a simple question: **does this organization have a heart for teaching?** It's not about lab infrastructure or delivery mechanisms — those belong to Build Capacity and Delivery Capacity. Training Commitment is about philosophical investment. Does the organization genuinely care that its learners become competent? A training catalog that exists is a start. A named customer enablement team, senior training leadership, and programs across multiple audiences show deeper commitment.

The dimension measures commitment along two axes:

**Breadth of audiences served:**
- **Employees** — do they invest in their own people's skills? (Pluralsight / Udemy / LinkedIn Learning contracts and internal programs count here)
- **Customers** — do they invest in their customers' success and competence?
- **Partners** — do they enable the channel, the ATPs, the resellers?
- **End-users at scale** — do they run learner-facing programs that reach millions?

An organization that trains ONE audience is making some commitment. An organization that trains customers AND partners AND employees is operating at the highest level of Training Commitment. Breadth of audience is as important as depth within any one audience.

**Depth of investment within each audience:**
- Formal customer enablement programs with named teams
- Active certification ecosystems with tested exam pass rates
- Senior training leadership (VP of Education, Chief Learning Officer) — level, not name
- Flagship training events (Cisco Live, Cohesity Connect, Microsoft Ignite with learning tracks)
- Explicit hands-on / lab / interactive / scenario-based language in published programs
- Formal onboarding programs with clear learning outcomes
- Compliance training programs (for regulated industries)

#### What Training Commitment Does NOT Measure

| Not this | That belongs to... |
|---|---|
| Whether they can BUILD labs themselves | **Pillar 3 Build Capacity** |
| Whether they have the delivery infrastructure to reach learners at scale | **Pillar 3 Delivery Capacity** |
| Whether they partner with outside platforms for strategic assets | **Pillar 3 Organizational DNA** |
| Whether the product itself warrants training | Pillar 2 |

**Training Commitment is philosophical, not operational.** An organization can have a deeply committed training culture with limited in-house build capacity — they care about their learners but outsource the heavy lifting. That's captured correctly in the dimension split: high Training Commitment, lower Build Capacity. The two aren't the same thing.

#### Organization-Type Baseline

Applied **before** any findings. The baseline is derived from the organization's type (identified during discovery via the company classification badge). Findings add strong or moderate credits on top; explicit negatives subtract. Capped at 25 / floored at 0.

| Organization Type | Baseline | Rationale |
|---|---|---|
| **TRAINING ORG** *(CompTIA, EC-Council, SANS, Cybrary, Skillsoft, ISACA)* | **23 / 25 (92%)** | Training IS their business. Philosophical commitment is definitional. |
| **ACADEMIC** *(Universities, community colleges, WGU, SLU)* | **22 / 25 (88%)** | Teaching is the mission. Top of the list on heart for teaching — about whether they want people to be good at this, not about labs. |
| **CONTENT DEVELOPMENT** *(GP Strategies and similar)* | **22 / 25 (88%)** | Their whole business is committed to training others. Same tier as training orgs. |
| **ENTERPRISE SOFTWARE** *(Microsoft, SAP, Oracle, Salesforce, Workday)* | **18 / 25 (72%)** | Big vendors invest heavily in training — enablement is core to retention and expansion. Customer + partner + employee programs are the norm. |
| **PROFESSIONAL SERVICES** *(consultancies with training practices)* | **18 / 25 (72%)** | Most professional services firms build training directly into their service offerings — training is part of their value proposition. |
| **SOFTWARE** *(category-specific — Trellix, Cohesity, Nutanix, Hyland, etc.)* | **16 / 25 (64%)** | Specialist vendors generally invest in training, with varying breadth and depth |
| **SYSTEMS INTEGRATOR** *(Deloitte, Accenture, Cognizant, TCS, Infosys)* | **16 / 25 (64%)** | Most SIs build training into their delivery motion for both their consultants and their clients |
| **Unknown / uncategorized** | **13 / 25 (52%)** | Neutral fallback — flag for classification review |
| **LMS PROVIDER** *(Cornerstone, Docebo, SAP SuccessFactors Learning)* | **11 / 25 (44%)** | LMS providers are great at licensing deals and hosting *other people's* training, but often not committed to training themselves or their own learners at depth |
| **TECH DISTRIBUTOR** *(Ingram, CDW, Arrow, Synnex)* | **9 / 25 (36%)** | Distribution-first. Trying to become value-added resellers with training, but historically not great at it |

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +6 | Named customer enablement team · Active certification program with tested exam pass rates · Formal onboarding with learning outcomes · Senior training leadership (VP Education, Chief Learning Officer) · Flagship training event at scale · Explicit hands-on / lab / interactive / scenario-based language in published programs · Strong compliance training program · **Multi-audience commitment** (employees + customers + partners) |
| **moderate** | +3 | Training catalog exists with real substance · Documented programs without scale evidence · Director-level training leader · Some compliance training · Single-audience focus (employees via Pluralsight / Udemy / LinkedIn Learning) · Partner program with modest depth · Customer onboarding without formal learning outcomes |
| **weak** | don't emit | Generic "we offer training" with no detail · No named programs or leaders |

**Note on weak signals:** a training catalog with no substance isn't worth firing a badge for, but it's captured in the baseline — the baseline is the "something exists at this org type" floor. Strong and moderate findings earn credit *on top* of the baseline.

#### Signal Categories — Positive

| Signal | What it means |
|---|---|
| `customer_enablement_team` | Named customer enablement / customer education team |
| `partner_enablement_program` | Formal partner / channel training program |
| `employee_learning_investment` | Internal employee L&D investment (Pluralsight / Udemy / LinkedIn Learning seats, internal programs) |
| `multi_audience_commitment` | Programs targeting employees AND customers AND partners — **breadth signal** |
| `cert_exam_active` | Active certification program with tested exam pass rates |
| `onboarding_program` | Formal customer onboarding with learning outcomes |
| `customer_success_investment` | Dedicated CS team with explicit learning / enablement mandate |
| `training_leadership_level` | Senior training leadership (VP Education, Chief Learning Officer) — level, not name |
| `training_events_at_scale` | Flagship events (Cisco Live, Cohesity Connect, Microsoft Ignite with learning tracks) |
| `hands_on_learning_language` | Explicit hands-on / lab / interactive / scenario-based language in published programs |
| `compliance_training_program` | Regulated-industry compliance training (healthcare, finance, legal) |
| `training_catalog_present` | Training catalog with real substance |

#### Signal Categories — Negative (penalties)

Training Commitment is philosophical — absence of training investment is as diagnostic as presence of it. A vendor that barely talks about training, has no customer enablement, and has no active certification isn't committed, and the score should reflect that.

| Signal | Color | Hit | When it fires |
|---|---|---|---|
| `no_customer_training` | **Amber Risk** | **−4** | **Badge: `No Customer Training`**. Research finds zero evidence of training offered to customers — no customer courses, no enablement programs, no cert paths, no published training calendar. The vendor is not investing in customer competence. |
| `thin_cert_program` | **Amber Risk** | **−3** | **Badge: `Thin Cert Program`**. Certification program is absent entirely, or present only as one or two nominal offerings with no active exam pass rates or career value. |
| `no_customer_success_team` | **Amber Risk** | **−3** | **Badge: `No Customer Success Team`**. No named customer success, customer enablement, or customer onboarding team. Training is not organizationally owned. |
| `minimal_training_language` | **Amber Context** | **−2** | **Badge: `Training Not Prioritized`**. Vendor website, marketing, and investor materials barely mention training, enablement, certification, or customer success. Training is an afterthought, not part of the commercial motion. |

**Penalty math:** penalties subtract from the baseline after positive findings are applied. Dimension score is floored at 0. A specialist software vendor with baseline 16, no customer training, thin certs, and minimal training language could land at 16 − 4 − 3 − 2 = **7 / 25** — a harsh but honest read.

#### Badge Naming — Finding-as-Name

| ✗ Wrong | ✓ Right |
|---|---|
| `Training Commitment` | `Customer Enablement Team` |
| `Certification` | `Active Cert Exam` |
| `Training Leadership` | `VP of Education` |
| `Events` | `Cisco Live 30K` |
| `Hands-on` | `Hands-on Lab Commitment` |

Variable badge name examples: `~200 Course Catalog`, `Cohesity Connect 5K`, `Partner Academy`, `Customer Success Team`, `Multi-Audience Programs`, `Employee LinkedIn Learning`.

#### Worked Examples

**Example 1 — Trellix (SOFTWARE — cybersecurity specialist):**

| Step | Value |
|---|---|
| Baseline (SOFTWARE category-specific) | **16** |
| `Partner Academy` (strong, `partner_enablement_program`) | +6 |
| `Customer Enablement Team` (strong, `customer_enablement_team`) | +6 |
| `Multi-Audience Programs` (strong, `multi_audience_commitment`) | +6 |
| **Final score** | **25 / 25** (capped from 34) |

**Example 2 — CompTIA (TRAINING ORG):**

| Step | Value |
|---|---|
| Baseline (TRAINING ORG) | **23** |
| `Active Cert Exam` (strong, `cert_exam_active`) | +6 |
| **Final score** | **25 / 25** (capped from 29) |

**Example 3 — Cornerstone (LMS PROVIDER):**

| Step | Value |
|---|---|
| Baseline (LMS PROVIDER) | **11** |
| `Training Catalog` (moderate, `training_catalog_present`) | +3 |
| **Final score** | **14 / 25** |

Honest outcome: Cornerstone hosts others' training but isn't deeply committed to training *their own* learners — they facilitate, they don't teach.

#### Typical Spread

| Org type | Expected Training Commitment |
|---|---|
| Training orgs, academic institutions, content development firms | **22-25** |
| Enterprise software, professional services, systems integrators | **18-25** |
| Software vendors (category-specific) | **16-25** (with multi-audience findings) |
| LMS providers, tech distributors | **10-18** |
| Unknown (pending classification review) | **13 baseline** |

---

### 3.2 Build Capacity (cap 20)

*Are you tailoring what you need, or just buying generic training? Are you actually building the hands-on content for your audience?*

#### What the Build Capacity Dimension Measures

Build Capacity asks: **does this organization tailor and build its own training content, or does it consume off-the-shelf content from somewhere else?** The strongest signal is evidence that the organization is actively *creating* technical training — especially hands-on training. The weakest signal is "they buy seats from Pluralsight and call it a training program." Everything else lives between those two poles.

Build Capacity is about **CREATE roles**, not delivery roles. An instructor who teaches is not Build Capacity — an instructor who also authors labs is. An SME who reviews content for accuracy is not Build Capacity — an SME who writes content is. A training department that runs workshops is not Build Capacity — a training department with named Lab Authors, Instructional Designers, and Tech Writers is.

**The strongest possible signal: "they're already building labs."** If the research shows a company has DIY lab authoring happening today — meaning they're already doing what Skillable would help them do better — that's a near-max finding. These companies understand the value of hands-on training and are investing in it. They're the easiest customers to sell to because the premise is already proven.

**Skillable Professional Services can fill a Build Capacity gap.** A company with low Build Capacity but strong Delivery Capacity and Training Commitment is a **Professional Services opportunity** — Skillable can build for them. This is why Build Capacity is weighted lowest within Customer Fit (20 vs. 30 for Delivery Capacity). It's important but not as structurally blocking as Delivery Capacity.

#### What Build Capacity Does NOT Measure

| Not this | That belongs to... |
|---|---|
| Delivery infrastructure (ATPs, LMS, events) | **Pillar 3 Delivery Capacity** |
| Whether they buy Pluralsight / Udemy seats for employees | **Pillar 3 Training Commitment** (employee enablement signal) |
| Whether they run training (workshops, instructors, bootcamps) | **Pillar 3 Delivery Capacity** — delivering is not building |
| SMEs whose role is review or accuracy validation only | Not captured — these are not authors |
| Pure delivery instructors, trainers, workshop leaders | **Pillar 3 Delivery Capacity** |

**Default routing for instructors: Delivery Capacity.** Build Capacity only fires for instructors when research finds explicit dual-role authoring evidence (instructor as lab author, tech writer, or content developer).

#### Organization-Type Baseline — Centered by Design

**Important:** Build Capacity baselines cluster in the middle because **Build Capacity is inward-facing and genuinely hard to verify from external research.** The AI can find partial evidence (job postings, conference talks, Trailblazer Community posts, vendor university branding) but the absence of public evidence doesn't mean internal capacity isn't there. The baselines reflect this uncertainty — most real organizations start in a middle band, and the **positive findings do most of the differentiation** as the AI surfaces evidence of actual authoring roles, named content teams, or DIY lab work.

| Organization Type | Baseline | Rationale |
|---|---|---|
| **CONTENT DEVELOPMENT** *(GP Strategies, el-Training firms)* | **14 / 20 (70%)** | Building training content IS their business — high confidence in some build capacity |
| **ACADEMIC** *(Universities, colleges)* | **12 / 20 (60%)** | Curriculum design is part of the faculty mission, though hands-on lab authoring varies |
| **TRAINING ORG** *(CompTIA, SANS, EC-Council)* | **12 / 20 (60%)** | Strong in-house content is typical, but varies — CompTIA builds, Skillsoft mostly licenses |
| **PROFESSIONAL SERVICES** | **12 / 20 (60%)** | Most build training into engagements, but practice-dependent |
| **SYSTEMS INTEGRATOR** *(Deloitte, Accenture, Cognizant)* | **11 / 20 (55%)** | Often build training into delivery but scale and consistency vary widely |
| **ENTERPRISE SOFTWARE** *(Microsoft, SAP, Oracle, Salesforce)* | **11 / 20 (55%)** | Big vendors typically have dedicated education teams, but hands-on content depth varies |
| **SOFTWARE** *(category-specific)* | **10 / 20 (50%)** | Varies widely — positive findings are what differentiates the genuine builders |
| **Unknown / uncategorized** | **10 / 20 (50%)** | Neutral fallback — flag for classification review |
| **LMS PROVIDER** *(Cornerstone, Docebo)* | **9 / 20 (45%)** | LMS providers facilitate others' content; rarely build hands-on content themselves |
| **TECH DISTRIBUTOR** *(Ingram, CDW, Arrow)* | **9 / 20 (45%)** | Distribution-first; content building is not historically their strength |

**Why the centered distribution?** Under the old, more extreme baselines (17 for Content Development, 6 for Tech Distributor) the baseline *itself* was doing too much of the work. But Build Capacity is hard to verify — we can't really know from outside research whether a given company has 30 Instructional Designers on staff. Centering the baselines and letting positive findings lift or negative findings push down is more honest. A Cisco with documented Lab Author roles should hit 17-20 from positive findings on top of the 11 baseline. A bank with explicit third-party content outsourcing stays near baseline or drops slightly via cautious penalties.

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +5 | **DIY lab authoring evidence (already building labs today)** · Named content team with explicit lab / tech writer / curriculum mandate · Named Instructional Designers · Named Lab Authors · Named Tech Writers / Editors · Product-Training partnership documented as collaborative content development · Documented content development partnerships with external firms |
| **moderate** | +3 | SME participation in content development mentioned · Named training department with some authoring signals · Third-party content firm engagement · Instructors with **explicit dual-role** authoring evidence |
| **weak** | don't emit | Just "training department exists" with no creation evidence · Plain instructor headcount · SMEs whose role is review or accuracy only · Buying off-the-shelf content (Pluralsight, Udemy, LinkedIn Learning) without any tailoring |

#### Signal Categories — Positive

| Signal | What it means |
|---|---|
| `diy_labs` | **Already building labs today** — the strongest signal |
| `content_team_named` | Named education / curriculum / content team explicitly responsible for content creation |
| `instructional_designers` | Named ID role(s) in the organization |
| `lab_authors` | Named lab author role(s) or lab creation practice |
| `tech_writers` | Named tech writer / tech editor role(s) with content creation mandate |
| `product_training_partnership` | Documented collaborative content development between product and training teams |
| `content_partnership` | Documented partnership with external content development firm |
| `instructor_authors_dual_role` | Instructors with explicit dual-role authoring evidence |
| `sme_content_authoring` | SMEs explicitly paired with content authoring (not review-only) |

#### Signal Categories — Negative (penalties — cautious by design)

**Research asymmetry matters here.** Unlike Delivery Capacity (outward-facing, where absence of evidence is strong evidence of absence), Build Capacity is inward-facing. The absence of public evidence does NOT prove the absence of internal capacity. **Only penalize when there is positive evidence of outsourcing or positive evidence that authoring roles don't exist** — not when research simply fails to find evidence.

| Signal | Color | Hit | When it fires |
|---|---|---|---|
| `confirmed_outsourcing` | **Amber Risk** | **−3** | **Badge: `Outsourced Content`**. Research finds explicit statements, case studies, or press releases documenting that the organization buys off-the-shelf content (Pluralsight, Udemy, generic e-learning vendors) and has no internal authoring mandate. The key is *explicit* — vendor partnerships referenced by the company itself. |
| `no_authoring_roles_found` | **Amber Risk** | **−3** | **Badge: `No Content Authors`**. After thorough research (LinkedIn, job postings, company pages), zero evidence of Instructional Designer, Curriculum Developer, Lab Author, or Tech Writer roles. Combined with explicit "we use Pluralsight" language, this becomes diagnostic. |
| `review_only_smes` | **Amber Context** | **−2** | **Badge: `Review-Only SMEs`**. SMEs are mentioned in content processes but only in review / accuracy-validation roles, never as authors. Weak signal of build capacity — they have subject matter expertise but aren't applying it to content creation. |

**Cautious penalty philosophy — the prompt will tell the AI:**

> *When evaluating Build Capacity penalties, be cautious. Do not penalize for absence of evidence — only penalize when you have direct, explicit evidence of outsourcing or of the organization buying off-the-shelf training exclusively. If research is inconclusive on whether internal authoring roles exist, default to baseline and do not penalize. The dimension is inward-facing and internal capacity is genuinely hard to verify from outside.*

The research asymmetry between Delivery Capacity (easy to verify) and Build Capacity (hard to verify) is intentional and documented. Delivery penalties fire aggressively on missing public evidence. Build penalties fire only on direct positive evidence of the negative.

#### Badge Naming — Finding-as-Name

| ✗ Wrong | ✓ Right |
|---|---|
| `Build Capacity` | `DIY Lab Authoring` |
| `Content Team` | `Workday Education Team` |
| `Lab Authors` | `~30 Lab Authors` |
| `Instructional Designers` | `IDs On Staff` |
| `Tech Writers` | `Tech Writer Team` |
| `Content Partnership` | `University Content Partnership` |

#### Worked Examples

**Example 1 — Trellix (SOFTWARE — cybersecurity specialist):**

| Step | Value |
|---|---|
| Baseline (SOFTWARE category-specific) | **10** |
| `Trellix Education Team` (strong, `content_team_named`) | +5 |
| `DIY Lab Authoring` (strong, `diy_labs`) | +5 |
| **Final score** | **20 / 20** (capped) |

**Example 2 — A Bank (buyer-style org, classified SYSTEMS INTEGRATOR for internal IT training practice):**

| Step | Value |
|---|---|
| Baseline (SYSTEMS INTEGRATOR) | **12** |
| No named content team, no DIY labs, buys Pluralsight | no emissions |
| **Final score** | **12 / 20** |

Honest outcome: The bank has moderate Build Capacity baseline reflecting that SIs *generally* build training, but with no findings the specific bank lands at the baseline — suggesting they should be reclassified or that they're a weak Build Capacity fit. Combined with the classification flag, this gives the seller the honest read: "ProServ opportunity."

**Example 3 — GP Strategies (CONTENT DEVELOPMENT):**

| Step | Value |
|---|---|
| Baseline (CONTENT DEVELOPMENT) | **17** |
| `Tech Writer Team` (strong, `tech_writers`) | +5 |
| **Final score** | **20 / 20** (capped from 22) |

#### Typical Spread

| Org type | Expected Build Capacity |
|---|---|
| Content development firms, training orgs with strong in-house content | **17-20** |
| Enterprise software, professional services, academic institutions | **12-20** |
| Category-specific software vendors | **10-20** (depending on in-house investment) |
| LMS providers | **6-14** |
| Tech distributors | **4-12** |
| Unknown (pending classification review) | **10 baseline** |

---

### 3.3 Delivery Capacity (cap 30)

*Once labs exist — whether the customer built them or Skillable Professional Services built them — does the organization have the infrastructure and network to get them to learners at scale?*

#### What the Delivery Capacity Dimension Measures

Delivery Capacity asks: **can this organization actually reach learners at scale with training?** It's measured by the *size and reach* of their delivery infrastructure, not whether they have it at all. Everyone "offers training" in some form — the question is whether the reach is Indiana, the US, the Western Hemisphere, or truly global.

Delivery Capacity is weighted highest within Customer Fit (30 out of 100) because of a **share-of-wallet** reality: having labs = cost, delivering labs to learners = value. Without delivery infrastructure, labs are a cost center that never reaches the audience that would benefit. A customer can have perfect Training Commitment and excellent Build Capacity, but if they have no channel to get the content in front of learners, the commercial case collapses. **Delivery Capacity is where commercial value lives.**

#### Three Delivery Layers — each is a separate signal, layers stack for bonus points

**Delivery capacity is measured across three distinct layers (Frank 2026-04-07).** Each layer is a separate fact. A vendor can have any subset or all three. Each deeper layer ADDS BONUS POINTS on top of the previous — the layers stack:

| Layer | What it is | How to detect | Example badges |
|---|---|---|---|
| **1. Vendor-Delivered** *(base)* | The vendor runs training directly. Official ILT, self-paced portal, vendor-run hands-on labs. Positive signal but bounded to what the vendor alone can reach. | Search the vendor's training / academy / university pages for "instructor-led training," "self-paced courses," "on-demand," "lab exercises." | `Vendor-Delivered ILT`, `Vendor Self-Paced Portal`, `Vendor-Delivered Labs`, `Published Course Calendar` |
| **2. Third-Party-Delivered** *(bonus)* | Independent training in the open market AND cert body curricula. Positive signal because independent trainers don't invest if nobody wants the training. **Cross-pillar with Market Demand.** | Search Coursera, Pluralsight, LinkedIn Learning, Udemy for courses on THIS product (count them). Search CompTIA, EC-Council, SANS, ISC2 curricula for product mentions. | `~15 Pluralsight Courses`, `~5 Coursera Courses`, `CompTIA Curriculum`, `EC-Council Track`, `No Independent Courses Found` (penalty) |
| **3. Auth-Partner-Delivered** *(TOP bonus)* | Formal Authorized Training Partner / Authorized Learning Partner program. Certified partners delivering the vendor's training at scale. ATP/ALP programs are typically more mature than vendor-direct training because they represent scaled multi-partner delivery capability. | Search for "ATP," "Authorized Training Partner," "ALP," "Authorized Learning Partner," "training partner directory," "partner finder." | `Global Partner Network`, `~500 ATPs`, `Regional Partner Network`, `No Training Partners` (penalty) |

**Trellix example:** Trellix has vendor-delivered training (ILT + self-paced + labs on Trellix Education Services) but NO formal ATP / ALP program. The honest answer emits BOTH: `Vendor-Delivered ILT` + `Vendor Self-Paced Portal` + `Vendor-Delivered Labs` (Layer 1 positives) AND `No Training Partners` (Layer 3 penalty). Layer 2 depends on whether Coursera / Pluralsight / CompTIA / SANS actually have Trellix-specific content. Don't conflate "has training" with "has training partners" — they are two separate facts.

Other Delivery Capacity signals:

- **Skillable-partner LMS platforms already in place** — Docebo, Cornerstone, Skillable TMS
- **Flagship training events at scale** — Cohesity Connect, Cisco Live, Microsoft Ignite with hands-on tracks
- **Existing lab platform** — Skillable (expansion), competitor (displacement), or `DIY Lab Platform` (replacement)
- **Global geographic reach** — presence in NAMER + EMEA + APAC vs. one region
- **Certification delivery infrastructure** — Pearson VUE, Certiport, PSI integration

A customer with ATPs spanning 80 countries and a flagship conference with 30K attendees has maximum Delivery Capacity. A customer with a regional training program in a single state does not.

#### Cross-Pillar Compounding with Market Demand

**Certain facts legitimately fire in BOTH Pillar 2 Market Demand AND Pillar 3 Delivery Capacity** — the AI should emit cross-pillar badges when the evidence supports it:

| Fact | Delivery Capacity credits | Market Demand (Pillar 2) credits |
|---|---|---|
| `~500 ATPs globally` | Strong Delivery Capacity — scaled reach | Strong Market Demand — partners don't exist without skill demand |
| `Active cert exam with tested pass rates` | Strong Delivery Capacity — cert delivery infrastructure | Strong Market Demand — certs exist because learners want them |
| `Flagship event (Cisco Live 30K, Cohesity Connect 5K)` | Strong Delivery Capacity — delivery at scale | Strong Market Demand — events attract because demand is real |

The prompt instructs the AI to cross-reference these facts between pillars when emitting badges.

#### What Delivery Capacity Does NOT Measure

| Not this | That belongs to... |
|---|---|
| Content creation roles (IDs, Lab Authors, Tech Writers) | **Pillar 3 Build Capacity** |
| Whether they *care* about training | **Pillar 3 Training Commitment** |
| Whether they partner culturally | **Pillar 3 Organizational DNA** |
| Whether the content itself is good | Not captured in scoring — content quality is a Designer concern |

#### Organization-Type Baseline

| Organization Type | Baseline | Rationale |
|---|---|---|
| **TRAINING ORG** *(CompTIA, SANS, EC-Council, Skillsoft)* | **24 / 30 (80%)** | Delivery IS their business. Global ATP networks, cert delivery, events are definitional. |
| **LMS PROVIDER** *(Cornerstone, Docebo)* | **24 / 30 (80%)** | They ARE a delivery platform — scaled reach is their product |
| **ENTERPRISE SOFTWARE** *(Microsoft, SAP, Oracle, Salesforce, Cisco)* | **22 / 30 (73%)** | Global partner networks, major events, cert programs, established delivery channels |
| **TECH DISTRIBUTOR** *(Ingram, CDW, Arrow, Synnex)* | **22 / 30 (73%)** | Distribution reach IS their core strength, even if training is newer |
| **SYSTEMS INTEGRATOR** *(Deloitte, Accenture, Cognizant, TCS)* | **20 / 30 (67%)** | Global reach via consultant networks, though training delivery is secondary |
| **PROFESSIONAL SERVICES** | **18 / 30 (60%)** | Varies by firm — some have strong delivery networks, some are regional |
| **SOFTWARE** *(category-specific)* | **16 / 30 (53%)** | Specialist vendors vary widely — some have global channels, some are regional |
| **ACADEMIC** | **16 / 30 (53%)** | Strong institutional reach to students, but limited external delivery infrastructure |
| **Unknown / uncategorized** | **16 / 30 (53%)** | Neutral fallback — flag for classification review |
| **CONTENT DEVELOPMENT** *(GP Strategies)* | **14 / 30 (47%)** | They build content but typically rely on clients' channels for delivery |

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +8 | Existing lab platform (Skillable = expansion, competitor name = displacement) · **Large global ATP / learning partner network at scale** · Skillable-partner LMS already in place (Docebo, Cornerstone, Skillable TMS) · Major flagship events with hands-on tracks at scale (10K+ attendees) · Scaled instructor-led delivery network · Certification delivery infrastructure (Pearson VUE, Certiport integration) |
| **moderate** | +4 | `No Lab Platform` (greenfield — opportunity, NOT deficiency) · `DIY Lab Platform` (replacement opportunity) · Regional ATP network · Other LMS in place · Moderate instructor delivery network · Smaller events · Single-region delivery presence |
| **weak** | don't emit | Plain "they offer training" with no named delivery infrastructure |

#### Signal Categories — Positive

| Signal | What it means |
|---|---|
| `lab_platform` *(variable — platform name)* | Existing lab platform — Skillable (expansion), competitor (displacement), DIY (replacement), or `No Lab Platform` (greenfield) |
| `atp_network` | Authorized training partner network — variable-sized (`~500 ATPs`, `Regional ATP Network`, etc.) |
| `lms_partner` | Skillable-partner LMS in place (Docebo, Cornerstone, Skillable TMS) |
| `lms_other` | Other LMS in place — still delivery infrastructure, just not Skillable-native |
| `instructor_delivery_network` | Scaled instructor / trainer network |
| `training_events_scale` | Flagship event with attendance at scale (e.g., Cisco Live, Cohesity Connect) |
| `cert_delivery_infrastructure` | Pearson VUE / Certiport / PSI / Certiverse integration — cert delivery reach |
| `geographic_reach` *(variable)* | Global, NAMER+EMEA, regional — captures delivery footprint |
| `published_course_calendar` | Vendor has a public course registration page / training calendar — real evidence of active ILT delivery |
| `gray_market` | Third-party training exists for the product — demand legitimized, conversation starter |

#### Signal Categories — Negative (penalties)

Customer Fit is diagnosed as much by what's *missing* as by what's present. Delivery Capacity should crater when a software vendor has no delivery infrastructure at all.

| Signal | Color | Hit | When it fires |
|---|---|---|---|
| `no_training_partners` | **Red Blocker** | **−10** | **Badge: `No Training Partners`**. Software vendor with zero ATP / reseller / channel training network. Fires when research finds no evidence of *any* training partners where partners *should* exist (Microsoft, SAP, Cisco, and peers all have them). A hard signal the vendor hasn't invested in delivery. |
| `no_classroom_delivery` | **Red Blocker** | **−10** | **Badge: `No Classroom Delivery`**. Zero evidence of instructor-led training, bootcamps, workshops, or a published course calendar. If nobody — internal OR external — is teaching the product, Delivery Capacity doesn't exist. |
| `no_independent_training_market` | **Amber Risk** | **−4** | **Badge: `No Independent Training`**. The open market hasn't built training on this product. Evidence: fewer than 3 courses found on Coursera, Pluralsight, LinkedIn Learning, or Udemy combined. **Cross-pillar signal** — also fires in Pillar 2 Market Demand as a negative. No independent training = limited delivery reach AND weak skill appetite. |
| `single_region_only` | **Amber Risk** | **−3** | **Badge: `Single-Region Reach`**. Delivery presence limited to one state or country. Real ceiling on reach. |
| `gray_market_only` | **Amber Context** | **−2** | **Badge: `Gray Market Only`**. Training exists only from unaffiliated third parties — the vendor hasn't invested in delivery and has left it to others. Not a blocker, but a signal. |

**Penalty math:** penalties subtract from the baseline after positive findings are applied. Dimension score is floored at 0 — a badly-penalized software vendor can legitimately score 0 / 30 Delivery Capacity, and that's the honest answer.

**Badge naming discipline for penalties.** The badge name describes what's *true about the customer*, not what search we did to prove it. "No Independent Training" is a finding about the customer's delivery reality. "Few Pluralsight Courses" is a description of our research methodology. The methodology lives in the evidence / hover text; the badge is the conclusion.

| ✗ Describes research methodology | ✓ Describes customer reality |
|---|---|
| `Few Pluralsight Courses` | `No Independent Training` |
| `No Evidence of Events` | `No Flagship Events` |
| `Research Found No Partners` | `No Training Partners` |
| `Unable to Find ILT` | `No Classroom Delivery` |

#### Cross-Pillar Compounding — Negatives Too

The cross-pillar insight works in both directions:

| Fact | Pillar 3 Delivery Capacity hit | Pillar 2 Market Demand hit |
|---|---|---|
| `~500 ATPs globally` | +8 (strong positive) | Strong positive — partners don't exist without skill demand |
| `Active cert exam` | +8 (strong positive) | Strong positive — certs exist because learners want them |
| `Cisco Live 30K` | +8 (strong positive) | Strong positive — events attract because demand is real |
| **Fewer than 3 courses on Coursera/Pluralsight/LinkedIn Learning for this product** | **−4 (amber)** | **−3 (amber)** — no open-market training = no skill appetite |
| **No ATP network for a scaled vendor** | **−10 (red)** | **−5 (amber)** — absence of partners suggests absence of demand too |

#### Lab Platform Naming Convention

The lab platform badge **IS** the platform name. No `Lab Platform:` prefix.

| State | Badge name | Color | Strength |
|---|---|---|---|
| Skillable customer (expansion) | `Skillable` | green | strong |
| Competitor (displacement) | `CloudShare`, `Instruqt`, `Skytap`, `Kyndryl`, `ReadyTech`, etc. | amber | strong |
| Greenfield (no incumbent) | `No Lab Platform` | gray Context | moderate |
| Built their own | `DIY Lab Platform` | gray Context | moderate |

**`No Lab Platform` is moderate, not weak.** Greenfield means no competitor to displace — just sell the hands-on premise. That's an opportunity.

#### Badge Naming — Finding-as-Name

Variable examples: `Skillable` · `CloudShare` · `No Lab Platform` · `~500 ATPs` · `Docebo Public` · `Cornerstone Internal` · `Cisco Live 30K` · `Cohesity Connect 5K` · `~200 Trainers` · `Global Reach` · `NAMER+EMEA`.

#### Worked Examples

**Example 1 — Trellix (SOFTWARE — cybersecurity specialist):**

| Step | Value |
|---|---|
| Baseline (SOFTWARE category-specific) | **16** |
| `No Lab Platform` (moderate, greenfield) | +4 |
| `Global Channel Network` (strong, `atp_network`) | +8 |
| `Compliance Training Partners` (moderate, `instructor_delivery_network`) | +4 |
| **Final score** | **30 / 30** (capped from 32) |

**Example 2 — Bank of America (no training org classification, treated as SOFTWARE fallback):**

| Step | Value |
|---|---|
| Baseline (fallback) | **16** |
| No external delivery infrastructure named | no emissions |
| **Final score** | **16 / 30** |

Honest outcome: internal-only delivery audience. The bank reaches its employees, but there's no scaled external learner audience for Skillable to monetize.

**Example 3 — CompTIA (TRAINING ORG):**

| Step | Value |
|---|---|
| Baseline (TRAINING ORG) | **24** |
| `Pearson VUE Partnership` (strong, `cert_delivery_infrastructure`) | +8 |
| **Final score** | **30 / 30** (capped from 32) |

#### Typical Spread

| Org type | Expected Delivery Capacity |
|---|---|
| Training orgs, LMS providers, major enterprise software vendors | **22-30** |
| Tech distributors, systems integrators, professional services | **18-30** |
| Category-specific software vendors | **16-30** (depending on channel reach) |
| Academic institutions, content development firms | **12-20** |
| Unknown (pending classification review) | **16 baseline** |

---

### 3.4 Organizational DNA (cap 25)

*Are you the kind of company that partners strategically with outside platforms to build strategic assets — or are you a "we build everything here" culture?*

#### What the Organizational DNA Dimension Measures

Organizational DNA asks the most consequential partnership question: **if Skillable proposes a strategic relationship to power your hands-on training, will you see it as a strategic partnership or as a procurement line item to squeeze?** Some companies see outside platforms as strategic assets — they happily adopt Salesforce for CRM, Workday for HR, Okta for identity, because building those themselves would be foolish and partnering is part of how they operate. Other companies see every outside vendor as a cost to control, every engagement as an RFP to run, and every partnership as a compliance checkpoint. The first kind of company makes a great Skillable customer. The second kind makes a painful one.

Organizational DNA is the cultural version of this question. It's not about whether they *have* partnerships — most companies have some. It's about whether partnerships are a **strategic competency** of the organization or an exception to the "build everything here" norm.

Strong DNA signals:
- **Multiple kinds of partnerships** — not just one channel program, but technology alliances, delivery partners, content partnerships, integration partners, co-marketing partners
- **Strategic asset partnerships documented** — the company says things like "we partnered with X to build Y" or "our platform integrates deeply with our alliance ecosystem"
- **Platform adoption patterns** — they use Salesforce rather than building their own CRM; Workday rather than building their own HCM; Okta rather than building their own IAM. This is evidence they understand the value of external platforms for non-core work.
- **Formal partner program** — tiered structure, partner certifications, clear value exchange, named alliance leadership
- **Nimble engagement** — accessible contact paths, documented fast decision-making, partner-friendly posture
- **Named partnership leadership** — VP of Partnerships, Head of Alliances, Chief Alliance Officer

Weak DNA patterns (these get penalized):
- **Long RFP processes** — every vendor engagement takes 9+ months, multiple committees, exhaustive questionnaires
- **Heavy procurement orgs** — large vendor management bureaucracy, vendors treated as cost centers to squeeze
- **"We build everything here" culture** — IBM-style, where outside platforms are seen as inferior by default
- **Closed architecture culture** — proprietary everything, no public APIs, no ecosystem investment
- **Hard to engage** — no accessible partner contact paths, bureaucratic slowness at legendary levels

#### What Organizational DNA Does NOT Measure

| Not this | That belongs to... |
|---|---|
| Technical architecture of their PRODUCT (API openness, modularity) | **Pillar 1** — this is a historical routing failure we caught on Trellix |
| "Open Platform Architecture" as a technical claim about the product | **Pillar 1** — not DNA |
| Whether their software is cloud-native vs on-prem | Classification metadata (not scoring) |
| Partnership existence in general — "they have partners" | Too shallow — DNA is about the *cultural pattern*, not the presence of any partnership |
| Whether their training programs are good | **Pillar 3 Training Commitment** |
| Whether they have the network to deliver at scale | **Pillar 3 Delivery Capacity** |

#### Organization-Type Baseline

Per the directive "start in a pretty good place," Organizational DNA baselines lean higher — most real organizations have *some* form of partnership culture, and strongly centralized "we build everything here" cultures are the exception.

| Organization Type | Baseline | Rationale |
|---|---|---|
| **TRAINING ORG** *(CompTIA, SANS, EC-Council)* | **19 / 25 (76%)** | Training organizations operate on partnerships by nature — test centers, content partners, delivery networks |
| **CONTENT DEVELOPMENT** *(GP Strategies)* | **19 / 25 (76%)** | Client-based business — partnerships with clients and platform providers are the model |
| **PROFESSIONAL SERVICES** | **18 / 25 (72%)** | Consultancies partner constantly — alliances with software vendors are core to the model |
| **SYSTEMS INTEGRATOR** *(Deloitte, Accenture, Cognizant)* | **18 / 25 (72%)** | Delivery IS partnership — SIs live on platform alliances |
| **ENTERPRISE SOFTWARE** *(Microsoft, SAP, Oracle, Salesforce)* | **17 / 25 (68%)** | Most big vendors have mature partner ecosystems (though some — IBM-style — are exceptions) |
| **TECH DISTRIBUTOR** *(Ingram, CDW, Arrow)* | **17 / 25 (68%)** | Distribution IS partnership by definition |
| **SOFTWARE** *(category-specific)* | **16 / 25 (64%)** | Varies widely — some have strong partner cultures, some are closed |
| **ACADEMIC** | **15 / 25 (60%)** | Universities partner with industry but institutional bureaucracy creates friction |
| **LMS PROVIDER** *(Cornerstone, Docebo)* | **16 / 25 (64%)** | Platform providers with licensing ecosystems — partnership-dependent |
| **Unknown / uncategorized** | **15 / 25 (60%)** | Neutral fallback — flag for classification review |

#### Strength Tiers

| Strength | Worth | Criterion |
|---|---|---|
| **strong** | +6 | Multiple kinds of partnerships documented (technology + channel + delivery + content) · Strategic asset partnerships (company publicly describes partnering to build something strategic) · Platform buyer evidence (uses Salesforce / Workday / Okta / external platforms instead of building) · Formal partner program with tiers and certifications · Named VP-level partnership leadership · Nimble engagement posture documented |
| **moderate** | +3 | Single partner program (channel OR content but not multiple kinds) · Mixed buyer-builder posture · Some alliance leadership below VP level · Moderate partner friendliness |
| **weak** | don't emit | Generic "they have partners" with no specifics — don't emit |

#### Signal Categories — Positive

| Signal | What it means |
|---|---|
| `many_partnership_types` | Multiple distinct kinds of partnerships (technology, channel, delivery, content, integration) — breadth signal |
| `strategic_asset_partnerships` | Documented examples of partnering to build something strategic together |
| `platform_buyer_behavior` | Uses external platforms for things companies might build in-house (Salesforce for CRM, Workday for HR, Okta for IAM) |
| `formal_channel_program` | Structured partner program with tiers, certifications, incentives, published value exchange |
| `nimble_engagement` | Accessible contacts, fast decision-making posture, documented partner-friendly culture |
| `named_alliance_leadership` | VP of Partnerships, Head of Alliances, Chief Alliance Officer — level, not name |

#### Signal Categories — Negative (penalties)

| Signal | Color | Hit | When it fires |
|---|---|---|---|
| `long_rfp_process` | **Amber Risk** | **−4** | **Badge: `Long RFP Process`**. Documented 9+ month vendor engagement cycles, exhaustive RFP committees, multiple approval gates. Real evidence (press, case studies, vendor complaints) that getting in takes forever. |
| `heavy_procurement` | **Amber Risk** | **−3** | **Badge: `Heavy Procurement`**. Large vendor management bureaucracy; vendors are treated as line items to extract value from rather than strategic relationships. |
| `build_everything_culture` | **Amber Risk** | **−4** | **Badge: `Builds Everything`**. Explicit "we build it ourselves" posture documented — the IBM pattern where outside platforms are treated as inferior by default. |
| `closed_platform_culture` | **Amber Risk** | **−3** | **Badge: `Closed Platform`**. Proprietary everything — no public APIs, no ecosystem investment, no developer community. Their technical culture matches their partnership culture. |
| `hard_to_engage` | **Red Blocker** | **−6** | **Badge: `Hard to Engage`**. Documented hostility or legendary bureaucratic slowness toward outside partners. Fires only with direct evidence — vendor complaints, analyst reports, or public friction. |

**Important — Build vs Buy is retired as a badge.** Historically, `Build vs Buy` was a single badge whose color carried three different findings (Platform Buyer / Mixed / Builds In-House). That violated the finding-as-name discipline — the badge label communicated nothing without a color legend. **The new canonicals are:**

| Old badge | New badge(s) |
|---|---|
| `Build vs Buy` (green) | `Platform Buyer` (positive) — via `platform_buyer_behavior` |
| `Build vs Buy` (gray) | Don't emit — "mixed" is the absence of a strong signal |
| `Build vs Buy` (amber) | `Builds Everything` (negative) — via `build_everything_culture` |

Similarly retired: `Partner Ecosystem` as a topic-labeled single badge, `Integration Maturity` as a topic label, `Ease of Engagement` as a topic label. Their replacements are finding-named (`Multi-Type Partnerships`, `Alliance Program`, `Partner-Friendly`, `Hard to Engage`, etc.).

#### Badge Naming — Finding-as-Name

| ✗ Wrong (topic label) | ✓ Right (finding) |
|---|---|
| `Build vs Buy` | `Platform Buyer` / `Builds Everything` |
| `Partner Ecosystem` | `Multi-Type Partnerships` |
| `Integration Maturity` | `Open Platform Culture` |
| `Ease of Engagement` | `Partner-Friendly` / `Hard to Engage` |
| `Channel Structure` | `500+ Channel Partners` / `Formal Alliance Program` |

Variable badge name examples: `Multi-Type Partnerships`, `~500 Channel Partners`, `Strategic Alliance Program`, `Platform Buyer`, `VP of Alliances`, `Partner-Friendly`, `Long RFP Process`, `Builds Everything`, `Heavy Procurement`, `Hard to Engage`.

#### Worked Examples

**Example 1 — Trellix (SOFTWARE specialist, open partner culture):**

| Step | Value |
|---|---|
| Baseline (SOFTWARE category-specific) | **16** |
| `Multi-Type Partnerships` (strong, `many_partnership_types`) | +6 |
| `Strategic Alliance Program` (strong, `formal_channel_program`) | +6 |
| **Final score** | **25 / 25** (capped from 28) |

**Example 2 — IBM (ENTERPRISE SOFTWARE, closed pattern):**

| Step | Value |
|---|---|
| Baseline (ENTERPRISE SOFTWARE) | **17** |
| `Builds Everything` (amber, `build_everything_culture`) | −4 |
| `Closed Platform` (amber, `closed_platform_culture`) | −3 |
| **Final score** | **10 / 25** |

Honest outcome: IBM has technology alliances but the "we build everything here" culture means a Skillable partnership would be fighting the organization's instincts.

**Example 3 — A Bank (fallback SOFTWARE classification):**

| Step | Value |
|---|---|
| Baseline (fallback) | **16** |
| `Long RFP Process` (amber, `long_rfp_process`) | −4 |
| `Heavy Procurement` (amber, `heavy_procurement`) | −3 |
| **Final score** | **9 / 25** |

Honest outcome: banks have partnerships, but every engagement is a procurement cycle. Organizational DNA correctly flags the cultural friction.

**Example 4 — Deloitte (SYSTEMS INTEGRATOR):**

| Step | Value |
|---|---|
| Baseline (SYSTEMS INTEGRATOR) | **18** |
| `Multi-Type Partnerships` (strong, `many_partnership_types`) | +6 |
| `Platform Buyer` (strong, `platform_buyer_behavior`) | +6 |
| **Final score** | **25 / 25** (capped from 30) |

#### Typical Spread

| Org type | Expected Organizational DNA |
|---|---|
| Training orgs, professional services, systems integrators, content development | **18-25** |
| Open-culture enterprise software vendors (Microsoft, Salesforce, Cisco) | **20-25** |
| Category-specific software vendors with healthy partner cultures | **16-25** |
| Closed-culture enterprise software (IBM pattern) | **8-14** |
| Banks, healthcare systems, government (heavy procurement, long RFPs) | **6-14** |
| Unknown (pending classification review) | **15 baseline** |

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
