"""TEMPORARY test — final per-motion paying-audience estimation with
org-type routing per Frank's rate card decisions (2026-04-17).

Motion set per org type:
  software            : customer_ilt, on_demand_learners, channel_enablement,
                         employee_training, cert_candidates, events_attendees
  gsi_var             : channel_enablement (Practice Leads & Consultants),
                         events_attendees (potential), customers_unquantifiable
  training_partner    : ilt_students, on_demand_learners, instructors
  industry_authority  : ilt_students, on_demand_learners, cert_candidates,
                         exam_prep_subscribers, instructors
  academic            : academic_students, academic_faculty, academic_staff,
                         academic_events

Post-hoc rate card (applied outside the prompt):
  Customer ILT / ILT students / Students      : $200/yr  (hyperscaler $30)
  On-demand Learning (SW paid)                 : $30/yr  (hyperscaler $5)
  On-demand Learning (ELP paid)                : $10/yr  (hyperscaler $3)
  On-demand Learning (free big library)        : $5/yr   (hyperscaler $2)
  Channel Enablement / Practice Leads          : $200/yr (hyperscaler $30)
  Employee Training                            : $30/yr  (hyperscaler $6)
  Cert Exam Labs                               : $10/yr  (hyperscaler $3, may tune up)
  Exam Prep Labs                               : $10/yr
  Events (hands-on)                            : $50/yr  (hyperscaler $15, may tune up)
  Instructors                                  : $200/yr
  Faculty / Staff (academic)                   : $30/yr
  Career Fairs (academic events)               : $50/yr
  Customers (GSI)                              : unquantifiable
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

from scorer import _call_claude

TESTS = [
    ("discovery_1f91b4f2.json", "Microsoft",            "software"),
    ("discovery_b54050c0.json", "Cisco",                "software"),
    ("discovery_1d04b0cb.json", "Nutanix",              "software"),
    ("discovery_5f47ed90.json", "Trellix",              "software"),
    ("discovery_10cbcbe3.json", "Quantum Corporation",  "software"),
    ("discovery_1cb7b6ab.json", "Hyland",               "software"),
    ("discovery_b5a1386c.json", "NVIDIA",               "software"),
    ("discovery_03ad4fb7.json", "Eaton Corporation",    "software"),
    ("discovery_40c644f6.json", "TRUMPF",               "software"),
    ("discovery_d7bd4176.json", "Milestone Systems",    "software"),
    ("discovery_594374c6.json", "Sage Group",           "software"),
    ("discovery_6e41edea.json", "Calix",                "software"),
    ("discovery_3d52775d.json", "Deloitte",             "gsi_var"),
    ("discovery_82068842.json", "QA",                   "training_partner"),
    ("discovery_aa71c3ce.json", "Firebrand Training",   "training_partner"),
    ("discovery_82409fa6.json", "Skillsoft",            "training_partner"),
    ("discovery_2ac24621.json", "CBT Nuggets",          "training_partner"),
    ("discovery_3d52f554.json", "Pluralsight",          "training_partner"),
    ("discovery_892e80c8.json", "CompTIA",              "industry_authority"),
    ("discovery_8a92e701.json", "EC-Council",           "industry_authority"),
    ("discovery_373d0614.json", "Arizona State University", "academic"),
]

# Rate card — post-hoc math.
# Hyperscaler names trigger the hyperscaler override.
HYPERSCALERS = {"microsoft", "cisco", "google", "aws", "amazon web services"}

RATES_LIST = {
    "ilt_students":            200,
    "customer_ilt":            200,  # alias
    "academic_students":       200,
    "on_demand_sw":             30,
    "on_demand_elp":            10,
    "on_demand_free_library":    5,
    "channel_enablement":      200,
    "practice_leads":          200,  # alias for GSI row
    "employee_training":        30,
    "cert_candidates":          10,
    "exam_prep_subscribers":    10,
    "events_attendees":         50,
    "academic_events":          50,
    "instructors":             200,
    "academic_faculty":         30,
    "academic_staff":           30,
}

RATES_HYPERSCALER = {
    "ilt_students":            30,
    "customer_ilt":            30,
    "academic_students":       30,   # n/a for academic but here for completeness
    "on_demand_sw":             5,
    "on_demand_elp":            3,
    "on_demand_free_library":   2,
    "channel_enablement":      30,
    "practice_leads":          30,
    "employee_training":         6,
    "cert_candidates":           3,   # may tune up to 5-8 after test
    "exam_prep_subscribers":     3,
    "events_attendees":         15,   # may tune up to 25-30
    "academic_events":          15,
    "instructors":              30,
    "academic_faculty":          6,
    "academic_staff":            6,
}


SYSTEM = """You are a market research analyst. Your job is to produce
HONEST per-motion paying-audience estimates for specific companies, grounded
in real public data. You distinguish clearly between TAM and actual paying
audience. You never invent numbers. You return 0 with "does_not_apply" when
a motion does not fit the company's business model. You return thin-evidence
triangulated estimates (low/high/midpoint with reasoning) when a motion
clearly exists but specific numbers aren't disclosed."""

PROMPT_TEMPLATE = """Estimate {company}'s ANNUAL PAYING audience across each
motion that applies to their org type ({org_type}). Reference year: 2024 or
2025 where data exists.

This is NOT TAM. This is NOT lifetime/cumulative. This IS the annual paying
audience who pay THIS company (directly or via a partner who pays them)
for hands-on lab content.

---
MOTIONS — return data ONLY for motions that apply to org_type={org_type}:

{motion_list}

---
SHARED DEFINITIONS (apply to all motions when relevant):

HANDS-ON LAB CONTENT = content with hands-on labs, hands-on learning, or
skill development experiences in live environments (sandboxes, VMs,
containers). Excludes video-only, quiz-only, reading, business-skills,
leadership, compliance, or lecture-only content.

CERT ISSUER vs PREP TRAINER: If this company ISSUES its own certification
(CompTIA, EC-Council, Microsoft AZ-series, AWS certs, Cisco CCNA, Nutanix
NCP), count cert candidates. If it's a PREP TRAINER (trains for someone
else's cert — Skillsoft, CBT Nuggets, Pluralsight preparing for CompTIA),
cert_candidates = 0.

ATP FLOW: If training delivery runs primarily through Authorized Training
Partners (ATPs) who pay Skillable directly, EXCLUDE those ATP-delivered
students from this company's direct count. Note the volume in `atp_flow_note`.

TRIANGULATION: When direct enrollment data is not disclosed, triangulate
from customer count × adoption rate (5-20%), partner count × staff per
partner (2-5), or employee count × trained fraction (10-30%). Never return
null when a motion clearly exists — estimate with thin_evidence confidence.
Only return 0 when the motion genuinely doesn't apply.

---
Context — what we already know about {company} from cached discovery:

ORG TYPE: {discovery_org_type}
DESCRIPTION: {description}

COMPANY SIGNALS:
{company_signals}

KNOWN PRODUCTS (TAM user base, NOT paying audience):
{products}

---
Return JSON only:
{{
  "motions": {{
{motion_schema}
  }},
  "tam_note": "<1-2 sentences on how TAM differs from paying audience for this company>",
  "atp_flow_note": "<ATP flow if relevant; otherwise 'n/a'>"
}}

For each motion's record, use:
{{"low": <int>, "high": <int>, "midpoint": <int>,
 "confidence": "confirmed" | "indicated" | "inferred" | "thin_evidence" | "does_not_apply",
 "evidence": "<2-3 sentences citing specific numbers/sources/triangulation logic>"}}

For `customers_unquantifiable` (GSI only), use:
{{"status": "unquantifiable", "note": "<why we can't estimate end-customer
   audience for this GSI — typically because they embed training in customer
   engagements rather than selling training as a standalone product>"}}
"""


MOTION_DEFINITIONS = {
    # ─── Software ─────────────────────────────────────────────────
    "customer_ilt": """CUSTOMER INSTRUCTOR-LED TRAINING
  Students who paid for a seat in an instructor-led training from this
  company — bootcamp, intensive, or traditional course (1-day through
  multi-week) — that included substantial hands-on labs (typically 5+
  hours of labs). Excludes: short workshops <4 hours of lab, apprenticeships,
  conceptual-only, free demos, or courses delivered by a different ATP.""",

    "on_demand_learners": """CUSTOMER ON-DEMAND LEARNING
  People who consumed an hour of asynchronous, on-demand, e-learning
  that included a hands-on lab, hands-on learning, or skill development
  experience in the reference year. Count individuals, not enterprise
  seats. Annual active.
  Also classify the catalog type in `catalog_type` field:
    "sw_paid" = paid software vendor catalog (Nutanix University, Hyland U)
    "elp_paid" = paid ELP catalog (CBT Nuggets, Pluralsight Skills, Percipio)
    "free_big_library" = free vendor-subsidized big library (Microsoft
                         Learn, AWS Skill Builder, Google Cloud Skills Boost)""",

    "channel_enablement": """CHANNEL ENABLEMENT (sellers/SEs)
  Sellers and technical sellers (pre-sales engineers, solutions engineers,
  channel solution consultants, technical consultants) employed by CHANNEL
  PARTNER COMPANIES (GSIs like Deloitte/Accenture/KPMG, VARs, SIs, MSSPs,
  implementation partners) who used this vendor's hands-on lab environments
  during the year for customer demos, POCs, practice sessions, or
  feature-learning. NOT internal vendor employees (those go in
  employee_training). NOT partner staff being TRAINED (that's separate
  and usually double-counts — don't create it).
  Triangulate from partner count × engineer density (2-5 small VAR;
  50-500 regional SI; 1K-20K top GSI) × lab-user fraction (10-30%).""",

    "employee_training": """EMPLOYEE TRAINING
  This company's OWN employees — including internal sales engineers (SEs),
  solutions engineers, solution architects, support engineers, consulting
  engineers, and technical staff — who received paid hands-on lab training
  in the reference year.""",

    "cert_candidates": """CERTIFICATION EXAM LABS (ISSUERS ONLY)
  Students who sat an exam this company ISSUES in the reference year
  (e.g., Microsoft AZ-900, Nutanix NCP, Cisco CCNA, CompTIA Security+).
  Cert prep trainers return 0.""",

    "events_attendees": """HANDS-ON LABS @ EVENTS
  Paid registrants SUMMED across ALL the company's hands-on conferences
  and summits annually (flagship + product summits + regional tours +
  partner events + developer conferences). Include only paid registrants
  at events with hands-on lab sessions. Large vendors (Microsoft, AWS,
  Cisco) may have 10+ events — sum them all.""",

    # ─── GSI / VAR ────────────────────────────────────────────────
    "practice_leads_consultants": """PRACTICE LEADS & CONSULTANTS
  The GSI/VAR/Distributor's OWN technical consultants, practice leads,
  solution architects, and cloud-practice engineers who used this company's
  lab environments during the year for customer-facing work. For Deloitte:
  the Azure/AWS/Cisco/etc practice consultants. Count individual
  consultants who actively touched labs.
  Same functional motion as `channel_enablement` for software companies —
  just from the partner's own side.""",

    "customers_unquantifiable": """CUSTOMERS (UNQUANTIFIABLE FLAG)
  End customers who consume labs through this GSI/VAR/distributor's
  embedded training in consulting engagements. We cannot reliably estimate
  this audience from public data. Return status: "unquantifiable" with
  a brief note.""",

    # ─── Training Partner / ELP / ATP ─────────────────────────────
    "ilt_students": """INSTRUCTOR-LED TRAINING
  Students who paid this training partner for a seat in an ILT course —
  bootcamp, intensive, or multi-day — that included substantial hands-on
  labs (5+ hours). Excludes short workshops, apprenticeships, conceptual-only.""",

    "instructors": """INSTRUCTORS
  The training partner's / industry authority's OWN instructors who used
  lab environments during the year for course preparation, practice,
  staying current, or delivering sessions. Triangulate from total
  instructor count (often published) × lab-active fraction (~50-80%).""",

    # ─── Industry Authority ───────────────────────────────────────
    "exam_prep_subscribers": """EXAM PREP LABS
  Annual paying subscribers to this issuer's practice-exam products
  (CertMaster Practice, CertMaster Labs, equivalent). Separate from
  on_demand_learners (which is learning content) and cert_candidates
  (which is the exam itself).""",

    # ─── Academic ─────────────────────────────────────────────────
    "academic_students": """STUDENTS
  Paying students at this academic institution who used hands-on lab
  environments during the year as part of paid coursework or workforce-
  development programs. Exclude free community programs.""",

    "academic_faculty": """FACULTY
  Faculty and instructors at this academic institution who used hands-on
  lab environments for teaching, curriculum development, or research.""",

    "academic_staff": """STAFF
  Non-faculty institution staff (IT, administrators, program coordinators)
  who used hands-on lab environments during the year.""",

    "academic_events": """CAREER FAIRS & EVENTS
  Paid attendees or participants at this institution's career fairs, hands-
  on events, or hackathons that used lab environments.""",
}


MOTIONS_BY_ORG_TYPE = {
    "software": ["customer_ilt", "on_demand_learners", "channel_enablement",
                 "employee_training", "cert_candidates", "events_attendees"],
    "gsi_var": ["practice_leads_consultants", "events_attendees",
                "customers_unquantifiable"],
    "training_partner": ["ilt_students", "on_demand_learners", "instructors"],
    "industry_authority": ["ilt_students", "on_demand_learners",
                           "cert_candidates", "exam_prep_subscribers",
                           "instructors"],
    "academic": ["academic_students", "academic_faculty", "academic_staff",
                 "academic_events"],
}


def build_motion_list(motion_keys: list[str]) -> str:
    lines = []
    for i, key in enumerate(motion_keys, 1):
        definition = MOTION_DEFINITIONS.get(key, f"(unknown motion: {key})")
        lines.append(f" {i}. {definition}")
    return "\n\n".join(lines)


def build_motion_schema(motion_keys: list[str]) -> str:
    lines = []
    for key in motion_keys:
        if key == "customers_unquantifiable":
            lines.append(f'    "{key}": {{"status": "unquantifiable", "note": "..."}}')
        elif key == "on_demand_learners":
            lines.append(f'    "{key}": {{"low": <int>, "high": <int>, "midpoint": <int>, "confidence": "...", "evidence": "...", "catalog_type": "sw_paid" | "elp_paid" | "free_big_library"}}')
        else:
            lines.append(f'    "{key}": {{"low": <int>, "high": <int>, "midpoint": <int>, "confidence": "...", "evidence": "..."}}')
    return ",\n".join(lines)


def compute_motion_acv(motion_key: str, midpoint: int, catalog_type: str,
                       hyperscaler: bool) -> int:
    """Apply rate card to a single motion midpoint."""
    if motion_key == "customers_unquantifiable":
        return 0
    if motion_key == "on_demand_learners":
        if catalog_type == "free_big_library":
            rate_key = "on_demand_free_library"
        elif catalog_type == "elp_paid":
            rate_key = "on_demand_elp"
        else:
            rate_key = "on_demand_sw"
    elif motion_key == "practice_leads_consultants":
        rate_key = "practice_leads"
    else:
        rate_key = motion_key
    rates = RATES_HYPERSCALER if hyperscaler else RATES_LIST
    rate = rates.get(rate_key, 0)
    return int((midpoint or 0) * rate)


def run_one(filename: str, company_label: str, org_type: str) -> dict:
    path = Path("data/company_intel") / filename
    if not path.exists():
        print(f"SKIP: {path} not found")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    cs = d.get("company_signals") or {}
    cs_lines = []
    for k, v in cs.items():
        if isinstance(v, str) and v.strip():
            cs_lines.append(f"- {k}: {v}")
    company_signals_block = "\n".join(cs_lines) if cs_lines else "(none)"

    prod_lines = []
    for p in (d.get("products") or [])[:30]:
        name = p.get("name")
        ub = p.get("estimated_user_base") or "(no estimate)"
        ev = (p.get("user_base_evidence") or "")[:120]
        prod_lines.append(f"- {name} | TAM: {ub} | {ev}")
    products_block = "\n".join(prod_lines) if prod_lines else "(no products)"

    motion_keys = MOTIONS_BY_ORG_TYPE.get(org_type, [])
    motion_list = build_motion_list(motion_keys)
    motion_schema = build_motion_schema(motion_keys)

    prompt = PROMPT_TEMPLATE.format(
        company=company_label,
        org_type=org_type,
        discovery_org_type=d.get("organization_type") or "(unknown)",
        description=(d.get("company_description") or "(none)")[:800],
        company_signals=company_signals_block,
        products=products_block,
        motion_list=motion_list,
        motion_schema=motion_schema,
    )

    print()
    print("=" * 76)
    print(f"{company_label}  [{org_type}]")
    print("=" * 76)

    try:
        result = _call_claude(SYSTEM, prompt, max_tokens=3500)
    except Exception as e:
        print(f"FAILED: {e}")
        return {}

    hyperscaler = company_label.lower() in HYPERSCALERS
    motions = result.get("motions") or {}
    total_acv_list = 0
    total_acv_hs = 0

    def fmt_n(n):
        return f"{n:,}" if isinstance(n, (int, float)) and n is not None else str(n)

    def fmt_d(n):
        return f"${n:,.0f}" if isinstance(n, (int, float)) and n is not None else "—"

    print(f"  {'motion':<28s} {'audience (low-high)':<22s} {'mid':>10s}   rate   {'list ACV':>12s}  {'HS ACV':>12s}")
    print(f"  {'-'*28} {'-'*22} {'-'*10}   {'-'*6} {'-'*12}  {'-'*12}")

    for key in motion_keys:
        m = motions.get(key) or {}

        if key == "customers_unquantifiable":
            status = m.get("status", "?")
            note = m.get("note", "")[:50]
            print(f"  {key:<28s} status={status:<15s}  note={note}")
            continue

        low = m.get("low")
        high = m.get("high")
        mid = m.get("midpoint") or 0
        conf = m.get("confidence", "")
        catalog_type = m.get("catalog_type", "sw_paid")

        acv_list = compute_motion_acv(key, mid, catalog_type, False)
        acv_hs = compute_motion_acv(key, mid, catalog_type, True)
        total_acv_list += acv_list
        total_acv_hs += acv_hs

        rate_list = RATES_LIST.get(
            "on_demand_sw" if key == "on_demand_learners" and catalog_type == "sw_paid" else
            "on_demand_elp" if key == "on_demand_learners" and catalog_type == "elp_paid" else
            "on_demand_free_library" if key == "on_demand_learners" and catalog_type == "free_big_library" else
            "practice_leads" if key == "practice_leads_consultants" else
            key,
            0
        )

        range_str = f"{fmt_n(low)}-{fmt_n(high)}"
        print(f"  {key:<28s} {range_str:<22s} {fmt_n(mid):>10s}   ${rate_list:>4d}   {fmt_d(acv_list):>12s}  {fmt_d(acv_hs):>12s}   [{conf}]")

    print()
    applied_acv = total_acv_hs if hyperscaler else total_acv_list
    hs_tag = "  (HYPERSCALER rates)" if hyperscaler else ""
    print(f"  TOTAL ACV Target:  list={fmt_d(total_acv_list)}   hyperscaler={fmt_d(total_acv_hs)}")
    print(f"  ACV Target (applied):  {fmt_d(applied_acv)}{hs_tag}")
    print()

    tam = result.get("tam_note", "")
    if tam:
        print(f"  TAM note: {tam[:200]}")
    atp = result.get("atp_flow_note", "")
    if atp and atp.strip().lower() not in ("n/a", "na", ""):
        print(f"  ATP flow: {atp[:200]}")
    print()

    return {
        "company": company_label,
        "org_type": org_type,
        "hyperscaler": hyperscaler,
        "acv_target_list": total_acv_list,
        "acv_target_hs": total_acv_hs,
        "acv_target_applied": applied_acv,
        "motions_raw": motions,
    }


if __name__ == "__main__":
    results = []
    for filename, label, org_type in TESTS:
        r = run_one(filename, label, org_type)
        if r:
            results.append(r)

    print()
    print("=" * 76)
    print("SUMMARY — ACV Target by company")
    print("=" * 76)
    print(f"  {'company':<30s} {'org_type':<22s} {'ACV Target':>14s}")
    print(f"  {'-'*30} {'-'*22} {'-'*14}")
    for r in sorted(results, key=lambda x: -x["acv_target_applied"]):
        hs = " (HS)" if r["hyperscaler"] else ""
        acv_str = f"${r['acv_target_applied']:,}"
        print(f"  {r['company']:<30s} {r['org_type']:<22s} {acv_str:>14s}{hs}")
