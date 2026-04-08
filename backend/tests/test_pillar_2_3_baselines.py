"""Category: Pillar 2 + Pillar 3 Baselines, Penalties, and Cross-Pillar Rules.

Guiding Principle: GP3 (Explainably Trustworthy) + GP4 (Self-Evident / Define-Once).

Validates the default-positive posture for Instructional Value and Customer Fit:

  - IV dimensions apply category-aware baselines from IV_CATEGORY_BASELINES
    (keyed by product top-level category).
  - CF dimensions apply organization-type baselines from CF_ORG_BASELINES
    (keyed by the normalized company classification).
  - CF penalty signals (no_training_partners, no_classroom_delivery,
    build_everything_culture, etc.) subtract their configured hit from the
    dimension raw total.
  - Unknown classification triggers the `classification_review_needed` flag
    and applies the neutral fallback baseline.
  - build_scoring_context normalizes raw inputs and handles missing values.
  - Cross-pillar rules are registered for every compounding case documented
    in the prompt template.

See docs/Badging-and-Scoring-Reference.md for the canonical baseline and
penalty values.
"""

import scoring_config as cfg
import scoring_math as sm


# ═══════════════════════════════════════════════════════════════════════════════
# UNKNOWN_CLASSIFICATION constant — Define-Once verification
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_classification_constant_exists():
    """The UNKNOWN_CLASSIFICATION constant must be defined in scoring_config."""
    assert hasattr(cfg, "UNKNOWN_CLASSIFICATION")
    assert isinstance(cfg.UNKNOWN_CLASSIFICATION, str)
    assert cfg.UNKNOWN_CLASSIFICATION


def test_iv_baselines_contain_unknown_key():
    """IV_CATEGORY_BASELINES must contain the UNKNOWN_CLASSIFICATION key so
    the neutral fallback is always available."""
    assert cfg.UNKNOWN_CLASSIFICATION in cfg.IV_CATEGORY_BASELINES


def test_cf_baselines_contain_unknown_key():
    """CF_ORG_BASELINES must contain the UNKNOWN_CLASSIFICATION key so the
    neutral fallback is always available."""
    assert cfg.UNKNOWN_CLASSIFICATION in cfg.CF_ORG_BASELINES


# ═══════════════════════════════════════════════════════════════════════════════
# IV_CATEGORY_BASELINES structural sanity
# ═══════════════════════════════════════════════════════════════════════════════

_IV_DIMENSION_KEYS = {"product_complexity", "mastery_stakes", "lab_versatility", "market_demand"}


def test_iv_baselines_every_category_has_all_iv_dimensions():
    """Every category in IV_CATEGORY_BASELINES must have all four IV
    dimension keys defined. Missing dimensions would silently produce
    zero baselines for that dimension and defeat the posture."""
    for category, dim_baselines in cfg.IV_CATEGORY_BASELINES.items():
        missing = _IV_DIMENSION_KEYS - set(dim_baselines.keys())
        assert not missing, f"Category {category!r} missing IV dimensions: {missing}"


def test_iv_baselines_do_not_exceed_dimension_caps():
    """No baseline may exceed the cap of its dimension — otherwise the
    category alone would push the dimension into capped state before any
    finding is considered."""
    # Derive caps from PILLAR_INSTRUCTIONAL_VALUE dimensions
    caps: dict[str, int] = {}
    for dim in cfg.PILLAR_INSTRUCTIONAL_VALUE.dimensions:
        key = dim.name.lower().replace(" ", "_")
        caps[key] = dim.cap if dim.cap is not None else dim.weight

    for category, dim_baselines in cfg.IV_CATEGORY_BASELINES.items():
        for dim_key, baseline in dim_baselines.items():
            cap = caps.get(dim_key)
            assert cap is not None, f"Unknown IV dimension key in baselines: {dim_key}"
            assert baseline <= cap, (
                f"IV baseline {category}/{dim_key}={baseline} exceeds cap {cap}"
            )
            assert baseline >= 0, (
                f"IV baseline {category}/{dim_key}={baseline} is negative"
            )


def test_iv_baselines_cybersecurity_top_tier():
    """Cybersecurity is the canonical top-tier category — per Frank's
    calibration, Product Complexity baseline is 32 (80% of cap 40)."""
    assert cfg.IV_CATEGORY_BASELINES["Cybersecurity"]["product_complexity"] == 32


def test_iv_baselines_social_entertainment_is_floor():
    """Social / Entertainment has no professional training market —
    baselines should be near zero across all IV dimensions."""
    ent = cfg.IV_CATEGORY_BASELINES["Social / Entertainment"]
    assert ent["product_complexity"] <= 6
    assert ent["mastery_stakes"] <= 4
    assert ent["market_demand"] == 0


def test_iv_baselines_ai_platforms_present():
    """AI Platforms & Tooling category must be in the master list — added
    per Frank's directive 2026-04-07 for Anthropic, OpenAI, LangChain, etc."""
    assert "AI Platforms & Tooling" in cfg.IV_CATEGORY_BASELINES


def test_iv_baselines_erp_and_crm_are_separate():
    """ERP and CRM must be split into separate categories (per Frank's
    2026-04-07 directive — CRM has lower stakes than ERP)."""
    assert "ERP" in cfg.IV_CATEGORY_BASELINES
    assert "CRM" in cfg.IV_CATEGORY_BASELINES
    # ERP should have higher Mastery Stakes than CRM (financial records
    # and SOX compliance vs. contact records and GDPR)
    assert (
        cfg.IV_CATEGORY_BASELINES["ERP"]["mastery_stakes"]
        > cfg.IV_CATEGORY_BASELINES["CRM"]["mastery_stakes"]
    )


def test_iv_baselines_simple_saas_retired():
    """Simple SaaS was retired — SaaS is a delivery mechanism, not a
    content area. It should not appear in the master category list."""
    assert "Simple SaaS" not in cfg.IV_CATEGORY_BASELINES


def test_iv_baselines_consumer_replaced_by_social_entertainment():
    """The old `Consumer` bucket was retired in favor of `Social /
    Entertainment` which is the true no-training-market category."""
    assert "Consumer" not in cfg.IV_CATEGORY_BASELINES
    assert "Social / Entertainment" in cfg.IV_CATEGORY_BASELINES


# ═══════════════════════════════════════════════════════════════════════════════
# CF_ORG_BASELINES structural sanity
# ═══════════════════════════════════════════════════════════════════════════════

_CF_DIMENSION_KEYS = {"training_commitment", "build_capacity", "delivery_capacity", "organizational_dna"}


def test_cf_baselines_every_org_type_has_all_cf_dimensions():
    """Every organization type in CF_ORG_BASELINES must have all four CF
    dimension keys defined."""
    for org_type, dim_baselines in cfg.CF_ORG_BASELINES.items():
        missing = _CF_DIMENSION_KEYS - set(dim_baselines.keys())
        assert not missing, f"Org type {org_type!r} missing CF dimensions: {missing}"


def test_cf_baselines_do_not_exceed_dimension_caps():
    """CF baselines must not exceed their dimension caps."""
    caps: dict[str, int] = {}
    for dim in cfg.PILLAR_CUSTOMER_FIT.dimensions:
        key = dim.name.lower().replace(" ", "_")
        caps[key] = dim.cap if dim.cap is not None else dim.weight

    for org_type, dim_baselines in cfg.CF_ORG_BASELINES.items():
        for dim_key, baseline in dim_baselines.items():
            cap = caps.get(dim_key)
            assert cap is not None, f"Unknown CF dimension key in baselines: {dim_key}"
            assert baseline <= cap, (
                f"CF baseline {org_type}/{dim_key}={baseline} exceeds cap {cap}"
            )
            assert baseline >= 0, (
                f"CF baseline {org_type}/{dim_key}={baseline} is negative"
            )


def test_cf_training_org_commitment_near_max():
    """TRAINING ORG — training IS their business. Training Commitment
    baseline should be high (>= 80% of cap). Per Frank's directive."""
    cap = cfg.PILLAR_CUSTOMER_FIT.dimensions[0].cap or 25  # Training Commitment
    assert cfg.CF_ORG_BASELINES["TRAINING ORG"]["training_commitment"] >= cap * 0.80


def test_cf_lms_provider_commitment_lower_than_training_org():
    """LMS providers facilitate others' training but don't always invest
    in teaching themselves. Commitment baseline should be clearly lower
    than TRAINING ORG. Per Frank's directive."""
    lms = cfg.CF_ORG_BASELINES["LMS PROVIDER"]["training_commitment"]
    training = cfg.CF_ORG_BASELINES["TRAINING ORG"]["training_commitment"]
    assert lms < training


def test_cf_tech_distributor_commitment_is_lowest():
    """Tech distributors are distribution-first and weakest on training
    commitment. Per Frank's directive."""
    all_commitments = {
        org: baselines["training_commitment"]
        for org, baselines in cfg.CF_ORG_BASELINES.items()
        if org != cfg.UNKNOWN_CLASSIFICATION  # exclude neutral fallback
    }
    assert all_commitments["TECH DISTRIBUTOR"] == min(all_commitments.values())


def test_cf_delivery_highest_weight_in_cf_pillar():
    """Delivery Capacity must be weighted highest within Customer Fit
    (30) because having labs = cost, delivering labs = value."""
    dim_weights = {
        dim.name.lower().replace(" ", "_"): dim.weight
        for dim in cfg.PILLAR_CUSTOMER_FIT.dimensions
    }
    assert dim_weights["delivery_capacity"] == max(dim_weights.values())


def test_cf_build_capacity_lowest_weight():
    """Build Capacity is weighted lowest (20) because ProServ can fill
    a build gap. Per the Customer Fit architecture."""
    dim_weights = {
        dim.name.lower().replace(" ", "_"): dim.weight
        for dim in cfg.PILLAR_CUSTOMER_FIT.dimensions
    }
    assert dim_weights["build_capacity"] == min(dim_weights.values())


# ═══════════════════════════════════════════════════════════════════════════════
# ORG_TYPE_NORMALIZATION — Define-Once mapping
# ═══════════════════════════════════════════════════════════════════════════════

def test_org_type_normalization_targets_are_baseline_keys():
    """Every ORG_TYPE_NORMALIZATION target must be a valid key in
    CF_ORG_BASELINES. Otherwise the mapping produces orphans that fall
    through to Unknown."""
    cf_keys = set(cfg.CF_ORG_BASELINES.keys())
    for raw, normalized in cfg.ORG_TYPE_NORMALIZATION.items():
        assert normalized in cf_keys, (
            f"ORG_TYPE_NORMALIZATION[{raw!r}] = {normalized!r} but that key "
            f"is not in CF_ORG_BASELINES"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# build_scoring_context — Define-Once seam
# ═══════════════════════════════════════════════════════════════════════════════

def test_build_scoring_context_normalizes_org_type():
    """build_scoring_context must normalize the raw snake_case org type
    to the canonical baseline key."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    assert ctx["org_type"] == "SOFTWARE"
    assert ctx["product_category"] == "Cybersecurity"


def test_build_scoring_context_unknown_fallbacks():
    """Missing raw values must fall back to UNKNOWN_CLASSIFICATION for
    both fields so the math layer can raise the review flag."""
    ctx = cfg.build_scoring_context(raw_org_type=None, raw_product_category=None)
    assert ctx["org_type"] == cfg.UNKNOWN_CLASSIFICATION
    assert ctx["product_category"] == cfg.UNKNOWN_CLASSIFICATION


def test_build_scoring_context_unrecognized_org_type_falls_back():
    """Unrecognized org type strings (not in ORG_TYPE_NORMALIZATION) must
    fall back to UNKNOWN_CLASSIFICATION — the AI emitted something we
    don't know, and we want the review flag raised."""
    ctx = cfg.build_scoring_context(
        raw_org_type="space_alien_company",
        raw_product_category="Cybersecurity",
    )
    assert ctx["org_type"] == cfg.UNKNOWN_CLASSIFICATION
    # Product category is preserved because the master list is open —
    # only explicit Unknown or empty falls back.
    assert ctx["product_category"] == "Cybersecurity"


def test_build_scoring_context_empty_strings_treated_as_missing():
    """Empty strings should be treated as missing values, not kept as-is."""
    ctx = cfg.build_scoring_context(raw_org_type="   ", raw_product_category="   ")
    assert ctx["org_type"] == cfg.UNKNOWN_CLASSIFICATION
    assert ctx["product_category"] == cfg.UNKNOWN_CLASSIFICATION


# ═══════════════════════════════════════════════════════════════════════════════
# compute_dimension_score WITH context — baseline application
# ═══════════════════════════════════════════════════════════════════════════════

def test_product_complexity_baseline_applied_cybersecurity():
    """A cybersecurity product with NO findings should score at the
    category baseline (32/40) — default-positive posture."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("product_complexity", [], ctx)
    assert r["baseline"] == 32
    assert r["score"] == 32


def test_product_complexity_baseline_plus_strong_finding():
    """Cybersecurity baseline 32 + one strong finding (+6) = 38."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("product_complexity", [
        {"name": "Multi-VM Architecture", "color": "green", "strength": "strong",
         "signal_category": "multi_vm_architecture"},
    ], ctx)
    assert r["baseline"] == 32
    assert r["score"] == 38


def test_product_complexity_caps_at_40_with_strong_findings():
    """Cybersecurity baseline 32 + three strong findings (+18) = 50 caps at 40."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("product_complexity", [
        {"name": "Multi-VM Architecture", "color": "green", "strength": "strong",
         "signal_category": "multi_vm_architecture"},
        {"name": "SIEM + EDR + Ticketing Chain", "color": "green", "strength": "strong",
         "signal_category": "integration_complexity"},
        {"name": "IOC Pivoting Workflow", "color": "green", "strength": "strong",
         "signal_category": "multi_phase_workflow"},
    ], ctx)
    assert r["baseline"] == 32
    assert r["score"] == 40
    assert r["capped"] is True


def test_social_entertainment_baseline_is_low():
    """Instagram / Facebook / TikTok baseline is 4 (no professional market)."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Social / Entertainment",
    )
    r = sm.compute_dimension_score("product_complexity", [], ctx)
    assert r["baseline"] == 4
    assert r["score"] == 4


def test_unknown_product_category_uses_fallback_baseline():
    """Unknown category falls back to the neutral Unknown baseline
    (not zero). Review flag handling is tested in the compute_all tests."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category=None,  # → Unknown
    )
    r = sm.compute_dimension_score("product_complexity", [], ctx)
    expected = cfg.IV_CATEGORY_BASELINES[cfg.UNKNOWN_CLASSIFICATION]["product_complexity"]
    assert r["baseline"] == expected
    assert r["score"] == expected


def test_no_context_means_zero_baseline_backward_compat():
    """Existing test_scoring_logic.py tests call compute_dimension_score
    without context. Backward compatibility requires baseline = 0 when
    no context is supplied."""
    r = sm.compute_dimension_score("product_complexity", [], None)
    assert r["baseline"] == 0
    assert r["score"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# CF dimension baselines — organization-type lookup
# ═══════════════════════════════════════════════════════════════════════════════

def test_training_commitment_baseline_software_company():
    """A category-specific SOFTWARE vendor with no findings starts at its
    Training Commitment baseline."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("training_commitment", [], ctx)
    expected = cfg.CF_ORG_BASELINES["SOFTWARE"]["training_commitment"]
    assert r["baseline"] == expected
    assert r["score"] == expected


def test_training_commitment_training_org_near_max():
    """TRAINING ORG Training Commitment baseline should be near max (23/25)
    — training IS their business."""
    ctx = cfg.build_scoring_context(
        raw_org_type="training_organization",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("training_commitment", [], ctx)
    assert r["baseline"] >= 22  # 22 or higher
    assert r["score"] >= 22


def test_delivery_capacity_tech_distributor_has_high_baseline():
    """TECH DISTRIBUTOR has high Delivery Capacity baseline (distribution IS
    their strength) — even though Training Commitment is low."""
    ctx = cfg.build_scoring_context(
        raw_org_type="technology_distributor",
        raw_product_category="Cybersecurity",
    )
    dc = sm.compute_dimension_score("delivery_capacity", [], ctx)
    tc = sm.compute_dimension_score("training_commitment", [], ctx)
    assert dc["baseline"] > tc["baseline"]


# ═══════════════════════════════════════════════════════════════════════════════
# CF penalty signals — hit subtraction
# ═══════════════════════════════════════════════════════════════════════════════

def test_no_training_partners_red_penalty_applied():
    """no_training_partners is a red penalty worth -10 on Delivery Capacity.
    A software vendor baseline 16 + strong finding +8 - red penalty 10 = 14."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("delivery_capacity", [
        {"name": "Small ATP Network", "color": "green", "strength": "strong",
         "signal_category": "atp_network"},
        {"name": "No Training Partners", "color": "red",
         "signal_category": "no_training_partners"},
    ], ctx)
    # Baseline 16 + strong 8 - penalty 10 = 14
    assert r["baseline"] == 16
    assert r["score"] == 14
    assert any(p["signal_category"] == "no_training_partners" for p in r["penalties_applied"])


def test_multiple_penalties_stack():
    """Two amber penalties stack — delivery capacity takes both hits."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("delivery_capacity", [
        {"name": "No Training Partners", "color": "red",
         "signal_category": "no_training_partners"},
        {"name": "No Classroom Delivery", "color": "red",
         "signal_category": "no_classroom_delivery"},
    ], ctx)
    # Baseline 16 - 10 - 10 = -4, floored at 0
    assert r["score"] == 0
    assert r["floored"] is True


def test_rubric_penalty_on_wrong_dimension_does_nothing():
    """A penalty signal_category only fires on its own dimension. A
    delivery-capacity penalty emitted against build_capacity must NOT
    deduct anything (it falls through to the rubric or color path)."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("build_capacity", [
        # Delivery Capacity's "no_training_partners" emitted in Build
        # Capacity — should NOT fire as a penalty here.
        {"name": "Weirdly Misrouted", "color": "red",
         "signal_category": "no_training_partners"},
    ], ctx)
    # Only the color fallback (-3 for red) should apply, not the -10 penalty.
    # Baseline 10 for SOFTWARE + red color contribution (-3) = 7.
    assert r["baseline"] == 10
    # No penalty entries
    assert not any(
        p.get("signal_category") == "no_training_partners"
        for p in r.get("penalties_applied", [])
    )


def test_build_capacity_penalty_confirmed_outsourcing():
    """confirmed_outsourcing is a Build Capacity amber penalty -3.
    SOFTWARE baseline 10 + no findings + penalty = 7."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("build_capacity", [
        {"name": "Outsourced Content", "color": "amber",
         "signal_category": "confirmed_outsourcing"},
    ], ctx)
    assert r["baseline"] == 10
    assert r["score"] == 7


def test_organizational_dna_builds_everything_penalty():
    """build_everything_culture is an amber -4 penalty on Organizational
    DNA. Tests the IBM pattern."""
    ctx = cfg.build_scoring_context(
        raw_org_type="enterprise_software",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("organizational_dna", [
        {"name": "Builds Everything", "color": "amber",
         "signal_category": "build_everything_culture"},
    ], ctx)
    expected_baseline = cfg.CF_ORG_BASELINES["ENTERPRISE SOFTWARE"]["organizational_dna"]
    assert r["baseline"] == expected_baseline
    assert r["score"] == expected_baseline - 4


def test_hard_to_engage_red_penalty_is_harsh():
    """hard_to_engage is a red -6 penalty — the harshest Organizational
    DNA penalty. Reserved for direct evidence of hostility."""
    penalty = next(
        p for p in cfg.RUBRIC_PENALTY_SIGNALS
        if p.category == "hard_to_engage"
    )
    assert penalty.color == "red"
    assert penalty.hit == 6


def test_market_demand_no_independent_training_penalty_fires():
    """The Trellix GTI regression: `no_independent_training_market` must
    fire as a penalty in Market Demand, not just in Delivery Capacity.

    Without this penalty, a product in a high-demand category (Cybersecurity
    baseline 14) that the open market doesn't teach can score 20/20 on
    Market Demand — masking a real demand gap. The fix is that
    RUBRIC_PENALTY_SIGNALS registers the same signal_category against
    BOTH market_demand and delivery_capacity.
    """
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    # Trellix GTI actual badges (abbreviated):
    r = sm.compute_dimension_score("market_demand", [
        {"name": "High-Demand Category", "color": "green",
         "strength": "strong", "signal_category": "category_demand"},
        {"name": "Enterprise Validated", "color": "green",
         "strength": "strong", "signal_category": "enterprise_validation"},
        {"name": "AI-Powered Product", "color": "green",
         "strength": "moderate", "signal_category": "ai_signal"},
        {"name": "No Independent Courses Found", "color": "amber",
         "strength": "moderate",
         "signal_category": "no_independent_training_market"},
    ], ctx)

    # Baseline 14 + 5 strong + 5 strong + 3 moderate - 4 penalty = 23 → capped at 20
    # The critical assertion: the penalty must be RECORDED (not fall
    # through to +3 moderate credit).
    assert any(
        p.get("signal_category") == "no_independent_training_market"
        for p in r.get("penalties_applied", [])
    ), (
        "Regression: no_independent_training_market should fire as a "
        "Market Demand penalty, not credit as +3 moderate rubric. "
        f"penalties_applied={r.get('penalties_applied')}"
    )
    # And the score should reflect the penalty hit — if it were +3 credit
    # the raw_total would be 27; with -4 penalty it's 23 → capped at 20.
    # Either way it caps, so assert on raw_total instead:
    assert r["raw_total"] == 23, (
        f"raw_total must reflect the penalty: baseline 14 + 5 + 5 + 3 - 4 = 23. "
        f"Got raw_total={r['raw_total']}"
    )


def test_market_demand_niche_within_category_penalty():
    """niche_within_category is an amber -3 penalty against the
    category-demand baseline. A product inside a hot category that is
    itself a narrow specialty should not get full marks."""
    ctx = cfg.build_scoring_context(
        raw_org_type="software_company",
        raw_product_category="Cybersecurity",
    )
    r = sm.compute_dimension_score("market_demand", [
        {"name": "High-Demand Category", "color": "green",
         "strength": "strong", "signal_category": "category_demand"},
        {"name": "Niche Within Category", "color": "amber",
         "strength": "moderate",
         "signal_category": "niche_within_category"},
    ], ctx)
    # Baseline 14 + 5 strong - 3 penalty = 16
    assert r["raw_total"] == 16
    assert any(
        p.get("signal_category") == "niche_within_category"
        for p in r.get("penalties_applied", [])
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Unknown classification review flag — compute_all integration
# ═══════════════════════════════════════════════════════════════════════════════

def test_classification_review_flag_on_unknown_category():
    """When product_category is Unknown, compute_all must set
    classification_review_needed = True."""
    result = sm.compute_all(
        badges_by_dimension={
            "product_complexity": [],
        },
        ceiling_flags=[],
        orchestration_method="Hyper-V",
        context={
            "product_category": cfg.UNKNOWN_CLASSIFICATION,
            "org_type": "SOFTWARE",
        },
    )
    assert result["classification_review_needed"] is True


def test_classification_review_flag_on_unknown_org_type():
    """When org_type is Unknown, compute_all must set the review flag."""
    result = sm.compute_all(
        badges_by_dimension={},
        ceiling_flags=[],
        orchestration_method="Hyper-V",
        context={
            "product_category": "Cybersecurity",
            "org_type": cfg.UNKNOWN_CLASSIFICATION,
        },
    )
    assert result["classification_review_needed"] is True


def test_classification_review_flag_false_for_clean_classification():
    """Clean classifications must NOT raise the review flag."""
    result = sm.compute_all(
        badges_by_dimension={},
        ceiling_flags=[],
        orchestration_method="Hyper-V",
        context={
            "product_category": "Cybersecurity",
            "org_type": "SOFTWARE",
        },
    )
    assert result["classification_review_needed"] is False


def test_classification_review_flag_false_without_context():
    """No context provided (legacy caller) — the flag must default to False
    for backward compatibility."""
    result = sm.compute_all(
        badges_by_dimension={},
        ceiling_flags=[],
        orchestration_method="Hyper-V",
        context=None,
    )
    assert result["classification_review_needed"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS_PILLAR_RULES — structural sanity
# ═══════════════════════════════════════════════════════════════════════════════

def test_cross_pillar_rules_defined():
    """At least the core Pillar 1 → Pillar 2 and Pillar 3 → Pillar 2 rules
    must be registered so the prompt template can teach them."""
    assert len(cfg.CROSS_PILLAR_RULES) > 0


def test_cross_pillar_multi_vm_lab_rule_exists():
    """Multi-VM Lab in Pillar 1 must compound into Pillar 2 Product
    Complexity — per Frank's explicit directive 2026-04-07."""
    rule = next(
        (r for r in cfg.CROSS_PILLAR_RULES
         if r.source_badge == "Multi-VM Lab"
         and r.target_dimension == "product_complexity"),
        None,
    )
    assert rule is not None
    assert rule.target_signal_category == "multi_vm_architecture"


def test_cross_pillar_atp_network_rule_exists():
    """ATP networks in Delivery Capacity must compound into Market Demand
    (partners don't exist without skill demand)."""
    rule = next(
        (r for r in cfg.CROSS_PILLAR_RULES
         if r.source_badge == "atp_network"
         and r.target_dimension == "market_demand"),
        None,
    )
    assert rule is not None


# ═══════════════════════════════════════════════════════════════════════════════
# RUBRIC_PENALTY_SIGNALS — structural sanity
# (Covers Pillar 2 + Pillar 3 rubric-model penalties)
# ═══════════════════════════════════════════════════════════════════════════════

def test_rubric_penalty_signals_have_valid_dimensions():
    """Every rubric penalty must target a real rubric-model dimension key.

    Valid targets are the dimensions of Pillar 2 (Instructional Value) and
    Pillar 3 (Customer Fit) — both use the rubric model.
    """
    valid_dim_keys = {
        dim.name.lower().replace(" ", "_")
        for pillar in (cfg.PILLAR_INSTRUCTIONAL_VALUE, cfg.PILLAR_CUSTOMER_FIT)
        for dim in pillar.dimensions
    }
    for p in cfg.RUBRIC_PENALTY_SIGNALS:
        assert p.dimension in valid_dim_keys, (
            f"Rubric penalty {p.category!r} targets unknown dimension {p.dimension!r}"
        )


def test_rubric_penalty_signals_have_valid_colors():
    """Penalty colors must be amber or red only — never green or gray."""
    for p in cfg.RUBRIC_PENALTY_SIGNALS:
        assert p.color in ("amber", "red"), (
            f"Rubric penalty {p.category!r} has invalid color {p.color!r}"
        )


def test_rubric_penalty_signals_have_positive_hits():
    """Penalty hits are stored as positive integers; the math layer negates
    them when applying the subtraction."""
    for p in cfg.RUBRIC_PENALTY_SIGNALS:
        assert p.hit > 0, (
            f"Rubric penalty {p.category!r} has non-positive hit {p.hit}"
        )


def test_rubric_penalty_signals_cover_both_pillars():
    """The list must contain penalties for BOTH Pillar 2 and Pillar 3,
    not just Customer Fit (the pre-2026-04-07 regression)."""
    iv_dim_keys = {
        dim.name.lower().replace(" ", "_")
        for dim in cfg.PILLAR_INSTRUCTIONAL_VALUE.dimensions
    }
    cf_dim_keys = {
        dim.name.lower().replace(" ", "_")
        for dim in cfg.PILLAR_CUSTOMER_FIT.dimensions
    }
    iv_penalties = [
        p for p in cfg.RUBRIC_PENALTY_SIGNALS if p.dimension in iv_dim_keys
    ]
    cf_penalties = [
        p for p in cfg.RUBRIC_PENALTY_SIGNALS if p.dimension in cf_dim_keys
    ]
    assert iv_penalties, "RUBRIC_PENALTY_SIGNALS must include at least one IV penalty"
    assert cf_penalties, "RUBRIC_PENALTY_SIGNALS must include at least one CF penalty"
