# Skillable Intelligence — Prospector

> Prospector runs the same intelligence pipeline as Inspector across a batch of companies at once — producing a ranked table of labability fit, partnership signals, and outreach contacts so you know exactly where to focus before you invest a single sales cycle.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md).

---

## Why Prospector Exists

Inspector exists to go deep on a single account. It runs a two-phase research pipeline, surfaces every relevant product, lets you select the one you care about, and produces a fully evidence-backed recommendation with delivery paths, consumption estimates, and the exact technical question your SE should ask in discovery. It's designed for when you already know an account matters and you need everything.

The problem is that most of the time you don't know that yet. You have a list.

The request that kicked off Prospector was simple: marketing had seen Inspector work and asked whether it could run the same analysis across a list of companies — not one at a time through the UI, but as a batch job they could kick off and come back to. The answer was yes, but with a deliberate trade-off. Running Inspector's full two-phase pipeline across 25 companies in parallel would be slow, expensive, and produce a lot of detail nobody needed at the prioritization stage. What marketing actually needed was signal — enough to separate the Highly Labable from the Do Not Pursues, get a contact name and LinkedIn URL, and export the result into their ABM tool.

So Prospector became Inspector's lighter sibling. It runs the same discovery phase — the same 12 parallel searches that surface deployment model, training ecosystem, partner program, certification structure, and existing labs — but it skips the deep Phase 2 product research and the interactive selection workflow. It auto-selects the single highest-labability product, scores it from discovery context, computes the same composite score Inspector would produce, and moves on to the next company. A 25-company batch that would take hours to run manually through Inspector completes in 5–8 minutes.

The intended flow was baked in from the start: Prospector surfaces the top 3–5 accounts from a batch, then Inspector goes deep on those. The Score Report link on every Prospector row makes that handoff a single click.

---

## Who Uses Prospector

**Marketing and demand generation teams** are the primary users. They typically start with a large unqualified list — pulled from ZoomInfo, assembled from event registrations, or sourced from a vertical database — and need to cut it down to high-confidence ABM targets before committing campaign spend. Prospector takes that raw list and gives them a ranked composite score, a Skillable Path signal (Labable / Simulations / Do Not Pursue), top contact name and LinkedIn URL, and a clean CSV or styled Excel export ready for upload into Salesforce or HubSpot. Typical triggers: a new vertical initiative, event list qualification, or quarterly pipeline build.

**AEs and SDRs** use Prospector to avoid working a bad list. Instead of discovering poor-fit companies through failed conversations, they run the list through Prospector first and direct their energy at accounts where the composite score is strong and the Skillable Path signal says there's something to pursue. The contact title is particularly useful here — it's one quick confirmation that the outreach is going to the right person. Typical triggers: a post-conference attendee list, a prospect list from LinkedIn Sales Navigator.

**Solution engineers** reach for Prospector in lighter-touch situations — territory planning, partner QBR prep, pre-sales team reviews where the goal is a quick scan of a set of accounts, not a full deep-dive on any one of them. The Score Report link is what makes it useful for SEs specifically: any account with a high score almost certainly has an existing Inspector cache hit, so the Prospector row becomes a direct link to the full analysis.

---

## What Prospector Delivers

You submit a list of up to 25 companies. Somewhere between 5 and 8 minutes later (depending on API response times and how many cache hits you get), you have a ranked table sorted by composite score.

Every row contains: the company's rank and name, a breakdown of product counts by labability tier (Highly Labable / Likely / Not Labable), the name of the top product that drove the score, the Lab Score for that product (0–100, color-coded green/amber/red), the Skillable Path label, a Lab Maturity score for organizational readiness, the Composite score that combines both, a set of partnership signal checkmarks (ATP Program, Channel Program, Existing Lab Partner, ILT/vILT, On-Demand, Certifications, Gray Market), two contacts with name, title, and LinkedIn URL, and a Score Report link that connects directly to Inspector.

You can export that table as a CSV or a dark-themed Excel file. You can flag companies as poor fits with a reason, and they'll be permanently excluded from future runs. And when you're ready to go deeper on any account, one click takes you there.

---

## How Prospector Works

You paste in company names — comma-separated or newline-separated — or upload a CSV (first column is used as the company list; a header row containing the word "company" is automatically skipped). You can also check "Force refresh" if you want fresh research regardless of what's cached.

The moment you submit, the batch job spins up. Up to 6 companies are analyzed in parallel, and a live progress feed streams each company's state back to the UI: waiting, analyzing, done, or cache (with a date stamp showing how old the cached result is). Companies that don't complete within 3 minutes are marked as skipped and the batch continues without them.

For each company in the batch, the analysis follows six steps. First, the same 12 parallel discovery searches that Inspector runs — surfacing deployment model, training programs, certifications, partner program, API and developer ecosystem, pricing, existing labs, and gray market activity. Second, automatic selection of the single highest-labability product from discovery output; if multiple products share the top tier, the first one returned is used, and that selection is logged in the job record. Third, lightweight scoring of that product from discovery context — the same `ProductLababilityScore` model as Inspector, but without the Phase 2 deep research evidence. Fourth, Lab Maturity scoring for organizational readiness. Fifth, composite scoring using the same formula and gating rules as Inspector. Sixth, extraction of the top 2 contacts.

When all companies are done (or timed out), the results table renders sorted by composite score. The poor-fit registry runs before any of this — companies flagged in previous runs are stripped from the input list before analysis begins, so they never consume API calls or semaphore slots.

---

## The Batch Orchestration Layer

**Why:** Running 25 analyses in parallel without rate-limiting or timeout enforcement would make the platform fragile — a few slow API responses would hold up the entire batch, and the UI would have no way to show meaningful progress.

**What:** Controlled parallel execution across the full company list, with per-company timeouts, a cancel endpoint, and live SSE progress streaming back to the UI.

**How:** Each company is submitted as a background thread. A semaphore caps concurrency at 6 simultaneous analyses. Timeout enforcement uses `concurrent.futures.wait()` with a 180-second parameter per company. SSE messages carry per-company state transitions that the UI renders as individual progress indicators.

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

**How:** Discovery runs first, producing the product list and evidence context. Product selection happens automatically. The lightweight scorer and Lab Maturity model run against that discovery context. The composite engine combines the results. Contacts are extracted in parallel.

### Discovery Engine

**Why it exists:** You can't score a company's labability without first understanding what it makes, how it's deployed, and whether it already has a training ecosystem.

**What it does:** Runs 12 parallel web searches covering the full range of discovery intents — company overview, product overview, deployment model, training programs, certification structure, partner programs, API and developer ecosystem, pricing, existing labs, gray market labs, technical documentation, and market context — and extracts structured evidence from the results.

**How it works:** This is the same discovery engine Inspector uses for Phase 1 — same 12 queries, same search intents, same evidence extraction model. See [intelligence-platform.md](intelligence-platform.md) §3 for the full Research Engine description. After discovery completes, Prospector takes the single top product ranked highest by labability tier, rather than surfacing a selection interface. If multiple products share the `highly_likely` tier, the first one returned by the model is used. The selected product and the reason for its selection are logged in the job record.

### Lightweight Scorer

**Why it exists:** Prospector needs a calibrated labability score without running Inspector's full Phase 2 deep research on every company in the batch.

**What it does:** Produces a `ProductLababilityScore` and `LabMaturityScore` from discovery-level evidence alone — the same data models as Inspector, built from shallower inputs.

**How it works:** The scoring prompt is identical to Inspector's. The difference is the evidence fed into it: discovery search summaries and fetched content from the company homepage, top product pages, and training and partner program pages. No Phase 2 product-specific searches. No fetched technical documentation, API reference pages, or Docker Hub listings. This means Technical Orchestrability scores will tend to be conservative — that dimension benefits most from the Phase 2 deep-dive, because containerization signals, REST API coverage, and SDK availability are often buried in technical docs that discovery doesn't reliably surface. The other dimensions — Content Richness, Training Ecosystem, Market Reach — are less affected by the lighter pass. The composite score is directionally accurate enough for prioritization; it just shouldn't be treated as a final verdict.

### Composite Score Engine

**Why it exists:** Lab Score and Lab Maturity need to be combined into a single ranking signal so the results table has a meaningful sort order.

**What it does:** Produces a composite score (0–100) that gates and weights both dimensions according to the same rules Inspector uses.

**How it works:** Same formula, same weight definitions, same gating rules as Inspector. See [intelligence-platform.md](intelligence-platform.md) §5.4 for the full specification. Prospector applies these with no modifications — the only difference from Inspector composite scores is that the Lab Score input is derived from lighter evidence, which propagates into the composite result.

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

**How it works:** Results are sorted by composite score descending. Score coloring applies green (`#24ED9B`) for scores ≥ 70, amber (`#F59E0B`) for scores ≥ 40, and red (`#F87171`) for scores below 40.

The full column set:

| Column | Description |
|---|---|
| **Rank** | Position in composite score order (1 = highest) |
| **Company** | Company name, linked to company URL |
| **Product Counts** | Counts by labability tier: Highly Labable / Likely / Not Labable |
| **Top Product** | Name of the highest-scoring product analyzed |
| **Lab Score** | Labability score of the top product (0–100), color-coded |
| **Skillable Path** | Software: "Labable", "Simulations", or "Do Not Pursue". Academic: school name or tier label |
| **Lab Maturity** | Organizational readiness score (0–100) |
| **Composite** | Weighted combination of Lab Score and Lab Maturity (0–100) |
| **Partnership Signals** | Checkmarks or counts for: ATP Program, Channel Program, Existing Lab Partner, ILT/vILT, On-Demand, Certifications, Gray Market |
| **Contact 1** | Name, title, LinkedIn URL |
| **Contact 2** | Name, title, LinkedIn URL |
| **Score Report** | Link to full Inspector analysis (cache hit) or pre-filled Inspector link (no cache) |

**Path labels — software companies:**

- Lab Score ≥ 50 → **"Labable"** (with delivery sublabel: Cloud Slice / Custom API / VM Lab)
- Lab Score ≥ 20 → **"Simulations"**
- Lab Score < 20 → **"Do Not Pursue"**

**Path labels — academic institutions:**

- No technology programs found → **"Not a Fit"**
- Has technology programs, school is a known Skillable anchor → **School name displayed**
- Has technology programs, high score → **"Academic — High Potential"**
- Has technology programs, lower score → **"Academic — Emerging"**

**Export formats:**

- **CSV:** 26 columns, filename pattern: `Prospector-{YYYY-MM-DD}-{count}-{job_id[:6]}.csv`
- **Excel (.xlsx):** 26 columns, dark-themed and styled for direct stakeholder delivery — header row background `#06100C`, data row background `#0D1A14`, frozen pane, score column coloring using the same green/amber/red thresholds

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
