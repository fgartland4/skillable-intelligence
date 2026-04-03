# Skillable Intelligence — Product Labability Scoring Reference
## Badge Vocabulary, Color Criteria, and Dimension Outline

This document is the single source of truth for badge names and color logic across all Skillable Intelligence tools (Inspector, Prospector, Designer). Use these exact names — no paraphrasing, no abbreviations.

**Color key:** ✅ Green = Strength or Opportunity · ⚠️ Yellow = Risk or caution · 🚫 Red = Blocker

---

## Composite Score — 40 / 30 / 20 / 10

| Dimension | Weight | The Question |
|---|---|---|
| **Product Labability** | 40% | Can we orchestrate this product? |
| **Instructional Value** | 30% | Does this product need labs? |
| **Organizational Readiness** | 20% | Do they have resources to create and deliver labs? |
| **Market Readiness** | 10% | Is the world interested? |

**Technical Fit Multiplier** (applied by the system after scoring):

| Product Labability Score | Orchestration Method | Multiplier |
|---|---|---|
| ≥32 | Any | 1.0× |
| 24–31 | Hyper-V / ESX / Container / Azure VM / AWS VM | 1.0× |
| 19–31 | Non-datacenter (cloud-only) | 0.75× |
| 10–18 | Any | 0.40× |
| 0–9 | Any | 0.15× |

---

## Dimension 1 — Product Labability (40%)
*"Can we orchestrate this product?"*

### 1.1 Provisioning

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
|---|---|---|---|---|
| `Runs in Hyper-V` | ✅⚠️ | Clean VM install confirmed; Skillable datacenter path | Installs but with complexity (large image, GPU, multi-step) | — |
| `Runs in Azure` | ✅⚠️ | Supported Azure service; Cloud Slice path confirmed | Azure path works but with friction (IaC gaps, non-standard services) | — |
| `Runs in AWS` | ✅⚠️ | Supported AWS service; Cloud Slice path confirmed | AWS path works but unsupported services in use | — |
| `Requires GCP` | ⚠️ | — | Product runs on GCP; Skillable has no native GCP fabric (Custom API path only) | — |
| `Runs in Containers` | ✅⚠️ | Genuinely container-native; all 4 Docker conditions met | Container image exists but dev-use only or disqualifiers present | — |
| `ESX Required` | ⚠️ | — | Nested virtualization or socket licensing requires ESX over Hyper-V (higher cost) | — |
| `Learner Isolation` | ✅⚠️🚫 | Strong per-learner isolation confirmed (dedicated VM, dedicated cloud sub, isolated API instance) | Isolation partial or dependent on vendor configuration | No per-learner isolation; shared tenant only |
| `Provisioning APIs` | ✅⚠️🚫 | Rich provisioning API confirmed; full lifecycle programmable | API exists but incomplete (provision-only, no configure/teardown) | No provisioning API; manual-only setup |
| `Lifecycle APIs` | ✅ | Full provision → configure → score → teardown API coverage confirmed | — | — |
| `Full Tenant Required` | ⚠️ | — | Product requires a full production tenant (not a dev/sandbox instance) — adds provisioning complexity | — |
| `Potential IaC Friction` | ⚠️ | — | IaC templates exist but untested, incomplete, or require significant customization | — |
| `Bare Metal Required` | 🚫 | — | — | Product requires physical hardware orchestration — no virtualization path exists |
| `No Deployment Method` | 🚫 | — | — | No viable deployment path found; cannot provision a lab environment |

**Orchestration Method Score Ranges:**

| Method | Full Lifecycle API | CLI Scripting | Standard | Limited | Complex Install |
|---|---|---|---|---|---|
| Hyper-V *(default)* | 35–40 | 32–36 | 28–32 | 24–28 | 16–24 |
| ESX *(nested virt / socket licensing only)* | 30–35 | 27–31 | 23–27 | 19–23 | 14–20 |
| Container *(all 4 conditions required)* | Native: 24–32 | Limited: 16–24 | — | — | — |

| Method | Full Lifecycle API | Entra ID SSO | Credential Pool | Manual SSO | Trial Account | Credit Card Required |
|---|---|---|---|---|---|---|
| Azure Cloud Slice | 32–38 | 28–35 | 24–30 | 18–24 | 11–18 | 6–11 |
| AWS Cloud Slice | 32–38 | — | 24–30 | — | 11–18 | 6–11 |
| Custom API (BYOC) | 22–28 | — | 16–22 | SSO Only: 11–18 | 6–12 | — |
| Simulation | 8–16 | — | — | — | — | — |

---

### 1.2 Licensing & Accounts

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
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

---

### 1.3 Scoring

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
|---|---|---|---|---|
| `Scoring APIs` | ✅⚠️🚫 | REST API or SDK surface confirmed; lab tasks can be validated programmatically | API exists but limited coverage (some tasks scorable, others GUI-only) | No programmatic scoring surface; GUI-only interface |
| `Script Scorable` | ✅⚠️🚫 | PowerShell, CLI, or config file state can be queried to validate learner work | Scripting surface exists but partial — covers some tasks, not all | No scriptable interface for scoring; AI Vision is the only option |

---

### 1.4 Teardown

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
|---|---|---|---|---|
| `Lifecycle APIs` | ✅ | Full provision → configure → score → teardown API coverage confirmed *(also in 1.1; omit for Hyper-V/VM — snapshot revert is automatic)* | — | — |
| `Full Tenant Required` | ⚠️ | — | Full tenant provisioning required; teardown must explicitly deprovision the tenant *(also in 1.1)* | — |
| `Teardown APIs` | ✅⚠️🚫 | DELETE or deprovision endpoint confirmed; clean teardown programmable | Teardown API exists but incomplete (partial cleanup, orphaned resources possible) | No DELETE endpoint; resources must be manually deprovisioned — ongoing cost risk |

**Penalty Deductions** (stack freely, no floor):

| Condition | Deduction | Flag |
|---|---|---|
| GPU required | −5 | `gpu_required` |
| MFA on admin accounts | −3 | `mfa_required` |
| Provisioning time >30 min | −3 | `long_provisioning` |
| GUI-only setup, no automation path | −2 | `gui_only_setup` |
| No NFR / dev license available | −2 | `no_nfr_license` |
| Socket-based licensing (ESX) AND VM >24 vCPUs | −2 | *(additional to ESX tier discount)* |

**Ceiling Flags** (cap tier regardless of score):

| Flag | Effect |
|---|---|
| `bare_metal_required` | Caps at less_likely (≥20) or not_likely (<20) |
| `no_api_automation` | Same |
| `saas_only` | Same |
| `multi_tenant_only` | Same |

---

## Dimension 2 — Instructional Value (30%)
*"Does this product need labs?"*

### 2.1 Difficult to Master

**Scoring signals** (sum; cap 30 across 2.1 + 2.2 combined):

| Signal | Points |
|---|---|
| Creating AI (product builds/trains/deploys AI — AI IS the product) | +5 |
| Learning AI-embedded features (AI embedded in larger product; requires hands-on practice) | +4 |
| Design & Architecture topics | +5 |
| Configuration & Tuning topics | +5 |
| Deployment & Provisioning topics | +5 |
| Support Scenarios (monitoring, alerting, incident response, lifecycle) | +5 |
| Troubleshooting topics (diagnosing failures in realistic broken states) | +5 |
| Role breadth (multiple distinct personas needing separate lab programs) | +2 |
| Multi-component topology (multiple VMs or services) | +2 |
| Integration complexity (external system connection is primary workflow) | +1 |

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
|---|---|---|---|---|
| `Product Breadth & Depth` | ✅⚠️ | Many distinct workflows and role-specific scenarios; large program opportunity | Limited workflows; one or two lab series at most | — |
| `Workflow Complexity` | ✅⚠️ | Multiple distinct workflow phases (design, configure, deploy, support, troubleshoot) each requiring hands-on practice | Some workflow depth but phases are similar or shallow | — |
| `Configuration Complexity` | ✅⚠️ | Deep configuration decisions with real consequences; many tuning options requiring practiced skill | Some configuration required but options are limited or forgiving | — |
| `Hands-On AI Features` | ✅⚠️ | Specific AI capability that requires iterative hands-on practice to use effectively | AI features present but shallow or passive (no meaningful practice loop) | — |
| `Not Lab Appropriate` | 🚫 | — | — | Consumer or wizard-driven UI; undo/redo; no meaningful consequence of error; tutorial suffices |

### 2.2 Mastery Matters

**Scoring signals** (additive, within cap 30):

| Signal | Points |
|---|---|
| High-stakes skills (misconfiguration causes data loss, breach, compliance failure, downtime) | +3 |
| Adoption & TTV risks (poor adoption or slow TTV is a documented risk) | +2 |
| Certification program (vendor has invested in certifying proficiency) | +2 |

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
|---|---|---|---|---|
| `High-Stakes Skills` | ✅ | Misconfiguration causes data loss, security breach, compliance failure, or significant downtime | — | — |
| `Adoption & TTV Risks` | ⚠️ | — | Poor adoption or slow time-to-value is a documented risk for this product's users | — |
| `Certification Program` | ✅ | Vendor has an active certification program — market has confirmed mastery matters | — | — |

---

## Dimension 3 — Organizational Readiness (20%)
*"Do they have resources to create and deliver labs?"*

**Scoring** (highest applicable combination, cap 20):

| Signal | Points |
|---|---|
| ATP / Learning Partner program | +8 |
| Certification program | +5 |
| Events / conferences | +4 |
| Channel demos & tailored PoCs | +3 |
| Gray market / community training | +3 |
| Formal employee enablement / internal L&D | +2 |
| Existing labs / sandboxes | +1 |

### 3.1 Content Development Capabilities

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
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

| Badge | Possible Colors | ✅ Green when… | ⚠️ Yellow when… | 🚫 Red when… |
|---|---|---|---|---|
| `ATP / Learning Program` | ✅ | Authorized Training Partner or Learning Partner network confirmed; channel credentials and hands-on lab mandates | — | — |
| `ILT / vILT Offerings` | ✅ | Confirmed instructor-led courses — signals curriculum infrastructure and hands-on training culture | — | — |
| `On-Demand Catalog` | ✅ | Self-paced eLearning library with meaningful scale and learner accessibility | — | — |
| `Gray Market Offering` | ⚠️ | — | Third-party unofficial courses exist — demand signal but also competing content | — |
| `LMS / LXP` | ✅⚠️ | Named LMS in use (Docebo, Cornerstone, Moodle, etc.) — delivery infrastructure confirmed; note Docebo/Cornerstone as tight Skillable partners | LMS mentioned but unnamed or unconfirmed | — |

---

## Dimension 4 — Market Readiness (10%)
*"Is the world interested?"*

**Scoring** (highest applicable category + 50% of next highest; AI signals additive and separate):

| Category | Points |
|---|---|
| Cybersecurity · Cloud Infrastructure · Networking/SDN · Data Science & Engineering · Data & Analytics · DevOps | +5 (High) |
| Data Protection · Infrastructure/Virtualization · App Development · ERP/CRM · Healthcare IT · FinTech · Collaboration · Content Mgmt · Legal Tech · Industrial/OT | +2 (Moderate) |
| Simple SaaS · Consumer | +0 (Low) |
| Creating AI (product builds, trains, or deploys AI models) | +5 AI signal |
| Learning AI-embedded features (AI embedded in larger product requiring hands-on practice) | +5 AI signal |
| Large/growing install base | +2 |
| Growing category | +1 |
| Limited competitor labs | +1 |
| **Cap** | **10** |

| Badge | Possible Colors | ✅ / ⚠️ / 🚫 when… |
|---|---|---|
| `Growth Trajectory` | ✅⚠️ | Suffix required: ↑ Growing / → Stable / ↓ Declining. Green = growing category; Yellow = stable or declining |
| `Geographic Reach` | ✅⚠️ | Suffix: Global / NAMER & EMEA / Primarily NAMER / etc. Green = broad global presence; Yellow = narrow geographic reach |
| `Annual Users` | ✅ | Prefix with ~NM in the claim (e.g., "~2M annual users") — large install base is a Strength |
| `Key Customers` | ✅ | Notable enterprise or government customers that validate strategic alignment with Skillable's market |

---

## Verdict / Tier Labels

| Composite Score | Verdict | Labable Tier |
|---|---|---|
| ≥70 | Strong Fit | highly_likely |
| 45–69 | Pursue | likely |
| 20–44 | Monitor | less_likely |
| <20 | Pass | not_likely |

*Ceiling flags override score: any ceiling flag + score ≥20 → less_likely; ceiling flag + score <20 → not_likely.*

---

## Badge Display by Tool

| Tool | What appears |
|---|---|
| **Prospector** | Color only (no badge name, no rationale) |
| **Inspector Caseboard** | Color + badge name (no rationale) |
| **Inspector Dossier hero** | Color + badge name; click-through to evidence |
| **Inspector Dossier drill-down** | Full evidence bullet with source and rationale |
| **Designer** | Green signals become program design inputs; badges not shown |

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
| Green / Yellow / Red | Pass / Partial / Fail |
| Blocker | Red (in badge context) |
| Learner Isolation | SaaS-only / multi-tenant (as disqualifier label) |
| Not Lab Appropriate | Consumer Product / Simple App / Phone App Only |
| Hands-On AI Features | AI Practice Surface / DTDS Coverage |
