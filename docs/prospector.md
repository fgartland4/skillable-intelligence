# Skillable Intelligence — Prospector

> Prospector parses Skillable Intelligence across a list of companies — producing a ranked table of qualification signals, partnership indicators, and outreach contacts so you know exactly where to focus before you invest a single sales cycle.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md). For guidance on how to interpret findings, confidence levels, and where hallucination risk is highest, see [Before You Read the Scores](intelligence-platform.md#before-you-read-the-scores).

---

## Why Prospector Exists

Prospector is the comparison and prioritization contextualization layer of Skillable Intelligence. It takes the same centralized company intelligence — the three qualification gates, the research signals, the scoring — and renders it in the form most useful for ranking and comparing a list of companies. The goal is not depth on any one account. The goal is signal across many accounts: which ones clear all three gates well enough to be worth pursuing, and which ones don't.

The three gates Prospector evaluates for every company in a batch:
- **Product Labability:** Can Skillable provision and orchestrate labs for this company's products?
- **Instructional Value:** Is the product technically rich enough to justify a lab program?
- **Organizational Readiness:** Does this company have the content team maturity and program infrastructure to build and sustain one?

What makes Prospector more than a fast Google search is what it's scoring against. The research runs those signals through Skillable's accumulated knowledge of what actually makes a lab program viable — which deployment models Skillable can orchestrate, which technical patterns are hard blockers vs. manageable risks, and which organizational signals genuinely predict a successful program.

The Workday example makes this concrete. Massive install base. A dedicated Workday Learning division with a serious partner program. Strong organizational signals across the board — Instructional Value and Organizational Readiness both pass. But Workday is pure multi-tenant SaaS with no per-learner environment isolation, no meaningful API surface for provisioning, and no deployment model Skillable can orchestrate. Product Labability fails, and the composite score reflects that regardless of how impressive everything else looks. A seller without this information might pursue that account for months. Prospector surfaces the reality in the first batch run.

Prospector operates in two modes:

**Batch Scoring** — Marketing, RevOps, or Sales inputs a list of companies. Prospector scores and ranks them against all three qualification gates, surfaces a fit rationale and key contacts for each, and writes the results to HubSpot so Marketing can activate immediately. The output answers: which of these companies are worth pursuing, and why?

**ICP Discovery** *(roadmap)* — Prospector finds companies you don't know about yet that match your ICP. Define the characteristics — industry, product type, deployment model, technical signals — and Prospector surfaces candidates ranked by fit. The output answers: who else looks like Fortinet?

The intended flow: Prospector surfaces the top accounts from a batch, then Inspector goes deep on those. The Score Report link on every Prospector row makes that handoff a single click.

**Customer expansion uses Inspector, not Prospector.** When the question is where there is more to sell within an existing account, the right tool is the Inspector Case Board — a full product portfolio scan, labability tiers, competitive landscape, and key contacts for that company. Expansion is a depth question. Prospector is a breadth tool.

---

## Who Uses Prospector

### ICP Outbound Mode

**Marketing and demand generation teams** are the primary ICP Outbound users. They typically start with a large unqualified list — pulled from ZoomInfo, assembled from event registrations, or sourced from a vertical database — and need to cut it to high-confidence ABM targets before committing campaign spend. Prospector scores and ranks that list against all three qualification gates, surfaces a fit rationale and contacts for each company, and writes results to HubSpot so Marketing can activate immediately. Typical triggers: a new vertical initiative, event list qualification, or quarterly pipeline build.

**AEs and SDRs** use ICP Outbound to avoid working a bad list. Instead of discovering poor-fit companies through failed conversations, they run the list through Prospector first and direct their energy at accounts where all three gates clear. Typical triggers: a post-conference attendee list, a prospect list from LinkedIn Sales Navigator.

**Solution Engineers** reach for ICP Outbound in lighter-touch situations — territory planning, partner QBR prep, quick scans where depth on any one account isn't the goal. The Score Report link is what makes it useful for SEs: a high-scoring company almost certainly has an existing Inspector cache hit, turning the Prospector row into a direct link to the full analysis.

### Customer Expansion

**Customer expansion uses Inspector Case Board, not Prospector.** AEs, Strategic Account Directors, and CSMs who want to understand where there is more to sell within an existing account run Inspector on that company — the full product portfolio scan, labability tiers, competitive landscape, and contacts. That is the right depth for an expansion conversation. Typical triggers: QBR preparation, renewal prep, active expansion motion.

Prospector is a breadth tool. It is not the right instrument when you already know the account and the question is depth.

---

## What Prospector Delivers

You submit a list of companies. Somewhere between 5 and 8 minutes later (depending on API response times and how many cache hits you get), you have a ranked table sorted by composite score.

Practical batch size is constrained by the underlying services — Serper search API and Claude API both have rate limits and concurrency ceilings. The platform itself imposes no hard limit; throughput is a function of which service tiers are provisioned. If Marketing needs higher volume, the conversation is about service capacity, not platform capability.

Every row contains: the company's rank and name, a breakdown of product counts by labability tier (Highly Labable / Likely / Not Labable), the name of the top product that drove the score, the Lab Score for that product (0–100, color-coded green/Amber/red), the Skillable Path label, an Organizational Readiness score, the Composite score that combines both, a set of partnership signal checkmarks (ATP Program, Channel Program, Existing Lab Partner, ILT/vILT, On-Demand, Certifications, Gray Market), two contacts with name, title, and LinkedIn URL, and a Score Report link that connects directly to Inspector.

You can export that table as a CSV or a dark-themed Excel file. You can flag companies as poor fits with a reason, and they'll be permanently excluded from future runs. And when you're ready to go deeper on any account, one click takes you there.

---

## How Prospector Works

You paste in company names — comma-separated or newline-separated — or upload a CSV (first column is used as the company list; a header row containing the word "company" is automatically skipped). You can also check "Force refresh" if you want fresh research regardless of what's cached.

The moment you submit, the batch job spins up. Up to 6 companies are analyzed in parallel, and a live progress feed streams each company's state back to the UI: waiting, analyzing, done, or cache (with a date stamp showing how old the cached result is). Companies that don't complete within 3 minutes are marked as skipped and the batch continues without them.

For each company in the batch, the analysis follows six steps. First, the same 12 parallel discovery searches that Inspector runs — surfacing deployment model, training programs, certifications, partner program, API and developer ecosystem, pricing, existing labs, and gray market activity. Second, automatic selection of the single highest-labability product from discovery output; if multiple products share the top tier, the first one returned is used, and that selection is logged in the job record. Third, lightweight scoring of that product from discovery context — the same `ProductLababilityScore` model as Inspector, but without the Phase 2 deep research evidence. Fourth, Organizational Readiness scoring. Fifth, composite scoring using the same formula and gating rules as Inspector. Sixth, extraction of the top 2 contacts.

When all companies are done (or timed out), the results table renders sorted by composite score. The poor-fit registry runs before any of this — companies flagged in previous runs are stripped from the input list before analysis begins, so they never consume API calls or semaphore slots.

---

## The Batch Orchestration Layer

**Why:** Running a large batch of analyses without concurrency controls and timeout enforcement would make the platform fragile — a few slow API responses could hold up the entire batch, and the UI would have no way to show meaningful progress. Throughput scales with the service tiers provisioned for Serper and Claude; the platform orchestration layer handles whatever capacity those services provide.

**What:** Controlled parallel execution across the full company list, with per-company timeouts, a cancel endpoint, and live SSE progress streaming back to the UI.

**How:** Each company is submitted as a background thread. A semaphore caps concurrency at 6 simultaneous analyses. Timeout enforcement uses `concurrent.futures.wait()` with a 180-second parameter per company. SSE messages carry per-company state transitions that the UI renders as individual progress indicators.

### Capacity Awareness

Prospector is responsible for knowing its own practical ceiling and communicating it clearly — before a run starts, during a run, and when limits are being approached or hit.

**Before a run:** The input screen surfaces expected time and throughput based on current service tier configuration. "At current capacity, a batch of 50 companies with no cache hits will take approximately 15–20 minutes." Cache hit rate materially affects this — a list where half the companies are already cached runs much faster — and the UI makes this visible.

**Recommended best practices (surfaced in the UI):**
- Break very large lists into batches that fit within a single session — easier to review, easier to cancel and restart
- Cache hits are effectively free; running Prospector on a list a second time is much faster than the first
- Companies that timed out in a prior run can be re-submitted; a transient API slowdown is often the cause
- If consistent timeouts suggest a service capacity problem, that is a signal to review the provisioned service tier

**During a run:** Status messages distinguish cache hits, active analyses, timeouts, and errors explicitly. A company that times out is labeled as such — not silently dropped. If the Claude or Serper API begins throttling, Prospector surfaces that in the status stream rather than letting the run silently degrade.

**Service tier visibility:** The capacity ceiling is configuration-driven, not hardcoded. When Marketing needs higher volume and the current tier is the constraint, Prospector makes that clear — the path forward is a service upgrade or API switch, and users should not need to deduce this from slow run times.

### Batch Job Manager

**Why it exists:** To coordinate parallel analysis across a list of companies without overwhelming the API or blocking the UI.

**What it does:** Manages thread lifecycle, semaphore acquisition, timeout enforcement, and cancellation — turning a flat list of company names into a controlled, observable parallel workload.

**How it works:** Companies are submitted as background threads. A semaphore limits concurrency to 6. Per-company timeout is 180 seconds via `concurrent.futures.wait()`. Companies that exceed the timeout are marked `skipped` with a timeout reason; the batch loop moves on to the next company rather than waiting. A cancel endpoint (`POST /prospector/cancel/<job_id>`) sets a cancellation flag on the job; the loop checks this flag before initiating each new company, and companies already in-flight at cancellation time are allowed to complete or timeout normally. Progress is tracked via the same SSE infrastructure as Inspector, with messages that distinguish cache hits (with date stamp), active analyses, timeouts, and errors.

### Caching

**Why it exists:** Running fresh web research for every company in every batch would be slow and expensive — and most of the time the data hasn't changed.

**What it does:** Makes cache hits effectively instant (a 45-day-old Inspector result for a company is still the right result for prioritization), and reduces research cost for companies that have been partially analyzed before.

**How it works:** Two cache layers, both 45 days, both shared with Inspector. The full analysis cache: if Inspector has previously scored a company, Prospector uses that result immediately with no web research. The discovery cache: if a discovery pass has run recently (by either tool), the product list and discovery context are reused, skipping Phase 1 searches entirely. Cache hits show a date stamp in the progress view — "From cache — 3/15/2026" — so analysts know how fresh the data is.

---

## The Analysis Layer

**Why:** Getting from a company name to a composite score requires resolving the company's product footprint, scoring the top product, assessing organizational readiness, and combining both signals — in that order, from discovery-level evidence only.

**What:** Four components that take raw discovery output and produce a ranked composite score plus two contacts, without any of the deep per-product research that Inspector's Phase 2 provides.

**How:** Discovery runs first, producing the product list and evidence context. Product selection happens automatically. The lightweight scorer and Organizational Readiness model run against that discovery context. The composite engine combines the results. Contacts are extracted in parallel.

### Discovery Engine

**Why it exists:** You can't score a company's labability without first understanding what it makes, how it's deployed, and whether it already has a training ecosystem.

**What it does:** Runs 12 parallel web searches covering the full range of discovery intents — company overview, product overview, deployment model, training programs, certification structure, partner programs, API and developer ecosystem, pricing, existing labs, gray market labs, technical documentation, and market context — and extracts structured evidence from the results.

**How it works:** This is the same discovery engine Inspector uses for Phase 1 — same 12 queries, same search intents, same evidence extraction model. See [intelligence-platform.md](intelligence-platform.md) §3 for the full Research Engine description. After discovery completes, Prospector takes the single top product ranked highest by labability tier, rather than surfacing a selection interface. If multiple products share the `highly_likely` tier, the first one returned by the model is used. The selected product and the reason for its selection are logged in the job record.

### Lightweight Scorer

**Why it exists:** Prospector needs a calibrated labability score without running Inspector's full Phase 2 deep research on every company in the batch.

**What it does:** Produces a `ProductLababilityScore` (displayed as Labability Score in the results table) and `LabMaturityScore` from discovery-level evidence alone — the same data models as Inspector, built from shallower inputs.

**How it works:** The scoring prompt is identical to Inspector's. The difference is the evidence fed into it: discovery search summaries and fetched content from the company homepage, top product pages, and training and partner program pages. No Phase 2 product-specific searches. No fetched technical documentation, API reference pages, or Docker Hub listings. This means Product Labability scores will tend to be conservative — that dimension benefits most from the Phase 2 deep-dive, because containerization signals, REST API coverage, and SDK availability are often buried in technical docs that discovery doesn't reliably surface. The other dimensions — Content Richness, Organizational Readiness, Market Readiness — are less affected by the lighter pass. The composite score is directionally accurate enough for prioritization; it just shouldn't be treated as a final verdict.

### Composite Score Engine

**Why it exists:** Lab Score and Organizational Readiness score need to be combined into a single ranking signal so the results table has a meaningful sort order.

**What it does:** Produces a composite score (0–100) that gates and weights both dimensions according to the same rules Inspector uses.

**How it works:** Same formula, same weight definitions, same gating rules as Inspector. See [intelligence-platform.md](intelligence-platform.md) §5.4 for the full specification. Prospector applies these with no modifications — the only difference from Inspector composite scores is that the Labability Score input is derived from lighter evidence, which propagates into the composite result.

### Contact Extractor

**Why it exists:** A prioritization table that tells you a company scores 84 on composite but gives you no idea who to contact isn't actionable.

**What it does:** Surfaces the two most relevant contacts per company — name, title, and LinkedIn URL — using role-type logic that differs between academic institutions and software companies.

**How it works:** For academic institutions, the extractor prefers contacts with titles containing faculty, curriculum, dean, or registrar. For software companies, it prioritizes `decision_maker` role types first (VP Training, Director of Learning, Head of Technical Education), then falls back to `influencer` or `champion` roles. If fewer than 2 contacts are found, available fields are populated and missing fields are left blank rather than substituting lower-quality contacts.

---

## The Results Layer

**Why:** A ranked table is only as good as what you can do with it — the results need to be readable in the platform, exportable into CRM and marketing automation tools, and automatically cleaned of companies that have already been disqualified.

**What:** A sorted, color-coded results table with full export support, and a persistent registry that keeps disqualified companies out of future runs.

**How:** Results render sorted by composite score descending, with score coloring applied across all numeric columns. Export produces either a flat CSV or a dark-themed Excel file ready for direct stakeholder delivery. The poor-fit registry runs upstream of the analysis pipeline so flagged companies never appear in the results at all.

### Results Table and Export

**Why it exists:** To turn a batch analysis into something that can be acted on immediately — either in the platform or in an external tool.

**What it does:** Renders the full ranked results with 26 columns of data per company, applies visual score coloring, and produces named export files in CSV or Excel format.

**How it works:** Results are sorted by composite score descending. Score coloring applies green (`#24ED9B`) for scores ≥ 70, Amber (`#F59E0B`) for scores ≥ 40, and red (`#F87171`) for scores below 40.

The full column set:

| Column | Description |
|---|---|
| **Rank** | Position in composite score order (1 = highest) |
| **Company** | Company name, linked to company URL |
| **Product Counts** | Counts by labability tier: Highly Labable / Likely / Not Labable |
| **Top Product** | Name of the highest-scoring product analyzed |
| **Labability Score** | Product labability score of the top product (0–100), color-coded |
| **Skillable Path** | Software: "Labable", "Simulations", or "Do Not Pursue". Academic: school name or tier label |
| **Organizational Readiness** | Organizational readiness score (0–100) |
| **Composite** | Weighted combination of Labability Score and Organizational Readiness (0–100) |
| **Partnership Signals** | Checkmarks or counts for: ATP Program, Channel Program, Existing Lab Partner, ILT/vILT, On-Demand, Certifications, Gray Market |
| **Contact 1** | Name, title, LinkedIn URL |
| **Contact 2** | Name, title, LinkedIn URL |
| **Score Report** | Link to full Inspector analysis (cache hit) or pre-filled Inspector link (no cache) |

**Path labels — software companies:**

- Labability Score ≥ 50 → **"Labable"** (with delivery sublabel: Cloud Slice / Custom API / VM Lab)
- Labability Score ≥ 20 → **"Simulations"**
- Labability Score < 20 → **"Do Not Pursue"**

**Path labels — academic institutions:**

- No technology programs found → **"Not a Fit"**
- Has technology programs, school is a known Skillable anchor → **School name displayed**
- Has technology programs, high score → **"Academic — High Potential"**
- Has technology programs, lower score → **"Academic — Emerging"**

**Export formats:**

- **CSV:** 26 columns, filename pattern: `Prospector-{YYYY-MM-DD}-{count}-{job_id[:6]}.csv`
- **Excel (.xlsx):** 26 columns, dark-themed and styled for direct stakeholder delivery — header row background `#06100C`, data row background `#0D1A14`, frozen pane, score column coloring using the same green/Amber/red thresholds

### Poor-Fit Registry

**Why it exists:** Without a memory of disqualified companies, every batch run risks re-analyzing accounts that have already been evaluated and ruled out — wasting API calls and semaphore slots on known non-candidates.

**What it does:** Maintains a persistent list of flagged companies that are stripped from future batch inputs before analysis begins. Flagged companies appear in a collapsible "Skipped" section at the bottom of the results page so analysts can confirm the right companies were excluded.

**How it works:** Any row in the results table can be flagged with a free-form reason. The flag record stores company name, reason text, UTC timestamp, and the job ID where the flag was created. On each new Prospector run, the input list is filtered against this registry using a case-insensitive match before any analysis threads are started — flagged companies never consume API calls or semaphore slots. The registry is available for audit and can be reviewed or cleared by platform administrators.

---

## Prospector vs. Inspector — When to Use Which

| Signal | Use Prospector | Use Inspector |
|---|---|---|
| You have a list of 5–25 companies to prioritize | ✓ | |
| You're building an ABM target list | ✓ | |
| You want a fast directional signal on an account | ✓ | |
| You've already Prospected and want to go deeper | | ✓ |
| You need a Delivery Path recommendation | | ✓ |
| You need consumption or revenue estimates | | ✓ |
| You're preparing for a discovery call | | ✓ |
| You need an Essential Technical Resource question | | ✓ |
| You want to seed Designer with scoring context | | ✓ |

The rule of thumb: Prospector tells you *which* accounts are worth your time. Inspector tells you *what to do* with those accounts.

---

## Prospector → Inspector Handoff

Every row in Prospector's results table includes a Score Report link in the final column. If Inspector has already analyzed the company, the link opens the full Inspector results page directly — no waiting, no research, instant deep-dive. If no Inspector analysis exists, clicking the link pre-fills the Inspector home screen with the company name so the only thing standing between you and a full analysis is a single click.

This handoff is the intended workflow. Prospector is not trying to replace Inspector — it's trying to make Inspector more effective by giving it a focused target list rather than a sprawling cold one. Run a 25-company batch, identify the top 3–5 accounts by composite score and Skillable Path signal, and then let Inspector build the full evidence-backed analysis on those accounts before you invest SE time or craft a tailored pitch. Prospector focuses. Inspector goes deep.

---

*Last updated: 2026-03-30*
*Maintained by: Skillable Intelligence platform team*
