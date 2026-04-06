"""Anti-hardcoding tests — Pre-Release Strict Mode.

See docs/Test-Plan.md Category 10 for the philosophy + false-positive watch.

These tests catch hardcoded values that should reference scoring_config.py
or _theme_new.html. The principle: no magic values in business logic.
Colors, thresholds, badge names, dimension names, rate values, etc. all
live in one canonical place.

False positives are EXPECTED during pre-release strict mode. When one
bites, see the "Decision protocol" in Test-Plan.md Category 10:
- Real signal → fix it
- Genuinely non-applicable → annotate with `# magic-allowed: <reason>`
- Pattern too broad → narrow the rule and document in Test-Plan.md
- Adding more friction than value → pytest.skip the specific test (last resort)

Tests are organized by phase so they can be enabled/relaxed independently.

Phase 1 (this file, today): template hex + inline-style scans
Phase 2: Python dict-with-color-keys + cross-file scoring_config constant scan
Phase 3: magic-number scan with annotation system
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Path helpers
# ─────────────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_BACKEND_DIR = _REPO_ROOT / "backend"

# Path-relative exclusions — files/dirs that ARE active in production but
# are deliberately scoped out of the anti-hardcoding scan for documented
# reasons. Each entry needs a clear "why" comment so future me knows whether
# the exclusion is still justified.
#
# Excluding a file here is NOT the same as ignoring the principle — these
# files are tracked in next-session-todo.md / decision-log.md as work that
# WILL happen. The exclusion is a "do this when" not a "do this never".
_EXCLUDED_PATHS: tuple[tuple[str, str], ...] = (
    # Designer tool — Frank deferred ALL Designer-related work until after
    # the new Designer code push lands. The current designer.html and
    # designer_home.html will be replaced wholesale, so cleaning up hex in
    # files that are about to be thrown away is wasted effort.
    ("tools/designer/", "deferred — waiting for Designer code push (next session)"),

    # Prospector tool — same deferral as Designer per Frank 2026-04-06.
    # Will be migrated to _nav_new.html / _theme_new.html in next session
    # alongside Designer. Tracked in next-session-todo.md.
    ("tools/prospector/", "deferred — migration scheduled for next session"),

    # Legacy shared nav + theme — currently used by unmigrated tools
    # (Designer + Prospector). Will be deleted once both tools migrate to
    # _nav_new.html / _theme_new.html. Tracked as the §6 carry-over in
    # docs/next-session-todo.md.
    ("tools/shared/templates/_nav.html", "legacy shared file — deleted post-migration"),
    ("tools/shared/templates/_theme.html", "legacy shared file — deleted post-migration"),
)


def _is_excluded(path: Path) -> bool:
    """Return True if the path matches any entry in _EXCLUDED_PATHS."""
    rel = path.relative_to(_REPO_ROOT).as_posix()
    for prefix, _reason in _EXCLUDED_PATHS:
        if rel == prefix or rel.startswith(prefix.rstrip("/") + "/"):
            return True
    return False


def _all_active_template_files() -> list[Path]:
    """Every .html template under tools/ that is NOT a _legacy_ file
    and NOT in _EXCLUDED_PATHS.

    Currently includes Inspector and Prospector tool templates plus the
    new shared theme. Designer is excluded — deferred until the new
    Designer code push. Legacy _nav.html / _theme.html shared files are
    excluded — tracked as the §6 migration task.
    """
    out: list[Path] = []
    for tool_dir in _TOOLS_DIR.iterdir():
        if not tool_dir.is_dir():
            continue
        templates_dir = tool_dir / "templates"
        if not templates_dir.exists():
            continue
        for path in templates_dir.rglob("*.html"):
            if path.name.startswith("_legacy_"):
                continue
            if _is_excluded(path):
                continue
            out.append(path)
    return sorted(out)


def _is_theme_file(path: Path) -> bool:
    """True if this file is a theme file (where hex literals legitimately
    live as the source of truth for CSS variables).
    """
    return path.name in ("_theme_new.html", "_theme.html")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1A — Hex literal scan in active templates
# ─────────────────────────────────────────────────────────────────────────────

# Match a hex color in a CSS-like context. Looks for:
#   color: #abc | background: #abcdef | border: 1px solid #abc | stroke="#abc"
# Won't match HTML entities like &#8594; (those use & not a property name).
_HEX_IN_CSS_CONTEXT = re.compile(
    r"(color|background|background-color|border|border-color|border-bottom|"
    r"border-top|border-left|border-right|border-top-color|border-bottom-color|"
    r"border-left-color|border-right-color|stroke|fill|stop-color|"
    r"box-shadow|outline|text-decoration-color|caret-color)"
    r"[^;{}\n]*"
    r"#[0-9a-fA-F]{3,8}\b"
)

# A line that starts a CSS variable definition inside :root, e.g.,
#   --sk-border:        #1e3329;
# Theme files legitimately have these — they ARE the source of truth.
_CSS_VAR_DEFINITION = re.compile(r"^\s*--[a-zA-Z][\w-]*\s*:\s*#[0-9a-fA-F]{3,8}\b")


def _scan_template_for_hex(path: Path) -> list[tuple[int, str]]:
    """Return list of (line_number, line) where a hex color appears in a
    forbidden CSS context. Theme files allow hex inside CSS variable
    definitions; everything else is reported.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    in_root_block = False
    findings: list[tuple[int, str]] = []
    is_theme = _is_theme_file(path)

    for line_num, line in enumerate(text.splitlines(), start=1):
        # Track :root { ... } block depth crudely — only matters in theme files
        if is_theme:
            if ":root" in line:
                in_root_block = True
            if in_root_block and "}" in line:
                in_root_block = False
                continue
            # Inside :root, allow CSS variable definitions
            if in_root_block and _CSS_VAR_DEFINITION.search(line):
                continue

        if _HEX_IN_CSS_CONTEXT.search(line):
            findings.append((line_num, line.strip()))

    return findings


def test_no_hardcoded_hex_in_active_templates():
    """Phase 1A — No hex color literals in active templates outside of
    :root variable definitions in theme files.

    See Test-Plan.md Category 10 for the false-positive watch.
    """
    violations: dict[str, list[tuple[int, str]]] = {}
    for path in _all_active_template_files():
        findings = _scan_template_for_hex(path)
        if findings:
            rel = path.relative_to(_REPO_ROOT).as_posix()
            violations[rel] = findings

    if violations:
        msg_lines = ["Hex color literals found in active templates:"]
        msg_lines.append(
            "  (Theme files allow hex INSIDE :root variable definitions only.)"
        )
        msg_lines.append("")
        for rel_path, findings in violations.items():
            msg_lines.append(f"  {rel_path}:")
            for line_num, line in findings[:6]:
                snippet = line[:120] + ("..." if len(line) > 120 else "")
                msg_lines.append(f"    line {line_num}: {snippet}")
            if len(findings) > 6:
                msg_lines.append(f"    ... and {len(findings) - 6} more")
            msg_lines.append("")
        msg_lines.append(
            "Fix: replace each hex with var(--sk-...) from "
            "tools/shared/templates/_theme_new.html. If you need a new color "
            "token, ADD it to _theme_new.html first, then reference it."
        )
        pytest.fail("\n".join(msg_lines))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1B — Inline style="..." attribute scan
# ─────────────────────────────────────────────────────────────────────────────

# Match inline style attributes that contain a hex color literal.
_INLINE_STYLE_HEX = re.compile(
    r"""style\s*=\s*['"][^'"]*#[0-9a-fA-F]{3,8}\b""",
    re.IGNORECASE,
)


def _scan_template_for_inline_style_hex(path: Path) -> list[tuple[int, str]]:
    """Return (line, snippet) entries where an inline style attribute
    embeds a hex color. These bypass the theme system entirely.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[tuple[int, str]] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        if _INLINE_STYLE_HEX.search(line):
            findings.append((line_num, line.strip()))
    return findings


def test_no_inline_style_hex_in_active_templates():
    """Phase 1B — No inline `style="color: #..."` or `style="background: #..."`
    attributes in markup. Inline hardcoded colors bypass the theme system
    entirely. Forces every color through CSS variables.

    See Test-Plan.md Category 10 for the false-positive watch.
    """
    violations: dict[str, list[tuple[int, str]]] = {}
    for path in _all_active_template_files():
        if _is_theme_file(path):
            # Theme files don't have markup; they're CSS-only
            continue
        findings = _scan_template_for_inline_style_hex(path)
        if findings:
            rel = path.relative_to(_REPO_ROOT).as_posix()
            violations[rel] = findings

    if violations:
        msg_lines = ["Inline style attributes with hex colors found:"]
        msg_lines.append("")
        for rel_path, findings in violations.items():
            msg_lines.append(f"  {rel_path}:")
            for line_num, line in findings[:6]:
                snippet = line[:120] + ("..." if len(line) > 120 else "")
                msg_lines.append(f"    line {line_num}: {snippet}")
            if len(findings) > 6:
                msg_lines.append(f"    ... and {len(findings) - 6} more")
            msg_lines.append("")
        msg_lines.append(
            "Fix: replace inline style hex with a CSS class that uses "
            "var(--sk-...) from _theme_new.html. If the color is dynamic "
            "(Jinja-driven), pick the variable in the Python view layer "
            "and pass the var name into the template."
        )
        pytest.fail("\n".join(msg_lines))
