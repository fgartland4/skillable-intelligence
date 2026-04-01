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

from routes.inspector_routes import inspector
from routes.prospector_routes import prospector
from routes.designer_routes import designer

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
    """Map poor_match_flag keys to display-friendly labels with correct capitalisation."""
    labels = {
        'bare_metal_required':      'Bare Metal Orchestration',
        'no_api_automation':        'Limited API Provisioning',
        'no_scoring_api':           'No APIs for Scoring',
        'credit_card_required':     'Credit Card and/or PII Required',
        'pii_required':             'Credit Card and/or PII Required',
        'broken_learner_experience':'Credit Card and/or PII Required',  # legacy cached results
        'consumer_product':         'Consumer Product',
        'saas_only':                'SaaS Only — No Learner Isolation',
        'multi_tenant_only':        'Shared Tenant — No Per-Learner Isolation',
        'no_provisioning_api':      'No Provisioning API',
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
# Platform landing page
# ---------------------------------------------------------------------------

@app.route("/")
def platform_home():
    recent = list_analyses()
    return render_template("home.html", recent=recent, platform_mode=True)


# ---------------------------------------------------------------------------
# Register blueprints
# ---------------------------------------------------------------------------

app.register_blueprint(inspector)
app.register_blueprint(prospector)
app.register_blueprint(designer)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning("ANTHROPIC_API_KEY not set — set it in .env or environment")
    app.run(debug=True, port=5000)
