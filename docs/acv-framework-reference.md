# ACV Framework Reference — Rate Card + Use Case Matrix

> **Audience: Marketing, RevOps, Sales, Sales Engineers, Executive.** This is the standalone ACV framework reference. For the full specification (prompt logic, audience sourcing, velocity factor, calibration anchors), see `docs/Platform-Foundation.md#acv-potential-model`.

## Why This Doc Exists

Every ACV conversation has three questions:
1. **How big is this deal if we win?** (ACV Target)
2. **What horizon can we capture it in?** (3-Year ACV)
3. **Where does the revenue come from?** (per-motion breakdown)

This doc gives you the same view the platform gives sellers: by org type, which use cases apply, at what rate.

---

## Labs-as-COG vs Labs-as-Enablement

**COG motions** — customer resells labs to an end learner; **every lab consumed generates revenue for the customer**. "They make money every time they pay us."

**Enablement motions** — customer's internal investment in its own staff, channel, or go-to-market. Not resold per learner.

| Category | Motions |
|---|---|
| **COG** | Customer ILT, Customer On-demand Learning, Certification Exam Labs, Exam Prep Labs, Students (academic) |
| **Enablement** | Channel Enablement, Practice Leads & Consultants, Employee Training, Instructors, Hands-on Labs @ Events, Faculty, Staff, Career Fairs |

---

## Use Cases by Organization Type

Each org type sees ONLY the motions that apply to its business model.

### 🟦 Software

*Microsoft, Cisco, Nutanix, Trellix, NVIDIA, Hyland, Milestone, Eaton, TRUMPF, Sage, Calix, Quantum, and similar tech vendors.*

| # | Use Case | Type | Rate (list) |
|---|---|---|---|
| 1 | Customer Instructor-led Training | **COG** | $200/student/yr |
| 2 | Customer On-demand Learning | **COG** | $30/learner (SW-paid) · $10 (ELP-paid) · $5 (free big library) |
| 3 | Channel Enablement (sellers/SEs) | Enablement | $200/engineer/yr |
| 4 | Employee Training | Enablement | $30/person/yr |
| 5 | Certification Exam Labs *(if cert issuer)* | **COG** | $10/candidate/yr |
| 6 | Hands-on Labs @ Events | Enablement | $50/attendee/yr |

### 🟩 GSI · VAR · Distributor · MSSP

*Deloitte, Accenture, KPMG, New Horizons, regional SIs, MSSPs.*

| # | Use Case | Type | Rate (list) |
|---|---|---|---|
| 1 | Practice Leads & Consultants | Enablement | $200/consultant/yr |
| 2 | Hands-on Labs @ Events | Enablement | $50/attendee/yr *(ACV potential — most don't do yet)* |
| 3 | Customers | COG | *Unquantifiable — flagged, not estimated* |

### 🟨 Training Partner · ELP · ATP

*QA, Firebrand, Skillsoft, CBT Nuggets, Pluralsight, LLPA, New Horizons (training delivery side).*

| # | Use Case | Type | Rate (list) |
|---|---|---|---|
| 1 | Instructor-led Training | **COG** | $200/student/yr |
| 2 | On-demand Learning | **COG** | $10/learner/yr |
| 3 | Instructors | Enablement | $200/instructor/yr |

### 🟥 Industry Authority

*CompTIA, EC-Council, ISC², SANS, ISACA, AXELOS.*

| # | Use Case | Type | Rate (list) |
|---|---|---|---|
| 1 | Instructor-led Training | **COG** | $200/student/yr |
| 2 | On-demand Learning | **COG** | $10/learner/yr |
| 3 | Instructors | Enablement | $200/instructor/yr |
| 4 | Certification Exam Labs | **COG** | $10/candidate/yr |
| 5 | Exam Prep Labs | **COG** | $10/subscriber/yr |

### 🟪 Academic

*ASU, Grand Canyon University, community colleges, K-12 districts, workforce programs.*

| # | Use Case | Type | Rate (list) |
|---|---|---|---|
| 1 | Students | **COG** | $200/student/yr |
| 2 | Faculty | Enablement | $30/person/yr |
| 3 | Staff | Enablement | $30/person/yr |
| 4 | Career Fairs & Events | Enablement | $50/attendee/yr |

---

## Rate Tiers

| Tier | Audience scale | Rate relationship | Applies to |
|---|---|---|---|
| **Mid** | < 100K total paying audience | List rates (per cards above) | Most software cos, mid-size training partners, academic |
| **Big** | 100K – 3M total paying audience | 40% of list | Mid-size ELPs, industry authorities, large training partners, Cisco |
| **Hyperscaler** | Named list — Microsoft · Google · AWS | ~15% of list (varies by motion) | The 3–4 truly hyperscale learning environments |

**Hyperscaler is by name, not audience threshold.** Microsoft, Google, AWS today. Cisco is at Big tier (its scale is within normal volume-discount territory). Oracle / Salesforce would join the hyperscaler list if and when they become Skillable customers.

### Hyperscaler rate detail

| Motion | List | Hyperscaler |
|---|---|---|
| Customer ILT / ILT students / Students | $200 | $30 |
| On-demand (SW-paid) | $30 | $5 |
| On-demand (ELP-paid) | $10 | $3 |
| On-demand (free big library) | $5 | $2 |
| Channel Enablement / Practice Leads | $200 | $30 |
| Employee Training | $30 | $6 |
| Certification Exam Labs | $10 | $3 *(specific values tunable)* |
| Exam Prep Labs | $10 | $3 |
| Events | $50 | $15 *(specific values tunable)* |
| Instructors | $200 | $30 |
| Faculty / Staff (academic) | $30 | $6 |
| Career Fairs (academic) | $50 | $15 |

---

## ACV Target vs 3-Year ACV

| Metric | What it means | Math |
|---|---|---|
| **ACV Target** | Size of the prize if Skillable fully served the company's paying audience | Σ (audience × rate) across applicable motions |
| **3-Year ACV** | Realistic 3-year capture given relationship stage | ACV Target × velocity factor |

### Velocity factor by relationship stage

| Relationship | 3-Year factor |
|---|---|
| Current customer with active expand motion | 0.8 – 1.2 |
| Current customer, mature relationship | 0.3 – 0.5 |
| Warm prospect (engaged, POC-stage) | 0.3 – 0.5 |
| Cold prospect (aware, no motion) | 0.1 – 0.2 |
| No relationship / green-field | 0.05 – 0.15 |

**Velocity is not a growth multiplier.** Growth is already baked into the honest current-state audience. Velocity reflects realistic 3-year capture given the relationship's starting point.

---

## Reading the Output

When the platform produces an ACV for a company, you see:

- **ACV Target** — the number to pursue, audience × rate
- **3-Year ACV** — the realistic 3-year bookings given relationship stage
- **Per-motion breakdown** — where the revenue lives (by use case), with COG / Enablement labels
- **Confidence per motion** — confirmed / indicated / inferred / thin_evidence
- **Evidence per motion** — 2–3 sentence rationale with specific sources

Confidence labels matter — a `thin_evidence` estimate warrants more discovery before committing to a number with a customer.

---

## What's Explicitly NOT in This Model

- **Growth multipliers** — growth shows up as a bigger current-state audience, not a side multiplier
- **Lab complexity multipliers** — ACV is revenue, not margin; complexity affects Skillable's COGS, not customer ACV
- **Artificial floors or ceilings** — no "caps at $X" or "minimums of $Y"; whatever the math produces is the number
- **Displacement adjustments as separate line items** — when we count audience, we implicitly include displacement of incumbent lab platforms (if a company has labs today, our audience estimate already reflects what we'd take over)
- **Cert attribution to prep trainers** — only cert issuers count cert candidates; a company that preps for CompTIA doesn't get CompTIA's cert revenue

All grounded in principle. Each exclusion has a reason; none is a knob to tune.

---

## Related Docs

- **Platform Foundation · ACV Potential Model** — full framework spec, prompt structure, calibration anchors
- **`backend/audience_grader.py`** — the Claude-driven audience estimator
- **`backend/acv_calculator.py`** — deterministic Python rate math
- **`backend/scoring_config.py`** — single source of truth for rate constants and tier thresholds
- **`backend/known_customers.json`** *(gitignored)* — confidential calibration data
