# Skillable Intelligence — Badging Framework Core
## Badge Vocabulary, Color Criteria, and Display Standards

This document is the single source of truth for badge names, color logic, and display standards across all Skillable Intelligence tools (Inspector, Prospector, Designer). Use these exact names — no paraphrasing, no abbreviations.

**Color key:** ✅ Green = Strength or Opportunity · ⚠️ Amber = Risk or caution · 🚫 Red = Blocker

**Qualifier labels** (used inside evidence bullets):
✅ `| Strength:` or `| Opportunity:` · ⚠️ `| Risk:` · 🚫 `| Blocker:`

*For scoring signals, point values, and score ranges, see Scoring-Framework-Core.*

---

## Composite Score — 40 / 30 / 20 / 10

| Dimension | Weight | The Question |
|---|---|---|
| **Product Labability** | 40% | Can we orchestrate this product? |
| **Instructional Value** | 30% | Does this product need labs? |
| **Organizational Readiness** | 20% | Do they have resources to create and deliver labs? |
| **Market Readiness** | 10% | Is the world interested? |

---

## Discovery-Stage Badges

These badges appear on the Caseboard — after discovery research, before the full scoring run. They are not scoring badges; they give the SE early context about the company and its products before selecting what to score.

### Company Classification

Displayed in the page header, immediately right of the company name. Replaces the standalone org-type badge.

All labels display in uppercase, matching the existing org badge style (small font, letter-spaced, all-caps).

**For software companies:** Format is **{CATEGORY} SOFTWARE** — the product category provides the meaningful context, separated by a single space (no dot or separator).

| Rule | Display | Example |
|---|---|---|
| Products span 3+ distinct top-level categories | **ENTERPRISE SOFTWARE** | Microsoft → ENTERPRISE SOFTWARE |
| Products span 1–2 categories | **{CATEGORY} SOFTWARE** | Trellix → CYBERSECURITY SOFTWARE |

**For all other company types:** Display the company type alone — the category is implied by the type and doesn't add value.

| Data value | Display | Example |
|---|---|---|
| `training_organization` | **TRAINING ORG** | EC-Council → TRAINING ORG |
| `academic_institution` | **ACADEMIC** | GCU → ACADEMIC |
| `systems_integrator` | **SYSTEMS INTEGRATOR** | Wipro → SYSTEMS INTEGRATOR |
| `technology_distributor` | **TECH DISTRIBUTOR** | TD Synnex → TECH DISTRIBUTOR |
| `professional_services` | **PROFESSIONAL SERVICES** | Accenture → PROFESSIONAL SERVICES |

### Product Subcategory

Displayed as a badge on each product row, replacing the top-level category badge. Provides a more specific classification so the SE can see the portfolio shape at a glance. Displays in uppercase to match all other badge styling.

Examples by top-level category:

| Top-Level Category | Subcategory examples |
|---|---|
| Cybersecurity | Endpoint Protection, Detection & Response, Data Protection, Network Security, Email Security, Threat Intelligence, SIEM/SOAR, Identity & Access |
| Cloud Infrastructure | Compute, Networking, Storage, Containers & Kubernetes, Serverless, Database, Identity & Access |
| Data Protection | Backup & Recovery, Disaster Recovery, Data Management, Archive & Compliance |
| DevOps | CI/CD, Infrastructure as Code, Monitoring & Observability, Configuration Management |
| ERP/CRM | Financial Management, HR & HCM, Supply Chain, Sales & Marketing, Customer Service |

Subcategories are AI-generated during discovery and may vary. The list above is representative, not exhaustive. The discovery prompt instructs Claude to use concise, industry-standard subcategory names.

### Deployment Model

Displayed as a badge on each product row. Indicates how the vendor delivers the product — an early signal about what Skillable delivery path to expect.

| Data Value | Display Label | Color | Description |
|---|---|---|---|
| `self-hosted` | **Installable** | Green (muted) | Has a downloadable installer, container image, or VM image that runs on customer-managed infrastructure — on-prem servers, VMs, or containers |
| `hybrid` | **Hybrid** | Green (muted) | Available both as an installable product and as a cloud/SaaS service — multiple delivery paths possible |
| `cloud` | **Cloud-Native** | Neutral/dim | Deployed on cloud infrastructure the customer controls (Azure, AWS, GCP subscriptions) — not vendor-hosted SaaS, but not a traditional installer either |
| `saas-only` | **SaaS-Only** | Amber | Vendor-managed only — no installer, no container image, no VM image. Customer accesses via browser; vendor controls all infrastructure. Learner isolation and API questions ahead. |

---

## Dimension 1 — Product Labability (40%)
*"Can we orchestrate this product?"*

### 1.1 Provisioning

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `Runs in Hyper-V` | ✅⚠️ | Clean VM install confirmed; Skillable datacenter path | Installs but with complexity (large image, GPU, multi-step) | — |
| `Runs in Azure` | ✅⚠️ | Supported Azure service; Cloud Slice path confirmed | Azure path works but with friction (IaC gaps, non-standard services) | — |
| `Runs in AWS` | ✅⚠️ | Supported AWS service; Cloud Slice path confirmed | AWS path works but unsupported services in use | — |
| `Requires GCP` | ⚠️ | — | Product runs on GCP; Skillable has no native GCP path (Custom API only) | — |
| `Runs in Containers` | ✅⚠️ | Genuinely container-native; all 4 Docker conditions met | Container image exists but dev-use only or disqualifiers present | — |
| `ESX Required` | ⚠️ | — | Nested virtualization or socket licensing requires ESX over Hyper-V (higher cost) | — |
| `Learner Isolation` | ✅⚠️🚫 | Strong per-learner isolation confirmed (dedicated VM, dedicated cloud sub, isolated API instance) | Isolation partial or dependent on vendor configuration | No per-learner isolation; shared tenant only |
| `Provisioning APIs` | ✅⚠️🚫 | Rich provisioning API confirmed; full lifecycle programmable | API exists but incomplete (provision-only, no configure/teardown) | No provisioning API; manual-only setup |
| `Lifecycle APIs` | ✅ | Full provision → configure → score → teardown API coverage confirmed | — | — |
| `Full Tenant Required` | ⚠️ | — | Product requires a full production tenant (not a dev/sandbox instance) — adds provisioning complexity | — |
| `Potential IaC Friction` | ⚠️ | — | IaC templates exist but untested, incomplete, or require significant customization | — |
| `Simulation` | ⚠️ | — | No real lab path is viable — provisioning is cost-prohibitive, operations are time-impractical (hours-long tasks), or all real delivery paths are blocked. Simulation is the recommended provisioning method. Score range: 8–16. | — |
| `Bare Metal Required` | 🚫 | — | — | Product requires physical hardware orchestration — no virtualization path exists |
| `No Deployment Method` | 🚫 | — | — | Product cannot be provisioned or simulated in any software environment — applies only to purely physical products (e.g., heavy equipment, physical machinery). Not used when Simulation is a viable alternative. |

### 1.2 Licensing & Accounts

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `AuthN/AuthZ APIs` | ✅⚠️🚫 | Bulk account creation and role assignment fully programmable | API exists but limited (create-only, no bulk, no recycle) | No authentication API; manual account creation only |
| `Credential Pool` | ✅⚠️🚫 | Credential pool confirmed viable; accounts recyclable between learners | Pool possible but limited (small supply, slow reset, partial state cleanup) | No recyclable credential mechanism; fresh accounts required every time |
| `Account Recycling` | ✅⚠️🚫 | Accounts reset cleanly between learners; automated wipe confirmed | Recycling possible but requires manual steps or leaves residual state | Accounts cannot be recycled; each learner needs a new account |
| `Supports NFR Accounts` | ✅🚫 | NFR / dev license program confirmed; free lab credentials available without credit card | — | No NFR program found; vendor engagement required before lab authoring can start |
| `High License Cost` | ⚠️ | — | Per-seat or per-core licensing significantly increases per-learner lab cost | — |
| `Tenant Provisioning Lag` | ⚠️ | — | Tenant or environment provisioning takes >5 minutes; may require Pre-Instancing | — |
| `Provisioning Rate Limits` | ⚠️🚫 | — | API rate limits constrain how many learner environments can launch simultaneously | Rate limits make concurrent lab delivery at scale infeasible |
| `Anti-Automation Controls` | ⚠️🚫 | — | CAPTCHA, bot detection, or ToS restrictions complicate automated provisioning | Automation explicitly blocked by vendor terms or technical controls |
| `MFA Required` | ⚠️🚫 | — | MFA required on admin accounts — blocks automated task scoring; MCQ fallback only | MFA cannot be bypassed and blocks all lab delivery automation |
| `Credit Card Required` | 🚫 | — | — | Trial or learner accounts require a credit card; cannot provision at scale |

### 1.3 Scoring

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `Scoring APIs` | ✅⚠️🚫 | REST API or SDK surface confirmed; lab tasks can be validated programmatically | API exists but limited coverage (some tasks scorable, others GUI-only) | No programmatic scoring surface; GUI-only interface |
| `Script Scorable` | ✅⚠️🚫 | PowerShell, CLI, or config file state can be queried to validate learner work | Scripting surface exists but partial — covers some tasks, not all | No scriptable interface for scoring; AI Vision is the only option |

### 1.4 Teardown

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `Lifecycle APIs` | ✅ | Full provision → configure → score → teardown API coverage confirmed *(also in 1.1; omit for Hyper-V/VM — snapshot revert is automatic)* | — | — |
| `Full Tenant Required` | ⚠️ | — | Full tenant provisioning required; teardown must explicitly deprovision the tenant *(also in 1.1)* | — |
| `Teardown APIs` | ✅⚠️🚫 | DELETE or deprovision endpoint confirmed; clean teardown programmable | Teardown API exists but incomplete (partial cleanup, orphaned resources possible) | No DELETE endpoint; resources must be manually deprovisioned — ongoing cost risk |

---

## Dimension 2 — Instructional Value (30%)
*"Does this product need labs?"*

### 2.1 Difficult to Master

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `Product Breadth & Depth` | ✅⚠️ | Many distinct workflows and role-specific scenarios; large program opportunity | Limited workflows; one or two lab series at most | — |
| `Workflow Complexity` | ✅⚠️ | Multiple distinct workflow phases (design, configure, deploy, support, troubleshoot) each requiring hands-on practice | Some workflow depth but phases are similar or shallow | — |
| `Configuration Complexity` | ✅⚠️ | Deep configuration decisions with real consequences; many tuning options requiring practiced skill | Some configuration required but options are limited or forgiving | — |
| `Hands-On AI Features` | ✅⚠️ | Specific AI capability that requires iterative hands-on practice to use effectively | AI features present but shallow or passive (no meaningful practice loop) | — |
| `Not Lab Appropriate` | 🚫 | — | — | Consumer or wizard-driven UI; undo/redo; no meaningful consequence of error; tutorial suffices |

### 2.2 Mastery Matters

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `High-Stakes Skills` | ✅ | Misconfiguration causes data loss, security breach, compliance failure, or significant downtime | — | — |
| `Adoption & TTV Risks` | ⚠️ | — | Poor adoption or slow time-to-value is a documented risk for this product's users | — |
| `Certification Program` | ✅ | Vendor has an active certification program — market has confirmed mastery matters | — | — |

### 2.3 Lab Format Opportunities

These badges surface when research detects signals for specialized lab formats beyond standard VM labs. Always additive — recommend alongside standard labs, never instead of them.

| Badge | Possible Colors | ✅ Green when… |
|---|---|---|
| `Collaborative Lab Opportunity` | ✅ | Multi-role ILT signals detected — Red Team/Blue Team, attacker/defender, cyber range, or sequential assembly-line workflows where multiple learners operate simultaneously *(ILT/vILT only — always flag this constraint)* |
| `Break/Fix Opportunity` | ✅ | Troubleshooting, fault injection, incident response, or diagnostic skill signals detected — advanced learners or certification prep benefit from realistic fault environments |
| `Simulated Attack Opportunity` | ✅ | SIEM, EDR, threat detection, threat hunting, SOC operations, or attack surface signals detected *(cybersecurity products only)* — solo or ILT Red/Blue Team scenario |

---

## Dimension 3 — Organizational Readiness (20%)
*"Do they have resources to create and deliver labs?"*

### 3.1 Content Development Capabilities

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `Dedicated Content Dept` | ✅ | Named training org, content leadership titles, job postings for Lab Author / ID / TW — actively building content capability | — | — |
| `Outsourced Content Creation` | ⚠️ | — | Catalog exists but authoring is outsourced to third-party agencies or freelancers — signals Skillable PS required, not just platform | — |

### 3.2 Content Delivery Ecosystem

**Lab platform badges** — use the exact platform name as the badge label:

| Badge | Color | What it signals |
|---|---|---|
| `Skillable` | ✅ | Existing Skillable customer — expansion opportunity |
| `Instruqt` | ⚠️ | Competitor platform in use — migration opportunity |
| `CloudShare` | ⚠️ | Competitor platform in use — migration opportunity |
| `Kyndryl / Skytap` | ⚠️ | Competitor platform in use — migration opportunity |
| `GoDeploy` | ⚠️ | Competitor platform in use |
| `Vocareum` | ⚠️ | Competitor platform in use |
| `Appsembler` | ⚠️ | Competitor platform in use |
| `ReadyTech` | ⚠️ | Competitor platform in use |
| `DIY` | ⚠️ | Home-built lab infrastructure — migration opportunity |
| `ACI Learning` | ⚠️ | Competitor / content partner |
| `Immersive Labs` | ⚠️ | Competitor platform in use |
| `Hack The Box` | ⚠️ | Competitor platform in use |
| `TryHackMe` | ⚠️ | Competitor platform in use |

**Delivery ecosystem badges:**

| Badge | Possible Colors | ✅ Green when… | ⚠️ Amber when… | 🚫 Red when… |
|---|---|---|---|---|
| `ATP / Learning Program` | ✅ | Authorized Training Partner or Learning Partner network confirmed; channel credentials and hands-on lab mandates | — | — |
| `ILT / vILT Offerings` | ✅ | Confirmed instructor-led courses — signals curriculum infrastructure and hands-on training culture | — | — |
| `On-Demand Catalog` | ✅ | Self-paced eLearning library with meaningful scale and learner accessibility | — | — |
| `Gray Market Offering` | ⚠️ | — | Third-party unofficial courses exist — demand signal but also competing content | — |
| `LMS / LXP` | ✅⚠️ | Named LMS in use (Docebo, Cornerstone, Moodle, etc.) — delivery infrastructure confirmed; note Docebo/Cornerstone as tight Skillable partners | LMS mentioned but unnamed or unconfirmed | — |

---

## Dimension 4 — Market Readiness (10%)
*"Is the world interested?"*

### 4.1 Product Popularity

| Badge | Possible Colors | ✅ / ⚠️ when… |
|---|---|---|
| `Growth Trajectory` | ✅⚠️ | Suffix required: ↑ Growing / → Stable / ↓ Declining. Green = growing category; Amber = stable or declining |
| `Geographic Reach` | ✅⚠️ | Suffix: Global / NAMER & EMEA / Primarily NAMER / etc. Green = broad global presence; Amber = narrow geographic reach |
| `Annual Users` | ✅ | Prefix with ~NM in the claim (e.g., "~2M annual users") — large install base is a Strength |
| `Key Customers` | ✅ | Notable enterprise or government customers that validate strategic alignment with Skillable's market |

---

## Badge Display by Tool

| Tool | What appears |
|---|---|
| **Prospector** | Color only (no badge name, no rationale) |
| **Inspector Caseboard** | Color + badge name (no rationale) |
| **Inspector Dossier hero** | Color + badge name; click-through to evidence |
| **Inspector Dossier drill-down** | Full evidence bullet with source and rationale |
| **Designer** | Green signals become program design inputs; badges not shown |

**Color qualifier labels** (used inside evidence bullets):
- ✅ `| Strength:` or `| Opportunity:`
- ⚠️ `| Risk:` *(Amber)*
- 🚫 `| Blocker:`

**Evidence format (universal):**
`**[Badge Name] | [Qualifier]:** [Specific finding] — [source title]. [What it means for lab delivery.]`

**Badge order within each component:** Positive signals (Strength / Opportunity) first · Caution signals (Risk) · Blockers last.

---

## Vocabulary — Locked Terms

| Use this | Not this |
|---|---|
| Product Labability | Technical Orchestrability |
| Instructional Value | Workflow Complexity / Product Complexity |
| Organizational Readiness | Training Ecosystem / Lab Maturity |
| Market Readiness | Market Fit / Strategic Fit |
| Difficult to Master | Product Depth / Hands-On Necessity |
| Mastery Matters | Stakes / Consequence of Error / Business Impact |
| Provisioning | Gate 1 |
| Licensing & Accounts | Gate 2 / Configure / Accounts & Identity |
| Scoring | Gate 3 |
| Teardown | Gate 4 |
| Green / Amber / Red | Pass / Partial / Fail |
| Blocker | Red (in badge context) |
| Learner Isolation | SaaS-only / multi-tenant (as disqualifier label) |
| Not Lab Appropriate | Consumer Product / Simple App / Phone App Only |
| Hands-On AI Features | AI Practice Surface / DTDS Coverage |
| Collaborative Lab Opportunity | Cyber Range Badge / Shared Lab Badge |
| Break/Fix Opportunity | Fault Injection Badge / Troubleshooting Badge |
| Simulated Attack Opportunity | Attack Simulation Badge |
