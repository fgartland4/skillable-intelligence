"""TEMPORARY recompute — apply a Big tier (100K-3M total audience) to the
existing test output. No re-run of Claude; just recomputes ACV with a
three-tier rate card (Mid / Big / Hyperscaler) instead of two-tier.

Rate card:
  Mid tier (<100K total audience):      LIST rates
  Big tier (100K-3M total audience):    40% of list
  Hyperscaler tier (Microsoft/AWS/Google only, by name): HS rates

Cisco moves from Hyperscaler to Big (too small for HS, too big for Mid).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

# ── Audiences from the run that just completed (parsed from output) ─────
# Format: (company, org_type, motion_dict)
# motion_dict: motion_key -> (midpoint, catalog_type_if_applicable)

RESULTS = {
    "Microsoft": ("software", {
        "customer_ilt":          (250_000, None),
        "on_demand_learners":    (22_000_000, "free_big_library"),
        "channel_enablement":    (380_000, None),
        "employee_training":     (50_000, None),
        "cert_candidates":       (1_600_000, None),
        "events_attendees":      (90_000, None),
    }),
    "Cisco": ("software", {
        "customer_ilt":          (90_000, None),
        "on_demand_learners":    (350_000, "sw_paid"),
        "channel_enablement":    (75_000, None),
        "employee_training":     (13_000, None),
        "cert_candidates":       (550_000, None),
        "events_attendees":      (55_000, None),
    }),
    "Nutanix": ("software", {
        "customer_ilt":          (5_000, None),
        "on_demand_learners":    (13_000, "sw_paid"),
        "channel_enablement":    (5_500, None),
        "employee_training":     (2_500, None),
        "cert_candidates":       (8_000, None),
        "events_attendees":      (3_500, None),
    }),
    "Trellix": ("software", {
        "customer_ilt":          (2_500, None),
        "on_demand_learners":    (1_500, "sw_paid"),
        "channel_enablement":    (550, None),
        "employee_training":     (900, None),
        "cert_candidates":       (0, None),
        "events_attendees":      (0, None),
    }),
    "Quantum Corporation": ("software", {
        "customer_ilt":          (400, None),
        "on_demand_learners":    (1_200, "sw_paid"),
        "channel_enablement":    (800, None),
        "employee_training":     (275, None),
        "cert_candidates":       (0, None),
        "events_attendees":      (200, None),
    }),
    "Hyland": ("software", {
        "customer_ilt":          (3_500, None),
        "on_demand_learners":    (5_500, "sw_paid"),
        "channel_enablement":    (1_500, None),
        "employee_training":     (1_500, None),
        "cert_candidates":       (1_200, None),
        "events_attendees":      (1_800, None),
    }),
    "NVIDIA": ("software", {
        "customer_ilt":          (25_000, None),
        "on_demand_learners":    (90_000, "sw_paid"),
        "channel_enablement":    (5_500, None),
        "employee_training":     (35_000, None),
        "cert_candidates":       (18_000, None),
        "events_attendees":      (12_000, None),
    }),
    "Eaton Corporation": ("software", {
        "customer_ilt":          (5_000, None),
        "on_demand_learners":    (0, "sw_paid"),
        "channel_enablement":    (800, None),
        "employee_training":     (275, None),
        "cert_candidates":       (2_000, None),
        "events_attendees":      (0, None),
    }),
    "TRUMPF": ("software", {
        "customer_ilt":          (5_500, None),
        "on_demand_learners":    (1_500, "sw_paid"),
        "channel_enablement":    (0, None),
        "employee_training":     (0, None),
        "cert_candidates":       (0, None),
        "events_attendees":      (5_000, None),
    }),
    "Milestone Systems": ("software", {
        "customer_ilt":          (2_500, None),
        "on_demand_learners":    (5_000, "sw_paid"),
        "channel_enablement":    (0, None),
        "employee_training":     (0, None),
        "cert_candidates":       (3_500, None),
        "events_attendees":      (1_400, None),
    }),
    "Sage Group": ("software", {
        "customer_ilt":          (8_000, None),
        "on_demand_learners":    (15_000, "sw_paid"),
        "channel_enablement":    (7_500, None),
        "employee_training":     (3_000, None),
        "cert_candidates":       (1_000, None),
        "events_attendees":      (4_000, None),
    }),
    "Calix": ("software", {
        "customer_ilt":          (750, None),
        "on_demand_learners":    (5_000, "sw_paid"),
        "channel_enablement":    (220, None),
        "employee_training":     (260, None),
        "cert_candidates":       (1_100, None),
        "events_attendees":      (100, None),
    }),
    "Deloitte": ("gsi_var", {
        "practice_leads_consultants": (30_000, None),
        "events_attendees":           (1_500, None),
    }),
    "QA": ("training_partner", {
        "ilt_students":       (55_000, None),
        "on_demand_learners": (75_000, "elp_paid"),
        "instructors":        (450, None),
    }),
    "Firebrand Training": ("training_partner", {
        "ilt_students":       (17_000, None),
        "on_demand_learners": (3_000, "elp_paid"),
        "instructors":        (130, None),
    }),
    "Skillsoft": ("training_partner", {
        "ilt_students":       (15_000, None),
        "on_demand_learners": (1_750_000, "elp_paid"),
        "instructors":        (750, None),
    }),
    "CBT Nuggets": ("training_partner", {
        "ilt_students":       (0, None),
        "on_demand_learners": (225_000, "elp_paid"),
        "instructors":        (60, None),
    }),
    "Pluralsight": ("training_partner", {
        "ilt_students":       (0, None),
        "on_demand_learners": (800_000, "elp_paid"),
        "instructors":        (0, None),
    }),
    "CompTIA": ("industry_authority", {
        "ilt_students":          (28_000, None),
        "on_demand_learners":    (190_000, "elp_paid"),  # CertMaster Learn ~ ELP
        "cert_candidates":       (1_100_000, None),
        "exam_prep_subscribers": (130_000, None),
        "instructors":           (2_500, None),
    }),
    "EC-Council": ("industry_authority", {
        "ilt_students":          (52_500, None),
        "on_demand_learners":    (130_000, "elp_paid"),
        "cert_candidates":       (150_000, None),
        "exam_prep_subscribers": (42_500, None),
        "instructors":           (3_250, None),
    }),
    "Arizona State University": ("academic", {
        "academic_students": (14_000, None),
        "academic_faculty":  (380, None),
        "academic_staff":    (110, None),
        "academic_events":   (150, None),
    }),
}

TARGETS = {
    "Microsoft": 45_000_000,
    "CompTIA": 6_000_000,
    "Skillsoft": 7_000_000,
    "EC-Council": 3_000_000,
    "QA": 2_000_000,
    "Cisco": 22_000_000,
    "Pluralsight": 8_000_000,
    "Deloitte": 15_000_000,
    "Sage Group": 5_000_000,
    "Firebrand Training": 3_000_000,
    "Nutanix": 3_000_000,
    "Arizona State University": 3_500_000,
    "CBT Nuggets": 2_000_000,
    "Milestone Systems": 2_000_000,
    "TRUMPF": 1_200_000,
    "Hyland": 700_000,
    "Eaton Corporation": 2_000_000,
    "Trellix": 3_000_000,
    "Calix": 650_000,
    "Quantum Corporation": 400_000,
    "NVIDIA": 14_000_000,
}

HYPERSCALERS = {"Microsoft", "AWS", "Amazon Web Services", "Google", "Google Cloud"}

# ─────────────────────────────────────────────────────────────────────
# Rate card — three tiers (Mid / Big / Hyperscaler)
# ─────────────────────────────────────────────────────────────────────
RATES_MID = {
    "customer_ilt":            200,
    "ilt_students":            200,
    "academic_students":       200,
    "on_demand_sw":             30,
    "on_demand_elp":            10,
    "on_demand_free_library":    5,
    "channel_enablement":      200,
    "practice_leads_consultants": 200,
    "employee_training":        30,
    "cert_candidates":          10,
    "exam_prep_subscribers":    10,
    "events_attendees":         50,
    "academic_events":          50,
    "instructors":             200,
    "academic_faculty":         30,
    "academic_staff":           30,
}

# Big tier = 40% of list (volume discount at 100K-3M audience scale)
BIG_FACTOR = 0.40
RATES_BIG = {k: int(v * BIG_FACTOR) for k, v in RATES_MID.items()}

RATES_HS = {
    "customer_ilt":            30,
    "ilt_students":            30,
    "academic_students":       30,
    "on_demand_sw":             5,
    "on_demand_elp":            3,
    "on_demand_free_library":   2,
    "channel_enablement":      30,
    "practice_leads_consultants": 30,
    "employee_training":         6,
    "cert_candidates":           3,
    "exam_prep_subscribers":     3,
    "events_attendees":         15,
    "academic_events":          15,
    "instructors":              30,
    "academic_faculty":          6,
    "academic_staff":            6,
}

BIG_TIER_MIN = 100_000
BIG_TIER_MAX = 3_000_000


def determine_tier(company: str, total_audience: int) -> str:
    """Hyperscaler by name; else by total audience into Mid/Big."""
    if company in HYPERSCALERS:
        return "HS"
    if BIG_TIER_MIN <= total_audience <= BIG_TIER_MAX:
        return "BIG"
    if total_audience > BIG_TIER_MAX:
        # Non-hyperscaler companies shouldn't realistically hit Massive
        # (that's a hyperscaler-only bucket). If they do, use Big rates.
        return "BIG"
    return "MID"


def get_rate(motion_key: str, catalog_type: str | None, tier: str) -> int:
    if motion_key == "on_demand_learners":
        if catalog_type == "free_big_library":
            rate_key = "on_demand_free_library"
        elif catalog_type == "elp_paid":
            rate_key = "on_demand_elp"
        else:
            rate_key = "on_demand_sw"
    else:
        rate_key = motion_key

    if tier == "HS":
        return RATES_HS.get(rate_key, 0)
    if tier == "BIG":
        return RATES_BIG.get(rate_key, 0)
    return RATES_MID.get(rate_key, 0)


def compute_one(company: str, org_type: str, motions: dict) -> dict:
    total_audience = sum(mid for mid, _ in motions.values() if mid)
    tier = determine_tier(company, total_audience)

    total_acv = 0
    breakdown = []
    for motion_key, (mid, catalog_type) in motions.items():
        if not mid:
            continue
        rate = get_rate(motion_key, catalog_type, tier)
        acv = mid * rate
        total_acv += acv
        breakdown.append((motion_key, mid, rate, acv))

    return {
        "company": company,
        "org_type": org_type,
        "tier": tier,
        "total_audience": total_audience,
        "total_acv": total_acv,
        "breakdown": breakdown,
    }


def main():
    results = [compute_one(c, ot, motions) for c, (ot, motions) in RESULTS.items()]
    results.sort(key=lambda x: -x["total_acv"])

    print("=" * 110)
    print("ACV with three-tier rate card (Mid < 100K / Big 100K-3M / Hyperscaler by name)")
    print(f"Big tier = {BIG_FACTOR:.0%} of list rates")
    print("=" * 110)
    print()
    print(f"  {'#':>2}  {'company':<30s} {'org_type':<22s} {'tier':<5s} {'audience':>12s} {'ACV':>14s} {'target':>14s} {'delta':>10s}")
    print(f"  {'-'*2}  {'-'*30} {'-'*22} {'-'*5} {'-'*12} {'-'*14} {'-'*14} {'-'*10}")
    for i, r in enumerate(results, 1):
        company = r["company"]
        target = TARGETS.get(company, 0)
        delta_pct = ((r["total_acv"] / target) - 1) * 100 if target else 0
        delta_str = f"{delta_pct:+.0f}%" if target else "—"
        acv_str = f"${r['total_acv']:,}"
        target_str = f"${target:,}" if target else "—"
        aud_str = f"{r['total_audience']:,}"
        print(f"  {i:>2}  {company:<30s} {r['org_type']:<22s} {r['tier']:<5s} {aud_str:>12s} {acv_str:>14s} {target_str:>14s} {delta_str:>10s}")

    print()
    print("─" * 110)
    print("Detail on the outliers (delta > 30% off target):")
    print("─" * 110)
    for r in results:
        company = r["company"]
        target = TARGETS.get(company, 0)
        if not target:
            continue
        delta_pct = ((r["total_acv"] / target) - 1) * 100
        if abs(delta_pct) < 30:
            continue
        print()
        print(f"  {company} — ACV ${r['total_acv']:,} vs target ${target:,} ({delta_pct:+.0f}%)")
        for motion_key, mid, rate, acv in r["breakdown"]:
            print(f"    {motion_key:<30s} {mid:>12,} × ${rate:>4d} = ${acv:>14,}")


if __name__ == "__main__":
    main()
