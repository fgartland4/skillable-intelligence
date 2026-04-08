"""Category 9: UX Consistency and Vocabulary

Guiding Principles: GP4 (Self-Evident Design), GP1 (Right Information, Right Person)

Validates that all templates use correct vocabulary, colors, classification
badges, and theme variables. No legacy terminology, no hardcoded colors,
no inconsistency across pages.

NOTE: These tests validate the NEW templates once built.
Until then, they serve as the specification.

See docs/Test-Plan.md for the full test strategy.
"""

import os
from pathlib import Path

import pytest

import scoring_config as cfg


# Path to the Inspector template directory (tool layer).
_INSPECTOR_TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "tools" / "inspector" / "templates"
)


# ── Search modal consistency ─────────────────────────────────────────────────

def test_templates_using_search_modal_include_styles():
    """GP4 regression test — catch the stale-cache modal CSS bug.

    Any Inspector template that calls `{{ sm.markup() }}` or `{{ sm.js() }}`
    MUST also call `{{ sm.styles() }}` inside a `<style>` block.  Without
    the styles call, the search modal HTML and JS load but render
    completely unstyled — the seller sees a tiny text block in the
    lower-left corner instead of a modal dialog, and the page appears
    to "do nothing" on Deep Dive.

    This fired for real on 2026-04-07 when the SCORING_LOGIC_VERSION bump
    to `pillars-2-3-posture-rewrite` triggered the stale-cache decision
    modal on Product Selection for the first time — revealing that
    `product_selection.html` had been calling `sm.markup()` and `sm.js()`
    without `sm.styles()` since the stale-cache modal was introduced in
    commit `7c69eb1`.  The latent bug didn't surface until a cache
    version change forced the flow.

    This test ensures that class of bug cannot silently re-emerge in any
    Inspector template.
    """
    if not _INSPECTOR_TEMPLATE_DIR.exists():
        pytest.skip(f"Inspector template dir not found: {_INSPECTOR_TEMPLATE_DIR}")

    offenders: list[str] = []
    for html_path in _INSPECTOR_TEMPLATE_DIR.glob("*.html"):
        content = html_path.read_text(encoding="utf-8")
        uses_markup = "sm.markup()" in content
        uses_js = "sm.js()" in content
        if uses_markup or uses_js:
            if "sm.styles()" not in content:
                offenders.append(html_path.name)

    assert not offenders, (
        f"These Inspector templates call sm.markup() or sm.js() but are "
        f"missing sm.styles(): {offenders}. The search modal will render "
        f"unstyled. Add {{{{ sm.styles() }}}} inside a <style> block."
    )


def test_templates_importing_search_modal_either_use_it_fully_or_not_at_all():
    """A template that imports `_search_modal.html` must use all three
    parts (styles / markup / js) — or none.  Partial usage always
    produces broken UX: styles without markup renders nothing; markup
    without styles renders unstyled; markup without js is non-
    interactive.  Importing the macro and not using it at all wastes a
    few bytes but is harmless.
    """
    if not _INSPECTOR_TEMPLATE_DIR.exists():
        pytest.skip(f"Inspector template dir not found: {_INSPECTOR_TEMPLATE_DIR}")

    broken: list[str] = []
    for html_path in _INSPECTOR_TEMPLATE_DIR.glob("*.html"):
        content = html_path.read_text(encoding="utf-8")
        imports_sm = "'_search_modal.html' as sm" in content
        if not imports_sm:
            continue

        uses_styles = "sm.styles()" in content
        uses_markup = "sm.markup()" in content
        uses_js = "sm.js()" in content

        # If the template uses ANY part, it must use ALL parts.
        if uses_styles or uses_markup or uses_js:
            if not (uses_styles and uses_markup and uses_js):
                missing = []
                if not uses_styles:
                    missing.append("sm.styles()")
                if not uses_markup:
                    missing.append("sm.markup()")
                if not uses_js:
                    missing.append("sm.js()")
                broken.append(f"{html_path.name} (missing: {', '.join(missing)})")

    assert not broken, (
        f"These Inspector templates use the search modal partially: "
        f"{broken}. If a template uses ANY of sm.styles() / sm.markup() "
        f"/ sm.js(), it must use ALL THREE."
    )


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


def test_no_eventsource_outside_shared_search_modal():
    """Platform-wide rule: the ONLY `new EventSource(` in the codebase
    lives in `_search_modal.html`.  Every long-running flow in every tool
    (Inspector today; Prospector and Designer later) renders progress
    through the SHARED search modal.  If this test fails, someone built
    a custom progress UI instead of reusing the shared modal — that is
    a Platform-Foundation violation, not a style issue.

    See `docs/Platform-Foundation.md` → "The Standard Search Modal" and
    `CLAUDE.md` → "The Standard Search Modal".
    """
    repo_root = Path(__file__).resolve().parents[2]
    tools_dir = repo_root / "tools"
    backend_dir = repo_root / "backend"
    shared_modal = repo_root / "tools" / "inspector" / "templates" / "_search_modal.html"
    self_path = Path(__file__).resolve()

    offenders: list[str] = []
    for root in (tools_dir, backend_dir):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in (".html", ".py", ".js"):
                continue
            if path == shared_modal or path == self_path:
                continue
            # Skip the legacy-reference quarantine — it is out of the
            # Python import path and not used by the active platform.
            if "legacy-reference" in path.parts or "_legacy_" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except Exception:
                continue
            if "new EventSource(" in src:
                offenders.append(str(path.relative_to(repo_root)))

    assert not offenders, (
        "Platform-wide rule violation: `new EventSource(` found outside "
        "the shared search modal. Every long-running flow must use the "
        "shared `_search_modal.html` via `openSearchModal({sseUrl: ...})`. "
        "See CLAUDE.md → 'The Standard Search Modal' and "
        "docs/Platform-Foundation.md → 'The Standard Search Modal'. "
        "Offenders:\n  - " + "\n  - ".join(offenders)
    )


def test_no_rendered_progress_templates_exist():
    """Platform-wide rule: there are no rendered full-page progress
    templates in the platform.  Progress lives INSIDE the shared modal
    (an overlay), not as a dedicated page.  The legacy `scoring.html`
    was deleted on 2026-04-07 for exactly this reason.

    Any file named like a progress / loading / scoring / waiting page
    that isn't a minimal shell importing `_search_modal.html` is a
    Platform-Foundation violation.
    """
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    # Files that would be suspicious as standalone progress pages.
    suspicious_names = {
        "scoring.html", "progress.html", "loading.html", "waiting.html",
        "searching.html", "running.html",
    }
    offenders: list[str] = []
    for path in tools_dir.rglob("*.html"):
        if path.name in suspicious_names:
            offenders.append(str(path.relative_to(tools_dir.parent)))

    assert not offenders, (
        "Platform-wide rule violation: a dedicated progress-page template "
        "was found. Progress lives INSIDE the shared search modal, not as "
        "a rendered page. Delete the file and route through "
        "`openSearchModal()` instead.\n"
        "Offenders:\n  - " + "\n  - ".join(offenders)
    )


def test_shared_search_modal_is_flow_agnostic():
    """The shared modal must stay flow-agnostic so Prospector and
    Designer can reuse it without forking.  No Inspector-specific hard
    references (routes, analysis IDs, discovery IDs, specific tool names)
    should appear inside the macros.
    """
    shared_modal = (Path(__file__).resolve().parents[2]
                    / "tools" / "inspector" / "templates" / "_search_modal.html")
    src = shared_modal.read_text(encoding="utf-8")

    # The functional code inside the macros (CSS rules, markup, JS) must
    # not hardcode any tool-specific URL pattern.  Usage examples and doc
    # comments are allowed to reference Inspector URLs for illustration —
    # strip them before checking.
    import re
    macro_start = src.find("{% macro styles()")
    assert macro_start > 0, "could not find macro definitions in _search_modal.html"
    macro_src = src[macro_start:]

    # Strip JS block comments /* ... */ and line comments `// ...`
    macro_src_no_block_comments = re.sub(r"/\*.*?\*/", "", macro_src, flags=re.DOTALL)
    lines = []
    for line in macro_src_no_block_comments.splitlines():
        stripped = line.lstrip()
        # Drop full-line JS comments
        if stripped.startswith("//"):
            continue
        # Drop inline JS comments
        if "//" in line:
            line = line.split("//", 1)[0]
        # Drop Jinja comments {# ... #}
        line = re.sub(r"\{#.*?#\}", "", line)
        lines.append(line)
    functional_src = "\n".join(lines)

    forbidden = [
        "/inspector/score",
        "/inspector/discover",
        "/inspector/analysis/",
        "/prospector/",
        "/designer/",
    ]
    found = [p for p in forbidden if p in functional_src]
    assert not found, (
        "The shared search modal must stay flow-agnostic so every tool can "
        "reuse it.  Found tool-specific references inside the FUNCTIONAL "
        f"macro bodies (not comments): {found}. Move these to the CALLER, "
        "not the shared component."
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
