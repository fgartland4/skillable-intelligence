"""Product archetype classifier — Skillable-labability shape.

The archetype answers: "what kind of product is this from a Skillable-labability
standpoint?" It is ORTHOGONAL to market category. Two products in the same
category (e.g., "Document Management") can have very different archetypes
(SharePoint → enterprise_admin, Acrobat → ic_productivity) and should be
scored differently.

Inferred deterministically in Python from signals already in the fact drawer:
  - category (market category set at discovery)
  - deployment_model (installable / cloud / hybrid / saas-only)
  - target_personas (who uses it — admins, IC, etc.)
  - complexity_signals (narrative text describing complexity)
  - api_surface (comprehensive / moderate / minimal / none)
  - subcategory (e.g., "CAD", "Creative Design")

Honors Frank's Rule #1 — research is immutable. The classifier reads existing
facts and produces a scoring-layer field. No re-research, only a
SCORING_MATH_VERSION bump.

Archetype enum (10 values):

  FULL IV CEILING (100):
    - enterprise_admin     — Azure admin, Workday, ServiceNow, Entra/Intune
    - security_operations  — Defender, Splunk, CrowdStrike, Palo Alto, Sentinel
    - developer_platform   — GitHub Actions, GitLab, Jenkins, Terraform, K8s
    - data_platform        — Snowflake, Databricks, Anaplan, Power BI, SQL Svr
    - integration_middleware — Marketo, AEM, Mulesoft, Adobe Commerce, SAP CPI
    - deep_infrastructure  — Storage (NetApp, Quantum), Backup (Commvault),
                             Networking (Aruba, Fortinet), Virtualization
    - engineering_cad      — Autodesk, Bentley, SolidWorks, Dassault, PTC, Ansys

  MIDDLE CEILING (~65):
    - creative_professional — Photoshop, Illustrator, Premiere, InDesign

  LOWER CEILINGS:
    - ic_productivity (~45) — Word, Excel, Outlook, Acrobat, Word-like tools
    - consumer_app (~25)    — pure end-user apps, no admin depth, no cert

Frank 2026-04-16.
"""

from __future__ import annotations

from typing import Any


# ── Archetype constants ──────────────────────────────────────────────────
ARCHETYPE_ENTERPRISE_ADMIN = "enterprise_admin"
ARCHETYPE_SECURITY_OPERATIONS = "security_operations"
ARCHETYPE_DEVELOPER_PLATFORM = "developer_platform"
ARCHETYPE_DATA_PLATFORM = "data_platform"
ARCHETYPE_INTEGRATION_MIDDLEWARE = "integration_middleware"
ARCHETYPE_DEEP_INFRASTRUCTURE = "deep_infrastructure"
ARCHETYPE_ENGINEERING_CAD = "engineering_cad"
ARCHETYPE_CREATIVE_PROFESSIONAL = "creative_professional"
ARCHETYPE_IC_PRODUCTIVITY = "ic_productivity"
ARCHETYPE_CONSUMER_APP = "consumer_app"

ALL_ARCHETYPES = (
    ARCHETYPE_ENTERPRISE_ADMIN,
    ARCHETYPE_SECURITY_OPERATIONS,
    ARCHETYPE_DEVELOPER_PLATFORM,
    ARCHETYPE_DATA_PLATFORM,
    ARCHETYPE_INTEGRATION_MIDDLEWARE,
    ARCHETYPE_DEEP_INFRASTRUCTURE,
    ARCHETYPE_ENGINEERING_CAD,
    ARCHETYPE_CREATIVE_PROFESSIONAL,
    ARCHETYPE_IC_PRODUCTIVITY,
    ARCHETYPE_CONSUMER_APP,
)

# ── IV ceilings by archetype ─────────────────────────────────────────────
# Full-ceiling archetypes have no cap (set to 100, which is the natural max).
# Middle and lower ceilings prevent IV inflation for products where Skillable-
# style hands-on labs are not the right delivery mechanism.
IV_CEILING_BY_ARCHETYPE: dict[str, int] = {
    ARCHETYPE_ENTERPRISE_ADMIN: 100,
    ARCHETYPE_SECURITY_OPERATIONS: 100,
    ARCHETYPE_DEVELOPER_PLATFORM: 100,
    ARCHETYPE_DATA_PLATFORM: 100,
    ARCHETYPE_INTEGRATION_MIDDLEWARE: 100,
    ARCHETYPE_DEEP_INFRASTRUCTURE: 100,
    ARCHETYPE_ENGINEERING_CAD: 100,
    ARCHETYPE_CREATIVE_PROFESSIONAL: 65,
    ARCHETYPE_IC_PRODUCTIVITY: 45,
    ARCHETYPE_CONSUMER_APP: 25,
}


# ── Category → archetype default mapping ─────────────────────────────────
# Hard category signals that reliably map to an archetype. When a category
# maps here unambiguously, the archetype is set from the map. Otherwise the
# deployment + personas rules below refine it.
_CATEGORY_TO_ARCHETYPE: dict[str, str] = {
    # Security-family categories
    "cybersecurity": ARCHETYPE_SECURITY_OPERATIONS,
    # Data-family
    "data & analytics": ARCHETYPE_DATA_PLATFORM,
    "data science & engineering": ARCHETYPE_DATA_PLATFORM,
    "ai platforms & tooling": ARCHETYPE_DATA_PLATFORM,
    # Infrastructure-family
    "cloud infrastructure": ARCHETYPE_ENTERPRISE_ADMIN,
    "networking / sdn": ARCHETYPE_DEEP_INFRASTRUCTURE,
    "infrastructure / virtualization": ARCHETYPE_DEEP_INFRASTRUCTURE,
    "data protection": ARCHETYPE_DEEP_INFRASTRUCTURE,
    "industrial / ot": ARCHETYPE_DEEP_INFRASTRUCTURE,
    # Developer-family
    "devops": ARCHETYPE_DEVELOPER_PLATFORM,
    "application development": ARCHETYPE_DEVELOPER_PLATFORM,
    # Enterprise apps
    "erp": ARCHETYPE_ENTERPRISE_ADMIN,
    "crm": ARCHETYPE_ENTERPRISE_ADMIN,
    "healthcare it": ARCHETYPE_ENTERPRISE_ADMIN,
    "legal tech": ARCHETYPE_ENTERPRISE_ADMIN,
    "fintech": ARCHETYPE_ENTERPRISE_ADMIN,
    # Content / collaboration — refined by personas/deployment below
    "collaboration": ARCHETYPE_IC_PRODUCTIVITY,  # default; overridden if admin-heavy
    "content management": ARCHETYPE_ENTERPRISE_ADMIN,
}


# ── Subcategory keyword tokens that force specific archetypes ────────────
# These override the category default when present — they're stronger
# signals than the broad category. Ordered from most-specific to least.
#
# IMPORTANT: short acronyms (3 chars or less) are NOT safe as substring
# matches — 'fea' matches 'feature', 'cad' matches 'cascade', 'cfd' matches
# 'coffered', etc. Those are listed separately in _SHORT_ACRONYM_TOKENS
# and matched with word-boundary logic.
_SUBCATEGORY_FORCING_TOKENS: list[tuple[tuple[str, ...], str]] = [
    # CAD / engineering — highest priority
    (("bim model", "3d modeling", "mechanical design",
      "product lifecycle", "civil engineering", "architecture design software",
      "engineering design software", "simulation & analysis",
      "finite element", "computational fluid dynamics", "mechanical cad",
      "3d cad"),
     ARCHETYPE_ENGINEERING_CAD),
    # Creative professional
    (("creative cloud", "graphic design", "photo editing", "video editing",
      "motion graphics", "illustration software", "desktop publishing",
      "digital audio workstation", "3d design & texturing",
      "raster graphics editor", "vector graphics editor"),
     ARCHETYPE_CREATIVE_PROFESSIONAL),
    # Integration middleware
    (("marketing automation", "b2b marketing automation", "cms / dam",
      "enterprise cms", "e-commerce platform", "integration platform",
      "api gateway", "ipaas"),
     ARCHETYPE_INTEGRATION_MIDDLEWARE),
    # IC productivity — document/email/productivity suite tools
    (("document management", "pdf editor", "productivity suite",
      "word processor", "email client", "spreadsheet",
      "team collaboration & conferencing"),
     ARCHETYPE_IC_PRODUCTIVITY),
]

# Short acronyms require word-boundary matching to avoid false positives
# ('fea' in 'feature', 'cad' in 'cascade'). Keyed by archetype.
_SHORT_ACRONYM_TOKENS: list[tuple[tuple[str, ...], str]] = [
    (("cad", "bim", "plm", "fea", "cfd"), ARCHETYPE_ENGINEERING_CAD),
]


# ── Persona-based refinement ─────────────────────────────────────────────
# Personas that push a borderline category toward enterprise_admin.
_ADMIN_PERSONA_TOKENS = (
    "admin", "administrator", "sysadmin", "tenant admin", "it ops",
    "it operations", "it professional", "platform engineer", "devops engineer",
    "sre", "site reliability", "security engineer", "security analyst",
    "soc analyst", "network engineer", "cloud architect", "solutions architect",
    "configurator",
)

_IC_PERSONA_TOKENS = (
    "end user", "end-user", "knowledge worker", "information worker",
    "individual contributor", "designer", "illustrator", "artist",
    "writer", "editor",
)


def _contains_any(text: str, tokens: tuple[str, ...] | list[str]) -> bool:
    """Case-insensitive substring match for any of the tokens."""
    if not text:
        return False
    t = text.lower()
    return any(tok in t for tok in tokens)


def _contains_any_word_boundary(text: str, acronyms: tuple[str, ...] | list[str]) -> bool:
    """Case-insensitive WHOLE-WORD match for short acronyms.

    Prevents 'fea' matching 'feature', 'cad' matching 'cascade', etc.
    Uses simple tokenization on non-alphanumeric boundaries.
    """
    if not text:
        return False
    import re
    t = text.lower()
    words = set(re.findall(r"[a-z0-9]+", t))
    return any(a.lower() in words for a in acronyms)


def classify_archetype(product: Any, discovery_data: dict | None = None) -> tuple[str, str]:
    """Infer the product's Skillable-labability archetype + rationale.

    Returns (archetype_value, rationale_text). Both are always strings —
    archetype falls back to ARCHETYPE_ENTERPRISE_ADMIN when nothing else
    matches (conservative default — full ceiling, treat as full product).

    Reads:
      - product.category                   (market category)
      - product.subcategory                (more specific subcategory)
      - product.deployment_model           (installable/cloud/hybrid/saas-only)
      - product.user_personas OR product.target_personas  (list or string)
      - product.complexity_signals         (narrative text)
      - product.description                (narrative text)

    Accepts either a dataclass (Product) or a dict form — duck-typed lookup.

    Frank 2026-04-16.
    """
    # Duck-typed field readers — support both dataclass and dict
    def _get(field: str, default: Any = "") -> Any:
        if hasattr(product, field):
            return getattr(product, field, default)
        if isinstance(product, dict):
            return product.get(field, default)
        return default

    category = (_get("category") or "").strip().lower()
    subcategory = (_get("subcategory") or "").strip().lower()
    deployment_model = (_get("deployment_model") or "").strip().lower()
    description = (_get("description") or "").strip()
    complexity_signals = (_get("complexity_signals") or "").strip()

    # Personas — field can be named user_personas or target_personas,
    # either list-of-strings or comma-separated string
    personas_raw = _get("user_personas") or _get("target_personas") or ""
    if isinstance(personas_raw, list):
        personas_text = ", ".join(str(x) for x in personas_raw).lower()
    else:
        personas_text = str(personas_raw).lower()

    rationale_parts: list[str] = []

    # ── Subcategory forcing tokens (highest priority) ────────────────────
    # Check long multi-word phrases with substring match (safe — low false
    # positive rate for 2+ word phrases) against BOTH subcategory and
    # description.
    for tokens, forced_archetype in _SUBCATEGORY_FORCING_TOKENS:
        if _contains_any(subcategory, tokens) or _contains_any(description, tokens):
            rationale_parts.append(
                f"subcategory/description matches {forced_archetype} tokens"
            )
            rationale = _compose_rationale(
                category, subcategory, deployment_model, personas_text,
                rationale_parts,
            )
            return forced_archetype, rationale

    # Check short acronyms with WORD-BOUNDARY match (prevents 'fea' from
    # matching 'feature' in descriptions). Only check subcategory — not
    # description — for short acronyms, because even word-boundary hits on
    # random 'CAD' appearing in company names can mislead.
    for acronyms, forced_archetype in _SHORT_ACRONYM_TOKENS:
        if _contains_any_word_boundary(subcategory, acronyms):
            rationale_parts.append(
                f"subcategory acronym matches {forced_archetype} ({acronyms})"
            )
            rationale = _compose_rationale(
                category, subcategory, deployment_model, personas_text,
                rationale_parts,
            )
            return forced_archetype, rationale

    # ── Category mapping ─────────────────────────────────────────────────
    category_archetype = _CATEGORY_TO_ARCHETYPE.get(category, "")
    if category_archetype:
        rationale_parts.append(
            f"category '{category}' → {category_archetype}"
        )

    # ── Persona refinement ───────────────────────────────────────────────
    has_admin_persona = _contains_any(personas_text, _ADMIN_PERSONA_TOKENS)
    has_ic_persona = _contains_any(personas_text, _IC_PERSONA_TOKENS)

    # ── Deployment refinement ────────────────────────────────────────────
    is_saas_only = deployment_model == "saas-only"
    is_installable = deployment_model in ("installable", "hybrid")

    # If no category mapping hit, derive from deployment + personas
    if not category_archetype:
        if has_admin_persona and is_installable:
            category_archetype = ARCHETYPE_ENTERPRISE_ADMIN
            rationale_parts.append("admin personas + installable → enterprise_admin")
        elif has_ic_persona and is_saas_only:
            category_archetype = ARCHETYPE_IC_PRODUCTIVITY
            rationale_parts.append("IC personas + SaaS-only → ic_productivity")
        else:
            category_archetype = ARCHETYPE_ENTERPRISE_ADMIN
            rationale_parts.append("no strong signal → enterprise_admin default")

    # Override: Collaboration category can be either IC productivity (Teams
    # chat) or enterprise admin (Teams admin, SharePoint admin). If the
    # personas tell us it's admin-heavy, promote.
    if category_archetype == ARCHETYPE_IC_PRODUCTIVITY and has_admin_persona:
        category_archetype = ARCHETYPE_ENTERPRISE_ADMIN
        rationale_parts.append("admin personas override IC default → enterprise_admin")

    # Downgrade: a "Cloud Infrastructure" product with explicit IC personas
    # and SaaS-only deployment is probably consumer-facing (rare, but possible)
    # Leave as enterprise_admin by default — this was the conservative call.

    rationale = _compose_rationale(
        category, subcategory, deployment_model, personas_text,
        rationale_parts,
    )
    return category_archetype, rationale


def _compose_rationale(
    category: str, subcategory: str, deployment_model: str,
    personas_text: str, parts: list[str],
) -> str:
    """Build a short rationale string that explains the classification.

    Downstream Claude calls (rubric grader, badge selector, briefcase
    generator) can read both `archetype` and `archetype_rationale` to make
    informed decisions about what signals to credit or suppress.
    """
    base = (
        f"category={category or '(none)'}"
        f", subcategory={subcategory or '(none)'}"
        f", deployment={deployment_model or '(none)'}"
    )
    if personas_text:
        # Truncate personas to keep rationale concise
        personas_trimmed = personas_text[:120] + (
            "..." if len(personas_text) > 120 else ""
        )
        base += f", personas={personas_trimmed}"
    if parts:
        reasoning = "; ".join(parts)
        return f"{base} → {reasoning}"
    return base


def get_iv_ceiling(archetype: str) -> int:
    """Return the IV ceiling for an archetype. Defaults to 100 for unknown."""
    return IV_CEILING_BY_ARCHETYPE.get(archetype, 100)
