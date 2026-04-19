"""Audience grader — Claude-in-Score for ACV audience estimation.

Architectural role
------------------
This module is the second narrow Claude slice in the Score layer (sibling
of `rubric_grader.py`). It produces the five use-case audience integers
that the deterministic ACV math consumes.

Design principle: **Claude for judgment, Python for math.**

Claude's job (this module):
  - Read the discovery facts (per-product + per-company + calibration anchors)
  - Estimate how many humans will be in each of the five use-case motions
    for this company in the coming year
  - Produce per-motion rationale and confidence

Python's job (acv_calculator.py):
  - Multiply each audience by the flat per-motion rate from
    scoring_config.MOTION_METADATA
  - Sum to raw company ACV
  - Apply the Product Labability harness (popularity-weighted average PL)
  - Write the canonical _company_acv onto the discovery

The grader does NOT do dollar math. Rates live in config; Python applies
them; changing a rate should never require re-calling Claude.

─── When the grader fires ──────────────────────────────────────────────────
  - Fresh discovery (always)
  - Discovery refresh (cache expiry or user-triggered)
  - Deep Dive that merges new company-level signals
  - NOT at every Deep Dive — only when company-level context changed

─── Cost ──────────────────────────────────────────────────────────────────
  ~$0.05 per company per grader invocation on Sonnet 4.6
  ~2-3 invocations per company per year in steady state

─── Status ────────────────────────────────────────────────────────────────
  Prompt construction + calibration block + diff check are implemented
  (pure Python, safe to import and call). The live Claude call in
  judge_training_audiences() is a stub — Commit 1 of the ACV architecture
  rewrite wires it up.

─── Full architecture spec ─────────────────────────────────────────────────
  docs/Platform-Foundation.md → ACV Potential Model
"""
from __future__ import annotations

import copy
import logging
from typing import Any

import scoring_config as cfg

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Output schema — the contract the judgment call produces
#
# Every call returns a dict matching this shape. Callers may rely on every
# key being present. Integers are always non-negative. Strings are never
# None (empty string when absent).
# ═══════════════════════════════════════════════════════════════════════════════

AUDIENCE_GRADER_OUTPUT_SCHEMA = {
    "audiences": {
        "customer_training":  "int — humans being trained on the company's products this year",
        "partner_training":   "int — partner employees (GSI/VAR/distributor SEs) being trained this year",
        "employee_training":  "int — technical employees at this company trained on their own products",
        "certification":      "int — humans who sit the product's cert exam this year",
        "events":             "int — attendees at the company's events with lab tracks",
    },
    "confidence":    "'low' | 'medium' | 'high' — overall confidence in the audience estimates",
    "rationale":     "str — 80–150 words. Market Demand first. Why these numbers, not larger or smaller.",
    "per_motion_rationale": "dict[str, str] — one sentence per motion explaining that motion's audience",
    "per_motion_confidence": "dict[str, str] — 'low' | 'medium' | 'high' per motion",
    "key_drivers":   "list[str] — up to 5 short sentences naming the signals that drove the estimate",
    "caveats":       "list[str] — up to 3 short sentences naming uncertainties",
    "market_demand_story": "str — one-line explanation of why paid training demand for this company is X, not larger or smaller",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Partnership-only short-circuit
#
# Content Development firms (GP Strategies, Waypoint Ventures, NetLogon-class
# partners) do not fit the audience × rate model — their Skillable revenue
# flows through client engagements, not directly. Before the judgment call
# fires, the pipeline checks org_type. For CONTENT_DEVELOPMENT we return a
# partnership result shape without calling Claude.
# ═══════════════════════════════════════════════════════════════════════════════

PARTNERSHIP_RESULT_SHAPE = {
    "audiences": {
        "customer_training":  0,
        "partner_training":   0,
        "employee_training":  0,
        "certification":      0,
        "events":             0,
    },
    "acv_type":   "partnership",
    "confidence": "partnership",
    "rationale":  "Content Development firms build learning programs for other companies — Skillable's revenue flows through downstream client engagements, not directly. Treated as a partnership-only opportunity, no direct ACV estimate produced.",
    "per_motion_rationale": {},
    "per_motion_confidence": {},
    "key_drivers": [],
    "caveats":     ["Direct ACV estimate intentionally not produced for this org type.",
                    "Pursue as a content / lab-build partnership, not a direct customer deal."],
    "market_demand_story": "N/A for partnership-only org types.",
}


def _is_partnership_only(discovery: dict) -> bool:
    """Return True when the discovery's org type is partnership-only.

    Partnership-only org types short-circuit the judgment call. The current
    set is {CONTENT DEVELOPMENT}. Defined in scoring_config.ACV_PARTNERSHIP_ONLY_ORG_TYPES.
    """
    org_type_raw = (discovery.get("organization_type") or "").lower().replace(" ", "_")
    normalized_org = cfg.ORG_TYPE_NORMALIZATION.get(org_type_raw, "")
    return normalized_org in cfg.ACV_PARTNERSHIP_ONLY_ORG_TYPES


# ═══════════════════════════════════════════════════════════════════════════════
# Prompt — system-level role framing and hard rules
#
# The full prompt is assembled in build_audience_grader_prompt(). The
# constants below are the fixed portions — the system framing, definitions,
# org-type framing, anti-pitfalls, and output schema. They are identical
# across every call. The per-company user portion (products, signals,
# calibration block) is rendered dynamically.
# ═══════════════════════════════════════════════════════════════════════════════

_ROLE_FRAMING = """
═══ YOUR ROLE ═══

You are a senior training-market analyst for Skillable — a hands-on lab
platform. Your job is to judge, for a specific company, how many humans
will be in each of five training-market motions over the coming twelve
months. You output the five audience numbers plus reasoning. Deterministic
Python downstream multiplies by rates, applies a Product Labability filter,
and sums to company ACV. You never do dollar math. You estimate humans.
"""

_WHAT_TRAINING_AUDIENCE_MEANS = """
═══ WHAT "TRAINING AUDIENCE" MEANS ═══

A training audience is humans whose lab consumption generates Skillable
revenue. Concretely:

- Humans who consume labs where someone pays Skillable for the lab hours.
- The learner usually does NOT pay personally. Whether the learner pays
  nothing, pays a subscription fee, or pays through an employer does not
  determine whether they're in the audience — Skillable gets paid by the
  builder/embedder regardless.
- A user who watches free content, reads documentation, or takes a course
  that has no embedded lab is NOT in the audience.
- You are estimating ONE year. Annual throughput. Not cumulative,
  not lifetime, not "across our history," not "total platform reach."

═══ "THE CUSTOMER" = WHOEVER BUILDS AND EMBEDS THE LAB ═══

This is the rule that determines which company's audience a given learner
belongs to. Skillable's customer for any given lab is the organization
that BUILT the lab and EMBEDDED it in their course/content. Not the
vendor whose technology the lab covers. Not the platform where the
learner accesses it. The BUILDER/EMBEDDER.

Examples:
- Microsoft builds labs on Microsoft products → Microsoft's audience.
- Microsoft builds labs on Databricks running on Azure, embedded in a
  Microsoft-built course → Microsoft's audience (they built it).
- Databricks builds labs on Databricks → Databricks's audience.
- Coursera builds labs on any vendor (Microsoft / AWS / etc.) and
  embeds them in a Coursera course → Coursera's audience.
- Pluralsight builds labs on AWS → Pluralsight's audience.
- An ATP delivers a Microsoft MOC course using Microsoft-built labs →
  Microsoft's audience (Microsoft built the labs; ATP just delivered).
- A partner builds its own labs for a course it sells → the partner's
  audience (the partner built them).

For ELPs like Coursera / Pluralsight / Skillsoft / Udemy / Udacity /
CBT Nuggets: the audience is learners consuming labs the ELP built,
summed across ALL tech catalogs the ELP operates (Microsoft + AWS +
Azure + cybersecurity + DevOps + data/AI + …). Not sliced by vendor.

═══ ANNUAL THROUGHPUT vs. ECOSYSTEM / CUMULATIVE / LIFETIME ═══

The single biggest error you can make: treating an ecosystem /
cumulative / lifetime number as an annual training audience.

- "30+ certifications" = catalog breadth, NOT this year's exam sitters.
- "400,000 partner organizations" = network size, NOT partner employees
  trained THIS YEAR.
- "10 million Coursera catalog enrollments" = cumulative enrollments
  across their entire catalog history, NOT this year's tech-catalog
  learners.
- "2 billion Windows users" = installed base, NOT annual Windows
  training audience.
- "500K lifetime cert holders" = everyone who ever passed this cert,
  NOT this year's sitters.

Annual paid training audiences are almost always a small fraction of
cumulative / lifetime numbers. When the only number you can find is a
cumulative or lifetime figure, translate: how many of those people are
IN training or SITTING an exam with an embedded lab THIS YEAR? That is
the audience. When in doubt, reason from the funnel: total ecosystem →
active users → users in training → users in paid training → users in
labbed paid training → users consuming labs the BUILDER/EMBEDDER owns.
Each step drops by a large factor.
"""

_FIVE_MOTIONS = """
═══ THE FIVE MOTIONS ═══

You produce ONE integer per motion. Five integers total.

1. customer_training
   Humans being trained on the company's products this year — whether
   directly or through ATPs / training partners. For a software company,
   these are their customers' people (not the customer count). For a
   wrapper org (ILT, Academic, ELP, GSI), these are the humans in the
   wrapper's delivered programs this year.

2. partner_training
   Channel partner employees being trained this year — GSI / VAR /
   distributor consultants, SEs, solution architects, implementation
   partners. These are people at PARTNER organizations who need to sell,
   deploy, implement, or support the company's products. NOT the end
   customers who happen to learn through partners (those are customer_training).
   Zero for companies with no channel.

3. employee_training
   Technical employees at THIS COMPANY who work on their own products —
   product team, SEs, support engineers, customer success engineers,
   trainers. Always a fraction of total headcount, not total headcount.
   Does not include non-technical staff (HR, finance, legal, etc. —
   unless they specifically need product training). For wrapper orgs,
   this is their own technical staff (instructors, curriculum developers,
   practice leads).

4. certification
   Humans who SIT the product's certification exam this year. Exam
   sitters — not training candidates (those are customer_training).
   Zero if no cert exists, or if the cert has no lab component. For
   certification bodies (CompTIA, EC-Council, SANS), this is the
   annual-sit-rate across their cert programs, not lifetime cert holders.

5. events
   Attendees at the company's flagship events (conferences, summits,
   user groups) with hands-on lab tracks. Use published attendance for
   named events when available. Zero when the company runs no events —
   events without labs today are the OPPORTUNITY (for the seller), not
   a real audience.
"""

_MARKET_DEMAND_AS_GATING_SIGNAL = """
═══ MARKET DEMAND IS THE GATING SIGNAL FOR EVERY MOTION ═══

A product's user count alone does not determine its training audience.
Windows has billions of users; almost none will buy paid Windows training
this year. A specialist cybersecurity platform with 300K operators may
have a large paid training audience relative to its user count. The test
is always: is the instructional value so important that people are
willing to pay for it?

Market Demand bounds ALL FIVE motions. If there is no paid training
market for a product:

- customer_training is small (no one pays)
- partner_training is small (no partners bother learning a dead product)
- certification is small (no one sits an exam for a non-marketable skill)
- events are small (no conference lab track for something nobody cares about)
- employee_training holds up (the company still trains its own people)

Use these signals as proxies for real demand:
  - Product complexity (admins need training; end-user tools rarely do)
  - Certification ecosystem (cert programs create paid training demand)
  - Third-party training market (Pluralsight / Coursera / LinkedIn Learning
    course counts exist because demand exists)
  - Partner programs (ATPs exist because selling requires training)
  - Flagship events with lab tracks (demand shows up at conferences)
  - Vendor training revenue (the company itself making training money)
"""

_ORG_TYPE_FRAMING = """
═══ ORG-TYPE FRAMING — HOW "AUDIENCE" IS INTERPRETED BY ORG TYPE ═══

The same motion means different things across org types. Anchor on the
framing that matches this company's org type:

- Software / Enterprise Software
    customer_training = customers worldwide who pay for training on the
    company's products this year. Scale with Market Demand — popular
    products with thin training markets have small audiences.

- Enterprise Learning Platform (Pluralsight, Skillsoft, CBT Nuggets,
  Coursera Business, Udemy Business, Udacity, LinkedIn Learning)
    customer_training = the ELP's own learners consuming labs the ELP
    built and embedded in its courses this year, across ALL the ELP's
    tech catalogs combined (Microsoft content + AWS content + Azure
    content + cybersecurity content + DevOps content + data/AI content
    + anything else they build labs for). The ELP owns the audience of
    learners who consume ELP-built labs — regardless of what underlying
    vendor's technology the labs cover. Do NOT carve the audience by
    one vendor slice; it's cumulative across all catalogs the ELP labs.
    Do NOT include leadership / compliance / soft-skills catalog learners
    (non-labable). A fraction of total platform subscribers — how many
    depends on how deep the tech catalog is and how many of the ELP's
    learners take tech courses with embedded labs in a given year.

- ILT Training Organization (New Horizons, LLPA, AXcademy, QA, ONLC,
  LearnQuest, Global Knowledge pre-merger)
    customer_training = students in this org's classrooms and virtual
    ILT courses this year. BOUNDED by the org's own delivery capacity
    (instructor count, schedule, seats, locations). NOT the underlying
    technology's global market.

- Academic Institution
    customer_training = students enrolled in TECHNOLOGY programs this
    year. Not total institution enrollment — only the subset in
    technology-facing programs (CS, engineering, cybersecurity, data
    science, IT) with labbed curriculum.

- Systems Integrator / VAR / Technology Distributor
    customer_training = consultants in the practice area this year.
    Internal practitioners being trained on the products the firm
    deploys. NOT the underlying technology's global customer base. The
    firm's OWN practice-area consultants, not the population of people
    using those technologies globally.

- Industry Authority (CompTIA, SANS, EC-Council, ISACA, (ISC)²)
    customer_training = ANNUAL training candidates for the cert programs.
    NOT lifetime cert holders. A person who got a cert years ago is
    NOT in this year's audience unless they're renewing/continuing this
    year.
    certification = ANNUAL exam sitters this year (not lifetime holders
    either). The funnel drops between training candidates and exam
    sitters — many train without sitting; some sit without formal
    training. Scale the two audiences independently.

- LMS Provider
    customer_training = learners on the platform consuming labbed
    technology courses this year.
"""

_COMMERCIAL_CALIBRATION = """
═══ ANONYMIZED REFERENCE DATA — Skillable's real customers ═══

The block below shows Skillable's actual customers grouped anonymously
by relationship stage. Each stage groups current ACV ranges across the
customers at that stage, and where known, estimated three-year Potential
ranges. Customer names never appear — only magnitudes and stage
groupings. You must NOT name any customer, anonymized or otherwise, in
your rationale. Reference stage patterns only.

This is data, not a target. Use it to understand what real Skillable
customer relationships look like at each stage, so your estimates for a
given company can reference comparable relationships — but do NOT
back-calculate your answer to force it into a stage's range.

{CALIBRATION_BLOCK}
"""

_ANTI_PITFALLS = """
═══ ANTI-PITFALLS — AVOID THESE ═══

1. Do NOT conflate user count with training audience. A product with 100M
   users may have a training audience of 10,000. Use Market Demand signals
   to scale from user count.

2. Do NOT use total company employees as the employee_training audience.
   The audience is the TECHNICAL subset who work on the product — not
   finance, HR, legal, general administrative staff.

3. Do NOT inflate academic or ILT audiences by the underlying technology's
   global market. The wrapper org's real audience is bounded by its own
   delivery capacity (classroom seats, instructor count, schedule).

4. Do NOT return a range. Return a single integer per motion. Express
   uncertainty via confidence (low / medium / high) + caveats. Widening
   the number hides uncertainty; stating it surfaces it.

5. Do NOT claim "high" confidence without specific evidence: named cert
   program with sit rate, named partner network with count, named events
   with attendance, third-party training market count. Absent that,
   confidence is low or medium.

6. Do NOT count people twice. Someone who learns through an ATP is counted
   ONCE in customer_training, not again in partner_training. Partners
   train their OWN employees (that's partner_training); end customers
   who happen to train through a partner are customer_training.

7. Do NOT invent customer names in rationale. The calibration block is
   anonymized on purpose. Reference stage patterns ("saturated-stage
   customers", "first-year-stage customers"), not specific names.

8. For Industry Authorities, keep training candidates (customer_training)
   separate from exam sitters (certification). They are a funnel: the
   interested population is larger than the training-candidate population
   is larger than the annual exam-sitter population. certification =
   sitters only; customer_training = training candidates only.

9. When the audience would be zero for a motion (company runs no events,
   has no channel, has no cert), return 0. Do not return a nominal small
   number as a placeholder.
"""

_OUTPUT_SCHEMA_PROMPT = """
═══ OUTPUT — RETURN ONLY JSON, NO PROSE, NO MARKDOWN ═══

{
  "audiences": {
    "customer_training":  <integer >= 0>,
    "partner_training":   <integer >= 0>,
    "employee_training":  <integer >= 0>,
    "certification":      <integer >= 0>,
    "events":             <integer >= 0>
  },
  "confidence": "low" | "medium" | "high",
  "rationale": "<80–150 word paragraph. Lead with Market Demand. Explain why these numbers, not larger or smaller. Do NOT name customers.>",
  "per_motion_rationale": {
    "customer_training":  "<one sentence — who this audience is, why this size>",
    "partner_training":   "<one sentence>",
    "employee_training":  "<one sentence>",
    "certification":      "<one sentence — or 'No cert program; zero sitters' when zero>",
    "events":             "<one sentence — or 'No company events; zero' when zero>"
  },
  "per_motion_confidence": {
    "customer_training":  "low" | "medium" | "high",
    "partner_training":   "low" | "medium" | "high",
    "employee_training":  "low" | "medium" | "high",
    "certification":      "low" | "medium" | "high",
    "events":             "low" | "medium" | "high"
  },
  "key_drivers": ["<up to 5 short sentences naming the signals that most drove the estimate>"],
  "caveats":     ["<up to 3 short sentences naming uncertainties>"],
  "market_demand_story": "<one-line explanation of why paid training demand for this company is X, not larger or smaller>"
}

No prose outside the JSON. No markdown code fences. No explanation
before or after. Just the JSON object, parseable as-is.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Calibration block — anonymized stage-grouped magnitudes
#
# Builds the calibration reference that the judgment call prompt includes.
# Reads known_customers.json via scoring_config.KNOWN_CUSTOMER_CURRENT_ACV
# (loaded lazily from gitignored file; empty dict in dev setups).
# Customer names NEVER enter the output — only stage groupings and
# magnitude ranges.
# ═══════════════════════════════════════════════════════════════════════════════

_STAGE_ORDER = ("saturated", "mature-small", "mid", "first-year", "early", "very-early")


def _format_dollars(amount: int) -> str:
    """Format a dollar amount as '$X' / '$Xk' / '$X.XM' for human reading."""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M".replace(".0M", "M")
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}k"
    return f"${amount}"


def _format_range(lo: int, hi: int) -> str:
    """Format '$Xk–$YM' for a (low, high) range. Single-value range collapses to one figure."""
    if lo == hi:
        return _format_dollars(lo)
    return f"{_format_dollars(lo)}–{_format_dollars(hi)}"


def build_calibration_block() -> str:
    """Build the anonymized stage-grouped magnitude reference for the prompt.

    Reads scoring_config.KNOWN_CUSTOMER_CURRENT_ACV. Customer names NEVER
    enter the output — only stage groupings and magnitude ranges.

    Returns an empty string when no known-customer data is available
    (dev / open-source environments). Callers should handle the empty
    case by including a plain commercial-reality paragraph in place of
    the reference block.
    """
    known = cfg.KNOWN_CUSTOMER_CURRENT_ACV
    if not known:
        return ""

    # Group by stage, deduping by (current_acv, stage) so aliases for the
    # same underlying customer (e.g. "siemens" and "siemens aktiengesellschaft")
    # count once. Accept the floor-of-accuracy risk that two genuinely-
    # different customers with the same (current, stage) collapse to one
    # entry — rare in practice, and the cost is one missing reference
    # rather than a leak.
    by_stage: dict[str, list[dict]] = {s: [] for s in _STAGE_ORDER}
    seen: set[tuple[int, str]] = set()
    for record in known.values():
        if not isinstance(record, dict):
            continue
        stage = record.get("stage", "")
        current = int(record.get("current_acv") or 0)
        if current <= 0 or stage not in by_stage:
            continue
        dedupe_key = (current, stage)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        by_stage[stage].append(record)

    lines: list[str] = []
    for stage in _STAGE_ORDER:
        entries = by_stage[stage]
        if not entries:
            continue
        count = len(entries)

        current_values = [int(e.get("current_acv") or 0) for e in entries]
        current_lo, current_hi = min(current_values), max(current_values)

        potential_lows = [
            int(e.get("acv_potential_low") or e.get("current_acv") or 0)
            for e in entries
            if (e.get("acv_potential_low") or e.get("current_acv"))
        ]
        potential_highs = [
            int(e.get("acv_potential_high") or e.get("current_acv") or 0)
            for e in entries
            if (e.get("acv_potential_high") or e.get("current_acv"))
        ]

        current_str = _format_range(current_lo, current_hi)
        if potential_lows and potential_highs:
            potential_str = _format_range(min(potential_lows), max(potential_highs))
            lines.append(
                f"  Stage '{stage}' ({count} reference customer"
                f"{'s' if count != 1 else ''}): "
                f"current ACV {current_str} · estimated ACV Potential {potential_str}"
            )
        else:
            lines.append(
                f"  Stage '{stage}' ({count} reference customer"
                f"{'s' if count != 1 else ''}): "
                f"current ACV {current_str}"
            )

    return "\n".join(lines) if lines else ""


# ═══════════════════════════════════════════════════════════════════════════════
# Per-company context formatting
# ═══════════════════════════════════════════════════════════════════════════════

def _format_product(product: dict) -> str:
    """Format one product's Tier 1/2 facts as a compact bullet block."""
    name = (product.get("name") or "UNNAMED").strip()
    relationship = (product.get("product_relationship") or "").strip()
    category = (product.get("category") or "").strip()
    subcategory = (product.get("subcategory") or "").strip()
    deployment = (product.get("deployment_model") or "").strip()
    user_base = (product.get("estimated_user_base") or "").strip() or "?"
    personas = (product.get("target_personas") or "").strip() or "?"
    api_surface = (product.get("api_surface") or "").strip() or "?"
    cert_inclusion = (product.get("cert_inclusion") or "").strip() or "?"
    complexity = (product.get("complexity_signals") or "").strip() or "?"
    rough_pl = product.get("rough_labability_score", "?")

    header_parts = [name]
    if relationship:
        header_parts.append(relationship)
    if category:
        header_parts.append(category + (f" / {subcategory}" if subcategory else ""))
    if deployment:
        header_parts.append(deployment)
    header = f"{name} ({', '.join(header_parts[1:])})" if len(header_parts) > 1 else name

    return (
        f"  • {header}\n"
        f"    estimated_user_base: {user_base}\n"
        f"    target_personas: {personas}\n"
        f"    api_surface: {api_surface}\n"
        f"    cert_inclusion: {cert_inclusion}\n"
        f"    complexity_signals: {complexity}\n"
        f"    rough_labability_score: {rough_pl}"
    )


def _format_company_signals(discovery: dict) -> str:
    """Format company-level Tier 3 signals as a compact bullet block."""
    signals = discovery.get("company_signals") or {}

    def _get(key: str) -> str:
        value = signals.get(key, "")
        if value is None:
            return "—"
        text = str(value).strip()
        return text if text else "—"

    return (
        f"  - training_programs:    {_get('training_programs')}\n"
        f"  - training_leadership:  {_get('training_leadership')}\n"
        f"  - training_breadth:     {_get('training_breadth')}\n"
        f"  - sales_channel:        {_get('sales_channel')}\n"
        f"  - atp_program:          {_get('atp_program')}\n"
        f"  - delivery_partners:    {_get('delivery_partners')}\n"
        f"  - events:               {_get('events')}\n"
        f"  - partnership_pattern:  {_get('partnership_pattern')}\n"
        f"  - engagement_model:     {_get('engagement_model')}\n"
        f"  - content_team_signals: {_get('content_team_signals')}\n"
        f"  - lab_platform:         {_get('lab_platform')}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Full prompt assembly
# ═══════════════════════════════════════════════════════════════════════════════

def build_audience_grader_prompt(discovery: dict) -> str:
    """Assemble the complete prompt for the audience judgment call.

    Returns a single string — the full message body to send to Claude.
    System framing + definitions + org-type framing + commercial calibration
    + anonymized reference block + anti-pitfalls + output schema + the
    per-company data (company name, org type, products, company signals).

    Args:
        discovery: The discovery dict, fully populated with Tier 1/2
            per-product facts + Tier 3 per-company signals.

    Returns:
        The assembled prompt as a single string ready to send to Claude.
    """
    company_name = (discovery.get("company_name") or "UNKNOWN").strip()
    org_type = (discovery.get("organization_type") or "").strip() or "unknown"
    products = discovery.get("products") or []
    product_count = len(products)

    calibration_block = build_calibration_block() or (
        "  (No anonymized reference magnitudes available in this environment.\n"
        "   Anchor strictly on the commercial reality section above: Microsoft\n"
        "   ceiling, $500K-$5M typical range, $20M skepticism threshold.)"
    )

    commercial_block = _COMMERCIAL_CALIBRATION.replace(
        "{CALIBRATION_BLOCK}", calibration_block
    )

    product_block = "\n\n".join(_format_product(p) for p in products) if products else "  (no products discovered)"
    signals_block = _format_company_signals(discovery)

    per_company_section = f"""
═══ COMPANY TO ESTIMATE ═══

Company: {company_name}
Org type: {org_type}
Product count: {product_count}

Company-level signals (Tier 3):
{signals_block}

Products (Tier 1/2 facts):
{product_block}

═══ YOUR TASK ═══

Produce ONE JSON object per the output schema above. Five audience
integers. Per-motion rationale and confidence. Overall rationale leading
with the Market Demand story. Key drivers and caveats.

Return JSON only. No prose. No markdown fences.
"""

    return (
        _ROLE_FRAMING
        + _WHAT_TRAINING_AUDIENCE_MEANS
        + _FIVE_MOTIONS
        + _MARKET_DEMAND_AS_GATING_SIGNAL
        + _ORG_TYPE_FRAMING
        + commercial_block
        + _ANTI_PITFALLS
        + _OUTPUT_SCHEMA_PROMPT
        + per_company_section
    )


# ═══════════════════════════════════════════════════════════════════════════════
# The narrow Claude call
# ═══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = (
    "You are a senior training-market analyst for Skillable. Follow the "
    "instructions exactly. Return ONLY a JSON object — no prose, no markdown."
)

# Safe default when the Claude call fails or returns malformed output.
# All audiences zero, low confidence, error surfaced in caveats. Callers
# get a well-formed dict back — never an exception, never a silent miss.
def _safe_default_result(reason: str) -> dict:
    return {
        "audiences": {
            "customer_training":  0,
            "partner_training":   0,
            "employee_training":  0,
            "certification":      0,
            "events":             0,
        },
        "confidence": "low",
        "rationale": f"Audience grader failed to produce a valid estimate: {reason}",
        "per_motion_rationale": {
            "customer_training":  "Grader failed; no estimate available.",
            "partner_training":   "Grader failed; no estimate available.",
            "employee_training":  "Grader failed; no estimate available.",
            "certification":      "Grader failed; no estimate available.",
            "events":             "Grader failed; no estimate available.",
        },
        "per_motion_confidence": {
            "customer_training":  "low",
            "partner_training":   "low",
            "employee_training":  "low",
            "certification":      "low",
            "events":             "low",
        },
        "key_drivers": [],
        "caveats": [f"Audience grader did not return a usable estimate: {reason}"],
        "market_demand_story": "No estimate produced.",
    }


def _validate_and_normalize(raw: dict, company_name: str) -> dict:
    """Validate Claude's raw JSON against the output schema and coerce defensively.

    Every field is filled with a safe default if missing or malformed.
    Audience integers are clamped at >= 0. String fields are coerced to
    strings. Confidence values that aren't one of low/medium/high fall
    back to low.

    Raises no exceptions — callers always get a well-formed dict.
    """
    _valid_confidence = ("low", "medium", "high")

    def _as_int(value: Any) -> int:
        try:
            n = int(value)
            return max(0, n)
        except (TypeError, ValueError):
            return 0

    def _as_confidence(value: Any, default: str = "low") -> str:
        text = str(value or "").strip().lower()
        return text if text in _valid_confidence else default

    def _as_str(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _as_list_of_str(value: Any, max_items: int) -> list[str]:
        if not isinstance(value, list):
            return []
        out: list[str] = []
        for item in value[:max_items]:
            text = _as_str(item)
            if text:
                out.append(text)
        return out

    # Audiences
    raw_audiences = raw.get("audiences") if isinstance(raw, dict) else None
    if not isinstance(raw_audiences, dict):
        raw_audiences = {}
    audiences = {
        "customer_training":  _as_int(raw_audiences.get("customer_training")),
        "partner_training":   _as_int(raw_audiences.get("partner_training")),
        "employee_training":  _as_int(raw_audiences.get("employee_training")),
        "certification":      _as_int(raw_audiences.get("certification")),
        "events":             _as_int(raw_audiences.get("events")),
    }

    # Per-motion dicts
    raw_pmr = raw.get("per_motion_rationale") if isinstance(raw, dict) else None
    if not isinstance(raw_pmr, dict):
        raw_pmr = {}
    per_motion_rationale = {m: _as_str(raw_pmr.get(m)) for m in cfg.MOTION_KEYS}

    raw_pmc = raw.get("per_motion_confidence") if isinstance(raw, dict) else None
    if not isinstance(raw_pmc, dict):
        raw_pmc = {}
    per_motion_confidence = {m: _as_confidence(raw_pmc.get(m)) for m in cfg.MOTION_KEYS}

    result = {
        "audiences": audiences,
        "confidence": _as_confidence(raw.get("confidence") if isinstance(raw, dict) else None),
        "rationale": _as_str(raw.get("rationale") if isinstance(raw, dict) else None),
        "per_motion_rationale": per_motion_rationale,
        "per_motion_confidence": per_motion_confidence,
        "key_drivers": _as_list_of_str(raw.get("key_drivers") if isinstance(raw, dict) else None, 5),
        "caveats": _as_list_of_str(raw.get("caveats") if isinstance(raw, dict) else None, 3),
        "market_demand_story": _as_str(raw.get("market_demand_story") if isinstance(raw, dict) else None),
    }

    # Sanity-check: a non-partnership company with ALL audiences at 0 and
    # low confidence is an implicit grader failure — worth a log warning
    # but still a valid result shape.
    if all(v == 0 for v in audiences.values()):
        log.warning(
            "audience_grader: all five audiences returned 0 for %r — "
            "likely a prompt or research gap, not a real zero company",
            company_name,
        )

    return result


def judge_training_audiences(discovery: dict) -> dict:
    """Judge the five motion audiences for a company.

    ONE Claude turn per company. Produces five audience integers plus
    per-motion rationale / confidence, overall rationale, key drivers,
    caveats, and market_demand_story.

    Short-circuits for partnership-only org types (Content Development)
    and returns PARTNERSHIP_RESULT_SHAPE without calling Claude.

    On Claude call failure or malformed output, returns a safe default
    result (all audiences zero, low confidence, error in caveats).
    Callers always get a well-formed dict — this function never raises.

    Args:
        discovery: The discovery dict.

    Returns:
        A dict matching AUDIENCE_GRADER_OUTPUT_SCHEMA. Strict format
        guaranteed — every key present.
    """
    company_name = discovery.get("company_name") or "UNKNOWN"

    # Partnership-only short-circuit (no Claude call needed)
    if _is_partnership_only(discovery):
        log.info(
            "audience_grader.judge_training_audiences: partnership-only org_type "
            "for %r — returning PARTNERSHIP_RESULT_SHAPE without Claude call",
            company_name,
        )
        return copy.deepcopy(PARTNERSHIP_RESULT_SHAPE)

    # Build prompt
    try:
        user_prompt = build_audience_grader_prompt(discovery)
    except Exception as e:
        log.exception(
            "audience_grader: prompt construction failed for %r: %s",
            company_name, e,
        )
        return _safe_default_result(f"prompt construction error: {e}")

    # Live Claude call — imports scorer._call_claude locally to avoid
    # circular imports (same pattern as rubric_grader.grade_dimension).
    try:
        from scorer import _call_claude  # local import to break cycle
        raw = _call_claude(
            _SYSTEM_PROMPT,
            user_prompt,
            max_tokens=3000,
        )
    except Exception as e:
        log.warning(
            "audience_grader: Claude call failed for %r: %s",
            company_name, e,
        )
        return _safe_default_result(f"Claude call error: {e}")

    # Validate and normalize defensively. Never raises — bad output
    # surfaces as a low-confidence result with caveats, not a crash.
    result = _validate_and_normalize(raw, company_name)
    log.info(
        "audience_grader: %r → customer=%d partner=%d employee=%d cert=%d events=%d (%s)",
        company_name,
        result["audiences"]["customer_training"],
        result["audiences"]["partner_training"],
        result["audiences"]["employee_training"],
        result["audiences"]["certification"],
        result["audiences"]["events"],
        result["confidence"],
    )
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Diff check — does a merged discovery carry new company-level signals?
#
# Used by intelligence.score() after a Deep Dive to decide whether to
# re-fire the judgment call or trust the cached audiences. New company-
# level signals (changed ATP count, new event, different partnership_pattern)
# trigger re-fire; product-only changes do not.
# ═══════════════════════════════════════════════════════════════════════════════

# Company-level fields that trigger a re-fire when they change materially.
# Per-product changes alone do NOT trigger re-fire.
JUDGMENT_REFIRE_SIGNAL_KEYS = (
    "training_programs",
    "training_leadership",
    "training_breadth",
    "sales_channel",
    "atp_program",
    "delivery_partners",
    "events",
    "partnership_pattern",
    "engagement_model",
    "lab_platform",
)


def _normalize_signal(value: Any) -> str:
    """Normalize a signal for comparison — case-fold + collapse whitespace.

    Treats None / empty / "no" / "none" / "n/a" as equivalent (all empty).
    """
    if value is None:
        return ""
    text = str(value).strip().lower()
    if text in ("", "no", "none", "n/a", "na", "unknown", "—"):
        return ""
    # Collapse internal whitespace runs to single spaces
    return " ".join(text.split())


def company_signals_changed_materially(
    old_signals: dict[str, Any],
    new_signals: dict[str, Any],
) -> bool:
    """Return True when new discovery surfaces company-level signals that
    should trigger a re-fire of the judgment call.

    Compares the subset of company_signals keys that are load-bearing for
    the audience estimate (JUDGMENT_REFIRE_SIGNAL_KEYS). Normalizes
    whitespace and case-folds so cosmetic differences don't cause spurious
    re-fires.

    Args:
        old_signals: company_signals dict from the cached discovery.
        new_signals: company_signals dict from the freshly-merged discovery.

    Returns:
        True if any JUDGMENT_REFIRE_SIGNAL_KEYS changed materially.
    """
    old_signals = old_signals or {}
    new_signals = new_signals or {}
    for key in JUDGMENT_REFIRE_SIGNAL_KEYS:
        old_value = _normalize_signal(old_signals.get(key))
        new_value = _normalize_signal(new_signals.get(key))
        if old_value != new_value:
            log.info(
                "audience_grader.company_signals_changed_materially: key %r changed "
                "(old=%r, new=%r) — re-fire",
                key, old_value[:80], new_value[:80],
            )
            return True
    return False
