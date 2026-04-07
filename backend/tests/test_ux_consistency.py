"""Category 9: UX Consistency and Vocabulary

Guiding Principles: GP4 (Self-Evident Design), GP1 (Right Information, Right Person)

Validates that all templates use correct vocabulary, colors, classification
badges, and theme variables. No legacy terminology, no hardcoded colors,
no inconsistency across pages.

NOTE: These tests validate the NEW templates once built.
Until then, they serve as the specification.

See docs/Test-Plan.md for the full test strategy.
"""

import pytest

import scoring_config as cfg


# ── Theme variables ─────────────────────────────────────────────────────────

def test_templates_use_css_variables_only():
    """All templates must use CSS theme variables — no hardcoded hex values
    outside of _theme.html.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Navigation consistency ──────────────────────────────────────────────────

def test_nav_consistent_across_pages():
    """The same nav header must render on Inspector, Product Selection,
    Full Analysis, Prospector, and Designer.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Org type badge colors ──────────────────────────────────────────────────

def test_org_badges_use_correct_color_groups():
    """Org type badges must use classification colors, not scoring colors.

    Purple — Software companies, Enterprise/multi-product
    Teal — Training & certification orgs, Academic institutions
    Warm blue — GSIs, Distributors, Professional services, LMS companies, Content dev firms

    Never green, amber, or red — those are scoring colors.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Deployment model badges ─────────────────────────────────────────────────

def test_deployment_badges_correct():
    """Deployment model badges must use correct labels and colors.

    Installable (green), Hybrid (gray), Cloud-Native (green), SaaS-Only (amber).
    """
    assert "installable" in cfg.DEPLOYMENT_MODELS
    assert cfg.DEPLOYMENT_MODELS["installable"]["display"] == "Installable"


def test_deployment_data_value_is_installable():
    """Data value must be 'installable', not 'self-hosted' (GP4)."""
    assert "self-hosted" not in cfg.DEPLOYMENT_MODELS


# ── Discovery tier labels ──────────────────────────────────────────────────

def test_discovery_tier_labels():
    """Discovery tier labels must be: Seems Promising, Likely, Uncertain, Unlikely.

    These communicate confidence at discovery depth — not conclusions.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Product selection limit ─────────────────────────────────────────────────

def test_product_selection_limit_configurable():
    """Product selection limit must be configurable, not hardcoded."""
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Page names ──────────────────────────────────────────────────────────────

def test_no_forbidden_page_names():
    """User-facing text must not contain retired page names.

    No 'Seller Action Plan', 'Dossier', or 'Caseboard' visible to users.
    'Product Selection' and 'Full Analysis' are the correct names.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Classification vs scoring colors ────────────────────────────────────────

def test_classification_badges_never_use_scoring_colors():
    """Classification badges (org type, subcategory) must never use
    green, amber, or red — those are reserved for scoring assessment.

    Classification colors: purple, teal, warm blue.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Standard Search Modal partial (added 2026-04-06) ───────────────────────
#
# The reusable progress + decision modal that overlays any page that needs
# to surface a long-running operation. Three modes: progress (subscribes to
# SSE), decision (Refresh / Ignore for now choice prompt), and a transition
# from decision to progress in place.

def test_search_modal_partial_parses():
    """The _search_modal.html partial must parse cleanly under Jinja with
    the project's standard custom filters stubbed in.
    """
    from pathlib import Path
    from jinja2 import Environment, FileSystemLoader

    template_dir = Path(__file__).resolve().parents[2] / "tools" / "inspector" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    # Stub the project's custom filters that templates expect at runtime
    for fname in ["score_color", "format_analyzed_date", "badge_color_class",
                  "inline_md", "bold_label", "deployment_display", "deployment_color"]:
        env.filters[fname] = lambda x, *args: x

    env.get_template("_search_modal.html")  # raises TemplateSyntaxError on bad jinja


def test_search_modal_macros_exist():
    """The partial must export the three expected macros: styles, markup, js.

    Renders each macro with stub args and confirms the output contains the
    expected anchor strings (DOM IDs and class names that downstream JS uses).
    """
    from pathlib import Path
    from jinja2 import Environment, FileSystemLoader

    template_dir = Path(__file__).resolve().parents[2] / "tools" / "inspector" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    for fname in ["score_color", "format_analyzed_date", "badge_color_class",
                  "inline_md", "bold_label", "deployment_display", "deployment_color"]:
        env.filters[fname] = lambda x, *args: x

    # Use a small wrapper template that imports the macros and exercises them.
    # We render via from_string + the env's loader so {% import %} works.
    src = (
        "{% import '_search_modal.html' as sm %}"
        "STYLES_START\n{{ sm.styles() }}\nSTYLES_END\n"
        "MARKUP_START\n{{ sm.markup() }}\nMARKUP_END\n"
        "JS_START\n{{ sm.js() }}\nJS_END\n"
    )
    rendered = env.from_string(src).render()

    # Each macro produced output
    assert "STYLES_START" in rendered and "STYLES_END" in rendered
    assert "MARKUP_START" in rendered and "MARKUP_END" in rendered
    assert "JS_START" in rendered and "JS_END" in rendered

    # Anchor strings the downstream JS / CSS / route plumbing depend on
    # — if any of these disappear, the modal will silently break.
    expected_anchors = [
        # CSS classes referenced from JS
        "search-modal-backdrop",
        "search-modal-card",
        "is-decision",
        "is-open",
        # DOM IDs the JS reads/writes
        "searchModalBackdrop",
        "searchModalEyebrow",
        "searchModalTitle",
        "searchModalStatus",
        "searchModalProgressFill",
        "searchModalTimer",
        "searchModalDecisionMsg",
        "searchModalIgnoreBtn",
        "searchModalRefreshBtn",
        "searchModalError",
        "searchModalErrorMsg",
        "searchModalErrorBtn",
        "searchModalCancel",
        # Public JS API names
        "openSearchModal",
        "openSearchModalDecision",
        "transitionSearchModalToProgress",
    ]
    for anchor in expected_anchors:
        # Some IDs use camelCase in markup (id="searchModalCard") but the
        # CSS only references the class .search-modal-card. Accept either.
        assert anchor in rendered, (
            f"Expected anchor {anchor!r} missing from search modal output. "
            f"This will silently break the JS or CSS contract."
        )


def test_full_analysis_imports_search_modal():
    """full_analysis.html must import the search modal partial and call
    its macros. Catches accidental removal of the import or the macro calls.
    """
    from pathlib import Path

    template_path = (Path(__file__).resolve().parents[2]
                     / "tools" / "inspector" / "templates" / "full_analysis.html")
    src = template_path.read_text(encoding="utf-8")

    assert "{% import '_search_modal.html' as sm %}" in src, (
        "full_analysis.html should import the search modal partial"
    )
    assert "{{ sm.styles() }}" in src, "should call sm.styles() in <style>"
    assert "{{ sm.markup() }}" in src, "should call sm.markup() in <body>"
    assert "{{ sm.js() }}" in src, "should call sm.js() in a <script>"
    assert "openSearchModalDecision" in src, (
        "should wire the decision modal trigger for the stale-cache case"
    )
    assert "openSearchModal" in src, "should use the progress modal somewhere"


def test_product_selection_drops_view_previous_button():
    """The 'View Previous' button has been retired in favor of the cached
    product pre-selection on Product Selection. Catches accidental re-add.
    """
    from pathlib import Path

    template_path = (Path(__file__).resolve().parents[2]
                     / "tools" / "inspector" / "templates" / "product_selection.html")
    src = template_path.read_text(encoding="utf-8")

    assert "btn-view-prev" not in src, (
        "Legacy 'View Previous' button (btn-view-prev) should be retired. "
        "Cached products are now pre-selected on Product Selection."
    )
    assert "View Previous" not in src, "View Previous label should be gone"


def test_product_selection_uses_cached_product_names():
    """Product Selection template must reference the cached_product_names
    set passed by the route, used for pre-selection and the 'In cache' chip.
    """
    from pathlib import Path

    template_path = (Path(__file__).resolve().parents[2]
                     / "tools" / "inspector" / "templates" / "product_selection.html")
    src = template_path.read_text(encoding="utf-8")

    assert "cached_product_names" in src, (
        "Product Selection should reference the cached_product_names context "
        "variable from the route to pre-select cached products."
    )
    assert "badge-cached" in src or "In cache" in src, (
        "Product Selection should render an 'In cache' indicator on cached products."
    )
