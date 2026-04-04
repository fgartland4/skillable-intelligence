# Skillable Intelligence — Scoring Framework Core
## Composite Scoring Model — Signals, Point Values, and Scoring Logic

This document defines how each dimension is scored. For canonical badge names, color criteria, and display standards, see Badging-Framework-Core.

---

## Composite Score — 40 / 30 / 20 / 10

| Dimension | Weight | One-liner |
|---|---|---|
| **Product Labability** | 40% | We can orchestrate this product |
| **Instructional Value** | 30% | This product needs labs |
| **Organizational Readiness** | 20% | They have resources to create and deliver labs |
| **Market Fit** | 10% | The world is interested |

### Technical Fit Multiplier (applied by the system after scoring)

| Product Labability Score | Orchestration Method | Multiplier |
|---|---|---|
| ≥32 | Any | 1.0× |
| 24–31 | Hyper-V / ESX / Container / Azure VM / AWS VM | 1.0× |
| 19–31 | Non-datacenter (cloud-only) | 0.75× |
| 10–18 | Any | 0.40× |
| 0–9 | Any | 0.15× |

---

## Dimension 1 — Product Labability (40%)
*"We can orchestrate this product"*

*See Badging-Framework-Core for canonical badge names.*

### 1.1 Provisioning — Orchestration Method Score Ranges

**Virtualization and Container methods:**

| Method | Full Lifecycle API | CLI Scripting | Standard | Limited | Complex Install |
|---|---|---|---|---|---|
| Hyper-V *(default — always prefer over ESX due to Broadcom pricing)* | 35–40 | 32–36 | 28–32 | 24–28 | 16–24 |
| ESX *(nested virt or socket-based licensing >24 vCPUs only — scores 4–5 pts lower than Hyper-V)* | 30–35 | 27–31 | 23–27 | 19–23 | 14–20 |
| Container Native *(all 4 Docker conditions required)* | 24–32 | 16–24 | — | — | — |

*4 Docker disqualifiers — check all before recommending: (1) dev-use image ≠ full product; (2) Windows GUI required; (3) multi-VM network complexity; (4) not genuinely container-native in production.*

**Cloud Slice and other methods:**

| Method | Full Lifecycle API | Entra ID SSO | Credential Pool | Manual SSO | Trial Account | Credit Card Required |
|---|---|---|---|---|---|---|
| Azure Cloud Slice | 32–38 | 28–35 | 24–30 | 18–24 | 11–18 | 6–11 |
| AWS Cloud Slice | 32–38 | — | 24–30 | — | 11–18 | 6–11 |
| Custom API (BYOC) | 22–28 | — | 16–22 | SSO Only: 11–18 | 6–12 | — |
| Simulation | 8–16 | — | — | — | — | — |

**Simulation — when to recommend:**
Simulation is a provisioning method, not a fallback. It is the correct recommendation when any of the following conditions are present:

| Trigger | Example |
|---|---|
| Cost-prohibitive real provisioning | GPU clusters, high-compute AI services, enterprise data platforms — hundreds of dollars per learner per hour at scale |
| Time-impractical operations | Database migrations, large security scans, big data processing jobs that take hours in the real world |
| All real provisioning paths blocked | GUI-only setup, no deployment method, no API, no VM/container/cloud path (e.g., Workday-pattern products) |

**Rule:** Recommending Simulation does not rescue the score. Score stays in the 8–16 range. Simulation is the right delivery choice — it is not a high-scoring one.

**`No Deployment Method`** applies only when the product cannot be provisioned or simulated in any software environment — purely physical products (heavy equipment, physical machinery). If Simulation is viable, use Simulation instead.

### Penalty Deductions (stack freely, no floor)

| Penalty | Deduction | Flag |
|---|---|---|
| GPU required | −5 | `gpu_required` |
| MFA on admin accounts | −3 | `mfa_required` |
| Provisioning time >30 min | −3 | `long_provisioning` |
| GUI-only setup, no automation path | −2 | `gui_only_setup` |
| No NFR / dev license available | −2 | `no_nfr_license` |
| Socket-based licensing (ESX) AND VM >24 vCPUs | −2 | *(additional to ESX tier discount)* |

### Ceiling Flags (cap tier regardless of score)

| Flag | Effect |
|---|---|
| `bare_metal_required` | Caps at less_likely (≥20) or not_likely (<20) |
| `no_api_automation` | Same |
| `saas_only` | Same |
| `multi_tenant_only` | Same |

---

## Dimension 2 — Instructional Value (30%)
*"This product needs labs"*

*See Badging-Framework-Core for canonical badge names.*

### 2.1 Difficult to Master

**Scoring signals (sum; cap 30 total across both 2.1 and 2.2):**

| Signal | Points |
|---|---|
| Creating AI (product builds/trains/deploys AI models — AI IS the product) | +5 |
| Learning AI-embedded features (AI embedded in a larger product requiring practice) | +4 |
| Design & Architecture topics | +5 |
| Configuration & Tuning topics | +5 |
| Deployment & Provisioning topics | +5 |
| Support Scenarios (monitoring, alerting, incident response, lifecycle) | +5 |
| Troubleshooting topics (diagnosing failures in realistic broken states) | +5 |
| Role breadth (multiple distinct personas needing separate programs) | +2 |
| Multi-component topology (multiple VMs or services) | +2 |
| Integration complexity (external system connection is primary workflow) | +1 |

**Documentation breadth is the primary signal** — count: (1) module count, (2) features per module, (3) options/steps per feature, (4) interoperability count.

**Gate 2 disqualifier:** Consumer apps and wizard-driven UIs with undo/redo and no consequence of error score LOW regardless of feature count. Apply explicitly.

### 2.2 Mastery Matters

**Scoring signals (additive, within cap 30):**

| Signal | Points |
|---|---|
| High-stakes skills (misconfiguration causes data loss, breach, compliance failure, downtime) | +3 |
| Adoption & TTV risks (poor adoption or slow TTV is a documented risk) | +2 |
| Certification program (vendor has invested in certifying proficiency) | +2 |

### 2.3 Lab Format Opportunities

*See Badging-Framework-Core for badge definitions. Trigger signals by scenario type:*

**Collaborative Lab** *(ILT/vILT ONLY — flag this constraint every time):*
- Pattern A — Parallel / Adversarial: Red Team/Blue Team, cyber range, SOC operations, incident response, penetration testing, multi-role attacker/defender, attack traffic simulation
- Pattern B — Sequential / Assembly Line: data pipeline workflows, data science/engineering stacks, DevOps multi-role handoffs, SDLC pipeline stages, role-based handoff workflows

**Break/Fix:**
Troubleshooting content in product docs, advanced certification testing diagnostic skills, incident response training, high-consequence error products (networking, security, infrastructure, database, SRE/DevOps), complex failure modes.

**Simulated Attack** *(cybersecurity products only):*
SIEM, EDR, identity protection, threat detection, network security, incident response, threat hunting, penetration testing, Red/Blue Team references, SOC operations, attack surface documentation.

---

## Dimension 3 — Organizational Readiness (20%)
*"They have resources to create and deliver labs"*

*See Badging-Framework-Core for canonical badge names.*

### Scoring (highest applicable combination, cap 20)

| Signal | Points |
|---|---|
| ATP / Learning Partner program | +8 |
| Certification program | +5 |
| Events / conferences | +4 |
| Channel demos & tailored PoCs | +3 |
| Gray market / community training | +3 |
| Formal employee enablement / internal L&D | +2 |
| Existing labs / sandboxes | +1 |

**Content team maturity hierarchy (observable from public sources):**
- *Strong:* job postings for Lab Author/ID/TW, dedicated learning portal, certification program, ATP program, LMS in use, existing labs/sandboxes
- *Moderate:* small catalog (5–10 courses), training mentioned but no portal, "Academy" branding with no depth
- *Negative:* training is PDF + YouTube, no dedicated learning leadership titles, cert is badge-only with no curriculum

---

## Dimension 4 — Market Fit (10%)
*"The world is interested"*

*See Badging-Framework-Core for canonical badge names.*

### Category Priors (score highest applicable, add 50% of next highest)

| Category | Points |
|---|---|
| Cybersecurity · Cloud Infrastructure · Networking/SDN · Data Science & Engineering · Data & Analytics · DevOps | +5 (High) |
| Data Protection · Infrastructure/Virtualization · App Development · ERP/CRM · Healthcare IT · FinTech · Collaboration · Content Mgmt · Legal Tech · Industrial/OT | +2 (Moderate) |
| Simple SaaS · Consumer | +0 (Low) |

### AI Signals (additive, separate from category prior)

| Signal | Points |
|---|---|
| Creating AI (product builds, trains, or deploys AI models) | +5 |
| Learning AI-embedded features (AI embedded in larger product requiring hands-on practice) | +5 |

### Other Signals (additive)

| Signal | Points |
|---|---|
| Large/growing install base | +2 |
| Growing category | +1 |
| Limited competitor labs | +1 |
| **Cap** | **10** |

### 4.2 Channel Ecosystem

Evidence bullets only — no badges. Content: named GSIs, MSP/VAR network scale, geographic reach limitations.

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

## Roadmap

- **Certification as Market Fit signal** — currently only in 2.2 Mastery Matters. If certification volume data becomes researchable, consider adding to 4.1 as a demand signal.
- **Role-Based Paths** — removed from scoring; pick up in Designer as a program architecture signal.
- **Dedicated SMEs** — removed from scoring; pick up in Designer as a program execution signal.
- **Consumption Potential model** (pending) — per-product table + customer rollup in dossier UI.
