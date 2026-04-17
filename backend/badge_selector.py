"""Badge selector — Step 6-lite (Frank 2026-04-08).

Reads the Pillar scoring output (facts + scores + rubric grades) and emits
display Badge objects. This is the POST-SCORING display layer — badges are
pure display and never influence the math.

Design principles (all locked in Chunk 1 Issue #3):

1. **Badge = finding, not fix.** The badge names the thing (noun: what is
   it, what was observed). The evidence text carries context + optional
   "something to explore" suggestions. Never prescribe fixes in badge names.

2. **Green / Amber / Red color semantics.**
   - Green = works, confidence, no action needed
   - Amber = uneasy, needs validation, SE should verify
   - Red = cannot do this / this specific thing doesn't work

3. **Multi-badge per dimension is legitimate.** A single dimension can fire
   multiple badges with different colors — `Teardown API` green + `Orphan Risk`
   amber is an honest multi-badge picture.

4. **Naming rules (D1–D5, all locked):**
   - Concise: ~25 chars / ~4 words max
   - Vendor's own acronym only (Product.vendor_official_acronym) — never invented
   - Title Case for words; acronyms ALL CAPS
   - Restricted vocabulary: never "Cloud Slice", "Labs", or Skillable-jargon
     names that aren't seller-facing
   - Absence findings use `No X` prefix
   - No periods anywhere in badge text

5. **Evidence text may include exploratory suggestions** framed as "Something
   to explore:" / "Worth investigating:" / never "The SE should" or
   "Recommendation: do X." The finding is the badge; the action is the SE's call.

Architecture layer: BADGE (post-scoring display) per the Three Layers of
Intelligence in docs/Platform-Foundation.md.

NO HARDCODING of point values. Badge names and colors are the canonical
vocabulary from scoring_config.py.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

import scoring_config as cfg
from models import (
    Badge,
    CompanyAnalysis,
    DimensionScore,
    Evidence,
    GradedSignal,
    PillarScore,
    Product,
)

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Evidence text helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _evidence(
    claim: str,
    confidence: str = "indicated",
    source_url: Optional[str] = None,
) -> Evidence:
    """Build a minimal Evidence record for a badge.

    Confidence hedging language (confirmed / indicated / inferred) is
    baked into the claim string per Frank's rule. The confidence field
    here mirrors the language so the downstream display can render
    color-coded confidence indicators.
    """
    return Evidence(
        claim=claim,
        confidence_level=confidence,
        confidence_explanation="",
        source_url=source_url,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar 1 — deterministic badge selection from facts
# ═══════════════════════════════════════════════════════════════════════════════

def _underlying_tech_summary(product: Product) -> str:
    """Build a short summary of underlying technologies for badge evidence.

    For wrapper orgs (certs, degrees, courses), names the specific
    technologies inside the wrapper. Returns empty string for software
    companies where the product IS the technology.
    """
    techs = getattr(product, "underlying_technologies", None) or []
    if not techs:
        return ""
    names = [t.get("name", "") for t in techs if t.get("name")]
    if not names:
        return ""
    if len(names) <= 4:
        return " (" + ", ".join(names) + ")"
    return " (" + ", ".join(names[:3]) + f", +{len(names) - 3} more)"


def _pillar_1_provisioning_badges(product: Product) -> list[Badge]:
    """Build the Provisioning dimension badges from ProductLababilityFacts.

    Reads the fact drawer directly and applies the canonical badge rules
    from tonight's Pillar 1 refinements (M365 fabric, Custom Cloud strength,
    Multi-Fabric Bonus, No GCP Path, Pre-Instancing? suggestion, ESX Required
    anomaly, GPU Required friction).
    """
    p = product.product_labability_facts.provisioning
    badges: list[Badge] = []
    tech_summary = _underlying_tech_summary(product)

    # ── Simulation hard override — emit fact-driven context badges ──
    # If the scorer picked Simulation as the fabric, Pillar 1 is in the hard
    # override state (12 / 12 / 0 / 12 = 36). Rather than render gray bars
    # with a single "No Deployment Method" absence badge (which hides WHY
    # Simulation was chosen), emit fact-driven context badges that explain
    # the specific researcher facts that drove the override. Every badge
    # below has a concrete fact trigger — no invention, no padding.
    # Frank 2026-04-16: "at least two, ideally 3-4 badges with real evidence
    # for why this dimension scored the way it did."
    if product.fit_score.product_labability is not None:
        prov_dim_score = next(
            (d for d in product.fit_score.product_labability.dimensions if d.name == "Provisioning"),
            None,
        )
        if prov_dim_score is not None and prov_dim_score.score == cfg.SIMULATION_PROVISIONING_POINTS:
            # Verify we're in the Simulation hard override case — check that
            # Scoring is also at the override value and Teardown matches too
            sc = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Scoring"), None)
            td = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Teardown"), None)
            if (sc is not None and sc.score == cfg.SIMULATION_SCORING_POINTS and
                td is not None and td.score == cfg.SIMULATION_TEARDOWN_POINTS):
                # Simulation fabric chosen — emit context badges explaining why.
                badges.append(Badge(
                    name="Simulation Fabric", color="gray", qualifier="Context",
                    evidence=[_evidence(
                        "No real per-learner provisioning path found in research — Simulation "
                        "is the honest fallback. Learners interact with a simulated UI and "
                        "workflow instead of the actual product instance.",
                        confidence="indicated",
                    )],
                ))
                if p.runs_as_saas_only and not p.has_sandbox_api:
                    badges.append(Badge(
                        name="SaaS-Only, No API", color="amber", qualifier="Risk",
                        evidence=[_evidence(
                            "Product runs as a vendor-hosted SaaS with no documented provisioning API. "
                            "No path to spin up per-learner environments programmatically. "
                            "Something to explore: whether the vendor has an undocumented admin API "
                            "or a partner-tier sandbox program that could unlock a real fabric.",
                            confidence="confirmed",
                        )],
                    ))
                elif p.runs_as_saas_only and p.has_sandbox_api and p.sandbox_api_granularity == "partial":
                    badges.append(Badge(
                        name="Partial API", color="amber", qualifier="Risk",
                        evidence=[_evidence(
                            "Partial vendor provisioning API indicated — some endpoints exist but coverage "
                            "was uncertain enough that Simulation is the safer current fabric. Sharpening "
                            "the API detection in future research runs may promote this to Sandbox API.",
                            confidence="indicated",
                        )],
                    ))
                if p.runs_as_saas_only:
                    badges.append(Badge(
                        name="SaaS-Only Deployment", color="gray", qualifier="Context",
                        evidence=[_evidence(
                            "Product is only available as a vendor-hosted managed service — "
                            "learners cannot install their own instance.",
                            confidence="confirmed",
                        )],
                    ))
                if p.needs_gcp:
                    badges.append(Badge(
                        name="No GCP Path", color="amber", qualifier="Risk",
                        evidence=[_evidence(
                            "GCP dependency contributed to Simulation selection — Skillable has no "
                            "native GCP fabric today. Alternative paths (VM, Azure, Sandbox API) "
                            "might meet the learning objectives if the GCP affinity is flexible.",
                            confidence="indicated",
                        )],
                    ))
                return badges

    # ── M365 fabric (highest-priority Pillar 1 fabric) ──
    if p.m365_scenario == "end_user":
        badges.append(Badge(
            name="M365 Tenant",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Microsoft 365 End User scenario confirmed — Skillable's automated M365 tenant provisioning applies "
                "(Base/Full/Full+AI tiers). Low-friction learner path: no credit card, no MFA, Skillable-owned tenant.",
                confidence="confirmed",
            )],
        ))
    elif p.m365_scenario == "administration":
        badges.append(Badge(
            name="M365 Admin",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "Microsoft 365 Administration scenario indicated — requires Global Admin access. "
                "Path is either MOC-provided tenant (for Microsoft Learning Partners) or learner-signed-up M365 Trial account "
                "(may require credit card or MFA identity verification by Microsoft).",
                confidence="indicated",
            )],
        ))

    # ── VM / Container / Cloud fabric badges ──
    if not p.m365_scenario:
        # Only fire VM/Cloud badges when M365 isn't the primary fabric
        if p.runs_as_installable:
            badges.append(Badge(
                name="Runs in VM",
                color="green",
                qualifier="Strength",
                evidence=[_evidence(
                    f"Installable on Windows / Linux confirmed{tech_summary} — Skillable hosts in Hyper-V by default "
                    "(or ESX when nested virtualization is required). Clean VM deployment path.",
                    confidence="confirmed",
                )],
            ))
            # ESX Required as an anomaly badge alongside the VM primary
            if p.requires_esx:
                reason = p.requires_esx_reason or "specific technical constraint documented"
                badges.append(Badge(
                    name="ESX Required",
                    color="amber",
                    qualifier="Risk",
                    evidence=[_evidence(
                        f"ESX Required indicated — {reason}. Broadcom licensing adds operational cost over Hyper-V. "
                        "Something to explore: whether a smaller VM footprint could avoid the ESX requirement.",
                        confidence="indicated",
                    )],
                ))
        elif p.runs_as_container and _container_is_viable(p):
            badges.append(Badge(
                name="Runs in Container",
                color="green",
                qualifier="Strength",
                evidence=[_evidence(
                    "Container-native production deployment confirmed — no disqualifiers. "
                    "Faster launch and lower cost than VMs for this workload.",
                    confidence="confirmed",
                )],
            ))
        elif p.runs_as_azure_native:
            badges.append(Badge(
                name="Runs in Azure",
                color="green",
                qualifier="Strength",
                evidence=[_evidence(
                    "Azure-native managed service confirmed — viable for Azure Cloud Slice provisioning per learner.",
                    confidence="confirmed",
                )],
            ))
        elif p.runs_as_aws_native:
            badges.append(Badge(
                name="Runs in AWS",
                color="green",
                qualifier="Strength",
                evidence=[_evidence(
                    "AWS-native managed service confirmed — viable for AWS Cloud Slice provisioning per learner.",
                    confidence="confirmed",
                )],
            ))

    # ── Sandbox API (multi-color finding badge) ──
    if p.has_sandbox_api:
        if p.sandbox_api_granularity == "rich":
            badges.append(Badge(
                name="Sandbox API",
                color="green",
                qualifier="Strength",
                evidence=[_evidence(
                    "Rich vendor provisioning API confirmed — full create / configure / delete cycle available. "
                    "Per-learner environments can be orchestrated directly through the vendor's API.",
                    confidence="confirmed",
                )],
            ))
        elif p.sandbox_api_granularity == "partial":
            badges.append(Badge(
                name="Sandbox API",
                color="amber",
                qualifier="Risk",
                evidence=[_evidence(
                    "Partial vendor provisioning API indicated — some endpoints exist but coverage is uncertain. "
                    "Something to explore: whether the gaps in the API can be worked around with Lifecycle Actions "
                    "or whether the vendor has undocumented endpoints that could close the gap.",
                    confidence="indicated",
                )],
            ))
        # Custom Cloud Skillable-strength context badge fires alongside
        badges.append(Badge(
            name="Custom Cloud",
            color="gray",
            qualifier="Context",
            evidence=[_evidence(
                "Skillable's Custom Cloud Labs pattern orchestrates this product's vendor API through Lifecycle Actions, "
                "Automated Activities, and Custom Start Page. Proven operational pattern for SaaS products with per-learner "
                "provisioning APIs — the Salesforce solution in Skillable docs is a working reference.",
                confidence="confirmed",
            )],
        ))

    # ── Pre-Instancing? suggestion badge ──
    if p.is_large_lab or p.has_pre_instancing_opportunity:
        badges.append(Badge(
            name="Pre-Instancing?",
            color="amber",
            qualifier="Explore",
            evidence=[_evidence(
                "Large-footprint lab indicated — Skillable's Pre-Instancing could pre-warm these environments before "
                "learners arrive, cutting launch time meaningfully. Something to explore: whether the customer's learner "
                "volume justifies the Pre-Instancing pool size and whether the product has a warm-idle state that "
                "Pre-Instancing can snapshot.",
                confidence="indicated",
            )],
        ))

    # ── Multi-VM Lab strength ──
    if p.is_multi_vm_lab:
        badges.append(Badge(
            name="Multi-VM Lab",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Multi-VM architecture indicated — multiple VMs work together for the product. Skillable competitive "
                "advantage: most competitors struggle with multi-VM topologies. Drives the ACV rate tier upward.",
                confidence="indicated",
            )],
        ))

    # ── Complex Topology strength ──
    if p.has_complex_topology:
        badges.append(Badge(
            name="Complex Topology",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Real network complexity indicated — routers, switches, firewalls, segmentation, or routing protocols. "
                "Skillable competitive advantage for networking and cybersecurity training scenarios.",
                confidence="indicated",
            )],
        ))

    # ── GPU Required friction ──
    if p.needs_gpu:
        badges.append(Badge(
            name="GPU Required",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "GPU requirement confirmed — forces Azure or AWS VM with GPU instance (via Compute Gallery). "
                "Launch time is longer and per-lab cost is higher than standard Hyper-V. Something to explore: "
                "whether a smaller GPU tier meets the learning objectives.",
                confidence="confirmed",
            )],
        ))

    # ── No GCP Path (amber simple case — Step 5.5 will add red+workaround nuance) ──
    if p.needs_gcp:
        badges.append(Badge(
            name="No GCP Path",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "GCP dependency indicated — Skillable does not have a native GCP path today. "
                "Something to explore: whether the lab objectives can be met via an alternative fabric (VM, Azure, "
                "or Sandbox API) without losing the core learning outcomes.",
                confidence="indicated",
            )],
        ))

    # ── Bare Metal Required blocker ──
    if p.needs_bare_metal:
        badges.append(Badge(
            name="Bare Metal Required",
            color="red",
            qualifier="Blocker",
            evidence=[_evidence(
                "Physical hardware requirement confirmed — no virtualization path exists for this product. "
                "Skillable cannot deliver this in a lab environment.",
                confidence="confirmed",
            )],
        ))

    return badges


def _container_is_viable(p) -> bool:
    """Mirror of the container viability rule from pillar_1_scorer."""
    if not p.runs_as_container:
        return False
    if not p.container_is_production_native:
        return False
    if p.container_is_dev_only:
        return False
    if p.container_needs_windows_gui:
        return False
    if p.container_needs_multi_vm_network:
        return False
    return True


def _pillar_1_lab_access_badges(product: Product) -> list[Badge]:
    """Build Lab Access dimension badges from facts."""
    la = product.product_labability_facts.lab_access
    p = product.product_labability_facts.provisioning
    badges: list[Badge] = []

    # Simulation hard override — emit fact-driven context badges instead of
    # returning empty. Every badge has a concrete fact trigger. Frank
    # 2026-04-16: 2–4 badges per dimension with real evidence for why it
    # scored the way it did.
    if product.fit_score.product_labability is not None:
        la_dim = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Lab Access"), None)
        if la_dim is not None and la_dim.score == cfg.SIMULATION_LAB_ACCESS_POINTS:
            prov_dim = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Provisioning"), None)
            if prov_dim is not None and prov_dim.score == cfg.SIMULATION_PROVISIONING_POINTS:
                # Context badge — explain that simulation removes real-product auth
                badges.append(Badge(
                    name="Simulated Access", color="gray", qualifier="Context",
                    evidence=[_evidence(
                        "In Simulation mode learners log into Skillable's simulated UI — "
                        "no vendor identity provisioning, no credential lifecycle, no training "
                        "license needed. Trade-off: the simulated experience won't exercise "
                        "real-product auth quirks the learner will encounter in production.",
                        confidence="confirmed",
                    )],
                ))
                # Real-product facts still matter as "what was skipped because of Simulation"
                if la.has_mfa_blocker:
                    badges.append(Badge(
                        name="Real-Product MFA", color="amber", qualifier="Risk",
                        evidence=[_evidence(
                            "Real product requires MFA — contributed to the Simulation fabric "
                            "decision (MFA blocks automated learner provisioning). Simulation "
                            "sidesteps this, but the learner won't practice the real MFA workflow.",
                            confidence="indicated",
                        )],
                    ))
                if la.has_anti_automation:
                    badges.append(Badge(
                        name="Anti-Automation", color="amber", qualifier="Risk",
                        evidence=[_evidence(
                            "Real product has anti-automation controls (CAPTCHA or bot detection). "
                            "Automated learner provisioning blocked — Simulation is the alternative.",
                            confidence="indicated",
                        )],
                    ))
                if la.training_license == "blocked":
                    badges.append(Badge(
                        name="Training License Blocked", color="red", qualifier="Blocker",
                        evidence=[_evidence(
                            "No documented non-production / NFR license path — real-product access "
                            "blocked. Simulation is the only viable approach today.",
                            confidence="confirmed",
                        )],
                    ))
                elif la.training_license == "medium_friction":
                    badges.append(Badge(
                        name="License Path Unclear", color="amber", qualifier="Risk",
                        evidence=[_evidence(
                            "Real-product licensing exists but would need SE validation "
                            "(partner tier, signup friction, or concurrent-user limits). "
                            "Part of why Simulation was chosen.",
                            confidence="indicated",
                        )],
                    ))
                return badges

    # ── Identity / auth path badges ──
    if la.auth_model == "entra_native_tenant" and p.runs_as_azure_native:
        badges.append(Badge(
            name="Entra ID SSO",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Entra ID SSO confirmed — Azure-native product pre-configured to use the customer's Entra tenant. "
                "Zero credential management for learners.",
                confidence="confirmed",
            )],
        ))
    elif la.user_provisioning_api_granularity == "rich":
        badges.append(Badge(
            name="Identity API",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Vendor Identity API confirmed — rich user provisioning and role assignment capability. "
                "Per-learner accounts can be created and torn down programmatically.",
                confidence="confirmed",
            )],
        ))
    elif la.user_provisioning_api_granularity == "partial":
        badges.append(Badge(
            name="Identity API",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "Vendor Identity API indicated — partial coverage (some endpoints missing or undocumented). "
                "Something to explore: whether the gaps block per-learner provisioning or can be worked around.",
                confidence="indicated",
            )],
        ))
    elif la.auth_model in ("sso_saml", "sso_oidc"):
        badges.append(Badge(
            name="Manual SSO",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "Generic SSO (SAML or OIDC) indicated — SSO works but learners still enter credentials manually. "
                "No per-learner identity provisioning API found.",
                confidence="indicated",
            )],
        ))

    # ── Credential lifecycle ──
    if la.credential_lifecycle == "recyclable":
        badges.append(Badge(
            name="Cred Recycling",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Credential recycling confirmed — customer credentials can be reset and reused between learners. "
                "Low operational overhead.",
                confidence="confirmed",
            )],
        ))
    elif la.credential_lifecycle == "pool_only":
        badges.append(Badge(
            name="Credential Pool",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Credential pool confirmed — pre-provisioned batch of credentials distributed to learners. "
                "Operationally heavier than recycling but workable.",
                confidence="confirmed",
            )],
        ))

    # ── Training License (universal amber default per Frank 2026-04-08) ──
    # Rule: amber is the default for essentially every product. Green is
    # reserved for the truly-zero-friction edge cases — open source with
    # no concurrent-user model, no tier choices, no add-on decisions —
    # and the researcher does not currently have enough fact signal to
    # claim that confidently, so green is not emitted by default. Most
    # products, including M365 End User, fire amber because real SE
    # conversations happen around almost every non-trivial licensing
    # arrangement (tier, count, add-ons, regional restrictions, commercial
    # vs training license terms, existing customer agreements).
    # Red fires only when the fact drawer reports the license is blocked
    # (no viable path).
    if la.training_license == "blocked":
        badges.append(Badge(
            name="Training License",
            color="red",
            qualifier="Blocker",
            evidence=[_evidence(
                "Training License blocked — no viable path found. Credit card required plus high cost plus no "
                "negotiation path documented.",
                confidence="confirmed",
            )],
        ))
    else:
        # Everything else fires Training License amber. Evidence text
        # adapts to M365 scenarios (where the Skillable automated M365
        # lane removes learner friction but the licensing design
        # conversation still happens) vs the general case (trial/dev/
        # partner license with SE terms validation).
        if p.m365_scenario:
            claim = (
                "Training License indicated amber — Microsoft 365 licensing has real SE questions to work out: "
                "which tier (Base/Full/Full+AI)? concurrent user count? which optional add-ons (Teams, Copilot, "
                "Power BI Premium)? existing customer tenants to integrate with? Skillable's automated M365 lane "
                "removes learner friction, but the licensing design conversation still happens."
            )
        else:
            claim = (
                "Training License indicated amber — licensing arrangement needs SE validation with the customer: "
                "concurrent user count, tier choice, optional add-ons, regional restrictions, commercial-vs-training "
                "license terms, and whether existing customer agreements apply. Green is reserved for truly "
                "zero-friction cases (unlimited free tier with no concurrent user model and no tier choices) and "
                "those are rare enough that the badge defaults to amber until an SE confirms otherwise."
            )
        badges.append(Badge(
            name="Training License",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(claim, confidence="indicated")],
        ))

    # ── Red blocker badges ──
    if la.has_mfa_blocker:
        badges.append(Badge(
            name="MFA Required",
            color="red",
            qualifier="Blocker",
            evidence=[_evidence(
                "Multi-factor authentication required confirmed — blocks automated per-learner account creation. "
                "Requires manual enrollment or a workaround from the vendor.",
                confidence="confirmed",
            )],
        ))
    if la.has_anti_automation:
        badges.append(Badge(
            name="Anti-Automation Controls",
            color="red",
            qualifier="Blocker",
            evidence=[_evidence(
                "Anti-automation controls confirmed — platform actively blocks automated account creation "
                "(CAPTCHA, bot detection, or enforced rate limits).",
                confidence="confirmed",
            )],
        ))
    if la.has_rate_limit_blocker:
        badges.append(Badge(
            name="Rate Limits",
            color="red",
            qualifier="Blocker",
            evidence=[_evidence(
                "Rate limits confirmed — API limits constrain concurrent learner provisioning. "
                "Something to explore: whether the vendor can raise the limit for training use.",
                confidence="confirmed",
            )],
        ))

    return badges


def _pillar_1_scoring_badges(product: Product) -> list[Badge]:
    """Build Scoring dimension badges from facts."""
    sc = product.product_labability_facts.scoring
    badges: list[Badge] = []

    # Simulation override — emit fact-driven context badges. Frank 2026-04-16.
    if product.fit_score.product_labability is not None:
        sc_dim = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Scoring"), None)
        prov_dim = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Provisioning"), None)
        if (sc_dim is not None and sc_dim.score == cfg.SIMULATION_SCORING_POINTS and
            prov_dim is not None and prov_dim.score == cfg.SIMULATION_PROVISIONING_POINTS):
            badges.append(Badge(
                name="No Scoring in Simulation", color="red", qualifier="Blocker",
                evidence=[_evidence(
                    "Skillable Simulations do not support automated scoring today. "
                    "Without scoring, labs cannot validate learner work — feature request "
                    "flagged; not a current capability.",
                    confidence="confirmed",
                )],
            ))
            # If the real product would have offered scoring surfaces, surface that —
            # simulation elides them but it's still useful context about what we're missing.
            if sc.state_validation_api_granularity in ("rich", "partial"):
                badges.append(Badge(
                    name="Real Scoring API Present", color="gray", qualifier="Context",
                    evidence=[_evidence(
                        "The real product exposes a state-validation API (" +
                        sc.state_validation_api_granularity +
                        " granularity). Simulation elides it — promoting this product "
                        "off Simulation would unlock API-based scoring.",
                        confidence="indicated",
                    )],
                ))
            if sc.scriptable_via_shell_granularity in ("full", "partial"):
                badges.append(Badge(
                    name="Real Script Surface", color="gray", qualifier="Context",
                    evidence=[_evidence(
                        "The real product has a shell scripting surface — unused under "
                        "Simulation. Would drive Grand Slam scoring if we had a VM fabric.",
                        confidence="indicated",
                    )],
                ))
            if sc.gui_state_visually_evident_granularity in ("full", "partial"):
                badges.append(Badge(
                    name="AI Vision Candidate", color="gray", qualifier="Context",
                    evidence=[_evidence(
                        "GUI-evident state reported — AI Vision could score the real product "
                        "but Simulation doesn't expose a real GUI to inspect.",
                        confidence="indicated",
                    )],
                ))
            return badges

    if sc.state_validation_api_granularity == "rich":
        badges.append(Badge(
            name="Scoring API",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Rich vendor scoring API confirmed — broad state-validation surface. "
                "Cloud-native lab scoring can be driven through the API.",
                confidence="confirmed",
            )],
        ))
    elif sc.state_validation_api_granularity == "partial":
        badges.append(Badge(
            name="Scoring API",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "Partial vendor scoring API indicated — some validation endpoints exist but coverage is uncertain.",
                confidence="indicated",
            )],
        ))

    if sc.scriptable_via_shell_granularity == "full":
        badges.append(Badge(
            name="Script Scoring",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Full shell scripting surface confirmed — PowerShell / Bash scoring scripts can validate config, "
                "files, services, and state end-to-end.",
                confidence="confirmed",
            )],
        ))
    elif sc.scriptable_via_shell_granularity == "partial":
        badges.append(Badge(
            name="Script Scoring",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "Partial shell scripting surface indicated — some scriptable areas but gaps in coverage.",
                confidence="indicated",
            )],
        ))

    if sc.gui_state_visually_evident_granularity == "full":
        badges.append(Badge(
            name="AI Vision",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "GUI-evident state confirmed — AI Vision is the right scoring tool for this product. "
                "Skillable's AI Vision is a real differentiator in the lab platform space.",
                confidence="confirmed",
            )],
        ))
    elif sc.gui_state_visually_evident_granularity == "partial":
        badges.append(Badge(
            name="AI Vision",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "AI Vision usable but indicated visual state ambiguity — some GUI states are ambiguous or hidden.",
                confidence="indicated",
            )],
        ))

    # ── No Scoring Methods red blocker ──────────────────────────────────
    # If none of the four viable scoring paths have any granularity and
    # simulation scoring isn't viable either, emit a red "No Scoring Methods"
    # badge so the Full Analysis view shows the dimension's state clearly
    # (the dimension already scores 0 on the math side by virtue of having
    # no credited signals; this is the display-layer surface of that zero).
    # Frank 2026-04-08 Trellix Intelligence as a Service — product had no
    # API, no scripting, no AI Vision, no simulation scoring, but the
    # Scoring dimension surfaced zero badges at all; the user had no way
    # to see "this product has no scoring path".
    if not badges and not sc.simulation_scoring_viable:
        badges.append(Badge(
            name="No Scoring Methods",
            color="red",
            qualifier="Blocker",
            evidence=[_evidence(
                "No viable scoring method found — no Scoring API, no Script Scoring, "
                "no AI Vision, no Simulation scoring. The product cannot be scored.",
                confidence="confirmed",
            )],
        ))

    return badges


def _pillar_1_teardown_badges(product: Product) -> list[Badge]:
    """Build Teardown dimension badges from facts."""
    td = product.product_labability_facts.teardown
    p = product.product_labability_facts.provisioning
    badges: list[Badge] = []

    # Simulation override — emit fact-driven context badges. Teardown under
    # Simulation is legitimately simple (session ends, nothing persists), so
    # 1-2 badges is honest here. Frank 2026-04-16: "Teardown is the one
    # dimension where 1 badge can be legitimate (more boolean)."
    if product.fit_score.product_labability is not None:
        td_dim = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Teardown"), None)
        prov_dim = next((d for d in product.fit_score.product_labability.dimensions if d.name == "Provisioning"), None)
        if (td_dim is not None and td_dim.score == cfg.SIMULATION_TEARDOWN_POINTS and
            prov_dim is not None and prov_dim.score == cfg.SIMULATION_PROVISIONING_POINTS):
            badges.append(Badge(
                name="Simulation Reset", color="gray", qualifier="Context",
                evidence=[_evidence(
                    "Simulation sessions end with the learner session — no vendor-side "
                    "infrastructure to tear down, no orphaned credentials, no resource leak. "
                    "Clean by construction.",
                    confidence="confirmed",
                )],
            ))
            if td.has_orphan_risk:
                badges.append(Badge(
                    name="Real-Product Orphan Risk", color="amber", qualifier="Risk",
                    evidence=[_evidence(
                        "If this product were promoted off Simulation to a real fabric, "
                        "documented orphan-risk signals would apply — vendor teardown API "
                        "either has gaps or is missing. Something for the SE to validate.",
                        confidence="indicated",
                    )],
                ))
            return badges

    # Normal Teardown path
    runs_in_real_fabric = p.runs_as_installable or p.runs_as_container
    if runs_in_real_fabric:
        badges.append(Badge(
            name="Datacenter",
            color="green",
            qualifier="Strength",
            evidence=[_evidence(
                "Datacenter automatic teardown confirmed — Hyper-V snapshot revert or container destroy handles cleanup "
                "between learners with zero operational cost.",
                confidence="confirmed",
            )],
        ))
    else:
        if td.vendor_teardown_api_granularity == "rich":
            badges.append(Badge(
                name="Teardown API",
                color="green",
                qualifier="Strength",
                evidence=[_evidence(
                    "Rich vendor teardown API confirmed — cleanup endpoints cover the full lifecycle. "
                    "Orchestrated cleanup through Lifecycle Actions.",
                    confidence="confirmed",
                )],
            ))
        elif td.vendor_teardown_api_granularity == "partial":
            badges.append(Badge(
                name="Teardown API",
                color="amber",
                qualifier="Risk",
                evidence=[_evidence(
                    "Partial vendor teardown API indicated — some cleanup endpoints exist but gaps may leave residue.",
                    confidence="indicated",
                )],
            ))
        else:
            badges.append(Badge(
                name="Manual Teardown",
                color="red",
                qualifier="Blocker",
                evidence=[_evidence(
                    "No programmatic teardown mechanism found — manual cleanup required between learners. "
                    "Real build task. Something to explore: whether the vendor has undocumented cleanup endpoints.",
                    confidence="confirmed",
                )],
            ))

    if td.has_orphan_risk:
        badges.append(Badge(
            name="Orphan Risk",
            color="amber",
            qualifier="Risk",
            evidence=[_evidence(
                "Orphan risk indicated — some resources, accounts, or data may be left behind even when the teardown "
                "API is called. Something to explore: whether the gaps are in specific services that can be skipped "
                "or whether the lab design needs to avoid those resources.",
                confidence="indicated",
            )],
        ))

    return badges


def select_pillar_1_badges(product: Product) -> dict[str, list[Badge]]:
    """Select Pillar 1 display badges for a product.

    Returns a dict keyed by dimension name → list of Badge objects.
    Reads the fact drawer + fit_score.product_labability (for Simulation
    override detection) and emits display-only badges per the rules locked
    in Chunk 1 Issue #3 on 2026-04-08.

    Absence badge rule (2026-04-12): a dimension with a score but zero
    badges must emit an absence finding so the seller sees WHY the score
    is what it is. "Absence is a finding, not a blank."
    """
    # Context-aware absence badges — emitted only when the dimension-specific
    # function returns zero badges. Checks product context to provide richer
    # evidence than generic "not found" text. Frank 2026-04-13.
    _GOVERNANCE_KEYWORDS = {"governance", "leadership", "management", "awareness",
                            "strategy", "compliance", "ethics", "policy", "risk management",
                            "program management", "executive", "officer", "ciso", "cscu"}

    def _is_governance_product() -> bool:
        sub = (product.subcategory or "").lower()
        name = (product.name or "").lower()
        return bool(_GOVERNANCE_KEYWORDS & set(sub.split()) or
                     _GOVERNANCE_KEYWORDS & set(name.split()))

    def _absence_badge(dim_name: str) -> Badge:
        is_gov = _is_governance_product()
        has_techs = bool(getattr(product, "underlying_technologies", None))
        defaults = {
            "Provisioning": (
                "No Deployment Method",
                ("Leadership/governance offering — hands-on tool labs are not applicable. "
                 "Consider simulation-based scenarios (tabletop exercises, risk simulations).")
                if is_gov else
                ("No provisioning path identified — research did not find "
                 "installable, cloud, container, or API-based deployment options.")
            ),
            "Lab Access": (
                "No Access Path",
                ("Leadership/governance offering — no learner identity or credential management needed "
                 "for simulation-based scenarios.")
                if is_gov else
                "No identity, credential, or learner isolation mechanism identified."
            ),
            "Scoring": (
                "No Scoring Method",
                ("Leadership/governance offering — assessment would be scenario-based "
                 "(decision quality, response effectiveness) rather than technical validation.")
                if is_gov else
                ("No API, script, or AI Vision scoring path identified. "
                 "Without scoring, labs cannot validate learner work.")
            ),
            "Teardown": (
                "No Teardown Path",
                ("Leadership/governance offering — simulation-based scenarios have no "
                 "infrastructure to tear down.")
                if is_gov else
                "No automated cleanup mechanism identified."
            ),
        }
        name, evidence = defaults.get(dim_name, ("Unknown", ""))
        return Badge(name=name, color="red" if not is_gov else "gray", evidence=evidence)

    result = {
        "Provisioning": _pillar_1_provisioning_badges(product),
        "Lab Access": _pillar_1_lab_access_badges(product),
        "Scoring": _pillar_1_scoring_badges(product),
        "Teardown": _pillar_1_teardown_badges(product),
    }

    # Emit absence badge for any dimension that has zero badges
    for dim_name, badges in result.items():
        if not badges:
            result[dim_name] = [_absence_badge(dim_name)]

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar 2 / Pillar 3 — direct mapping from GradedSignal to Badge
# ═══════════════════════════════════════════════════════════════════════════════

def _strength_to_qualifier(strength: str) -> str:
    """Map the grader's strength tier to a human-readable qualifier."""
    mapping = {
        "strong": "Strength",
        "moderate": "Context",
        "weak": "Context",
        "informational": "Context",
    }
    return mapping.get(strength, "Context")


#: Locked word abbreviations for rubric-grader badge names. Frank 2026-04-08:
#: "Long words" — tightening to ~20 chars per badge. Applied word-for-word
#: after Title Case, before the length cap. This is the single source of
#: truth for grader-emitted badge abbreviations; extend here, never inline
#: at call sites.
_BADGE_NAME_ABBREVIATIONS: dict[str, str] = {
    # Length abbreviations
    "Geographic": "Geo",
    "Consequences": "Risks",
    "Certification": "Cert",
    "Configuration": "Config",
    "Administrator": "Admin",
    "Administration": "Admin",
    "Authentication": "Auth",
    "Development": "Dev",
    "Operations": "Ops",
    "Application": "App",
    "Environment": "Env",
    "Production": "Prod",
    "Documentation": "Docs",
    "Performance": "Perf",
    "Repository": "Repo",
    "Infrastructure": "Infra",
    "Recommendation": "Reco",
    "Organizational": "Org",
    "Organization": "Org",
    "Integration": "Integ",
    "Instructional": "ID",   # e.g. "Instructional Designers" -> "ID Designers" -> "IDs On Staff"
    "Designers": "IDs",      # canonical phrase: "IDs On Staff"
    "Designer": "ID",
    "Partnerships": "Partners",
    "Partnership": "Partner",
    # "Enablement" stays unabbreviated — "Enable" reads awkwardly as a
    # standalone word ("Customer Enable Team" vs "Customer Enablement
    # Team"). The 24-char cap now accommodates "Customer Enablement".
    "Independent": "Indep",
    "Professional": "Pro",
    "Technical": "Tech",
    "Commitment": "Commit",
    "Delivery": "Delivery",  # explicit pass-through so a later rename is one edit
    "Requirements": "Reqs",
    "Complexity": "Depth",
    "Complicated": "Complex",
    "Multi-Audience": "Multi-Aud",
    "Reference": "Ref",
    "Customers": "Customers",  # locked — DO NOT shorten to "Custs"
}

#: Acronyms that must render ALL CAPS when they appear as whole Title-Cased words.
#: Frank 2026-04-08: "AI" needs to be ALL CAPS, not "Ai" — caught on Trellix.
#: Extend this tuple as new acronyms appear; never special-case inline.
_BADGE_NAME_ACRONYMS: tuple[str, ...] = (
    # Core platform / scoring vocabulary
    "Api", "Atp", "Alp", "Mfa", "Sso", "Saml", "Vm", "Sme", "Id", "Ids",
    "Diy", "Lms", "Gpu", "Cpu", "Nfr", "Mcq", "Kyc", "Pii", "Rest",
    # AI / ML — Frank 2026-04-08
    "Ai", "Ml", "Llm", "Rag", "Nlp", "Gpt", "Mlops",
    # Cybersecurity / general
    "Ctf", "Siem", "Edr", "Soc", "Ilt",
    # Security stack
    "Soc", "Siem", "Edr", "Xdr", "Soar", "Iam", "Dlp", "Waf", "Ids",
    "Ips", "Zta", "Ztna", "Casb", "Sase",
    # Business / ops
    "Poc", "Crm", "Erp", "Hris", "Saas", "Paas", "Iaas", "Rpa", "Bpm",
    # DevOps / infra
    "Ci", "Cd", "Iac", "Rbac", "Cicd", "Sdlc", "Dns", "Cdn", "Vpc",
    # Net / standards
    "Url", "Ssl", "Tls", "Tcp", "Udp", "Http", "Https", "Json", "Xml",
    # Cloud
    "Aws", "Gcp",
    # Hardware
    "Sql", "Nosql", "Etl", "Elt",
    # Misc
    "Sdk", "Ide", "Cli", "Gui",
)

#: Hard max character budget per rubric-emitted badge. Frank 2026-04-08 —
#: tuned to 24 after Trellix showed that the 20-char cap was chopping
#: single characters off real rubric labels: "Multi VM Architecture"
#: (21 chars) → "Multi VM Architectur", "Niche Within Category" (21 chars)
#: → "Niche Within Categor". 24 lets full, properly-titled multi-word
#: labels render intact while still keeping badges visually compact.
_BADGE_NAME_MAX_CHARS = 24


#: Phrase-level display overrides for signal_category -> badge name. Applied
#: BEFORE Title Case / abbreviations / caps. Use this when the default
#: word-by-word transformation can't produce the desired badge text -- e.g.
#: when the display name should drop words, reorder, or include punctuation
#: that snake_case can't carry. Frank 2026-04-08 Cohesity feedback:
#:   - "Hands On Learning" too wordy -> "Hands On"
#:   - "Instructor Authors Dual" awkward order -> "Dual Instructors/Authors"
#: Extend here, never special-case inline. Values bypass the character cap
#: because we author them directly -- the author is responsible for length.
_SIGNAL_CATEGORY_DISPLAY_OVERRIDES: dict[str, str] = {
    "hands_on_learning_language": "Hands On",
    "instructor_authors_dual_role": "Dual Instructors/Authors",
    # Badge naming fixes — locked 2026-04-12, deterministic enforcement
    # because prompt-only instructions are unreliable for exact naming.
    "content_team_named": "Content Team",
    "instructional_designers": "IDs on Staff",
    # Naming rules from Badging-and-Scoring-Reference.md line 103:
    # "Name the specific provider, not the category."
    "published_course_calendar": "ILT Calendar",
    "vendor_published_on_third_party": "Third-Party Courses",
    "cert_delivery_infrastructure": "Cert Delivery Infra",  # grader should emit provider name; this is fallback
    # Academic vocabulary overrides
    "training_catalog_present": "Training Catalog",
    "customer_success_investment": "Customer Success",
    "customer_enablement_team": "Enablement Team",
    "multi_audience_commitment": "Multi Audience Commit",
    "training_leadership_level": "Training Leadership",
    "training_events_at_scale": "Events at Scale",
    "compliance_training_program": "Compliance Training",
    "employee_learning_investment": "Employee Learning",
    "partner_enablement_program": "Partner Enablement",
    # Delivery Capacity
    "atp_network": "ATP ALP Program",
    "instructor_delivery_network": "Instructor Network",
    "geographic_reach": "Geo Reach",
    # Organizational DNA
    "many_partnership_types": "Many Partner Types",
    "strategic_asset_partnerships": "Strategic Asset Partners",
    "platform_buyer_behavior": "Platform Buyer Behavior",
    "formal_channel_program": "Formal Channel Program",
    "nimble_engagement": "Nimble Engagement",
    "named_alliance_leadership": "Named Alliance",
    # Build Capacity
    "lab_build_capability": "Lab Build Capability",
    "sme_content_authoring": "SME Content Authoring",
    "product_training_partnership": "Training Partnership",
    "content_partnership": "Content Partnership",
}


def _prettify_signal_category(category: str) -> str:
    """Turn a signal_category snake-case key into a short display name.

    First checks _SIGNAL_CATEGORY_DISPLAY_OVERRIDES for a phrase-level
    override; if present, returns that directly (author is responsible
    for length and formatting). Otherwise applies Title Case, then the
    abbreviation dictionary word-for-word, then ALL-CAPS for standalone
    acronyms, then a hard character cap. Single source of truth for
    grader-emitted badge naming -- extend _SIGNAL_CATEGORY_DISPLAY_OVERRIDES
    for phrase-level renames, _BADGE_NAME_ABBREVIATIONS for word-level
    substitutions, or _BADGE_NAME_ACRONYMS for ALL-CAPS rules. Never
    special-case inline.
    """
    # Phrase-level override first -- skips all transforms and cap
    override = _SIGNAL_CATEGORY_DISPLAY_OVERRIDES.get(category)
    if override:
        return override

    words = category.replace("_", " ").split()
    out_words: list[str] = []
    for w in words:
        title = w.capitalize()
        if title in _BADGE_NAME_ABBREVIATIONS:
            out_words.append(_BADGE_NAME_ABBREVIATIONS[title])
        else:
            out_words.append(title)

    name = " ".join(out_words)

    # ALL CAPS for standalone acronym words (not when they're embedded in a word)
    for acronym in _BADGE_NAME_ACRONYMS:
        # Replace the Title-Cased form as a whole word
        name = _replace_whole_word(name, acronym, acronym.upper())

    # Hard character cap, word-aware: never slice mid-word. If there is
    # any space in the first _BADGE_NAME_MAX_CHARS characters, cut there
    # and drop the remaining partial word entirely. Only when the first
    # word itself already exceeds the cap (rare — e.g. a single long
    # compound word) do we fall back to a hard slice. Frank 2026-04-08:
    # the old 6-char rescue window produced "Multi VM Architectur" and
    # "Niche Within Categor" — last-character amputations that read as
    # bugs. Dropping the partial word is always the correct read.
    if len(name) > _BADGE_NAME_MAX_CHARS:
        truncated = name[:_BADGE_NAME_MAX_CHARS]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            name = truncated[:last_space]
        else:
            name = truncated
    return name


def _replace_whole_word(text: str, old: str, new: str) -> str:
    """Whole-word replace — `Id` in `Identity` should NOT become `ID`entity."""
    import re
    return re.sub(rf"\b{re.escape(old)}\b", new, text)


def _graded_signals_to_badges(
    grades: list[GradedSignal],
    max_badges: int = 4,
    dynamic_overrides: dict[str, str] | None = None,
) -> list[Badge]:
    """Convert a list of rubric-grader GradedSignal records into display Badges.

    The grader already wrote evidence_text with confidence hedging. Badge
    selection sorts by strength, applies the abbreviation dictionary
    (`_prettify_signal_category`), and caps at max_badges per dimension.

    `dynamic_overrides` lets callers substitute a fact-sourced display name
    for a signal_category — for example, replacing the generic "Customer
    Enablement Team" badge with the vendor's actual program name ("Cohesity
    Academy") when the researcher captured it in the fact drawer. Dynamic
    overrides take precedence over the static
    `_SIGNAL_CATEGORY_DISPLAY_OVERRIDES`; the static dictionary still wins
    over the prettifier for signal_categories not covered by the dynamic
    dict. Dynamic override strings are respected at their authored length
    (caller is responsible for sanity-checking against the _BADGE_NAME_MAX_CHARS
    budget if strict-length compliance matters).
    """
    if not grades:
        return []

    strength_rank = {"strong": 3, "moderate": 2, "weak": 1, "informational": 0}
    sorted_grades = sorted(
        grades,
        key=lambda g: (-strength_rank.get(g.strength, 0), g.signal_category),
    )

    badges: list[Badge] = []
    for g in sorted_grades[:max_badges]:
        # Dynamic fact-sourced override takes precedence over static rules
        if dynamic_overrides and g.signal_category in dynamic_overrides:
            badge_name = dynamic_overrides[g.signal_category]
        else:
            badge_name = _prettify_signal_category(g.signal_category)
        badges.append(Badge(
            name=badge_name,
            color=g.color or "gray",
            qualifier=_strength_to_qualifier(g.strength),
            evidence=[_evidence(
                g.evidence_text or g.signal_category,
                confidence=g.confidence or "indicated",
            )],
        ))
    return badges


def select_pillar_2_badges(product: Product) -> dict[str, list[Badge]]:
    """Select Pillar 2 (Instructional Value) display badges for a product."""
    grades_by_dim = product.rubric_grades or {}
    return {
        "Product Complexity": _graded_signals_to_badges(grades_by_dim.get("product_complexity", [])),
        "Mastery Stakes": _graded_signals_to_badges(grades_by_dim.get("mastery_stakes", [])),
        "Lab Versatility": _graded_signals_to_badges(grades_by_dim.get("lab_versatility", [])),
        "Market Demand": _graded_signals_to_badges(grades_by_dim.get("market_demand", [])),
    }


def select_pillar_3_badges(company: CompanyAnalysis) -> dict[str, list[Badge]]:
    """Select Pillar 3 (Customer Fit) display badges for a company.

    Builds a dynamic_overrides map from `customer_fit_facts` so that generic
    signal_category labels get replaced by the vendor's actual named program
    when the researcher captured it. Frank 2026-04-08: "Instead of 'Customer
    Enablement Team' maybe logic should be to put a name like 'Cohesity
    Academy' on the badge." Falls back to the generic prettified label when
    the name fact is empty.
    """
    grades_by_dim = company.customer_fit_rubric_grades or {}

    # Dynamic overrides sourced from the Pillar 3 fact drawer. Keep names
    # under the badge character budget so the layout stays uniform; longer
    # author-supplied names get truncated at a word boundary.
    dyn: dict[str, str] = {}
    tc = company.customer_fit_facts.training_commitment if company.customer_fit_facts else None
    if tc and tc.customer_enablement_team_name:
        name = tc.customer_enablement_team_name.strip()
        if len(name) > _BADGE_NAME_MAX_CHARS:
            truncated = name[:_BADGE_NAME_MAX_CHARS]
            last_space = truncated.rfind(" ")
            name = truncated[:last_space] if last_space > 0 else truncated
        if name:
            dyn["customer_enablement_team"] = name

    return {
        "Training Commitment": _graded_signals_to_badges(
            grades_by_dim.get("training_commitment", []),
            dynamic_overrides=dyn,
        ),
        "Build Capacity": _graded_signals_to_badges(grades_by_dim.get("build_capacity", [])),
        "Delivery Capacity": _graded_signals_to_badges(grades_by_dim.get("delivery_capacity", [])),
        "Organizational DNA": _graded_signals_to_badges(grades_by_dim.get("organizational_dna", [])),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level: attach badges to Product / CompanyAnalysis
# ═══════════════════════════════════════════════════════════════════════════════

def _attach_badges_to_pillar(pillar: PillarScore, badges_by_dim: dict[str, list[Badge]]) -> None:
    """Mutate a PillarScore in place, populating the badges list on each dimension."""
    for dim in pillar.dimensions:
        dim.badges = badges_by_dim.get(dim.name, [])


def attach_badges_to_product(product: Product, company: CompanyAnalysis) -> None:
    """Populate Product.fit_score with display badges for Pillars 1, 2, and 3.

    Called after the Step 5 cutover flip so fit_score contains the authoritative
    Python-scored PillarScore objects. Badge selection is a post-scoring display
    concern — it does not modify scores, only populates the `badges` list on
    each DimensionScore.
    """
    p1_badges = select_pillar_1_badges(product)
    _attach_badges_to_pillar(product.fit_score.product_labability, p1_badges)

    p2_badges = select_pillar_2_badges(product)
    _attach_badges_to_pillar(product.fit_score.instructional_value, p2_badges)

    p3_badges = select_pillar_3_badges(company)
    _attach_badges_to_pillar(product.fit_score.customer_fit, p3_badges)
