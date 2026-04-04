# Skillable Intelligence — Prospector

> Prospector runs Skillable Intelligence across a list of companies — producing a ranked table of qualification signals, partnership indicators, and outreach contacts so you know exactly where to focus before you invest a single sales cycle.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md). For guidance on interpreting findings, confidence levels, and hallucination risk, see [Before You Read the Scores](intelligence-platform.md#before-you-read-the-scores).

---

## Why Prospector Exists

Prospector is the prioritization layer of Skillable Intelligence. It takes centralized company intelligence — qualification signals, research evidence, scoring — and renders it in the form most useful for ranking and comparing a list of companies. The goal is not depth on any one account. The goal is signal across many accounts: which ones are worth pursuing, and which ones aren't.

What makes Prospector more than a fast Google search is what it's scoring against. The research runs signals through Skillable's accumulated knowledge of what actually makes a lab program viable — which deployment models Skillable can orchestrate, which technical patterns are hard blockers vs. manageable risks, and which organizational signals genuinely predict a successful program.

The Workday example makes this concrete. Massive install base. A dedicated Workday Learning division with a serious partner program. Strong Instructional Value and Organizational Readiness signals. But Workday is pure multi-tenant SaaS with no per-learner environment isolation, no meaningful API surface for provisioning, and no deployment model Skillable can orchestrate. Product Labability fails, and the composite score reflects that regardless of how impressive everything else looks. A seller without this information might pursue that account for months. Prospector surfaces the reality in the first batch run.

### Two Modes

**Batch Scoring** — Marketing, RevOps, or Sales inputs a list of companies. Prospector scores and ranks them against all four qualification dimensions, surfaces a fit rationale and key contacts for each, and writes results to HubSpot so Marketing can activate immediately. The output answers: *which of these companies are worth pursuing, and why?*

**Product Lookalikes** *(roadmap)* — Prospector finds companies you don't know about yet by working backwards from products. Intelligence already knows the attributes of products Skillable can labify — deployment models, API surfaces, orchestration patterns, technical characteristics. Product Lookalikes searches for products across the internet that share those attributes, then reverse-engineers the company target from the product match. The output answers: *who else has products that look like the ones we're already labifying?*

### Prospector → Inspector Flow

Prospector surfaces the top accounts. Inspector goes deep on those. The Score Report link on every Prospector row makes that handoff a single click.

**Customer expansion uses Inspector, not Prospector.** When the question is where there is more to sell within an existing account, the right tool is the Inspector Case Board. Expansion is a depth question. Prospector is a breadth tool.

---

## Who Uses Prospector

**Marketing and demand generation teams** are the primary users. They start with a large unqualified list — pulled from ZoomInfo, assembled from event registrations, or sourced from a vertical database — and need to cut it to high-confidence ABM targets before committing campaign spend. Typical triggers: a new vertical initiative, event list qualification, or quarterly pipeline build.

**RevOps** uses Prospector to qualify lists before they enter HubSpot — ensuring pipeline quality at the source rather than cleaning it downstream.

**AEs and SDRs** use Prospector to avoid working a bad list. Instead of discovering poor-fit companies through failed conversations, they run the list first and direct energy at accounts where all four dimensions clear. Typical triggers: a post-conference attendee list, a prospect list from LinkedIn Sales Navigator.

**Solution Engineers** reach for Prospector in lighter-touch situations — territory planning, partner QBR prep, quick scans where depth on any one account isn't the goal. The Score Report link is what makes it useful for SEs: a high-scoring company almost certainly has an existing Inspector cache hit, turning the Prospector row into a direct link to the full analysis.

---

## What Prospector Delivers

You submit a list of companies. Somewhere between 5 and 8 minutes later (depending on API response times and cache hits), you have a ranked table sorted by composite score.

Every row contains:

| Column | Description |
|---|---|
| **Rank** | Position in composite score order (1 = highest) |
| **Company** | Company name, linked to company URL |
| **Product Counts** | Counts by labability tier: Highly Labable / Likely / Not Labable |
| **Top Product** | Name of the highest-scoring product |
| **Lab Score** | Product labability score of the top product (0–100), color-coded |
| **Skillable Path** | Software: "Labable", "Simulations", or "Do Not Pursue". Academic: school name or tier label |
| **Composite** | Weighted combination of all four dimensions (0–100) |
| **Partnership Signals** | Checkmarks for: ATP Program, Channel Program, Existing Lab Partner, ILT/vILT, On-Demand, Certifications, Gray Market |
| **Contact 1 & 2** | Name, title, LinkedIn URL |
| **Score Report** | Link to full Inspector analysis or pre-filled Inspector search |

You can export the table as CSV or a dark-themed Excel file. You can flag companies as poor fits with a reason, and they'll be permanently excluded from future runs. When you're ready to go deeper on any account, one click takes you to Inspector.

### Path Labels

**Software companies:**
- Lab Score ≥ 50 → **"Labable"** (with delivery sublabel: Cloud Slice / Custom API / VM Lab)
- Lab Score ≥ 20 → **"Simulations"**
- Lab Score < 20 → **"Do Not Pursue"**

**Academic institutions:**
- No technology programs → **"Not a Fit"**
- Known Skillable anchor school → **School name displayed**
- High score → **"Academic — High Potential"**
- Lower score → **"Academic — Emerging"**

### Export Formats

- **CSV:** 26 columns, filename: `Prospector-{YYYY-MM-DD}-{count}-{job_id[:6]}.csv`
- **Excel (.xlsx):** Dark-themed, styled for direct stakeholder delivery — frozen header, score column coloring (green ≥ 70, Amber ≥ 40, red < 40)

---

## How Prospector Works

### Input

Paste company names (comma or newline-separated) or upload a CSV (first column used as the company list; header rows containing "company" are auto-skipped). Check "Force refresh" to bypass cached results.

### Batch Execution

Up to 6 companies are analyzed in parallel. A live progress feed streams each company's state: waiting, analyzing, done, or cached (with a date stamp). Companies that don't complete within 3 minutes are marked as timed out; the batch continues without them. Companies flagged as poor fits in previous runs are stripped from the input before analysis begins.

### Per-Company Analysis

For each company, Prospector runs six steps:

1. **Discovery** — The same 12 parallel web searches Inspector uses, covering deployment model, training programs, certifications, partner programs, API ecosystem, pricing, existing labs, and gray market activity
2. **Product selection** — Automatic selection of the single highest-labability product from discovery output
3. **Lightweight scoring** — Product Labability scored from discovery-level evidence only (no Phase 2 deep research). Uses the same scoring prompt and model as Inspector, but with shallower inputs. Product Labability scores tend to be conservative — this dimension benefits most from deep research that discovery doesn't surface. Instructional Value, Organizational Readiness, and Market Fit are less affected.
4. **Composite scoring** — Same formula, weights, and gating rules as Inspector (40/30/20/10)
5. **Contact extraction** — Top 2 contacts per company. Software companies: prioritizes decision makers (VP Training, Director of Learning), then influencers. Academic institutions: prioritizes faculty, curriculum, dean, or registrar titles.
6. **Results assembly** — Row built, sorted into the ranked results table

### Caching

Two cache layers, both 45 days, both shared with Inspector:
- **Analysis cache:** If Inspector has previously scored a company, Prospector uses that result immediately — no research needed
- **Discovery cache:** If a discovery pass ran recently (by either tool), the product list and context are reused, skipping Phase 1 searches

Cache hits show a date stamp in the progress view so analysts know how fresh the data is.

### Capacity

Batch size is constrained by Serper and Claude API rate limits, not the platform itself. If Marketing needs higher volume, the path forward is a service tier upgrade. The UI surfaces expected run time before a batch starts, distinguishes cache hits from fresh analyses during a run, and labels timeouts explicitly rather than silently dropping them.

### Poor-Fit Registry

Any row in the results table can be flagged with a free-form reason. Flagged companies are stored persistently and stripped from all future batch inputs before analysis begins — they never consume API calls or processing slots. A collapsible "Skipped" section at the bottom of results confirms which companies were excluded.

---

## Prospector vs. Inspector

| Signal | Prospector | Inspector |
|---|---|---|
| Prioritize a list of 5–25 companies | ✓ | |
| Build an ABM target list | ✓ | |
| Fast directional signal on an account | ✓ | |
| Go deeper after Prospector | | ✓ |
| Delivery path recommendation | | ✓ |
| Consumption or revenue estimates | | ✓ |
| Prepare for a discovery call | | ✓ |
| Seed Designer with scoring context | | ✓ |
| Expand within an existing account | | ✓ |

**Prospector tells you *which* accounts are worth your time. Inspector tells you *what to do* with those accounts.**

---

*Last updated: 2026-04-03*
*Maintained by: Skillable Intelligence platform team*
