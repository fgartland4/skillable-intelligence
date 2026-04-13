"""Post-filters — deterministic guardrails for AI output quality.

The AI does the research. Deterministic code enforces the rules.
Every locked rule that the AI sometimes drifts on gets a post-filter
here. These run in milliseconds after the AI calls return — no
additional API calls, no web searches, no tokens burned.

Architecture layer: Intelligence (shared). All three tools call
these filters. Per CLAUDE.md Layer Discipline.

Two entry points:
  1. filter_discovery(discovery_data) — runs after discovery parsing
  2. filter_scoring(product, company_analysis) — runs after scoring

GP4: Self-Evident Design — one file, one audit point for all
deterministic guardrails.
"""

import logging
import scoring_config as cfg

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWN DELIVERY PLATFORM PATTERNS
#
# These are lab platforms, LMS platforms, or learning delivery tools that
# belong in company_signals.lab_platform, NOT in the product list.
# Case-insensitive substring matching.
# ═══════════════════════════════════════════════════════════════════════════════

_DELIVERY_PLATFORM_PATTERNS: tuple[str, ...] = (
    # CompTIA
    "certmaster",
    # EC-Council
    "ilabs",
    "ilearn",
    # Pluralsight / A Cloud Guru
    "a cloud guru",
    "cloud guru",
    # Generic lab/LMS platform indicators
    "lab platform",
    "practice platform",
    "practice environment",
    "learning management",
    "lms platform",
    # Specific LMS products (when found as sub-products of non-LMS companies)
    "canvas lms",
    "blackboard",
    "moodle",
)

# Products that exactly match these names (case-insensitive) are always
# delivery platforms regardless of context.
_DELIVERY_PLATFORM_EXACT: set[str] = {
    "certmaster learn",
    "certmaster labs",
    "certmaster practice",
    "certmaster ce",
    "a cloud guru",
    "ilabs",
    "ilearn",
}

# Valid product categories — "Other" is never allowed.
_VALID_CATEGORIES: set[str] = {
    "Cloud Infrastructure",
    "Cybersecurity",
    "Data Protection",
    "Networking / SDN",
    "DevOps",
    "Application Development",
    "Data & Analytics",
    "Data Science & Engineering",
    "Collaboration",
    "ERP",
    "CRM",
    "Healthcare IT",
    "Industrial / OT",
    "Content Management",
    "Legal Tech",
    "FinTech",
    "AI Platforms & Tooling",
    "Infrastructure / Virtualization",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DISCOVERY POST-FILTERS
# ═══════════════════════════════════════════════════════════════════════════════

def filter_discovery_products(
    products: list[dict],
    company_signals: dict,
) -> list[dict]:
    """Filter discovered products — remove delivery platforms, fix categories.

    Mutates company_signals["lab_platform"] when delivery platforms are
    detected. Returns the filtered product list (may be shorter than input).
    """
    filtered: list[dict] = []
    platforms_found: list[str] = []

    for p in products:
        name = (p.get("name") or "").strip()
        name_lower = name.lower()

        # ── Delivery platform check ──
        is_platform = False

        # Exact match
        if name_lower in _DELIVERY_PLATFORM_EXACT:
            is_platform = True

        # Substring match
        if not is_platform:
            for pattern in _DELIVERY_PLATFORM_PATTERNS:
                if pattern in name_lower:
                    is_platform = True
                    break

        if is_platform:
            platforms_found.append(name)
            log.info("post_filter: moved '%s' to lab_platform (delivery platform)", name)
            continue

        # ── Category validation ──
        category = (p.get("category") or "").strip()
        if category == "Other" or category not in _VALID_CATEGORIES:
            # Try to infer from subcategory or description
            log.warning(
                "post_filter: product '%s' has invalid category '%s' — "
                "flagging for review", name, category,
            )
            # Don't remove the product — just flag it. The researcher
            # should have categorized it correctly. A missing category
            # is better than a missing product.

        filtered.append(p)

    # Write discovered platforms to company_signals
    if platforms_found:
        existing = company_signals.get("lab_platform") or ""
        new_platforms = ", ".join(platforms_found)
        if existing:
            company_signals["lab_platform"] = f"{existing}, {new_platforms}"
        else:
            company_signals["lab_platform"] = new_platforms

    if len(filtered) < len(products):
        log.info(
            "post_filter: removed %d delivery platforms from product list "
            "(%d → %d products)",
            len(products) - len(filtered), len(products), len(filtered),
        )

    return filtered


def validate_deployment_model(product: dict) -> None:
    """Fix deployment_model contradictions in place.

    If runs_as_saas_only is true in the facts but deployment_model says
    "installable", the facts win — the product has an installer.
    """
    facts = product.get("product_labability_facts") or {}
    prov = facts.get("provisioning") or {}

    deploy = (product.get("deployment_model") or "").lower()
    runs_installable = prov.get("runs_as_installable", False)
    runs_saas_only = prov.get("runs_as_saas_only", False)

    if deploy == "saas-only" and runs_installable:
        product["deployment_model"] = "hybrid"
        log.info(
            "post_filter: '%s' deployment_model corrected saas-only → hybrid "
            "(runs_as_installable=true in facts)",
            product.get("name", "?"),
        )
    elif deploy == "installable" and runs_saas_only and not runs_installable:
        product["deployment_model"] = "saas-only"
        log.info(
            "post_filter: '%s' deployment_model corrected installable → saas-only "
            "(runs_as_saas_only=true, runs_as_installable=false in facts)",
            product.get("name", "?"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIENCE SANITY POST-FILTERS
# ═══════════════════════════════════════════════════════════════════════════════

# Companies large enough that install_base > 50M is plausible
_MEGA_SCALE_COMPANIES: set[str] = {
    "microsoft", "google", "apple", "meta", "amazon", "salesforce",
    "adobe", "oracle", "sap",
}


def filter_audience_estimates(
    acv_potential: dict,
    company_name: str = "",
) -> None:
    """Sanity-check audience estimates in ACV motions. Mutates in place.

    Catches:
    - install_base > 50M for non-mega-scale companies
    - employee_subset > install_base (flipped)
    - Any single motion with unreasonable population
    """
    motions = acv_potential.get("motions")
    if not isinstance(motions, list):
        return

    is_mega = company_name.lower().strip() in _MEGA_SCALE_COMPANIES

    customer_motion = None
    employee_motion = None

    for m in motions:
        if not isinstance(m, dict):
            continue
        label = m.get("label") or m.get("rationale") or ""

        if "Customer Training" in label:
            customer_motion = m
        elif "Employee Training" in label:
            employee_motion = m

        # Cap unreasonable populations for non-mega companies
        pop = float(m.get("population_low") or 0)
        if pop > 50_000_000 and not is_mega:  # magic-allowed: 50M sanity cap
            log.warning(
                "post_filter: capping population for '%s' from %.0f to 50M",
                label, pop,
            )
            m["population_low"] = 50_000_000  # magic-allowed: 50M sanity cap
            m["population_high"] = 50_000_000  # magic-allowed: 50M sanity cap

    # Swap if employee > customer (likely flipped)
    if customer_motion and employee_motion:
        cust_pop = float(customer_motion.get("population_low") or 0)
        emp_pop = float(employee_motion.get("population_low") or 0)
        if emp_pop > cust_pop and cust_pop > 0:
            log.warning(
                "post_filter: swapping customer/employee populations "
                "(employee %.0f > customer %.0f — likely flipped)",
                emp_pop, cust_pop,
            )
            customer_motion["population_low"], employee_motion["population_low"] = (
                employee_motion["population_low"], customer_motion["population_low"],
            )
            customer_motion["population_high"], employee_motion["population_high"] = (
                employee_motion["population_high"], customer_motion["population_high"],
            )


def filter_acv_motions(acv_potential: dict, company_name: str = "") -> None:
    """Cap unreasonable per-motion ACV values. Mutates in place.

    If any single motion produces more than $50M annually for a
    non-mega-scale company, cap it. This catches inflated audience
    estimates that slip through the population filter.
    """
    motions = acv_potential.get("motions")
    if not isinstance(motions, list):
        return

    is_mega = company_name.lower().strip() in _MEGA_SCALE_COMPANIES
    acv_cap = 50_000_000  # magic-allowed: $50M per-motion sanity cap

    for m in motions:
        if not isinstance(m, dict):
            continue
        acv_low = float(m.get("acv_low") or 0)
        if acv_low > acv_cap and not is_mega:
            label = m.get("label") or "?"
            log.warning(
                "post_filter: capping ACV for motion '%s' from $%.0f to $%.0f",
                label, acv_low, acv_cap,
            )
            # Scale down proportionally
            ratio = acv_cap / acv_low if acv_low > 0 else 1
            m["population_low"] = int(float(m.get("population_low") or 0) * ratio)
            m["population_high"] = int(float(m.get("population_high") or 0) * ratio)
