"""Pillar 1 Python scorer — canned-fact spot tests.

Step 3 of the Research → Store → Score → Badge rebuild (see
docs/next-session-todo.md §0c Step 3).  Feeds synthetic ProductLababilityFacts
drawers into backend/pillar_1_scorer.py and asserts the resulting scores
match expectations derived from scoring_config.py point values.

Test strategy per the rebuild spot-test discipline:
  - NO hardcoded expected score values in assertions — every expected score
    is computed from scoring_config.py constants so a config tweak
    automatically updates the assertions.
  - One test per load-bearing scenario: clean Hyper-V, Cloud Slice, Sandbox
    API rich/partial, Sandbox API red cap, Grand Slam scoring, risk cap
    reduction, Teardown on SaaS path.
  - Tests live at the scorer contract level (input facts → output
    PillarScore), not at the intelligence.py wiring level — wiring is
    covered separately by the smoke test on Trellix.
"""

from __future__ import annotations

import pytest

import scoring_config as cfg
import pillar_1_scorer as pls
from models import (
    LabAccessFacts,
    ProductLababilityFacts,
    ProvisioningFacts,
    ScoringFacts,
    TeardownFacts,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — look up config values so tests have zero hardcoded numbers
# ─────────────────────────────────────────────────────────────────────────────

def _sig(dim_name: str, signal_name: str) -> int:
    """Look up a scoring signal's point value from config."""
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            if dim.name == dim_name:
                for s in dim.scoring_signals:
                    if s.name == signal_name:
                        return s.points
    raise AssertionError(f"signal {signal_name!r} not found in dimension {dim_name!r}")


def _pen(dim_name: str, penalty_name: str) -> int:
    """Look up a penalty deduction from config."""
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            if dim.name == dim_name:
                for p in dim.penalties:
                    if p.name == penalty_name:
                        return p.deduction
    raise AssertionError(f"penalty {penalty_name!r} not found in dimension {dim_name!r}")


def _dim_weight(dim_name: str) -> int:
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            if dim.name == dim_name:
                return dim.weight
    raise AssertionError(f"dimension {dim_name!r} not found")


# ─────────────────────────────────────────────────────────────────────────────
# Provisioning — fabric priority order
# ─────────────────────────────────────────────────────────────────────────────

def test_provisioning_clean_hyperv_earns_full_signal_credit():
    """Installable product → Runs in Hyper-V → full +30, no friction."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_installable=True),
    )
    result = pls.score_provisioning(facts)
    expected = _sig("Provisioning", "Runs in Hyper-V")
    assert result.raw_total == expected
    # Cap should not affect — signal value is below the dimension weight
    assert result.dimension_score.score == expected
    assert result.amber_risks == 0 and result.red_risks == 0


def test_provisioning_azure_native_beats_sandbox_api():
    """Azure-native product that also has a sandbox API uses Cloud Slice as
    the PRIMARY fabric, not Sandbox API. The product also gets an optionality
    bonus because Sandbox API is viable as a secondary, and Custom Cloud fires
    as a Skillable-strength context badge. Frank 2026-04-08 refinements."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(
            runs_as_azure_native=True,
            has_sandbox_api=True,
            sandbox_api_granularity="rich",
        ),
    )
    result = pls.score_provisioning(facts)
    names = [n for n, _ in result.signals_matched]
    # Azure must be the primary fabric (picked first)
    assert "Runs in Azure" in names
    # Sandbox API is NOT the primary but Custom Cloud strength badge fires
    assert "Sandbox API" not in names
    assert "Custom Cloud" in names
    # Multi-fabric optionality bonus fires because Sandbox API is a viable secondary
    assert "Multi-Fabric Bonus" in names
    # Raw total = Azure base credit + optionality bonus
    azure_pts = _sig("Provisioning", "Runs in Azure")
    assert result.raw_total == azure_pts + cfg.MULTI_FABRIC_OPTIONALITY_BONUS_PER_EXTRA


def test_provisioning_sandbox_api_rich_is_green():
    """SaaS-only product with rich sandbox API → full Sandbox API credit, no cap.
    Custom Cloud strength badge also fires alongside."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(
            runs_as_saas_only=True,
            has_sandbox_api=True,
            sandbox_api_granularity="rich",
        ),
    )
    result = pls.score_provisioning(facts)
    # Raw total is Sandbox API full credit (Custom Cloud is 0 pts)
    assert result.raw_total == _sig("Provisioning", "Sandbox API")
    assert not result.ceiling_flags
    names = [n for n, _ in result.signals_matched]
    assert "Sandbox API" in names
    assert "Custom Cloud" in names  # Skillable strength badge fires alongside


def test_provisioning_sandbox_api_partial_is_amber_half_credit():
    """Partial sandbox API granularity → half credit + amber risk counted.
    Custom Cloud strength badge still fires (context, not scoring)."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(
            runs_as_saas_only=True,
            has_sandbox_api=True,
            sandbox_api_granularity="partial",
        ),
    )
    result = pls.score_provisioning(facts)
    assert result.raw_total == _sig("Provisioning", "Sandbox API") // 2
    assert result.amber_risks == 1


def test_provisioning_saas_only_no_sandbox_uses_simulation_override():
    """Pure SaaS with no Sandbox API → falls through to Simulation hard override.
    Frank 2026-04-08: Simulation is a hard override (5/12/0/25), NOT the old
    sandbox_api_red_sim_viable ceiling flag path. The simulation_chosen flag
    triggers the composer to apply all four dimension overrides."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_saas_only=True),
    )
    result = pls.score_provisioning(facts)
    # New behavior: Simulation hard override fires, no sandbox_red ceiling
    assert result.simulation_chosen is True
    assert result.simulation_viable is True
    assert result.dimension_score.score == cfg.SIMULATION_PROVISIONING_POINTS
    # The only signal matched is Simulation
    assert result.signals_matched == [("Simulation", cfg.SIMULATION_PROVISIONING_POINTS)]
    # Old sandbox_red ceiling flag is NOT raised — the Simulation override is
    # the canonical answer for no-real-provisioning-path now.
    assert "sandbox_api_red_sim_viable" not in result.ceiling_flags


def test_provisioning_gpu_required_applies_penalty_and_amber_risk():
    """GPU Required on an installable product → full Hyper-V credit + penalty."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(
            runs_as_installable=True,
            needs_gpu=True,
        ),
    )
    result = pls.score_provisioning(facts)
    hv = _sig("Provisioning", "Runs in Hyper-V")
    gpu_pen = _pen("Provisioning", "GPU Required")
    assert result.raw_total == hv + gpu_pen
    assert result.amber_risks == 1


# ─────────────────────────────────────────────────────────────────────────────
# Lab Access
# ─────────────────────────────────────────────────────────────────────────────

def test_lab_access_entra_sso_only_fires_for_azure_native():
    """Entra ID SSO only fires when auth_model is entra_native_tenant
    AND the product is Azure-native.  Scope rule from config."""
    # Azure-native + entra_native_tenant → Entra ID SSO fires
    f1 = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_azure_native=True),
        lab_access=LabAccessFacts(auth_model="entra_native_tenant"),
    )
    r1 = pls.score_lab_access(f1)
    assert any(n == "Entra ID SSO" for n, _ in r1.signals_matched)

    # Non-Azure product + entra_native_tenant → Entra ID SSO does NOT fire
    f2 = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_installable=True),
        lab_access=LabAccessFacts(auth_model="entra_native_tenant"),
    )
    r2 = pls.score_lab_access(f2)
    assert not any(n == "Entra ID SSO" for n, _ in r2.signals_matched)


def test_lab_access_identity_api_rich_fires_for_non_azure():
    """Rich user_provisioning_api_granularity on a non-Azure product → Identity API green."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_installable=True),
        lab_access=LabAccessFacts(user_provisioning_api_granularity="rich"),
    )
    r = pls.score_lab_access(facts)
    assert any(n == "Identity API" and p == _sig("Lab Access", "Identity API")
               for n, p in r.signals_matched)


def test_lab_access_mfa_blocker_applies_red_penalty():
    """MFA Required → red penalty + red risk counted."""
    facts = ProductLababilityFacts(
        lab_access=LabAccessFacts(has_mfa_blocker=True),
    )
    r = pls.score_lab_access(facts)
    mfa_pen = _pen("Lab Access", "MFA Required")
    assert any(n == "MFA Required" and d == mfa_pen for n, d in r.penalties_applied)
    assert r.red_risks >= 1


def test_lab_access_risk_cap_reduction_applies():
    """Amber risks should reduce the effective cap per AMBER_RISK_CAP_REDUCTION."""
    facts = ProductLababilityFacts(
        lab_access=LabAccessFacts(
            user_provisioning_api_granularity="rich",   # Identity API green
            credential_lifecycle="recyclable",          # Cred Recycling green
            training_license="medium_friction",         # amber risk
        ),
    )
    r = pls.score_lab_access(facts)
    # Raw should include Identity API full + Cred Recycling full + Training License half
    id_api = _sig("Lab Access", "Identity API")
    cred = _sig("Lab Access", "Cred Recycling")
    tl_half = _sig("Lab Access", "Training License") // 2
    assert r.raw_total == id_api + cred + tl_half
    # Effective cap should be dim weight minus one amber reduction
    assert r.effective_cap == _dim_weight("Lab Access") - cfg.AMBER_RISK_CAP_REDUCTION
    assert r.amber_risks == 1


# ─────────────────────────────────────────────────────────────────────────────
# Scoring dimension — Grand Slam rule
# ─────────────────────────────────────────────────────────────────────────────

def test_scoring_grand_slam_vm_ai_vision_plus_script_hits_full_cap():
    """AI Vision + Script Scoring → Grand Slam VM → full dimension cap (15)."""
    facts = ProductLababilityFacts(
        scoring=ScoringFacts(
            scriptable_via_shell_granularity="full",
            gui_state_visually_evident_granularity="full",
        ),
    )
    r = pls.score_scoring(facts)
    full_cap = _dim_weight("Scoring")
    assert r.effective_cap == full_cap
    assert r.dimension_score.score == full_cap


def test_scoring_grand_slam_cloud_ai_vision_plus_api_hits_full_cap():
    """AI Vision + Scoring API → Grand Slam cloud → full dimension cap."""
    facts = ProductLababilityFacts(
        scoring=ScoringFacts(
            state_validation_api_granularity="rich",
            gui_state_visually_evident_granularity="full",
        ),
    )
    r = pls.score_scoring(facts)
    assert r.effective_cap == _dim_weight("Scoring")


def test_scoring_ai_vision_alone_caps_at_config_constant():
    """AI Vision alone → cap at SCORING_AI_VISION_ALONE_CAP (not full cap)."""
    facts = ProductLababilityFacts(
        scoring=ScoringFacts(gui_state_visually_evident_granularity="full"),
    )
    r = pls.score_scoring(facts)
    assert r.effective_cap == cfg.SCORING_AI_VISION_ALONE_CAP


def test_scoring_api_alone_caps_at_config_constant():
    """Scoring API alone → cap at SCORING_API_ALONE_CAP."""
    facts = ProductLababilityFacts(
        scoring=ScoringFacts(state_validation_api_granularity="rich"),
    )
    r = pls.score_scoring(facts)
    assert r.effective_cap == cfg.SCORING_API_ALONE_CAP


def test_scoring_script_alone_hits_full_cap():
    """Script Scoring alone → VM context, full cap reachable."""
    facts = ProductLababilityFacts(
        scoring=ScoringFacts(scriptable_via_shell_granularity="full"),
    )
    r = pls.score_scoring(facts)
    assert r.effective_cap == _dim_weight("Scoring")


def test_scoring_nothing_caps_at_zero():
    """No programmatic methods → cap at 0."""
    facts = ProductLababilityFacts()
    r = pls.score_scoring(facts)
    assert r.effective_cap == 0
    assert r.dimension_score.score == 0


# ─────────────────────────────────────────────────────────────────────────────
# Teardown
# ─────────────────────────────────────────────────────────────────────────────

def test_teardown_datacenter_fires_for_installable():
    """Installable product → Datacenter green → full Teardown credit."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_installable=True),
    )
    r = pls.score_teardown(facts)
    dc = _sig("Teardown", "Datacenter")
    assert r.raw_total == dc


def test_teardown_api_rich_for_cloud_native():
    """Cloud-native product with rich teardown API → Teardown API green."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_azure_native=True),
        teardown=TeardownFacts(vendor_teardown_api_granularity="rich"),
    )
    r = pls.score_teardown(facts)
    assert r.raw_total == _sig("Teardown", "Teardown API")


def test_teardown_manual_penalty_for_cloud_without_api():
    """Cloud-native product with no teardown API → Manual Teardown penalty."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_azure_native=True),
        teardown=TeardownFacts(),
    )
    r = pls.score_teardown(facts)
    mt_pen = _pen("Teardown", "Manual Teardown")
    assert any(n == "Manual Teardown" and d == mt_pen for n, d in r.penalties_applied)


def test_teardown_orphan_risk_stacks_with_partial_api():
    """Orphan Risk penalty stacks alongside partial Teardown API."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_azure_native=True),
        teardown=TeardownFacts(
            vendor_teardown_api_granularity="partial",
            has_orphan_risk=True,
        ),
    )
    r = pls.score_teardown(facts)
    names = [n for n, _ in r.signals_matched] + [n for n, _ in r.penalties_applied]
    assert "Teardown API" in names
    assert "Orphan Risk" in names


# ─────────────────────────────────────────────────────────────────────────────
# Pillar composer — cross-dimension ceilings
# ─────────────────────────────────────────────────────────────────────────────

def test_pillar_clean_hyperv_grand_slam_scores_near_cap():
    """Trellix-EPS-style: clean Hyper-V, Cred Recycling, Grand Slam scoring,
    Datacenter teardown → Pillar 1 should be near 100."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_installable=True),
        lab_access=LabAccessFacts(
            credential_lifecycle="recyclable",
            training_license="low_friction",
        ),
        scoring=ScoringFacts(
            scriptable_via_shell_granularity="full",
            gui_state_visually_evident_granularity="full",
        ),
        teardown=TeardownFacts(),  # Datacenter fires because runs_as_installable
    )
    pillar = pls.score_product_labability(facts)
    assert pillar.score >= 85  # near-perfect threshold
    assert pillar.score_override is None  # no ceiling should fire


def test_pillar_simulation_override_sums_to_config_constants():
    """SaaS with no real provisioning path → Simulation hard override applies
    ALL FOUR dimensions: SIMULATION_PROVISIONING_POINTS + SIMULATION_LAB_ACCESS_POINTS
    + SIMULATION_SCORING_POINTS + SIMULATION_TEARDOWN_POINTS.

    Frank 2026-04-08: the old sandbox_api_red_sim_viable ceiling flag behavior
    (cap at 25) is REPLACED by the Simulation hard override (42 = 5+12+0+25).
    The normal dimension scorers for Lab Access / Scoring / Teardown are
    bypassed entirely — their facts don't matter when Simulation is the fabric."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(runs_as_saas_only=True),
        lab_access=LabAccessFacts(
            credential_lifecycle="recyclable",
            training_license="low_friction",
        ),
        scoring=ScoringFacts(gui_state_visually_evident_granularity="full"),
        teardown=TeardownFacts(),
    )
    pillar = pls.score_product_labability(facts)
    expected_total = (
        cfg.SIMULATION_PROVISIONING_POINTS
        + cfg.SIMULATION_LAB_ACCESS_POINTS
        + cfg.SIMULATION_SCORING_POINTS
        + cfg.SIMULATION_TEARDOWN_POINTS
    )
    assert pillar.score == expected_total
    # Each dimension matches its Simulation override constant exactly —
    # the other dimension scorers' facts are ignored under the override.
    dim_by_name = {d.name: d.score for d in pillar.dimensions}
    assert dim_by_name["Provisioning"] == cfg.SIMULATION_PROVISIONING_POINTS
    assert dim_by_name["Lab Access"] == cfg.SIMULATION_LAB_ACCESS_POINTS
    assert dim_by_name["Scoring"] == cfg.SIMULATION_SCORING_POINTS
    assert dim_by_name["Teardown"] == cfg.SIMULATION_TEARDOWN_POINTS


def test_pillar_bare_metal_required_caps_hard():
    """Bare metal → Pillar 1 capped at SANDBOX_API_RED_CAP_NOTHING_VIABLE
    (the hard-cap constant for can't-be-labbed-at-all)."""
    facts = ProductLababilityFacts(
        provisioning=ProvisioningFacts(needs_bare_metal=True),
    )
    pillar = pls.score_product_labability(facts)
    assert pillar.score <= cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE


# ─────────────────────────────────────────────────────────────────────────────
# Structural invariants
# ─────────────────────────────────────────────────────────────────────────────

def test_all_canonical_names_match_scoring_config():
    """Module-load verification already runs _verify_canonical_names.
    This test asserts the module was imported successfully — any name
    drift between this scorer and scoring_config would fail at import."""
    assert pls._PL_PILLAR.name == "Product Labability"
    assert pls._PROV_DIM.name == "Provisioning"
    assert pls._LA_DIM.name == "Lab Access"
    assert pls._SC_DIM.name == "Scoring"
    assert pls._TD_DIM.name == "Teardown"


def test_pillar_weights_sum_to_100():
    """Sanity: the four Pillar 1 dimensions sum to the pillar cap (100)."""
    total = (
        _dim_weight("Provisioning")
        + _dim_weight("Lab Access")
        + _dim_weight("Scoring")
        + _dim_weight("Teardown")
    )
    assert total == 100
