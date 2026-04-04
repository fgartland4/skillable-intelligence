"""Skillable Intelligence — unified Flask backend for Inspector, Designer, Prospector."""

import logging
import os
import re as _re
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

import jinja2
from flask import Flask, render_template
from markupsafe import Markup, escape as _escape
from storage import list_analyses

from config import validate_startup
from constants import SCORE_COLOR_HIGH, SCORE_COLOR_MID
from core import _verdict, _parse_hero_badge, _badge_subsection
from routes.inspector_routes import inspector
from routes.prospector_routes import prospector
from routes.designer_routes import designer

# Validate required config, files, and directories at startup — fail fast
# with a clear message rather than cryptic errors minutes into an analysis.
validate_startup()

# ---------------------------------------------------------------------------
# App setup — multi-tool template loader
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).parent
_TOOLS_DIR = _BACKEND_DIR.parent / "tools"
_STATIC_DIR = _BACKEND_DIR.parent / "static"

app = Flask(
    __name__,
    static_folder=str(_STATIC_DIR),
    static_url_path="/static",
    template_folder=str(_TOOLS_DIR / "inspector" / "templates"),  # default fallback
)

# Allow templates to be found across all three tool directories
app.jinja_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "shared" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "inspector" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "designer" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "prospector" / "templates")),
])

app.jinja_env.tests['match'] = lambda value, pattern: bool(_re.match(pattern, str(value or '')))

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# Template filters (registered on app, available in all blueprints)
# ---------------------------------------------------------------------------

_WARNING_LABELS = {'Blockers', 'Blocker', 'Note', 'Warning', 'Risk', 'Limitation'}


def _apply_bold(text: str) -> str:
    """Convert **text** to <strong>text</strong> with colored labels.

    Suffix convention (from scorer.py):
      **Label — Blocker:**     → label in red    (#e05252)
      **Label — Risk:**        → label in orange (#f59e0b)
      **Label — Strength:**    → label in green  (#24ED9B)
      **Label — Opportunity:** → label in green  (#24ED9B)
    Fallback: first-word matches against _WARNING_LABELS → red.
    """
    def _replace(m):
        label = m.group(1)
        colon_pos = label.find(':')
        label_text = label[:colon_pos].strip() if colon_pos != -1 else label.strip()
        rest = label[colon_pos:] if colon_pos != -1 else ''

        if label_text.endswith('| Blocker') or label_text.endswith('— Blocker') or label_text.endswith('\u2014 Blocker'):
            return f'<strong><span style="color:#e05252;">{label_text}</span>{rest}</strong>'
        if label_text.endswith('| Risk') or label_text.endswith('— Risk') or label_text.endswith('\u2014 Risk'):
            return f'<strong><span style="color:#f59e0b;">{label_text}</span>{rest}</strong>'
        if (label_text.endswith('| Strength') or label_text.endswith('| Opportunity')
                or label_text.endswith('— Strength') or label_text.endswith('\u2014 Strength')
                or label_text.endswith('— Opportunity') or label_text.endswith('\u2014 Opportunity')):
            return f'<strong><span style="color:#24ED9B;">{label_text}</span>{rest}</strong>'

        first_word = label_text.split()[0] if label_text else label_text
        if first_word in _WARNING_LABELS:
            return f'<strong><span style="color:#e05252;">{label_text}</span>{rest}</strong>'

        return f'<strong>{label}</strong>'
    return _re.sub(r'\*\*(.+?)\*\*', _replace, text)


@app.template_filter('flag_label')
def flag_label_filter(flag):
    """Map poor_match_flag keys to display-friendly badge names (locked vocabulary).

    Badge name = what displays in the UI. Color is determined by context (red for all poor_match_flags).
    One badge name per concept — aligned with reference_badge_pattern.md.
    """
    labels = {
        # 1.1 Provisioning — blockers
        'bare_metal_required':       'Bare Metal Required',
        'no_api_automation':         'Provisioning APIs',        # red: no viable automation
        'no_provisioning_api':       'Provisioning APIs',        # red: alias
        'saas_only':                 'No Learner Isolation',     # red: no per-learner environment
        'multi_tenant_only':         'No Learner Isolation',     # red: shared tenant only
        # 1.2 Licensing & Accounts — blockers
        'credit_card_required':      'Credit Card Required',
        'pii_required':              'PII Required',
        # 1.3 Scoring — blockers
        'no_scoring_api':            'Scoring APIs',             # red: no scoring surface
        # Consumer / not appropriate
        'consumer_product':          'Not Lab Appropriate',
        # Legacy — map to closest current badge
        'broken_learner_experience': 'No Learner Isolation',     # legacy cached results
    }
    return labels.get(flag, flag.replace('_', ' ').title())


@app.template_filter('flag_labels')
def flag_labels_filter(flags):
    """Convert a list of poor_match_flag keys to deduplicated display labels."""
    seen = []
    for flag in (flags or []):
        label = flag_label_filter(flag)
        if label not in seen:
            seen.append(label)
    return seen


@app.template_filter('bold_labels')
def bold_labels(text):
    """Convert **text** markdown to <strong>text</strong> HTML."""
    return Markup(_apply_bold(str(text)))


@app.template_filter('rec_bullet')
def rec_bullet(text: str, max_desc: int = 120) -> Markup:
    """Distil a recommendation string to a short Next Steps bullet.

    Input:  '**Label | Risk:** Long paragraph of explanation...'
    Output: '<strong>Label</strong> — first sentence, max 120 chars…'

    Strips the qualifier suffix (| Risk / | Blocker / | Strength) from the label
    so bullets read cleanly without the scoring vocabulary leaking into seller copy.
    """
    s = str(text).strip()
    m = _re.match(r'\*\*(.+?)\*\*:?\s*(.*)', s, _re.DOTALL)
    if not m:
        # No bold label — truncate plain text
        return Markup(_escape(s[:max_desc] + ('…' if len(s) > max_desc else '')))

    label = m.group(1).strip().rstrip(':')
    # Strip qualifier suffix (| Risk, | Blocker, | Strength, | Opportunity, — Risk, etc.)
    label = _re.sub(r'\s*[\|—–]\s*(Risk|Blocker|Strength|Caution|Opportunity)$', '', label, flags=_re.IGNORECASE)

    desc = m.group(2).strip()
    # Take first sentence only (split on '. ' or ' — ')
    for sep in ['. ', ' — ', ' – ', '\n']:
        idx = desc.find(sep)
        if idx != -1 and idx < max_desc:
            desc = desc[:idx]
            break
    if len(desc) > max_desc:
        desc = desc[:max_desc].rstrip() + '…'

    label_html = _apply_bold(f'**{label}:**')
    desc_html = str(_escape(desc)) if desc else ''
    result = label_html + (f' {desc_html}' if desc_html else '')
    return Markup(result)


@app.template_filter('linkify')
def linkify(text):
    """Convert [label](url) markdown links to <a> HTML, then apply bold with warning colors."""
    result = str(text)
    result = _re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" class="rec-link">\1</a>',
        result,
    )
    result = _apply_bold(result)
    return Markup(result)


@app.template_filter('link_product_name')
def link_product_name(text, name, url):
    """Wrap the first occurrence of the product name in a description with a link."""
    if not url or not name:
        return Markup(str(text))
    safe_text = str(_escape(text))
    safe_url = str(_escape(url))
    safe_name = str(_escape(name))
    linked = safe_text.replace(safe_name, f'<a href="{safe_url}" target="_blank" class="product-name-link">{safe_name}</a>', 1)
    return Markup(linked)


# ---------------------------------------------------------------------------
# Evidence parsing filters — replaces fragile Jinja2 string parsing
#
# These filters extract badge names, qualifiers, colors, and subsection
# groupings from evidence claim strings.  The claim format is:
#   **Badge Name | Qualifier:** Description text — source.
# where Qualifier is one of: Blocker, Risk, Caution, Strength, Opportunity
# ---------------------------------------------------------------------------

_BADGE_RE = _re.compile(r'\*\*(.+?)\*\*')


def _parse_badge_from_claim(claim: str) -> dict | None:
    """Parse a badge name and qualifier from an evidence claim string.

    Returns {"name": str, "qualifier": str} or None if no badge found.
    Qualifier is lowercased: blocker, risk, caution, strength, opportunity.
    """
    m = _BADGE_RE.match(claim)
    if not m:
        return None
    label = m.group(1).rstrip(":")
    if " | " in label:
        name, qualifier = label.rsplit(" | ", 1)
    else:
        name, qualifier = label, "strength"
    return {"name": name.strip(), "qualifier": qualifier.strip().lower()}


def _badge_color(qualifier: str) -> str:
    """Map a qualifier to a CSS color class: green, amber, or red."""
    if qualifier == "blocker":
        return "red"
    if qualifier in ("risk", "caution"):
        return "amber"
    return "green"


def _badge_emoji(qualifier: str) -> str:
    """Map a qualifier to its display emoji."""
    if qualifier == "blocker":
        return "\U0001f6ab"   # 🚫
    if qualifier in ("risk", "caution"):
        return "\u26a0\ufe0f"  # ⚠️
    return "\u2705"            # ✅


def _get_claim(ev) -> str:
    """Extract claim text from an evidence item (dict or object)."""
    if isinstance(ev, dict):
        return ev.get("claim", "")
    return getattr(ev, "claim", "")


@app.template_filter('parse_badges')
def parse_badges_filter(ev_list):
    """Parse an evidence list into grouped badge dicts sorted by color.

    Returns: {"green": [{"name", "qualifier"}], "amber": [...], "red": [...]}
    Used by dossier template to render dimension badge chips.
    """
    groups = {"green": [], "amber": [], "red": []}
    seen = set()
    for ev in (ev_list or []):
        badge = _parse_badge_from_claim(_get_claim(ev))
        if badge and badge["name"] not in seen:
            seen.add(badge["name"])
            color = _badge_color(badge["qualifier"])
            groups[color].append(badge)
    return groups


@app.template_filter('group_labability')
def group_labability_filter(ev_list):
    """Group Product Labability evidence by subsection.

    Returns: {"provisioning": [...], "licensing": [...], "scoring": [...],
              "teardown": [...], "other": [...]}
    Each value is a list of the original evidence items (dicts or objects).
    Used by dossier template to render the SE drill-down grouped view.
    """
    groups = {"provisioning": [], "licensing": [], "scoring": [], "teardown": [], "other": []}
    for ev in (ev_list or []):
        claim = _get_claim(ev)
        badge = _parse_badge_from_claim(claim)
        if badge:
            section = _badge_subsection(badge["name"])
            groups.get(section, groups["other"]).append(ev)
        else:
            groups["other"].append(ev)
    return groups


@app.template_filter('group_instructional_value')
def group_instructional_value_filter(ev_list):
    """Group Instructional Value evidence by subsection.

    Returns: {"difficult_to_master": [...], "mastery_matters": [...],
              "lab_format": [...], "other": [...]}
    """
    from core import _iv_subsection
    groups = {"difficult_to_master": [], "mastery_matters": [], "lab_format": [], "other": []}
    for ev in (ev_list or []):
        claim = _get_claim(ev)
        badge = _parse_badge_from_claim(claim)
        if badge:
            section = _iv_subsection(badge["name"])
            groups.get(section, groups["other"]).append(ev)
        else:
            groups["other"].append(ev)
    return groups


@app.template_filter('group_org_readiness')
def group_org_readiness_filter(ev_list):
    """Group Organizational Readiness evidence by subsection.

    Returns: {"content_development": [...], "content_delivery": [...], "other": [...]}
    """
    from core import _or_subsection
    groups = {"content_development": [], "content_delivery": [], "other": []}
    for ev in (ev_list or []):
        claim = _get_claim(ev)
        badge = _parse_badge_from_claim(claim)
        if badge:
            section = _or_subsection(badge["name"])
            groups.get(section, groups["other"]).append(ev)
        else:
            groups["other"].append(ev)
    return groups


@app.template_filter('group_market_readiness')
def group_market_readiness_filter(ev_list):
    """Group Market Fit evidence by subsection.

    Returns: {"product_popularity": [...], "other": [...]}
    Only includes badges that belong to Dimension 4 (Market Fit).
    Badges from other dimensions (e.g. Hands-On AI Features) are excluded.
    """
    from core import _MR_SUBSECTION
    _allowed = {k.lower() for k in _MR_SUBSECTION}
    groups = {"product_popularity": [], "other": []}
    for ev in (ev_list or []):
        claim = _get_claim(ev)
        badge = _parse_badge_from_claim(claim)
        if badge:
            # Only include badges that actually belong to Market Fit
            if any(allowed in badge["name"].lower() for allowed in _allowed):
                groups["product_popularity"].append(ev)
        else:
            groups["other"].append(ev)
    return groups


@app.template_filter('dedup_evidence')
def dedup_evidence_filter(ev_list):
    """Deduplicate evidence by badge name — keep first occurrence only."""
    seen = set()
    result = []
    for ev in (ev_list or []):
        claim = _get_claim(ev)
        badge = _parse_badge_from_claim(claim)
        key = badge["name"] if badge else claim[:60]
        if key not in seen:
            seen.add(key)
            result.append(ev)
    return result


@app.template_filter('badge_color')
def badge_color_filter(qualifier):
    """Map a qualifier string to a CSS color class."""
    return _badge_color(str(qualifier).lower())


@app.template_filter('badge_emoji_filter')
def badge_emoji_filter_fn(qualifier):
    """Map a qualifier string to its display emoji."""
    return _badge_emoji(str(qualifier).lower())


# ---------------------------------------------------------------------------
# Platform landing page
# ---------------------------------------------------------------------------

@app.route("/")
def platform_home():
    recent = list_analyses()
    return render_template("home.html", recent=recent, platform_mode=True)


# ---------------------------------------------------------------------------
# Jinja2 globals — available in all templates
# ---------------------------------------------------------------------------

app.jinja_env.globals.update(
    verdict=_verdict,
    hero_badge=_parse_hero_badge,
    badge_subsection=_badge_subsection,
    SCORE_COLOR_HIGH=SCORE_COLOR_HIGH,
    SCORE_COLOR_MID=SCORE_COLOR_MID,
)


# ---------------------------------------------------------------------------
# Register blueprints
# ---------------------------------------------------------------------------

app.register_blueprint(inspector)
app.register_blueprint(prospector)
app.register_blueprint(designer)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
