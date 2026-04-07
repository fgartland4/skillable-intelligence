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

## Pillar 2 — Instructional Value (30%)

*Does this product have instructional value for hands-on training?*

The commercial case. Measures whether this product genuinely warrants hands-on lab experiences. Combined with Product Labability, these two product-level pillars represent 70% of the Fit Score.

| Dimension | Weight | Question |
|---|---|---|
| PRODUCT COMPLEXITY | 40 | Is this product hard enough to require hands-on practice? |
| MASTERY STAKES | 25 | How much does competence matter? |
| LAB VERSATILITY | 15 | What kinds of hands-on experiences can we build? |
| MARKET DEMAND | 20 | Does the broader market validate the need? |

### 2.1 Product Complexity (40 pts)

*Is this product hard enough to require hands-on practice?*

#### Scoring Signals

| Signal | Points |
|---|---|
| Design & Architecture topics | +5 |
| Configuration & Tuning topics | +5 |
| Deployment & Provisioning topics | +5 |
| Support Scenarios (monitoring, alerting, incident response) | +5 |
| Troubleshooting topics | +5 |
| Creating AI (product builds/trains/deploys AI) | +5 |
| Learning AI-embedded features | +4 |
| Integration complexity (external systems are primary workflow) | +3 |
| Role breadth (multiple personas need separate programs) | +2 |
| Multi-component topology (multiple VMs or services) | +2 |
| Consumer Grade | -20 |
| Simple UX | -15 |

Documentation breadth is the primary signal — count modules, features per module, options per feature, interoperability.

Cap: 40.

#### Badges

| Badge | Green | Amber | Red |
|---|---|---|---|
| **Deep Configuration** | Many options, real consequences | Some config, limited | — |
| **Multi-Phase Workflow** | Multiple distinct phases | Some depth, similar phases | — |
| **Role Diversity** | Many personas need separate programs | Few roles, not distinct | — |
| **Troubleshooting** | Rich fault scenarios confirmed | Some troubleshooting, limited | — |
| **Complex Networking** | VLANs, routing, multi-network topologies | Some networking, straightforward | — |
| **Integration Complexity** | External systems are primary workflow | Some integrations | — |
| **AI Practice Required** | AI features need iterative practice | AI present but shallow | — |
| **Consumer Grade** | — | Might be consumer-oriented (inferred) | Consumer app confirmed |
| **Simple UX** | — | Might be too simple (inferred) | Straightforward interface confirmed |

---

### 2.2 Mastery Stakes (25 pts)

*How much does competence matter?*

#### Scoring Signals

| Signal | Points |
|---|---|
| High-stakes skills (misconfiguration causes breach, data loss, compliance failure, downtime) | +10 |
| Steep learning curve (long path from beginner to competent, multiple stages) | +8 |
| Adoption risk (poor adoption or slow TTV is documented) | +7 |

Cap: 25.

#### Badges

| Badge | Green | Amber |
|---|---|---|
| **High-Stakes Skills** | Misconfiguration causes real harm | Stakes exist but moderate |
| **Steep Learning Curve** | Long path to competence, multiple stages | Some learning curve but manageable |
| **Adoption Risk** | Poor adoption is a documented concern | Some adoption challenges |

---

### 2.3 Lab Versatility (15 pts)

*What kinds of hands-on experiences can we build?*

These are special, high-value lab types — not the standard step-by-step labs everyone builds. The AI picks 1-2 that fit the specific product from the menu below. Most simple products get none.

These badges serve dual purpose: in Inspector, they provide **conversational competence** for sellers. In Designer, they feed **program recommendations**.

#### Lab Type Menu (AI picks 1-2 per product)

| Badge | What it signals | Likely product types |
|---|---|---|
| **Red vs Blue** | Adversarial team scenarios | Cybersecurity — EDR, SIEM, network security |
| **Simulated Attack** | Realistic attack, learner responds | Cybersecurity — any defensive product |
| **Incident Response** | Production down, diagnose under pressure | Infrastructure, security, cloud, databases |
| **Break/Fix** | Something's broken, figure it out | Broad — complex failure modes |
| **Team Handoff** | Multi-person sequential workflow | DevOps, data engineering, SDLC |
| **Bug Bounty** | Find the flaws — competitive discovery | Development platforms, data, security |
| **Cyber Range** | Full realistic network, live threats | Network security, SOC operations |
| **Performance Tuning** | System works but needs optimization | Databases, infrastructure, cloud, data |
| **Migration Lab** | Move from A to B | Enterprise software, cloud, infrastructure |
| **Architecture Challenge** | Design and build from requirements | Cloud, infrastructure, networking, data |
| **Compliance Audit** | Validate configurations against regulations | Healthcare, finance, security, regulated |
| **Disaster Recovery** | Systems failed, recover operations | Infrastructure, cloud, data protection |

Scoring: +5 per badge found, cap 15. All badges are green (opportunities).

---

### 2.4 Market Demand (20 pts)

*Does the broader market validate the need for hands-on training on this product?*

The AI looks at company-specific signals first, product signals second, category as the floor.

#### Category Priors

| Category | Points |
|---|---|
| Cybersecurity, Cloud Infrastructure, Networking/SDN, Data Science & Engineering, Data & Analytics, DevOps | +8 (High) |
| Data Protection, Infrastructure/Virtualization, App Development, ERP/CRM, Healthcare IT, FinTech, Collaboration, Content Management, Legal Tech, Industrial/OT | +4 (Moderate) |
| Simple SaaS, Consumer | +0 (Low) |

#### AI Signals

| Signal | Points |
|---|---|
| Creating AI (product builds, trains, deploys AI) | +3 |
| Learning AI-embedded features (hands-on practice needed) | +3 |

#### Other Signals

| Signal | Points |
|---|---|
| Active Certification (credentialing ecosystem) | +2 |
| Competitor Labs Confirmed (other providers invest) | +2 |
| Large/growing install base | +2 |
| Growing category | +1 |

Cap: 20.

#### Market Demand Badges (variable-driven)

| Area | Example badge text | Color logic |
|---|---|---|
| Company growth | **Rapid Growth**, **Series D $200M**, **IPO 2024**, **Layoffs Reported** | Green / Amber |
| Install base | **~2M Users**, **~50K Users**, **~500 Users** | Green / Gray / Amber |
| Geography | **Global**, **NAMER & EMEA**, **US Only**, **APAC Only** | Green / Gray |
| Certification | **Active Certification**, **Emerging Certification** | Green / Gray |
| Competitor labs | **Competitor Labs Confirmed** | Green |
| Category | **High-Demand Category**, **AI-Powered Product**, **AI Platform** | Green |
| Enterprise validation | **Enterprise Validated** | Green |

---

## Pillar 3 — Customer Fit (30%)

*Is this organization a good match for Skillable?*

Everything about the organization in one Pillar. Combines training commitment, organizational character, delivery capacity, and build capability. 30% of the Fit Score — meaningful but never overriding the product truth.

| Dimension | Weight | Question |
|---|---|---|
| TRAINING COMMITMENT | 25 | Have they invested in training? What's the evidence? |
| ORGANIZATIONAL DNA | 25 | Are they the kind of company that partners and builds training? |
| DELIVERY CAPACITY | 30 | Can they get labs to learners at scale? |
| BUILD CAPACITY | 20 | Can they create the labs? |

### 3.1 Training Commitment (25 pts)

*Have they invested in training? What's the evidence?*

Badges are evidence of organizational commitment across three motivation categories. The three motivations (product adoption, skill development, compliance & risk) also serve as a **framing variable** — they shape how recommendations are communicated, not just scored.

#### Badges

**Product Adoption evidence:**

| Badge | Green | Amber |
|---|---|---|
| **Customer Enablement** | Dedicated program confirmed | Mentioned but unstructured |
| **Customer Success** | Dedicated CS team confirmed | Mentioned but unclear scope |
| **Channel Enablement** | Partner training program confirmed | Channel exists, no formal enablement |

**Skill Development evidence:**

| Badge | Green | Amber |
|---|---|---|
| **Certification Program** | Active certification with exams | Mentioned, no active exams |
| **Training Catalog** | Published courses, meaningful scale | Small catalog or shallow |

**Compliance & Risk evidence:**

| Badge | Green | Gray |
|---|---|---|
| **Regulated Industry** | Healthcare, finance, cybersecurity — compliance inherent | Some regulation, not compliance-driven |
| **Compliance Training Program** | Training built around regulatory requirements | — |
| **Audit Requirements** | External audits require demonstrated competence | — |

**Cross-cutting:**

| Badge | Green | Gray | Amber |
|---|---|---|---|
| **Training Leadership** | C-level or VP dedicated to learning/enablement | Director-level training leader | Managers only |
| **Training Culture** | Training permeates the business — multiple teams across the lifecycle | Some investment, concentrated in one area | Minimal — one or two people |

---

### 3.2 Organizational DNA (25 pts)

*Are they the kind of company that partners and builds training programs?*

The character of the organization — do they partner or build in-house? Are they easy or hard to do business with? All badges are variable-driven.

| Badge area | Example badge text | Green | Gray | Amber |
|---|---|---|---|---|
| Partner ecosystem | **~500 ATPs**, **Strong Channel Program** | Strong partner network | Some partnerships | **No Partner Program**, **Limited Partners** |
| Build vs Buy | **Platform Buyer**, **Mixed Approach** | Uses external platforms | Some build, some buy | **Builds In-House** |
| Integration maturity | **Open Platform**, **API Available** | Rich APIs, marketplace, SDKs | APIs exist but limited | **Closed System** |
| Ease of engagement | **Accessible**, **Complex Organization** | Mid-size, partner-friendly | Large but workable | **Hard to Engage** |

---

### 3.3 Delivery Capacity (30 pts)

*Can they get labs to learners at scale?*

Weighted highest within Customer Fit. Having labs = cost. Delivering labs = value. Without delivery channels, labs never reach learners.

#### Delivery Badges

| Badge | Color logic |
|---|---|
| **ATP / Learning Partners** | Green = scaled network. Amber = limited. |
| **{LMS Name} (Public/Internal)** | Green = Skillable partner (Docebo, Cornerstone, Skillable TMS). Gray = other LMS. Variable: shows specific platform + audience. |
| **{Lab Platform Name}** | Green = Skillable (expansion). Amber = competitor (migration). DIY noted in evidence. |
| **Gray Market Offering** | Amber = third-party training exists — conversation starter. |

Skillable TMS is green — our own platform.

---

### 3.4 Build Capacity (20 pts)

*Can they create the labs?*

Weighted lowest because Skillable Professional Services or partners fill this gap. Low Build Capacity + strong Delivery Capacity = **Professional Services Opportunity**.

| Badge | Green | Amber |
|---|---|---|
| **Content Dev Team** | Named training org, Lab Authors, IDs, Tech Writers | — |
| **Technical Build Team** | Can build lab environments, not just content | — |
| **DIY Labs** | Already building labs themselves — have the skills | — |
| **Content Outsourcing** | — | Third parties build content — ProServ opportunity |

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
