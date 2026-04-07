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
    """Badge naming principles, including the universal META-PRINCIPLE
    that badge names must be canonical vocabulary entries with
    product-specific details living in the evidence payload on hover.
    """
    return "\n".join([
        "## META-PRINCIPLE — read this first, apply it everywhere",
        "",
        "**Badge name = canonical vocabulary entry. Product-specific details live in the evidence payload on hover, NEVER in the badge name itself.**",
        "",
        "Examples of the rule in action:",
        "",
        "| ❌ WRONG (product-specific, AI-invented, or topic-label) | ✅ RIGHT (canonical name + evidence on hover) |",
        "|---|---|",
        "| `ePO Admin Credential` | Badge: `Cred Recycling` · Evidence: 'ePO administrator credentials can be recycled between learners...' |",
        "| `ePO API Scoring` | Badge: `Scoring API` · Evidence: 'ePO REST API enables programmatic state validation...' |",
        "| `REST API Surface` | Badge: `Scoring API` · Evidence: 'Diligent publishes a REST API at developer.diligent.com...' |",
        "| `No Sandbox API` (AI-invented) | Badge: `Sandbox API` (red) · Evidence: 'No public REST API documented for per-learner provisioning...' |",
        "| `Deployment Model` (topic label) | (don't emit — deployment model is discovery metadata, not a badge) |",
        "| `Shared Tenant Cleanup` | Badge: `Manual Teardown` (red) · Evidence: 'No vendor cleanup API; tenant state must be manually reset...' |",
        "",
        "**The rule:**",
        "",
        "- **NEVER put a product name in a badge name** (Trellix, Workday, Cohesity, ePO, Diligent — any vendor or product noun). Product names live in evidence on hover.",
        "- **NEVER lead the evidence `claim` field with a vendor product name in the bold prefix.** The bold prefix at the start of an evidence claim renders prominently in the dossier and is visible like a sub-heading. Use a generic descriptive label there, NOT a product-specific term: ❌ `**ePO REST API | Strength:** ...`  ✅ `**Lifecycle API Coverage | Strength:** Trellix ePO exposes a REST API ...`. The vendor name belongs in the body of the claim, not in its title bar.",
        "- **NEVER use a topic label as a badge name** (`Deployment Model`, `REST API Surface`, `Self Hosted Option`). The badge is the *finding*, not the *category*.",
        "- **NEVER invent a badge name** that's not in the canonical vocabulary listed below. If the finding doesn't fit any canonical, the right move is usually to put the finding in evidence on a related canonical, or skip emitting a badge for it.",
        "- **NEVER use a positive canonical name for a negative finding** (`Runs in Azure | Risk: No Marketplace Listing` is a polarity error — `Runs in Azure` is for confirmed Azure-native viability, not its absence).",
        "- **NEVER credit the same physical mechanism in two different dimensions.** If snapshot revert wipes lab state, that earns `Datacenter` (or `Automatic (VM/Container)`) in **Teardown** — period. It does NOT also earn `Cred Recycling` in **Lab Access**, even though the credentials happen to disappear with the rest of the VM. `Cred Recycling` requires the product to expose a real credential reset mechanism (API endpoint, account reset call, user-management surface). Side-effects of the platform's teardown do not qualify. The same rule applies in reverse: a real credential reset API earns `Cred Recycling` in Lab Access — it does NOT additionally earn a Teardown credit just because resetting credentials wipes some user state.",
        "",
        "## Standard naming",
        "",
        "- Badge names are short noun phrases (2-4 words) drawn from the canonical vocabulary listed below, by dimension.",
        "- Use the canonical badge name exactly as listed — no synonyms, abbreviations, variations, or pluralization changes.",
        "- Qualifier labels (Strength, Opportunity, Risk, Blocker, Context) are appended after a pipe: `Badge Name | Qualifier`",
        "- Variable-driven badges include the variable in the evidence text after the qualifier (e.g., `Partner Ecosystem | Strength:` followed by '~500 ATPs across 50 countries...').",
        "",
        "## One badge per finding — never duplicate canonical names",
        "",
        "If you have two distinct findings about the same topic (e.g., 'clean Hyper-V install' AND 'cluster init time exceeds 30 min'), emit them as **two distinct canonical badges**, not two badges with the same name:",
        "",
        "- ✅ `Runs in Hyper-V` (green) + `Pre-Instancing` (green opportunity for the slow init)",
        "- ❌ `Runs in Hyper-V` (green) + `Runs in Hyper-V` (amber)",
        "",
        "If you can't find a second canonical that fits, fold the second finding into the evidence on the first badge. Never emit the same canonical name twice in one dimension.",
        "",
        "## Flat-tier scoring",
        "",
        "There are no quality tier modifiers (`Hyper-V: Standard`, `Hyper-V: Moderate`, `Hyper-V: Weak`) — those have been retired. Each canonical badge earns its full base credit when emitted green. Friction is expressed via SEPARATE friction badges (`GPU Required`, `Pre-Instancing`, etc.) that the math layer combines with the green credit. The user sees one clean canonical chip, not two badges that look the same.",
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


def _format_iv_master_category_list() -> str:
    """Format the master category list for Pillar 2 baseline lookup.

    Derived from `cfg.IV_CATEGORY_BASELINES.keys()` — the AUTHORITATIVE
    source for the master category taxonomy.  Any add / rename in
    scoring_config.py propagates to the AI prompt automatically.  This
    is the Define-Once seam between the scoring math layer and the AI
    prompt: they read from the same config data at generation time.
    """
    # Ordered buckets for readability — Unknown last, Social/Entertainment
    # just before it.  Every other category is alphabetized within its
    # natural group.  Order is cosmetic only; the AI may emit any key.
    all_categories = list(cfg.IV_CATEGORY_BASELINES.keys())
    unknown_label = cfg.UNKNOWN_CLASSIFICATION

    # Split off the special fallbacks
    special = [c for c in all_categories if c == unknown_label or "Social" in c]
    regular = [c for c in all_categories if c not in special]

    lines = [
        "| Category | Use for |",
        "|---|---|",
    ]
    for cat in regular:
        lines.append(f"| `{cat}` | Products in the {cat} space |")
    for cat in special:
        if cat == unknown_label:
            lines.append(f"| `{cat}` | Genuinely novel or multi-category products — triggers the classification review flag |")
        else:
            lines.append(f"| `{cat}` | Consumer social / entertainment platforms with no professional training market (Facebook, Instagram, TikTok, Netflix, Spotify) |")
    return "\n".join(lines)


def _format_org_type_values() -> str:
    """Format the AI-emitted organization_type values.

    The AI must emit one of these lowercase snake_case strings.  The math
    layer normalizes to the human-readable baseline keys via
    `cfg.ORG_TYPE_NORMALIZATION`.  Both directions of the mapping come
    from the same config dict.
    """
    lines = [
        "| `organization_type` (emit this) | Normalizes to | Example companies |",
        "|---|---|---|",
    ]
    example_by_key = {
        "ENTERPRISE SOFTWARE": "Microsoft, SAP, Oracle, Salesforce, Workday, Cisco",
        "SOFTWARE": "Category-specific vendors (Trellix, Cohesity, Nutanix, Hyland)",
        "TRAINING ORG": "CompTIA, SANS, EC-Council, Cybrary, ISACA, Skillsoft",
        "ACADEMIC": "Universities, community colleges, WGU, SLU",
        "SYSTEMS INTEGRATOR": "Deloitte, Accenture, Cognizant, TCS, Infosys",
        "PROFESSIONAL SERVICES": "Consultancies with training practices",
        "CONTENT DEVELOPMENT": "GP Strategies, el-Training firms",
        "LMS PROVIDER": "Cornerstone, Docebo, SAP SuccessFactors Learning",
        "TECH DISTRIBUTOR": "Ingram, CDW, Arrow, Synnex",
    }
    # Use insertion order of ORG_TYPE_NORMALIZATION to produce a stable table.
    for raw, normalized in cfg.ORG_TYPE_NORMALIZATION.items():
        example = example_by_key.get(normalized, "")
        lines.append(f"| `{raw}` | {normalized} | {example} |")
    return "\n".join(lines)


def _format_cf_penalty_signals() -> str:
    """Format all CF penalty signal categories as reference tables.

    Derived from `cfg.CF_PENALTY_SIGNALS`.  The AI reads these tables to
    know which negative signal categories are valid for each CF dimension
    and what the exact penalty hit is.  Grouped by dimension for clarity.
    """
    # Group penalties by dimension key
    by_dimension: dict[str, list[cfg.PenaltySignal]] = {}
    for p in cfg.CF_PENALTY_SIGNALS:
        by_dimension.setdefault(p.dimension, []).append(p)

    # Friendly dimension labels for the headings — derived from cfg.PILLARS
    dim_labels: dict[str, str] = {}
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            dim_labels[dim.name.lower().replace(" ", "_")] = dim.name

    lines: list[str] = []
    for dim_key, penalties in by_dimension.items():
        label = dim_labels.get(dim_key, dim_key)
        lines.append(f"**{label} penalties:**")
        lines.append("")
        lines.append("| signal_category | Color | Hit | Badge label | When to fire |")
        lines.append("|---|---|---|---|---|")
        for p in penalties:
            lines.append(
                f"| `{p.category}` | {p.color} | −{p.hit} | `{p.badge_name}` | {p.description} |"
            )
        lines.append("")
    return "\n".join(lines).strip()


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


def _format_pillar_rubrics(pillar: cfg.Pillar) -> str:
    """Format the rubric model for a Pillar 2 or Pillar 3 pillar.

    For each dimension that has a rubric, emit:
      - Dimension name + cap + question
      - The strength tier table (strong / moderate / weak with point values + criteria)
      - IS / IS NOT routing boundaries
      - signal_category list the AI must pick from
    """
    sections: list[str] = []
    for dim in pillar.dimensions:
        if dim.rubric is None:
            continue
        rubric = dim.rubric
        cap = dim.cap if dim.cap is not None else dim.weight

        section = [
            f"### {dim.name} (cap {cap})",
            "",
            f"*{dim.question}*",
            "",
            "**Strength tiers (rubric — math credits by strength × dimension):**",
            "",
            "| Strength | Worth | Criterion |",
            "|---|---|---|",
        ]
        for tier in rubric.tiers:
            criterion = tier.criterion.replace("|", "\\|")
            worth = "don't emit" if tier.points == 0 and tier.strength == "weak" else f"+{tier.points}"
            section.append(f"| **{tier.strength}** | {worth} | {criterion} |")
        section.append("")

        section.append("**This dimension IS about:**")
        for item in rubric.is_about:
            section.append(f"- {item}")
        section.append("")

        section.append("**This dimension IS NOT about (do not route findings here):**")
        for item in rubric.is_not_about:
            section.append(f"- ❌ {item}")
        section.append("")

        section.append("**signal_category — pick exactly ONE per badge from this list:**")
        section.append("")
        for cat in rubric.signal_categories:
            section.append(f"- `{cat}`")
        section.append("")

        if dim.notes:
            section.append(f"*Note:* {dim.notes}")
            section.append("")

        sections.append("\n".join(section))

    return "\n\n".join(sections)


def _format_canonical_badge_names() -> str:
    """Per-dimension list of the canonical badge vocabulary.

    Each dimension surfaces the exact set of badge names the AI is
    allowed to emit. There is ONE vocabulary per dimension — no separate
    'scoring signals' second-vocabulary. The flat-tier sharpening retired
    the two-badge pattern (canonical + signal); each canonical badge now
    earns its base credit when emitted green, with friction expressed via
    separate friction badges.

    The math layer reads each badge name and either matches it as a
    scoring signal (full credit), as a penalty (deduction), or falls back
    to color points. The badge name in the config and the signal/penalty
    name in the config MUST match exactly so the math wires through.
    """
    sections: list[str] = []
    seen_badges: set[str] = set()

    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            badge_names = [b.name for b in dim.badges if b.name not in seen_badges]
            if not badge_names:
                continue
            section = [f"#### {dim.name}", "Allowed badge names (use EXACTLY as listed — no variations):"]
            for n in badge_names:
                section.append(f"- {n}")
                seen_badges.add(n)
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
        "strength": "strong|moderate|weak",
        "signal_category": "<one of the dimension's signal_categories — Pillar 2/3 only>",
        "claim": "...",
        "confidence": "confirmed|indicated|inferred",
        "source_url": "...",
        "source_title": "..."
      }
    ]
  },
  "_strength_field_note": "REQUIRED for every Pillar 2 (Instructional Value) and Pillar 3 (Customer Fit) badge. The math layer credits points by (dimension, strength) lookup against the dimension's rubric. Pillar 1 badges do NOT use the strength field — Pillar 1 uses canonical name matching against scoring signals. The signal_category field is REQUIRED for Pillar 2 and 3 badges and must be picked from the dimension's signal_categories list — see the Pillar 2 and Pillar 3 sections.",
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

        # Pillar 2 + Pillar 3 rubric blocks (rubric model — variable badge names,
        # strength grading, signal_category tags). Replaces the old PILLAR_2_DIMENSIONS
        # and PILLAR_3_DIMENSIONS tables in the prompt template.
        "PILLAR_2_RUBRICS": _format_pillar_rubrics(p2),
        "PILLAR_3_RUBRICS": _format_pillar_rubrics(p3),

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

        # Pillar 2 master category taxonomy (Define-Once from
        # cfg.IV_CATEGORY_BASELINES)
        "IV_MASTER_CATEGORY_LIST": _format_iv_master_category_list(),

        # Pillar 3 organization type values (Define-Once from
        # cfg.ORG_TYPE_NORMALIZATION)
        "CF_ORG_TYPE_VALUES": _format_org_type_values(),

        # Pillar 3 CF penalty signal tables (Define-Once from
        # cfg.CF_PENALTY_SIGNALS)
        "CF_PENALTY_SIGNALS": _format_cf_penalty_signals(),

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
