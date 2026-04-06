# Skillable Intelligence Platform — Shared Architecture

> This document describes the shared research, evidence, and scoring infrastructure that powers Designer, Inspector, and Prospector. Individual tool documents reference and extend this foundation.

---

## 1. What Problem Does This Platform Solve?

Skillable is a platform-as-a-service company. We are not looking for buyers of a product — we are looking for builders of lab programs on a platform. That distinction changes everything about how qualification works.

A SaaS company asks: does this organization have the budget, the pain point, and the authority to buy our product? Standard CRM scoring, firmographic data, and intent signals can answer that question reasonably well.

Skillable has to ask three harder questions:

1. **Product Labability** — Can Skillable's platform provision, configure, score, and tear down a lab for what this company sells? Does their product have the deployment model, API surface, and technical architecture that Skillable can orchestrate?

2. **Instructional Value** — Would a lab program for this product create meaningful business impact for the customer AND meaningful skill and career impact for their learners? The customer's end users — customers, partners, technical sellers, employees — genuinely need hands-on experience because the product is too complex to learn by reading or watching alone. And people who get hands-on practice will be measurably more confident using the product on the job and more capable of advancing their careers. Products that are too simple, too shallow, or too narrow in audience score low here regardless of orchestrability.

3. **Organizational Readiness** — Does this company have the content team skills, technical enablement maturity, and program leadership to build and sustain a lab program — not just complete a pilot?

All three gates must clear. A technically compatible product at a company with no content capability produces a slow, high-risk program. An organizationally mature company whose product can't be orchestrated hits a wall before the first lab is built. No standard lead generation or CRM scoring tool can evaluate any of these three things — they require deep product research and Skillable-specific platform knowledge.

That is what this platform is built to do.

---

## The Core Architecture: Intelligence Layer + Contextualization Layers

**Intelligence** is the centralized data layer. It accumulates, stores, and maintains company intelligence — the three qualification gates, research signals, scoring, and accumulated company knowledge. It doesn't know or care which tool is asking.

**Each tool is a purpose-built contextualization layer** that parses the same underlying Intelligence and renders it in the form most useful to a specific person doing a specific job:

- **Prospector** — comparison and ranking. Parses Intelligence across a list of companies to tell Marketing and Sales which accounts are worth pursuing and why.
- **Inspector** — depth and evidence. Parses Intelligence at full resolution for sellers and SEs who need to walk into a conversation fully prepared.
- **Designer** — execution. Translates Intelligence signals into a realistic lab program architecture that a content team can actually build.

Every new tool added to the platform is a new contextualization layer — not a new intelligence system. When research or scoring logic improves in Intelligence, every tool improves simultaneously.

---

### How the Platform Came Together

**Designer** was built first — to answer the question of what it would take to give a lab author everything they need to build a great program without starting from a blank page. The intelligence that question required became the foundation for everything else.

**Inspector** emerged when that same intelligence was applied to qualification: could it help sellers and SEs understand whether a company's product is worth pursuing *before* investing in design?

**Prospector** emerged when Marketing asked whether Inspector could run across a list of companies — producing ranked signal for prioritization rather than deep analysis for a single account.

The three tools share a common intelligence stack. The difference is in what each tool does with that intelligence and who it serves.

---

## 2. The Intelligence Stack

Every analysis in this platform runs through three layers:

```
Layer 1: Research Engine         — web search + page fetch + source classification
Layer 2: Evidence Extraction     — Claude reads sources, extracts labeled claims
Layer 3: Scoring + Recommendations — structured rubrics mapped to Skillable capabilities
```

Each layer exists because the previous one isn't enough on its own. Raw search results are noisy and unstructured — the Research Engine turns them into focused, source-attributed text. That text doesn't directly answer labability questions — Evidence Extraction turns it into specific, labeled claims organized by the lab lifecycle. And claims alone don't produce a recommendation — the Scoring layer applies Skillable's accumulated platform knowledge to convert evidence into calibrated scores, flags the constraints that matter, and generates recommendations grounded in what Skillable can actually build and deliver.

These layers are shared across all three tools. Inspector runs the full pipeline — discovery plus deep per-product research. Prospector runs a lighter version (discovery only, one product, no deep research) for throughput. Designer consumes Inspector's scored output and applies additional intelligence to generate program structure, lab content, and environment specifications.

---

## Before You Read the Scores

Skillable Intelligence produces a lot of numbers: scores, percentages, population estimates, revenue ranges, contact names, adoption rates. Before any of those numbers get used in a seller conversation or a business case, there are a few things everyone working with this platform should understand.

**We only read what's publicly accessible.** The Research Engine fetches public web pages, reads search snippets, and scrapes technical documentation. It does not authenticate to any vendor system, access paywalled content, or read internal roadmaps. It sees what a well-prepared SE with a browser and a few hours would see — and sometimes less, because not every vendor documents their deployment model clearly on a public page. When the research finds strong evidence, that's genuine signal. When it doesn't, scores reflect that gap — not a judgment that the product is weak.

**Scores are Claude's interpretation of available evidence — not measurements.** A Product Labability score of 34 means Claude found strong evidence of a clean provisioning path, a REST API with lifecycle coverage, and no blocking dependencies. It does not mean an SE with a test environment confirmed all of this. Every score is calibrated against real Skillable customer deployments (Tanium, Cohesity, Hyland, Microsoft, Cisco, and others) to ensure that a 70 here means the same thing across different analyses and different people running the tool — but calibrated AI judgment is still AI judgment. Treat scores as a strong hypothesis, not a measurement.

**Findings are directional. They are not a substitute for conversation.** The right use of an Inspector or Prospector result is to walk into a discovery call knowing which questions to ask, which risks to probe, and which signals to validate — not to present the score as a verdict. The Essential Technical Resource in each product's recommendation exists specifically for this reason: it is the explicit acknowledgment of the single most important thing the research could not confirm from public sources alone.

**Cached findings may be up to 45 days old.** Both the full analysis cache and the discovery cache have a 45-day TTL. A company's product line, deployment model, API surface, or training ecosystem can change materially in that window. The analysis date is displayed on every result. If you're preparing for a high-stakes conversation on a cached result, consider running a force-refresh — especially if the company has had a recent product announcement, acquisition, or major release.

**AI can and does hallucinate — and some sections are higher-risk than others.** The platform is designed to minimize this through structured prompts, calibration anchors, and server-side validation of arithmetic. But certain outputs carry more inherent uncertainty than others, and the documentation calls these out explicitly where they occur. Two areas where readers should apply particular skepticism:

- **Contacts** — Names and titles are extracted from LinkedIn snippets in search results. These are not scraped directly from LinkedIn profiles; they come from cached Google/Bing snippets that may be months out of date. People change roles constantly. Treat every contact as a starting point for verification, not a confirmed outreach target.
- **Consumption Potential** — Population ranges, hours-per-user estimates, and adoption rates are AI-generated estimates from public signals. They are deliberately conservative (see §5 for the exact values used), but they are still estimates. The right way to use them in a conversation is directional: this is a signals-based estimate of whether this opportunity is a 50-hour-per-year engagement or a 50,000-hour-per-year engagement, not a projection you should take to a CFO without further validation.

None of this undermines the value of the platform. A well-prepared hypothesis grounded in structured research is dramatically more useful than starting a discovery call cold. The goal is to make sure everyone using these findings knows what they are: a strong, research-backed starting point that gets better the moment a human validates it through conversation.

---

## 3. Layer 1 — Research Engine

### 3.1 What It Does

The research engine answers: *"What can we learn about this company and product from publicly available sources?"*

It runs a parallel set of targeted web searches and then fetches and reads the highest-value pages from the results.

### 3.2 Search Queries

The engine runs distinct query categories designed to surface specific signal types:

| Query Category | What It's Looking For | Used By |
|---|---|---|
| **Product portfolio** | What products/solutions does this company sell? | Both |
| **Technical / deployment** | How is the product installed, hosted, or accessed? VM? SaaS? Container? | Both |
| **API / automation** | Is there a REST API, PowerShell module, CLI, or SDK? | Both |
| **Training / certification** | Does the company have a formal training organization, catalog, or cert program? | Both |
| **Partner / ATP** | Is there an Authorized Training Partner program? Channel partner ecosystem? | Both |
| **Customer success / LMS** | Does the company have a customer education function? LMS in use? | Both |
| **Marketplace** | Is the product available on Azure Marketplace or AWS Marketplace? | Inspector |
| **Container / Docker** | Is there an official Docker image or container deployment path? | Inspector |
| **NFR / Developer license** | Can Skillable get a free or evaluation license without a credit card? | Inspector |
| **AI features** | Does the product have AI/Copilot features that require hands-on practice? | Inspector |
| **Competitive labs** | Are there existing hands-on labs from CloudShare, Instruqt, Appsembler, etc.? | Both |
| **Organizational contacts** | Who leads training/enablement? (VP, Director, Program Manager) | Both |

**Concurrency:** All queries run in parallel (up to 12 at a time for Inspector, 11 for Prospector) using a thread pool. This reduces total research time to roughly the duration of the slowest single query.

### 3.3 Page Fetching

After searches return result snippets, the engine selects the highest-signal pages and fetches their full content. Page selection prioritizes:

1. Official vendor documentation (not marketing)
2. Technical/deployment guides
3. Training catalog or learning portal pages
4. Partner program pages

Pages are fetched in parallel (up to 10 at a time). Content is truncated to prevent token overflow while preserving the sections most likely to contain evidence.

### 3.4 Source Data Types

The engine works with four types of source material:

| Type | Examples | What It Signals |
|---|---|---|
| **Technical Documentation** | Install guides, API references, system requirements, deployment guides | Provisioning path, scripting surface, automation potential |
| **Training / Education Content** | Learning portals, course catalogs, certification pages, ATP program pages | Training ecosystem maturity, hands-on demand |
| **Partner / Channel Pages** | Partner portals, reseller programs, ISV pages | Partner program structure, channel enablement |
| **Corporate / Marketing Pages** | About us, press releases, product overview pages | Org type, company scale, product portfolio |
| **Public Profiles** | LinkedIn profiles (via search snippet, not direct scrape) | Training/enablement contacts, org structure |
| **Repository / Marketplace Listings** | GitHub repos, Azure/AWS Marketplace entries, Docker Hub images | Container/API/deployment signals |

**Important:** The engine does not authenticate to any system, does not access paywalled content, and does not use web scraping in the traditional sense — it fetches publicly accessible pages only.

### 3.5 Caching

Research is expensive (API calls, web fetches, Claude tokens). The platform caches aggressively:

- **Analysis cache (45 days):** Full scored analysis keyed by company name. If a fresh cache hit exists, skip everything — return cached results instantly.
- **Discovery cache (45 days):** Discovery findings (product list, partnership signals) keyed by company name. If fresh, skip web searches — jump directly to product selection.
- **Research cache (per-discovery):** Web search results and page contents stored per product within the discovery file. If a product was previously researched, reuse its search results without re-running queries.

---

## 4. Layer 2 — Evidence Extraction

### 4.1 What It Does

Claude reads the fetched sources and extracts structured, labeled evidence claims. These claims are the foundation of every score.

The key design principle: **evidence must be verifiable and specific, not inferred or generic.**

### 4.2 The Evidence Model

Every piece of evidence follows this structure:

```
Claim:       A specific finding, labeled with a bold 2-4 word label
Source URL:  The page where this was found
Source Title: The title of that page
```

**Claim format — bold labels are required:**

```
**Windows Install:** Silent installer confirmed in deployment guide — no manual
                    intervention required during provisioning.

**REST API:** Full CRUD API surface documented at api.vendor.com/v2;
              DELETE endpoint confirmed for teardown automation.

**No DELETE Endpoint — Risk:** Teardown requires manual portal action;
                                resource leak risk in multi-learner sessions.

**MFA Dependency — Risk:** OAuth flow requires interactive MFA on first login;
                            blocks headless automation for scoring.
```

Labels serve three purposes:
1. **Skimmability** — a reviewer can scan labels down a list and understand the scoring logic without reading every claim
2. **Consistency** — the same label across analyses enables comparison and pattern detection
3. **Severity tagging** — `— Risk` and `— Blocker` suffixes trigger visual highlighting in the UI (orange and red respectively)

### 4.3 Evidence Quality Rules

Evidence must follow the lab lifecycle — Provision → Configure → Score → Teardown. This structure ensures evidence tells the full solutioning story, not just the "it exists" story.

| Phase | What to Evidence | Example Label |
|---|---|---|
| **Provision** | How is the environment created? Silent install? Docker pull? API call? | `**Windows Install:**`, `**Docker Image:**`, `**Azure Service:**` |
| **Configure** | What setup steps happen after provisioning? Seed data? Policy creation? | `**REST Seed Data:**`, `**PowerShell Config:**` |
| **Score** | How can learner work be validated? API check? CLI output? Screenshot? | `**REST API:**`, `**PowerShell Module:**`, `**GUI Only — Risk:**` |
| **Teardown** | How is the environment cleaned up? Auto-deprovision? Manual? Leak risk? | `**Auto Teardown:**`, `**No DELETE Endpoint — Risk:**` |

**Maximum 3 evidence items per scoring dimension.** One specific, well-sourced bullet beats three vague ones.

### 4.4 Source Attribution

Every evidence claim carries a source URL and title. This serves two functions:
1. **Traceability** — a reviewer can click through to validate the claim
2. **Confidence calibration** — evidence from official technical documentation is more reliable than evidence from a marketing overview page

---

## 5. Layer 3 — Scoring and Recommendations

### 5.1 How Scores Connect to Skillable Capabilities

Scores are not abstract quality ratings. Every scoring dimension maps directly to a specific question about Skillable's ability to deliver labs for this product.

Each scoring dimension maps directly to one of the three qualification gates — and to a specific question about Skillable's ability to deliver and sustain a lab program.

| Dimension | Gate | The Skillable Question It Answers |
|---|---|---|
| **Product Labability** | Product Labability | Can Skillable's automation platform provision, configure, score, and tear down a lab for this product without manual intervention? |
| **Instructional Value** | Instructional Value | Are there enough meaningful, repeatable technical tasks to justify a multi-lab program — things that require a real environment to learn, not a video or walkthrough? |
| **Organizational Readiness** | Instructional Value | Is there demonstrated demand for hands-on training on this product? Do the customer's end users — customers, partners, sellers, employees — need to learn it, and will hands-on practice make them meaningfully more capable and confident? |
| **Market Fit** | Instructional Value | Does this align with the verticals and skill areas where Skillable has proven lab program ROI? |
| **Organizational Readiness** | Organizational Readiness | Does this company have the organizational infrastructure — content team skills, program leadership, technical readiness — to build and scale a lab program? |

### 5.2 Skillable Path — The Core Qualification Decision

Before any dimension score is calculated, the platform determines which Skillable delivery fabric can support this product. This is the **Skillable Path** — and it drives the entire scoring model.

| Path | Fabric | What It Means |
|---|---|---|
| **Azure Cloud Slice** | Azure infrastructure provisioned per learner via Skillable's Cloud Slice engine | Product runs natively on Azure; Entra ID provides per-learner isolation; richest automation surface |
| **Custom API / BYOC** | Vendor's own cloud API, called by Skillable Life Cycle Actions | Product lives on vendor's infrastructure; Skillable calls vendor APIs to provision/teardown; MFA is a risk |
| **Hyper-V / VM** | Hyper-V, ESX, or Docker fabric; software installed in a VM or container | Product installs on Windows/Linux; the VM image IS the lab; provisioning APIs not required |
| **Simulation** | Simulated interface; no live product instance | Real lab is impractical (cost, duration, data sensitivity); simulation captures workflows only |
| **Unknown** | Cannot determine without more information | Insufficient evidence; scores conservatively; Essential Technical Resource question is required |

**Why the path matters for scoring:** The Product Labability dimension has a different score ceiling for each path. A product that only runs in its vendor's cloud (Custom API / BYOC) with a flawed API cannot score as high as an Azure Cloud Slice product with Entra ID isolation — even if both products are "technically possible" to lab.

### 5.3 The Multiplier Model — Why Low Technical Scores Cap Everything Else

The platform uses a **multiplier** on non-technical dimensions based on the Product Labability score. This prevents a product with a great training ecosystem but a terrible technical story from scoring well overall.

```
If Product Labability score ≥ 32:                      multiplier = 1.0x   (full credit for all dimensions)
If Product Labability score ≥ 24 AND Hyper-V / VM:     multiplier = 1.0x   (VM image solves provisioning)
If Product Labability score ≥ 19:                      multiplier = 0.75x
If Product Labability score ≥ 10:                      multiplier = 0.40x
If Product Labability score < 10:                      multiplier = 0.15x

Total = min(100, Product Labability + round(Other × multiplier))
```

**Why this is valid:** A product that cannot be provisioned or scored automatically is a custom professional services engagement, not a scalable lab product. No amount of organizational readiness makes that viable at scale. The multiplier enforces this constraint in the score rather than leaving it to interpretation.

### 5.4 The Composite Score — Balancing Product Fit and Organizational Readiness

The Composite Score blends Product Labability (can Skillable build the lab?) with Organizational Readiness (can this organization deliver it?).

Scoring uses the 40/30/20/10 composite model. See Scoring-Framework-Core for the 40/30/20/10 composite scoring model.

**Gating rules** (applied before composite calculation):
- Software company with Product score < 30 → Composite capped at 25
- Channel org with Product score < 20 → Composite capped at 30

### 5.5 How Recommendations Are Generated and Why They're Valid

Recommendations are not generic templates. They are generated by Claude from the specific evidence collected for each product, guided by a structured prompt that requires:

1. **Delivery Path** — which specific Skillable fabric and provisioning pattern based on the evidence found
2. **Scoring Approach** — how learner completion will be validated (REST API check, PowerShell script, AI Vision, MCQ) based on the API surface found
3. **Essential Technical Resource** — the single most important open question that blocks a pilot (e.g., "Can the product be silently installed without internet?"), plus which vendor team owns the answer
4. **Next Step** — pursue / pilot with specific qualification step / monitor roadmap / do not pursue, with rationale

**Why they're valid:** Recommendations reference the same labeled evidence claims that the scores are based on. The Delivery Path recommendation is grounded in the provisioning evidence. The Scoring Approach is grounded in the API/CLI evidence. The Essential Technical Resource is the specific gap the evidence couldn't resolve. There are no generic recommendations — if a product has no DELETE endpoint, the recommendation addresses that specifically.

---

## 6. The Skillable Feature Knowledge Layer

The platform's scoring prompts contain embedded knowledge of Skillable's actual capabilities. This knowledge is what makes the gap analysis meaningful rather than generic.

### 6.1 Delivery Fabrics (What Skillable Can Provision)

| Fabric | What It Supports | Key Constraints |
|---|---|---|
| **Hyper-V** | Windows Server, Windows 11, Ubuntu, CentOS VMs | 4 vCPU max; Integration Services required; multi-VM startup delay ~2min/VM |
| **VMware ESX** | Same as Hyper-V; ESX host available for specific customer requirements | Fewer availability guarantees than Hyper-V |
| **Docker** | Linux containers; web-based IDEs via reverse proxy; shared storage volumes | No nested Docker; code assessment via mounted volumes; display via noVNC/web |
| **Azure Cloud Slice** | Any Azure service a learner subscription can provision | Resource Provider registration, quota scaling, lab instance ID tagging for teardown |
| **AWS Cloud Slice** | EC2, S3, IAM, most regional AWS services | Region-specific AMIs; permission boundaries required; some services restricted |
| **Custom API / BYOC** | Vendor clouds via Life Cycle Action scripts (PowerShell/Bash) | Vendor must have API; MFA blocks headless; long provisioning → Pre-Instancing needed |
| **Simulation** | AI Vision + MCQ scoring against recorded screen interactions | No live environment; good for GUI-heavy workflows; limited to observable actions |

### 6.2 Scoring Mechanisms (How Skillable Validates Learner Work)

| Mechanism | How It Works | Best For |
|---|---|---|
| **Activity-Based Assessment (ABA)** | PowerShell/Bash scripts run against live environment, return pass/fail | Configuration tasks, resource creation, policy application |
| **Performance-Based Testing (PBT)** | ABA scripts, but learner submits all at the end (exam mode) | Certification exams, high-stakes assessment |
| **Scoring Bot** | Hidden VM runs assessment scripts against learner environment invisibly | Tamper-proof scoring; learner can't see scoring mechanism |
| **AI Vision** | Screenshot-based; AI evaluates learner screen against rubric | GUI-only workflows with no API surface |
| **MCQ / Fill-in-blank** | Traditional question response | Knowledge checks; where live scoring isn't possible |

### 6.3 Integration Patterns (How Skillable Connects to LMS/LXP)

- **xAPI / SCORM** — lab completion events to any LMS
- **LTI 1.3** — seamless SSO launch from Moodle, Canvas, Cornerstone, Degreed, etc.
- **Webhooks** — real-time completion/score events to vendor systems
- **Credential Pool** — Skillable manages a pool of pre-provisioned accounts; recycles after each learner
- **SSO Bridge** — Skillable generates per-learner credentials for SSO-only systems

### 6.4 Known Blockers (What Skillable Cannot Do)

These constraints are encoded in the scoring prompts so the AI flags them appropriately:

| Blocker | Impact |
|---|---|
| Bare metal required | Cannot virtualize; Hyper-V / VM path impossible |
| Hardware-locked licensing (BIOS GUID) | **Not a blocker** — Skillable VM profiles can pin BIOS GUIDs |
| Credit card required for trial | Risk, not a blocker; flags NFR license question |
| MFA on API authentication | Blocks headless scoring (Custom API / BYOC); MCQ/Vision only |
| Provisioning time > 30 minutes | Risk; Pre-Instancing required (keeps lab "warm" before learner starts) |
| No programmatic teardown | Resource leak risk; requires manual cleanup script |
| GPU required | Not universally available; flags availability question |

---

## 7. What "Good" Looks Like — Reference Benchmarks

The platform's scoring is calibrated against real Skillable customer deployments. Evidence of this calibration appears in the scoring prompts.

| Signal | What It Means for Scoring |
|---|---|
| Product in Azure Marketplace | Strong Azure Cloud Slice signal; near-certain cloud slice path |
| Official Docker Hub image with automated build | Strong Hyper-V / VM signal; VM lab straightforward |
| PowerShell module in PSGallery | Strong scoring surface for Hyper-V / VM; ABA scripts likely |
| Entra ID / Azure SSO support | Azure Cloud Slice path; per-learner isolation free; credential management eliminated |
| Existing CloudShare or Instruqt labs | Confirmed training demand; migration opportunity; Instructional Value signal |
| Named ATP/Learning Partner network with 5+ partners | Strong partner program signal; channel enablement labs likely valuable |
| Active hiring for "Lab Author" or "Training Developer" | Company is building content capability; strong Organizational Readiness signal |
| Pre-sales POC labs (7x win rate increase — Tanium benchmark) | Strongest business case signal available |

---

*Last updated: 2026-03-30*
*Maintained by: Skillable Intelligence platform team*
