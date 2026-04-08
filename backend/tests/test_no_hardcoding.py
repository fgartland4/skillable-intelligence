"""Anti-hardcoding tests — Pre-Release Strict Mode.

See docs/Test-Plan.md Category 10 for the philosophy + false-positive watch.

These tests catch hardcoded values that should reference scoring_config.py
or _theme.html. The principle: no magic values in business logic.
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
    # Will be migrated to _nav.html / _theme.html in next session
    # alongside Designer. Tracked in next-session-todo.md.
    ("tools/prospector/", "deferred — migration scheduled for next session"),

    # Legacy shared nav + theme — currently used by unmigrated tools
    # (Designer + Prospector). Will be deleted once both tools migrate to
    # _nav.html / _theme.html. Tracked as the §6 carry-over in
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
    return path.name in ("_theme.html", "_theme.html")


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
            "tools/shared/templates/_theme.html. If you need a new color "
            "token, ADD it to _theme.html first, then reference it."
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


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 path scope — which Python files are "production business logic"?
# ─────────────────────────────────────────────────────────────────────────────
#
# Scan rule: every active backend/*.py file that's part of the running platform
# after the 2026-04-07 rename + legacy cleanup. The legacy proof-of-concept
# code now lives in legacy-reference/ (out of the Python import path) and is
# explicitly excluded from this scan. designer_engine.py is a forward-looking
# stub for the Designer Foundation Session, also excluded.

_PYTHON_SCAN_FILES: tuple[str, ...] = (
    "backend/acv_calculator.py",
    "backend/app.py",
    "backend/badge_selector.py",
    "backend/core.py",
    "backend/fit_score_composer.py",
    "backend/intelligence.py",
    "backend/models.py",
    "backend/pillar_1_scorer.py",
    "backend/pillar_2_scorer.py",
    "backend/pillar_3_scorer.py",
    "backend/researcher.py",
    "backend/rubric_grader.py",
    "backend/scorer.py",
    "backend/storage.py",
)


def _python_files_to_scan() -> list[Path]:
    return [_REPO_ROOT / rel for rel in _PYTHON_SCAN_FILES if (_REPO_ROOT / rel).exists()]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2A — Python dict literals with color-name keys
# ─────────────────────────────────────────────────────────────────────────────

# A dict literal where ALL keys are color-name strings is almost always a
# duplicate of cfg.BADGE_COLOR_POINTS or cfg.BADGE_COLOR_DISPLAY_PRIORITY.
# This is the exact pattern that bit us last night in two files.
_COLOR_KEY_NAMES = frozenset({"green", "amber", "red", "gray", "yellow"})


def _find_color_key_dict_literals(path: Path) -> list[tuple[int, str]]:
    """Walk the AST of a Python file and return (line, snippet) for any
    dict literal whose keys are all string constants from _COLOR_KEY_NAMES.
    """
    import ast

    findings: list[tuple[int, str]] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return findings

    source_lines = path.read_text(encoding="utf-8").splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        if not node.keys:
            continue
        # All keys must be string constants
        if not all(isinstance(k, ast.Constant) and isinstance(k.value, str) for k in node.keys):
            continue
        key_set = {k.value.lower() for k in node.keys}
        if not key_set:
            continue
        # All keys must be in our color name set (allow extra "" for empty fallback)
        if not key_set.issubset(_COLOR_KEY_NAMES | {""}):
            continue
        # At least 2 of the 4 main color names must be present (filter out
        # `{"green": ...}` alone which could legitimately be a single-color thing)
        if len(key_set & _COLOR_KEY_NAMES) < 2:
            continue
        line_no = node.lineno
        snippet = source_lines[line_no - 1].strip() if 0 < line_no <= len(source_lines) else ""
        findings.append((line_no, snippet))

    return findings


def test_no_python_dicts_with_color_keys():
    """Phase 2A — Python dict literals where all keys are color names should
    not exist outside scoring_config.py. Such dicts are almost always a
    duplicate of BADGE_COLOR_POINTS or BADGE_COLOR_DISPLAY_PRIORITY and
    should reference cfg.* instead.

    See Test-Plan.md Category 10 for the false-positive watch.
    """
    violations: dict[str, list[tuple[int, str]]] = {}
    for path in _python_files_to_scan():
        findings = _find_color_key_dict_literals(path)
        if findings:
            rel = path.relative_to(_REPO_ROOT).as_posix()
            violations[rel] = findings

    if violations:
        msg_lines = ["Python dict literals with color-name keys found:"]
        msg_lines.append(
            "  These are almost always duplicates of "
            "cfg.BADGE_COLOR_POINTS or cfg.BADGE_COLOR_DISPLAY_PRIORITY."
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
            "Fix: replace the literal dict with `cfg.BADGE_COLOR_POINTS` "
            "(scoring) or `cfg.BADGE_COLOR_DISPLAY_PRIORITY` (display "
            "severity). Import scoring_config as cfg if needed."
        )
        pytest.fail("\n".join(msg_lines))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2B — Cross-file scan for distinctive scoring_config string constants
# ─────────────────────────────────────────────────────────────────────────────

# Curated list of distinctive scoring_config constants whose VALUES are
# unique enough that finding the literal value anywhere else in production
# code is almost always a hardcoding violation.
#
# We use a curated list (rather than dynamic discovery from cfg.__dict__)
# because dynamic discovery would catch many short common strings ("low",
# "high", "Lab Access" appears in display contexts) and produce noise.
#
# When a NEW distinctive constant is added to scoring_config, add its name
# here. The test imports cfg to get the actual value, so renaming the
# constant doesn't break the test — only renaming AND inlining the value
# elsewhere would.
_DISTINCTIVE_CFG_CONSTANTS: tuple[str, ...] = (
    "DEFAULT_RATE_TIER_NAME",
)


def _find_distinctive_cfg_literals(path: Path, forbidden: dict[str, str]) -> list[tuple[int, str, str]]:
    """Walk the AST and return (line, constant_name, snippet) for any
    string literal whose value matches one in `forbidden`.
    """
    import ast

    findings: list[tuple[int, str, str]] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return findings

    source_lines = path.read_text(encoding="utf-8").splitlines()
    value_to_name = {v: name for name, v in forbidden.items()}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if not isinstance(node.value, str):
            continue
        if node.value not in value_to_name:
            continue
        line_no = getattr(node, "lineno", 0)
        snippet = source_lines[line_no - 1].strip() if 0 < line_no <= len(source_lines) else ""
        # Skip lines that already reference cfg (likely the lookup itself,
        # e.g., `cfg.DEFAULT_RATE_TIER_NAME` — but the AST sees the resolved
        # string only after import, not the attribute access. The string
        # literal in the source is the literal value. If the line contains
        # the constant NAME as text, it's probably a comment/docstring/lookup.)
        if any(c in snippet for c in _DISTINCTIVE_CFG_CONSTANTS):
            continue
        findings.append((line_no, value_to_name[node.value], snippet))

    return findings


def test_no_hardcoded_distinctive_scoring_config_constants():
    """Phase 2B — Distinctive string constants exported from scoring_config
    should not appear as literals anywhere else in production code. If you
    see "Standard VM (1-3 VMs)" in the Score layer files, you should be using
    cfg.DEFAULT_RATE_TIER_NAME instead.

    Curated list — only constants distinctive enough that a literal match
    is overwhelmingly a hardcoding violation. See Test-Plan.md Category 10
    for the rationale.
    """
    import scoring_config as cfg

    forbidden: dict[str, str] = {}
    for name in _DISTINCTIVE_CFG_CONSTANTS:
        if hasattr(cfg, name):
            value = getattr(cfg, name)
            if isinstance(value, str):
                forbidden[name] = value

    violations: dict[str, list[tuple[int, str, str]]] = {}
    for path in _python_files_to_scan():
        findings = _find_distinctive_cfg_literals(path, forbidden)
        if findings:
            rel = path.relative_to(_REPO_ROOT).as_posix()
            violations[rel] = findings

    if violations:
        msg_lines = ["Distinctive scoring_config constant values found as literals:"]
        msg_lines.append("")
        for rel_path, findings in violations.items():
            msg_lines.append(f"  {rel_path}:")
            for line_num, const_name, line in findings[:6]:
                snippet = line[:120] + ("..." if len(line) > 120 else "")
                msg_lines.append(f"    line {line_num}: should be cfg.{const_name}")
                msg_lines.append(f"      {snippet}")
            if len(findings) > 6:
                msg_lines.append(f"    ... and {len(findings) - 6} more")
            msg_lines.append("")
        msg_lines.append(
            "Fix: import scoring_config as cfg and reference cfg.<NAME> "
            "instead of the literal value. Renames in scoring_config will "
            "then automatically propagate."
        )
        pytest.fail("\n".join(msg_lines))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Magic-number scan with annotation system
# ─────────────────────────────────────────────────────────────────────────────
#
# Pre-Release Strict Mode: any int or float literal in the Score layer
# files that isn't a "well-known bareword constant" (0, 1, -1, 100) must
# either:
#   1. Reference a named constant from scoring_config, OR
#   2. Carry a `# magic-allowed: <reason>` annotation on the same line
#
# Score layer files specifically: they're the math layer for the whole
# scoring system. Any numeric literal here that isn't from config is a
# definition that lives in two places and will silently rot. The whole
# point of scoring_config.py is that the scorers read from it.
#
# Phase 3 deliberately starts narrow so we don't drown in false positives
# from route handlers, HTTP status codes, polling intervals, etc.

_PHASE_3_SCAN_FILES: tuple[str, ...] = (
    "backend/acv_calculator.py",
    "backend/fit_score_composer.py",
    "backend/pillar_1_scorer.py",
    "backend/pillar_2_scorer.py",
    "backend/pillar_3_scorer.py",
    "backend/app.py",
)

# Numeric literals that don't need to come from config or be annotated.
# The "well-known barewords" — these are universal constants whose meaning
# is unambiguous in any code context.
_ALLOWED_BAREWORD_NUMBERS: frozenset[float] = frozenset({
    # Truly universal
    0, 0.0,
    1, 1.0,
    -1, -1.0,
    100, 100.0,
    # HTTP status codes — universal in any web framework, not "magic"
    200, 201, 202, 204,
    301, 302, 304,
    400, 401, 403, 404, 405, 409, 422, 429,
    500, 502, 503, 504,
})

# Annotation marker — same-line comment that opts a literal out of the scan.
# Format: `# magic-allowed: <reason>` with at least 5 chars of reason text.
_MAGIC_ALLOWED_PATTERN = re.compile(r"#\s*magic-allowed\s*:\s*\S{4,}")


def _find_unannotated_magic_numbers(path: Path) -> list[tuple[int, str, str]]:
    """Walk the AST and return (line, literal_value, snippet) for any
    int/float literal that:
      - is not in _ALLOWED_BAREWORD_NUMBERS
      - does not have a `# magic-allowed: ...` annotation on its line
      - is not inside a docstring (AST distinguishes Constant strings from
        these — string literals aren't matched anyway, only numeric)
      - is not a tuple/list index (ast.Subscript) — those are fine
    """
    import ast

    findings: list[tuple[int, str, str]] = []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return findings

    source_lines = source.splitlines()

    # Collect lines that have a `# magic-allowed: ...` annotation
    allowed_lines: set[int] = set()
    for line_num, line in enumerate(source_lines, start=1):
        if _MAGIC_ALLOWED_PATTERN.search(line):
            allowed_lines.add(line_num)

    # Collect literal positions that belong to subscript-style indexing —
    # array[5], uuid[:8], rows[1:10:2] etc. These are positional indices
    # not magic numbers.
    indexing_lines: set[tuple[int, float]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            slice_node = node.slice
            # Direct constant index: arr[5]
            if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, (int, float)):
                indexing_lines.add((slice_node.lineno, float(slice_node.value)))
            # Slice with constants: arr[:8], arr[3:], arr[1:10:2]
            elif isinstance(slice_node, ast.Slice):
                for part in (slice_node.lower, slice_node.upper, slice_node.step):
                    if isinstance(part, ast.Constant) and isinstance(part.value, (int, float)):
                        indexing_lines.add((part.lineno, float(part.value)))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        value = node.value
        # Bool is a subclass of int — exclude True/False
        if isinstance(value, bool):
            continue
        if not isinstance(value, (int, float)):
            continue
        if float(value) in _ALLOWED_BAREWORD_NUMBERS:
            continue

        line_no = getattr(node, "lineno", 0)
        if line_no in allowed_lines:
            continue
        if (line_no, float(value)) in indexing_lines:
            continue

        snippet = source_lines[line_no - 1].strip() if 0 < line_no <= len(source_lines) else ""

        # Skip if the line is clearly inside a docstring (heuristic — looks
        # for an enclosing triple-quote on the same or prior visible line).
        # The AST doesn't tag literals inside docstrings as Constants of int
        # type because docstrings are strings, but be defensive.
        if snippet.startswith('"""') or snippet.startswith("'''"):
            continue

        findings.append((line_no, repr(value), snippet))

    return findings


def test_no_unannotated_magic_numbers_in_score_layer():
    """Phase 3 — Magic-number scan over the Score layer files.

    Any int/float literal that isn't a well-known bareword (0, 1, -1, 100)
    must either reference a config constant via cfg.* or carry a
    `# magic-allowed: <reason>` annotation on the same line.

    Pre-release strict mode. False positives are EXPECTED — annotate or
    refactor. See Test-Plan.md Category 10.
    """
    violations: dict[str, list[tuple[int, str, str]]] = {}
    for rel in _PHASE_3_SCAN_FILES:
        path = _REPO_ROOT / rel
        if not path.exists():
            continue
        findings = _find_unannotated_magic_numbers(path)
        if findings:
            violations[rel] = findings

    if violations:
        msg_lines = [
            "Unannotated magic numbers found in scoring math files:",
            "",
            "  Allowed barewords: 0, 1, -1, 100",
            "  Anything else must either:",
            "    - reference a constant from scoring_config.py via cfg.X, or",
            "    - carry a `# magic-allowed: <reason>` comment on the same line",
            "",
        ]
        for rel_path, findings in violations.items():
            msg_lines.append(f"  {rel_path}:")
            for line_num, literal, line in findings[:12]:
                snippet = line[:120] + ("..." if len(line) > 120 else "")
                msg_lines.append(f"    line {line_num}: literal {literal}")
                msg_lines.append(f"      {snippet}")
            if len(findings) > 12:
                msg_lines.append(f"    ... and {len(findings) - 12} more")
            msg_lines.append("")
        msg_lines.append(
            "Fix: either move the value into scoring_config.py and reference "
            "it via cfg.<NAME>, or annotate with "
            "`# magic-allowed: <reason>` if it's genuinely a one-off."
        )
        pytest.fail("\n".join(msg_lines))


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
            "var(--sk-...) from _theme.html. If the color is dynamic "
            "(Jinja-driven), pick the variable in the Python view layer "
            "and pass the var name into the template."
        )
        pytest.fail("\n".join(msg_lines))
