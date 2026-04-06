"""Skillable Intelligence Platform — Prompt Generator.

Reads the scoring template (backend/prompts/scoring_template.md) and replaces
every {PLACEHOLDER} with formatted data from scoring_config.py.  The result
is the complete prompt the AI receives at runtime.

Primary function:
    generate_scoring_prompt() -> str

Validation:
    validate_generated_prompt(prompt) -> list[str]

Standalone usage:
    python -m backend.prompt_generator
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from backend import scoring_config as cfg

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template path
# ---------------------------------------------------------------------------
_TEMPLATE_DIR = Path(__file__).resolve().parent / "prompts"
_TEMPLATE_PATH = _TEMPLATE_DIR / "scoring_template.md"


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _format_skillable_capabilities() -> str:
    """Format SKILLABLE_CAPABILITIES as a bulleted list."""
    lines = []
    for cap in cfg.SKILLABLE_CAPABILITIES:
        lines.append(f"- **{cap.name}:** {cap.description}")
    return "\n".join(lines)


def _format_competitor_profiles() -> str:
    """Format COMPETITOR_PROFILES (the tuple of CompetitorProfile dataclasses)."""
    lines = []
    for cp in cfg.COMPETITOR_PROFILES:
        lines.append(f"### {cp.name}\n\n**Skillable advantage:** {cp.skillable_advantage}")
    # Also include decisive advantages
    lines.append("\n### Skillable Decisive Advantages\n")
    for adv in cfg.SKILLABLE_DECISIVE_ADVANTAGES:
        lines.append(f"- {adv}")
    return "\n\n".join(lines)


def _format_reasoning_sequence() -> str:
    """Format REASONING_SEQUENCE as numbered sections."""
    sections = []
    for step in cfg.REASONING_SEQUENCE:
        header = f"### Step {step.number}: {step.name}\n\n{step.instruction}"
        if step.skip_condition:
            header += f"\n\n*Skip condition:* {step.skip_condition}"
        sections.append(header)
    return "\n\n".join(sections)


def _format_pillar_structure() -> str:
    """Summary table of all 3 pillars with weights and dimensions."""
    lines = [
        "| Pillar | Weight | Level | Dimensions |",
        "|--------|--------|-------|------------|",
    ]
    for pillar in cfg.PILLARS:
        dim_names = ", ".join(d.name for d in pillar.dimensions)
        lines.append(
            f"| {pillar.name} | {pillar.weight}% | {pillar.level} | {dim_names} |"
        )
    return "\n".join(lines)


def _format_dimension_table(pillar: cfg.Pillar) -> str:
    """Detailed dimension table with badges and scoring for a single pillar."""
    sections = []
    for dim in pillar.dimensions:
        parts = [f"### {dim.name} ({dim.weight}%)\n"]
        parts.append(f"*{dim.question}*\n")
        if dim.notes:
            parts.append(f"{dim.notes}\n")

        # Badges
        if dim.badges:
            parts.append("**Badges:**\n")
            parts.append("| Badge | Colors |")
            parts.append("|-------|--------|")
            for badge in dim.badges:
                color_str = "; ".join(
                    f"{bc.color}: {bc.criterion}" for bc in badge.colors
                )
                parts.append(f"| {badge.name} | {color_str} |")
            parts.append("")

        # Scoring signals
        if dim.scoring_signals:
            parts.append("**Scoring Signals:**\n")
            parts.append("| Signal | Points | Description |")
            parts.append("|--------|--------|-------------|")
            for sig in dim.scoring_signals:
                parts.append(f"| {sig.name} | {sig.points:+d} | {sig.description} |")
            parts.append("")

        # Penalties
        if dim.penalties:
            parts.append("**Penalties:**\n")
            parts.append("| Penalty | Deduction | Description |")
            parts.append("|---------|-----------|-------------|")
            for pen in dim.penalties:
                parts.append(f"| {pen.name} | {pen.deduction:+d} | {pen.description} |")
            parts.append("")

        # Cap / floor
        if dim.cap is not None:
            parts.append(f"*Cap: {dim.cap}*\n")
        if dim.floor is not None:
            parts.append(f"*Floor: {dim.floor}*\n")

        sections.append("\n".join(parts))

    return "\n\n".join(sections)


def _format_provisioning_scoring_tiers() -> str:
    """Format provisioning scoring signals grouped by orchestration method."""
    prov_dim = cfg.PILLAR_PRODUCT_LABABILITY.dimensions[0]  # Provisioning
    lines = ["| Signal | Points | Description |",
             "|--------|--------|-------------|"]
    for sig in prov_dim.scoring_signals:
        lines.append(f"| {sig.name} | {sig.points} | {sig.description} |")
    return "\n".join(lines)


def _format_provisioning_penalties() -> str:
    """Format provisioning penalty table."""
    prov_dim = cfg.PILLAR_PRODUCT_LABABILITY.dimensions[0]
    lines = ["| Penalty | Deduction | Description |",
             "|---------|-----------|-------------|"]
    for pen in prov_dim.penalties:
        lines.append(f"| {pen.name} | {pen.deduction:+d} | {pen.description} |")
    return "\n".join(lines)


def _format_ceiling_flags() -> str:
    """Format ceiling flag table from CEILING_FLAGS dict.

    Each flag, when emitted by the AI, caps the Product Labability pillar
    score at the listed max_score. The math layer enforces this — the AI
    cannot bypass it by claiming a higher score.
    """
    lines = [
        "| Flag | Caps Product Labability at | Reason |",
        "|------|----------------------------|--------|",
    ]
    for flag, rules in cfg.CEILING_FLAGS.items():
        max_score = rules.get("max_score", "—")
        reason = rules.get("reason", "")
        lines.append(f"| `{flag}` | {max_score} | {reason} |")
    return "\n".join(lines)


def _format_evidence_standards() -> str:
    """Format evidence standards as numbered rules."""
    lines = []
    for i, es in enumerate(cfg.EVIDENCE_STANDARDS, 1):
        lines.append(f"{i}. **{es.rule}:** {es.description}")
    # Add the evidence format
    lines.append(f"\n**Evidence format:** `{cfg.EVIDENCE_FORMAT}`")
    lines.append(f"\n**Evidence ordering within dimension:** {' → '.join(cfg.EVIDENCE_ORDERING)}")
    return "\n".join(lines)


def _format_badge_colors() -> str:
    """Format the four badge colors."""
    lines = ["| Color | Meaning | Qualifier Labels |",
             "|-------|---------|------------------|"]
    for color, info in cfg.BADGE_COLORS.items():
        labels = ", ".join(info["qualifier_labels"])
        lines.append(f"| {color} | {info['meaning']} | {labels} |")
    return "\n".join(lines)


def _format_confidence_levels() -> str:
    """Format confidence level table."""
    lines = ["| Level | Meaning | Example |",
             "|-------|---------|---------|"]
    for cl in cfg.CONFIDENCE_LEVELS:
        lines.append(f"| {cl.level} | {cl.meaning} | {cl.example_phrasing} |")
    return "\n".join(lines)


def _format_badge_naming_principles() -> str:
    """Bullet list of badge naming principles derived from config patterns."""
    return "\n".join([
        "- Badge names are short noun phrases (2-4 words)",
        "- Use the canonical badge name exactly as listed — no synonyms, abbreviations, or variations",
        "- Qualifier labels (Strength, Opportunity, Risk, Blocker, Context) are appended after a pipe: `Badge Name | Qualifier`",
        "- Never create new badge names — if a signal does not match a canonical badge, use the closest match",
        "- Variable-driven badges include context after the qualifier (e.g., `Partner Ecosystem | Strength: ~500 ATPs`)",
        "",
        "**UNIVERSAL DISAMBIGUATION RULE — read carefully**",
        "",
        "When you have **more than one badge to emit for the same canonical name**, you must give every badge a unique name. Never emit the same canonical badge twice in one dimension.",
        "",
        "- **First occurrence**: keep the canonical badge name as-is (e.g., `Runs in Hyper-V`).",
        "- **Subsequent occurrences**: rename them using a more specific variable from the dimension's vocabulary, in this priority order:",
        "  1. **PREFERRED — pick a matching scoring signal name** from the dimension's `Scoring Signals` list (e.g., `Hyper-V: Standard`, `Hyper-V: CLI Scripting`, `Azure Cloud Slice: Entra ID SSO`). These names carry real point values and lift the score appropriately.",
        "  2. **FALLBACK — derive a specific label** from the qualifier and the actual finding (e.g., `Install Complexity`, `Multi-VM Topology`, `License Friction`). These don't lift the score but they prevent visual duplicates and make the evidence specific.",
        "",
        "**Why this matters**: the math layer credits scoring-signal names with real point values (e.g., `Hyper-V: Standard` = +30 in Provisioning) and falls back to color points for everything else. When you have a clean Hyper-V install at standard quality, you should emit `Runs in Hyper-V` AS THE FIRST BADGE plus `Hyper-V: Standard` AS A SECOND BADGE — that gives the user the friendly chip AND credits the +30 signal value.",
        "",
        "**Each dimension's scoring signals are listed in the dimension section below** under `Scoring Signals`. Use the EXACT signal name from that list when emitting a second badge. If no signal matches your finding, use the qualifier-derived fallback.",
    ])


def _format_lab_type_menu() -> str:
    """Format lab versatility menu with likely product types."""
    lines = ["| Lab Type | Description | Likely Product Types |",
             "|----------|-------------|---------------------|"]
    for lt in cfg.LAB_TYPE_MENU:
        lines.append(f"| {lt.name} | {lt.description} | {lt.likely_product_types} |")
    return "\n".join(lines)


def _format_category_priors() -> str:
    """Format category prior table."""
    lines = ["| Category | Points | Demand Level |",
             "|----------|--------|-------------|"]
    for cp in cfg.CATEGORY_PRIORS:
        lines.append(f"| {cp.category} | +{cp.points} | {cp.demand_level} |")
    return "\n".join(lines)


def _format_market_demand_ai_signals() -> str:
    """Format AI signal table from Market Demand dimension."""
    md_dim = cfg.PILLAR_INSTRUCTIONAL_VALUE.dimensions[3]  # Market Demand
    lines = ["| Signal | Points | Description |",
             "|--------|--------|-------------|"]
    for sig in md_dim.scoring_signals:
        if "category prior" not in sig.name.lower():
            lines.append(f"| {sig.name} | +{sig.points} | {sig.description} |")
    return "\n".join(lines)


def _format_technical_fit_multiplier() -> str:
    """Format multiplier table."""
    lines = ["| Score Range | Method | Multiplier |",
             "|------------|--------|------------|"]
    for m in cfg.TECHNICAL_FIT_MULTIPLIERS:
        lines.append(f"| {m.score_min}-{m.score_max} | {m.method} | {m.multiplier}x |")
    lines.append(f"\nDatacenter methods: {', '.join(cfg.DATACENTER_METHODS)}")
    return "\n".join(lines)


def _format_intelligence_signals() -> str:
    """Bullet list of intelligence signals from reasoning step 6."""
    step6 = None
    for step in cfg.REASONING_SEQUENCE:
        if step.number == 6:
            step6 = step
            break
    if not step6:
        return "- (Intelligence signals not configured)"
    # Parse the instruction into bullet points
    signals = [
        "M365 tenant provisioning (automated via Azure Cloud Slice)",
        "Entra ID SSO (zero credential management)",
        "Marketplace listings (Azure Marketplace, AWS Marketplace)",
        "IaC templates (Terraform, Bicep, ARM, CloudFormation)",
        "NFR / developer licenses available",
        "Existing competitor labs (CloudShare, Instruqt, Skytap)",
        "Existing Skillable labs (expansion opportunity)",
        "Deployment guides and installation documentation",
        "xAPI / LTI requirements",
        "Exam delivery provider integrations (Pearson VUE, Certiport, PSI, Certiverse)",
        "Flagship events and user conferences",
    ]
    return "\n".join(f"- {s}" for s in signals)


def _format_delivery_patterns() -> str:
    """Format delivery pattern signals."""
    lines = []
    for dp in cfg.DELIVERY_PATTERNS:
        lines.append(f"- **{dp.name}:** {dp.guidance}")
    return "\n".join(lines)


def _format_consumption_motions() -> str:
    """Format consumption motion table."""
    lines = ["| Motion | Adoption Range | Description |",
             "|--------|---------------|-------------|"]
    for m in cfg.CONSUMPTION_MOTIONS:
        pct_range = f"{m.adoption_ceiling_low:.0%}-{m.adoption_ceiling_high:.0%}"
        lines.append(f"| {m.label} | {pct_range} | {m.description} |")
    return "\n".join(lines)


def _format_adoption_ceilings() -> str:
    """Format adoption ceiling rules."""
    return (
        f"- **Events & Conferences:** Never exceed {cfg.ADOPTION_CEILING_EVENTS:.0%} adoption rate\n"
        f"- **All other motions:** Never exceed {cfg.ADOPTION_CEILING_NON_EVENTS:.0%} adoption rate"
    )


def _format_rate_tables() -> str:
    """Format rate tier table."""
    lines = ["| Delivery Path | Rate Low | Rate High | Notes |",
             "|--------------|----------|-----------|-------|"]
    for rt in cfg.RATE_TABLES:
        lines.append(
            f"| {rt.delivery_path} | ${rt.rate_low:.2f}/hr | ${rt.rate_high:.2f}/hr | {rt.notes} |"
        )
    return "\n".join(lines)


def _format_product_category_rate_priors() -> str:
    """Format category rate priors."""
    lines = ["| Category | Typical VMs | Rate Tier | Rate Range | Seat Time | Examples |",
             "|----------|-------------|-----------|------------|-----------|----------|"]
    for p in cfg.PRODUCT_CATEGORY_RATE_PRIORS:
        lines.append(
            f"| {p['category']} | {p['typical_vms']} | {p['rate_tier']} "
            f"| {p['rate_range']} | {p['seat_time']} | {p['examples']} |"
        )
    return "\n".join(lines)


def _format_contact_guidance() -> str:
    """Format contact guidance from the CONTACT_GUIDANCE dict."""
    cg = cfg.CONTACT_GUIDANCE
    parts = []

    parts.append("### Decision Maker Titles\n")
    for title in cg["decision_maker_titles"]:
        parts.append(f"- {title}")
    parts.append(f"\n**Test:** {cg['decision_maker_test']}\n")

    parts.append("### NOT Decision Makers\n")
    for title in cg["not_decision_makers"]:
        parts.append(f"- {title}")

    parts.append("\n### Influencer Titles\n")
    for title in cg["influencer_titles"]:
        parts.append(f"- {title}")
    parts.append(f"\n**Minimum level:** {cg['influencer_minimum_level']}")
    parts.append(f"\n**NOT influencers:** {cg['not_influencers']}")

    parts.append(f"\n**Exclude entirely:** {cg['exclude_entirely']}")
    parts.append(f"\n**Alumni signal:** {cg['alumni_signal']}")
    parts.append(f"\n**Unknown fallback:** {cg['unknown_fallback']}")

    return "\n".join(parts)


def _format_locked_vocabulary() -> str:
    """Format locked terms table."""
    lines = ["| Use This | Never This |",
             "|----------|------------|"]
    for lt in cfg.LOCKED_VOCABULARY:
        not_this = ", ".join(lt.not_this) if lt.not_this else "—"
        lines.append(f"| {lt.use_this} | {not_this} |")
    return "\n".join(lines)


def _format_canonical_badge_names() -> str:
    """Two grouped lists of allowed badge names per dimension:

    - **Canonical badges** — visual chip vocabulary (e.g., `Runs in Hyper-V`).
      The AI should always use one of these as the FIRST badge for any given
      finding to keep the UI consistent.
    - **Scoring signals** — point-bearing names that map to a specific
      quality/intensity within a dimension (e.g., `Hyper-V: Standard` = +30).
      The AI should emit a SECOND badge using one of these whenever there's
      specific quality nuance to capture for scoring.

    Grouping per-dimension makes it obvious which signals belong to which
    canonical badge, and the AI can pair them naturally.
    """
    sections: list[str] = []
    seen_badges: set[str] = set()
    seen_signals: set[str] = set()

    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            badge_names = [b.name for b in dim.badges if b.name not in seen_badges]
            signal_names = [s.name for s in dim.scoring_signals if s.name not in seen_signals]
            if not badge_names and not signal_names:
                continue
            section = [f"#### {dim.name}"]
            if badge_names:
                section.append("Canonical badges (use as the FIRST badge):")
                for n in badge_names:
                    section.append(f"- {n}")
                    seen_badges.add(n)
            if signal_names:
                section.append("")
                section.append("Scoring signals (use as a SECOND badge for nuance):")
                for n in signal_names:
                    section.append(f"- {n}")
                    seen_signals.add(n)
            sections.append("\n".join(section))

    return "\n\n".join(sections)


def _format_output_json_template() -> str:
    """Generate the JSON output format template."""
    # Build dimension scoring entries for each pillar
    pillar_sections = {}
    for i, pillar in enumerate(cfg.PILLARS, 1):
        dim_entries = []
        for dim in pillar.dimensions:
            dim_entries.append(
                f'        "{dim.name.lower().replace(" ", "_")}": {{"score": 0, "summary": "..."}}'
            )
        pillar_sections[i] = ",\n".join(dim_entries)

    # Build the first motion label
    first_motion = cfg.CONSUMPTION_MOTIONS[0].label if cfg.CONSUMPTION_MOTIONS else "Motion"

    template = """{
  "product_name": "...",
  "company_name": "...",
  "organization_type": "<""" + "|".join(ot.type_key for ot in cfg.ORGANIZATION_TYPES) + """>",
  "organization_label": "<""" + "|".join(ot.display_label for ot in cfg.ORGANIZATION_TYPES) + """>",
  "deployment_model": "<""" + "|".join(cfg.DEPLOYMENT_MODELS.keys()) + """>",
  "orchestration_method": "<Hyper-V|ESX|Container|Azure Cloud Slice|AWS Cloud Slice|Custom API|Simulation>",
  "product_category": "...",
  "product_subcategory": "...",
  "user_personas": ["..."],
  "customer_motivations": [
    {"name": "...", "core_drive": "...", "stakes": "...", "learner_outcome": "..."}
  ],
  "pillar_scores": {
    \"""" + cfg.PILLARS[0].name + """": {
      "score": 0,
      "weight": """ + str(cfg.PILLARS[0].weight) + """,
      "dimensions": {
""" + pillar_sections[1] + """
      }
    },
    \"""" + cfg.PILLARS[1].name + """": {
      "score": 0,
      "weight": """ + str(cfg.PILLARS[1].weight) + """,
      "dimensions": {
""" + pillar_sections[2] + """
      }
    },
    \"""" + cfg.PILLARS[2].name + """": {
      "score": 0,
      "weight": """ + str(cfg.PILLARS[2].weight) + """,
      "dimensions": {
""" + pillar_sections[3] + """
      }
    }
  },
  "fit_score": 0,
  "technical_fit_multiplier": 1.0,
  "evidence": {
    "<dimension_name>": [
      {
        "badge": "...",
        "qualifier": "Strength|Opportunity|Risk|Blocker|Context",
        "color": "green|gray|amber|red",
        "claim": "...",
        "confidence": "confirmed|indicated|inferred",
        "source_url": "...",
        "source_title": "..."
      }
    ]
  },
  "poor_match_flags": ["..."],
  "lab_types": ["..."],
  "lab_concepts": [
    {"title": "...", "description": "...", "persona": "...", "phase": "..."}
  ],
  "recommendations": [
    {"label": "...", "suffix": null, "text": "..."}
  ],
  "contacts": {
    "decision_maker": {"name": "...", "title": "...", "linkedin_url": "..."},
    "influencer": {"name": "...", "title": "...", "linkedin_url": "..."}
  },
  "consumption_potential": {
    "motions": [
      {
        "label": \"""" + first_motion + """",
        "population_low": 0,
        "population_high": 0,
        "hours_low": 0,
        "hours_high": 0,
        "adoption_pct": 0.0,
        "rate_low": 0.0,
        "rate_high": 0.0,
        "acv_low": 0,
        "acv_high": 0
      }
    ],
    "total_acv_low": 0,
    "total_acv_high": 0,
    "acv_tier": "high|medium|low"
  },
  "verdict": {
    "label": "...",
    "color": "...",
    "description": "..."
  },
  "proserv_opportunity": false,
  "summary": "..."
}"""
    return template


# ═══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDER MAP
# ═══════════════════════════════════════════════════════════════════════════════

def _build_placeholder_map() -> dict[str, str]:
    """Build the complete map of placeholder names to formatted values."""
    p1 = cfg.PILLAR_PRODUCT_LABABILITY
    p2 = cfg.PILLAR_INSTRUCTIONAL_VALUE
    p3 = cfg.PILLAR_CUSTOMER_FIT

    partner_lms_names = [
        lms.name for lms in cfg.CANONICAL_LMS_PARTNERS if lms.is_skillable_partner
    ]

    placeholders: dict[str, str] = {
        # Skillable capabilities and competitors
        "SKILLABLE_CAPABILITIES": _format_skillable_capabilities(),
        "COMPETITOR_PROFILES": _format_competitor_profiles(),

        # Reasoning sequence
        "REASONING_SEQUENCE": _format_reasoning_sequence(),

        # Pillar structure
        "PILLAR_STRUCTURE": _format_pillar_structure(),

        # Pillar 1
        "PILLAR_1_NAME": p1.name,
        "PILLAR_1_WEIGHT": str(p1.weight),
        "PILLAR_1_QUESTION": p1.question,
        "PILLAR_1_DIMENSIONS": _format_dimension_table(p1),

        # Pillar 2
        "PILLAR_2_NAME": p2.name,
        "PILLAR_2_WEIGHT": str(p2.weight),
        "PILLAR_2_QUESTION": p2.question,
        "PILLAR_2_DIMENSIONS": _format_dimension_table(p2),

        # Pillar 3
        "PILLAR_3_NAME": p3.name,
        "PILLAR_3_WEIGHT": str(p3.weight),
        "PILLAR_3_QUESTION": p3.question,
        "PILLAR_3_DIMENSIONS": _format_dimension_table(p3),

        # Provisioning details
        "PROVISIONING_SCORING_TIERS": _format_provisioning_scoring_tiers(),
        "PROVISIONING_PENALTIES": _format_provisioning_penalties(),

        # Ceiling flags
        "CEILING_FLAGS": _format_ceiling_flags(),
        "CEILING_FLAGS_SAAS_ONLY_MAX": str(cfg.CEILING_FLAGS["saas_only"].get("max_score", "N/A")),
        "CEILING_FLAGS_MULTI_TENANT_MAX": str(cfg.CEILING_FLAGS["multi_tenant_only"].get("max_score", "N/A")),

        # Evidence and badges
        "EVIDENCE_STANDARDS": _format_evidence_standards(),
        "BADGE_COLORS": _format_badge_colors(),
        "CONFIDENCE_LEVELS": _format_confidence_levels(),
        "BADGE_NAMING_PRINCIPLES": _format_badge_naming_principles(),

        # Lab types and versatility
        "LAB_TYPE_MENU": _format_lab_type_menu(),
        "LAB_VERSATILITY_CAP": str(
            cfg.PILLAR_INSTRUCTIONAL_VALUE.dimensions[2].cap or 15  # Lab Versatility
        ),

        # Category priors and market demand
        "CATEGORY_PRIORS": _format_category_priors(),
        "MARKET_DEMAND_AI_SIGNALS": _format_market_demand_ai_signals(),

        # Partner and platform lists
        "SKILLABLE_PARTNER_LMS_LIST": ", ".join(partner_lms_names),
        "CANONICAL_LAB_PLATFORMS": ", ".join(cfg.CANONICAL_LAB_PLATFORMS),

        # Technical fit multiplier
        "TECHNICAL_FIT_MULTIPLIER": _format_technical_fit_multiplier(),

        # Intelligence signals and delivery patterns
        "INTELLIGENCE_SIGNALS": _format_intelligence_signals(),
        "DELIVERY_PATTERNS": _format_delivery_patterns(),

        # Consumption motions and rates
        "CONSUMPTION_MOTIONS": _format_consumption_motions(),
        "ADOPTION_CEILINGS": _format_adoption_ceilings(),
        "ADOPTION_CEILING_EVENTS": f"{cfg.ADOPTION_CEILING_EVENTS:.0%}",
        "ADOPTION_CEILING_NON_EVENTS": f"{cfg.ADOPTION_CEILING_NON_EVENTS:.0%}",
        "RATE_TABLES": _format_rate_tables(),
        "PRODUCT_CATEGORY_RATE_PRIORS": _format_product_category_rate_priors(),

        # Contact guidance
        "CONTACT_GUIDANCE": _format_contact_guidance(),

        # Locked vocabulary and canonical names
        "LOCKED_VOCABULARY": _format_locked_vocabulary(),
        "CANONICAL_BADGE_NAMES": _format_canonical_badge_names(),

        # Output format
        "OUTPUT_JSON_TEMPLATE": _format_output_json_template(),

        # Enum-style values for the JSON template references
        "ORGANIZATION_TYPE_VALUES": "|".join(ot.type_key for ot in cfg.ORGANIZATION_TYPES),
        "DEPLOYMENT_MODEL_VALUES": "|".join(cfg.DEPLOYMENT_MODELS.keys()),
        "ORCHESTRATION_METHOD_VALUES": "Hyper-V|ESX|Container|Azure Cloud Slice|AWS Cloud Slice|Custom API|Simulation",
        "MOTION_LABELS": cfg.CONSUMPTION_MOTIONS[0].label if cfg.CONSUMPTION_MOTIONS else "",

        # AWS service lists — not defined as separate constants in config,
        # so provide a sensible reference
        "AWS_SUPPORTED_SERVICES": "See Skillable AWS Cloud Slice supported services list (maintained separately)",
        "AWS_UNSUPPORTED_SERVICES": "See Skillable AWS Cloud Slice unsupported services list (maintained separately)",
    }

    return placeholders


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def generate_scoring_prompt() -> str:
    """Generate the complete scoring prompt by merging template + config.

    Reads the template from backend/prompts/scoring_template.md, replaces
    every {PLACEHOLDER} with formatted data from scoring_config, and returns
    the complete prompt string ready to send to the AI.

    Returns:
        The fully rendered prompt string.

    Raises:
        FileNotFoundError: If the template file is missing.
    """
    # Read template
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")

    # Build placeholder map
    placeholders = _build_placeholder_map()

    # Replace all placeholders
    prompt = template
    for key, value in placeholders.items():
        token = "{" + key + "}"
        if token in prompt:
            prompt = prompt.replace(token, value)
        else:
            logger.debug("Placeholder %s not found in template (may be optional)", key)

    # Check for any remaining unreplaced placeholders and warn
    remaining = re.findall(r"\{([A-Z][A-Z0-9_]+)\}", prompt)
    for placeholder in remaining:
        if placeholder not in placeholders:
            logger.warning(
                "Unresolved placeholder {%s} in generated prompt — "
                "no matching config value found",
                placeholder,
            )

    return prompt


def validate_generated_prompt(prompt: str) -> list[str]:
    """Check the generated prompt for any remaining {PLACEHOLDER} strings.

    Args:
        prompt: The generated prompt string to validate.

    Returns:
        A list of unresolved placeholder names. Empty list means all
        placeholders were successfully replaced.
    """
    # Match {UPPER_CASE_WITH_UNDERSCORES} patterns — the placeholder convention
    matches = re.findall(r"\{([A-Z][A-Z0-9_]+)\}", prompt)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unresolved: list[str] = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unresolved.append(m)
    return unresolved


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    prompt = generate_scoring_prompt()
    issues = validate_generated_prompt(prompt)
    print(prompt)
    print("\n" + "=" * 60)
    print(f"Prompt length: {len(prompt)} chars")
    if issues:
        print(f"WARNING — Unresolved placeholders: {issues}")
    else:
        print("All placeholders resolved successfully.")
