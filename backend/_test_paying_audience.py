"""TEMPORARY test — can Claude honestly produce ANNUAL PAYING TRAINING AUDIENCE?

Grounds the prompt with the cached discovery context so Claude sees what we
already know about each company, then asks for a separate paying-audience
figure with evidence. Goal: verify the signal is gettable before we rewrite
the researcher prompt. Safe to delete.

Usage: python _test_paying_audience.py
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
    ("discovery_1f91b4f2.json", "Microsoft"),
    ("discovery_2ac24621.json", "CBT Nuggets"),
    ("discovery_892e80c8.json", "CompTIA"),
]

SYSTEM = """You are a market research analyst. Your job is to produce
HONEST estimates of annual paying training audiences for specific companies,
grounded in real public data. You distinguish clearly between:

- TAM (Total Addressable Market): people who COULD train on a topic
- Annual paying training audience: people who actually PAID this company
  in a typical recent year (2024 or 2025) for training

You are ruthless about not confusing these two. You return thin evidence
honestly rather than inflating numbers."""

PROMPT_TEMPLATE = """Estimate {company}'s ANNUAL PAYING TRAINING AUDIENCE —
the unique humans who, in a typical recent year (2024 or 2025), PAY this
company (directly, or via a partner who pays them) for training content
that includes or could include hands-on labs.

This is NOT:
  - TAM (people who could theoretically train)
  - Lifetime / cumulative users (e.g. "1M since 2002")
  - Peak historical audience
  - Fortune 500 employee counts × adoption rates
  - Global cert-candidate populations (unless this company ISSUES the cert)

Rules:
  - If this company is a CERT ISSUER (e.g. CompTIA, EC-Council, AWS),
    annual cert exam volume counts toward audience.
  - If this company is a CERT PREP TRAINER (e.g. CBT Nuggets, Skillsoft),
    do NOT count exam candidates — count their own subscribers only.
  - If audience flows PRIMARILY through Authorized Training Partners (ATPs),
    the ATP-delivered audience is NOT this company's paying audience
    (the ATPs pay Skillable, not the vendor). Call this out explicitly.
  - Be honest when evidence is thin. Return a range with confidence.

Ground the estimate in at least one of:
  - Public subscription or learner counts (annual active)
  - Reported training-segment revenue ÷ implied per-learner price
  - Disclosed enterprise customer count × realistic active-user fraction
  - Annual cert exam delivery statistics (for cert issuers)

Context — here is what we already know about {company} from cached discovery:

ORG TYPE: {org_type}
COMPANY DESCRIPTION: {description}

COMPANY SIGNALS:
{company_signals}

KNOWN PRODUCTS (name + estimated TAM user base from prior research):
{products}

Return JSON only, no prose:
{{
  "annual_paying_audience_low":  <int>,
  "annual_paying_audience_high": <int>,
  "midpoint":                    <int>,
  "confidence":                  "confirmed" | "indicated" | "inferred",
  "evidence": "<2-3 sentences citing specific numbers/sources>",
  "tam_note": "<1-2 sentences: how the TAM you'd cite differs from this paying number, and why>",
  "atp_flow_note": "<if most audience goes through ATPs/partners who pay Skillable directly, explain the attribution here; otherwise 'n/a'>"
}}"""


def run_one(filename: str, company_label: str) -> None:
    path = Path("data/company_intel") / filename
    if not path.exists():
        print(f"SKIP: {path} not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    # Assemble company_signals narrative block
    cs = d.get("company_signals") or {}
    cs_lines = []
    for k, v in cs.items():
        if isinstance(v, str) and v.strip():
            cs_lines.append(f"- {k}: {v}")
    company_signals_block = "\n".join(cs_lines) if cs_lines else "(none)"

    # Products block
    prod_lines = []
    for p in (d.get("products") or []):
        name = p.get("name")
        ub = p.get("estimated_user_base") or "(no estimate)"
        ev = (p.get("user_base_evidence") or "")[:140]
        prod_lines.append(f"- {name} | TAM: {ub} | evidence: {ev}")
    products_block = "\n".join(prod_lines) if prod_lines else "(no products)"

    prompt = PROMPT_TEMPLATE.format(
        company=company_label,
        org_type=d.get("organization_type") or "(unknown)",
        description=(d.get("company_description") or "(none)")[:800],
        company_signals=company_signals_block,
        products=products_block,
    )

    print()
    print("=" * 72)
    print(f"{company_label} ({d.get('organization_type')})")
    print("=" * 72)

    try:
        result = _call_claude(SYSTEM, prompt, max_tokens=1500)
    except Exception as e:
        print(f"FAILED: {e}")
        return

    # Print pretty
    low = result.get("annual_paying_audience_low")
    high = result.get("annual_paying_audience_high")
    mid = result.get("midpoint")
    conf = result.get("confidence")
    evidence = result.get("evidence")
    tam_note = result.get("tam_note")
    atp = result.get("atp_flow_note")

    def fmt(n):
        return f"{n:,}" if isinstance(n, (int, float)) else str(n)

    print(f"  Paying audience: {fmt(low)} — {fmt(high)}  (midpoint: {fmt(mid)})")
    print(f"  Confidence: {conf}")
    print()
    print(f"  Evidence: {evidence}")
    print()
    print(f"  TAM vs paying: {tam_note}")
    print()
    print(f"  ATP flow note: {atp}")
    print()


if __name__ == "__main__":
    for filename, label in TESTS:
        run_one(filename, label)
