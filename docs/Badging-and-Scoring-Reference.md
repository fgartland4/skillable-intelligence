# Skillable Intelligence — Badging and Scoring Reference

This document is the operational reference for all badge names, color criteria, scoring signals, point values, and display standards across Skillable Intelligence tools. It implements the strategic framework defined in **Platform-Foundation.md**, which is the authoritative source for Pillar definitions, Guiding Principles, and platform architecture.

This document also serves as the **in-app explainability layer** (GP3). Each section can be linked from the UX so users can see exactly how any part of the framework works — one source of truth, one click, digestible.

This document reflects best current thinking. As thinking evolves, this document evolves with it — fully synthesized, never appended.

---

## Scoring Hierarchy

- **Fit Score** — composite of three Pillars
  - **Pillars** — weighted components (Product Labability 40%, Instructional Value 30%, Customer Fit 30%)
    - **Dimensions** — four specific areas within each Pillar, each with its own weight out of 100
      - **Requirements** — what the AI researches and evaluates; surface as badges in the UX

Each Pillar scores out of 100 internally, then gets weighted. A Product Labability score of 85/100 contributes 85 x 0.40 = 34 points to the Fit Score.

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
| **Inspector Dossier hero** | Color + badge name; click-through to evidence |
| **Inspector Dossier drill-down** | Full evidence bullet with source and rationale |
| **Designer** | Green signals become program design inputs; badges not shown |

**HubSpot Integration** (data sent, not UX controlled): Fit Score, ACV Potential, HubSpot ICP Context, key badges, product list, contacts. HubSpot ICP Context is regenerated from best current intelligence every time data is sent (GP5).

---

## Two Hero Metrics

| Metric | What it answers | How it's determined |
|---|---|---|
| **Fit Score** | Should we pursue this? | Composite of three Pillars |
| **ACV Potential** | How big is this if we win? | Calculated: population x adoption x hours x rate |

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

Displayed in the page header, right of company name. All labels uppercase.

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

Displayed as a badge on each product row. AI-generated during discovery.

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
| `self-hosted` | **Installable** | Green (muted) | Downloadable installer, container image, or VM image |
| `hybrid` | **Hybrid** | Gray | Available as both installable and cloud/SaaS |
| `cloud` | **Cloud-Native** | Green (muted) | Deployed on customer-controlled cloud infrastructure |
| `saas-only` | **SaaS-Only** | Amber | Vendor-managed only — learner isolation and API questions ahead |

---

## Pillar 1 — Product Labability (40%)

*How labable is this product? Can Skillable deliver a complete lab lifecycle?*

The gatekeeper. If this fails, nothing else matters. Provisioning determines difficulty for everything else — when a product runs in Skillable's infrastructure (VM, container, Cloud Slice), the other dimensions are largely within Skillable's control. When a product runs in the vendor's own cloud, every dimension depends on the vendor's APIs.

| Dimension | Weight | Question |
|---|---|---|
| Provisioning | 35 | How do we get this product into Skillable? |
| Lab Access | 25 | Can we get people in with their own identity, reliably, at scale? |
| Scoring | 15 | Can we assess what they did, and how granularly? |
| Teardown | 25 | Can we clean it up when it's over? |

### 1.1 Provisioning (35 pts)

*How do we get this product into Skillable?*

#### Scoring — VM and Container

| Method | Strong | Moderate | Weak |
|---|---|---|---|
| **Hyper-V** (default) | 30-35 | 21-30 | 14-21 |
| **ESX** (4-5 pts lower) | 26-31 | 17-26 | 12-17 |
| **Container** | 21-28 | 14-21 | — |

Container disqualifiers: (1) dev-use image only; (2) Windows GUI required; (3) multi-VM network complexity; (4) not genuinely container-native.

#### Scoring — Cloud and Other

| Method | Strong | Moderate | Weak |
|---|---|---|---|
| **Azure Cloud Slice** | 28-33 | 16-28 | 5-16 |
| **AWS Cloud Slice** | 28-33 | 16-28 | 5-16 |
| **Custom API (BYOC)** | 19-25 | 10-19 | 5-10 |
| **Simulation** | 7-14 | — | — |

Simulation is a provisioning method, not a fallback. Correct when real provisioning is cost-prohibitive, time-impractical, or all paths are blocked. Does not rescue the score.

#### Provisioning Badges

| Badge | Green | Amber | Red |
|---|---|---|---|
| **Runs in Hyper-V** | Clean VM install confirmed | Installs with complexity | — |
| **Runs in Azure** | Supported Azure service | Azure path with friction | — |
| **Runs in AWS** | Supported AWS service | AWS path with friction | — |
| **Requires GCP** | — | No native Skillable GCP path | — |
| **Runs in Containers** | Container-native confirmed | Image exists but disqualifiers | — |
| **ESX Required** | — | Nested virt or socket licensing | — |
| **Simulation** | — | No real lab path viable | — |
| **Bare Metal Required** | — | — | Physical hardware required |
| **No Deployment Method** | — | — | Cannot be provisioned or simulated |

#### Provisioning Penalties (deduct from base)

| Penalty | Deduction |
|---|---|
| GPU required | -5 |
| GUI-only setup | -5 |
| Provisioning time >30 min | -3 |
| No NFR / dev license | -2 |
| Socket licensing (ESX) + >24 vCPUs | -2 |

#### Ceiling Flags

| Flag | Effect |
|---|---|
| `bare_metal_required` | Caps at Monitor (>=20) or Pass (<20) |
| `no_api_automation` | Same |
| `saas_only` | Same |
| `multi_tenant_only` | Same |

---

### 1.2 Lab Access (25 pts)

*Can we get people in with their own identity, reliably, at scale?*

#### Lab Access Scoring (base + penalties)

| Item | Score | Color |
|---|---|---|
| Full Lifecycle API | +21 to +25 | Green |
| Entra ID SSO | +18 to +22 | Green |
| Credential Pool | +16 to +20 | Green |
| NFR Accounts Available | +14 to +18 | Green |
| Manual SSO | +10 to +14 | Amber |
| Trial Account | +5 to +10 | Amber |
| Credit Card Required | -10 | Red |
| MFA Required | -10 | Red |
| Anti-Automation Controls | -5 | Red |
| Rate Limits | -5 | Red |
| Tenant Provisioning Lag | -5 | Red |
| High License Cost | -5 | Red |

Floor: 0. Badges name the solution (e.g., "NFR Accounts Available" not "Account Creation"). Penalties are red badges.

---

### 1.3 Scoring (15 pts)

*Can we assess what they did, and how granularly?*

| Item | Score | Color |
|---|---|---|
| API Scorable (rich) | +13 to +15 | Green |
| API Scorable (partial) | +9 to +13 | Amber |
| Script Scorable (strong) | +11 to +14 | Green |
| Script Scorable (partial) | +7 to +11 | Amber |
| Simulation Scorable | +7 to +10 | Amber |
| AI Vision Scorable | +5 to +8 | Amber |
| MCQ Scorable | +3 to +5 | Amber |

Scoring always has a fallback (AI Vision, MCQ). The score reflects the quality of the method.

---

### 1.4 Teardown (25 pts)

*Can we clean it up when it's over?*

For VM/container labs, teardown is automatic and scores full marks. Badges only surface when there's a finding.

| Item | Score | Color |
|---|---|---|
| Automatic (VM/Container) | +25 | Green |
| Teardown APIs (full) | +20 to +25 | Green |
| Teardown APIs (partial) | +12 to +20 | Amber |
| No Teardown API | -10 | Red |
| Orphan Risk | -5 | Red |

Floor: 0.

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
| Product Complexity | 40 | Is this product hard enough to require hands-on practice? |
| Mastery Stakes | 25 | How much does competence matter? |
| Lab Versatility | 15 | What kinds of hands-on experiences can we build? |
| Market Demand | 20 | Does the broader market validate the need? |

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
| Training Commitment | 25 | Have they invested in training? What's the evidence? |
| Organizational DNA | 25 | Are they the kind of company that partners and builds training? |
| Delivery Capacity | 30 | Can they get labs to learners at scale? |
| Build Capacity | 20 | Can they create the labs? |

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
