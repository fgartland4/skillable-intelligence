#!/usr/bin/env python3
"""
validate-badge-names.py
Pre-commit hook: blocks commits that introduce legacy badge vocabulary.
Run via: python scripts/validate-badge-names.py
Or as a git hook: called automatically on git commit.

Updated 2026-04-05 to align with Platform Foundation and Badging-and-Scoring-Reference.md.
See docs/Badging-and-Scoring-Reference.md "Vocabulary — Locked Terms" for the canonical list.
"""

import subprocess
import sys
import re

# Legacy terms that must never appear in committed files.
# These are the "Not this" column from the locked vocabulary table
# in Badging-and-Scoring-Reference.md.
LEGACY_TERMS = [
    "Technical Orchestrability",
    "Workflow Complexity",
    "Training Ecosystem",
    "Lab Maturity",
    "Training Motivation",
    "Content Delivery Ecosystem",
    "Content Development Capabilities",
    "Dedicated Content Dept",
    "Outsourced Content Creation",
    r"\bComposite Score\b",
    r"\bLab Score\b",
    r"\bPath A1\b",
    r"\bPath A2\b",
    r"\bPath B\b(?!uild)",         # Path B but not "Path Build" — \b prevents matching inside "path b..." words
    r"\bPath C\b(?!loud)",         # Path C but not "Path Cloud" — \b prevents matching inside "path c..." words
    r"\bYellow\b",                 # badge color (Amber is correct)
    r"\bPass\b.*badge",            # Pass as badge color (use Red/Blocker)
    r"\bPartial\b.*badge",         # Partial as badge color (use Amber)
    r"\bFail\b.*badge",            # Fail as badge color (use Red)
    "Difficult to Master",
    "Mastery Matters",
    "Consequence of Failure",
    "Lab Format Opportunities",
    "Licensing & Accounts",
    "self-hosted",                 # renamed to installable (GP4)
]

# Files to check (only scan these extensions)
SCAN_EXTENSIONS = {".md", ".txt", ".py", ".html", ".js"}

# Files/paths to skip — these legitimately reference legacy terms
# in "Not this" columns, vocabulary tables, or explanatory context
SKIP_PATHS = [
    "scripts/validate-badge-names.py",     # this file itself
    "CLAUDE.md",                            # locked vocab table lists legacy terms
    "docs/Badging-and-Scoring-Reference.md",  # "Not this" column lists legacy terms
    "docs/Badging-Framework-Core.md",       # legacy doc — will be deleted
    "docs/Scoring-Framework-Core.md",       # legacy doc — will be deleted
    "backend/scoring_config.py",            # locked vocabulary section lists legacy terms
    "backend/prompts/product_scoring.txt",  # legacy prompt — will be deleted
    "docs/intelligence-platform.md",        # legacy doc
    "docs/Designer-Session-Prep.md",        # references legacy terms when identifying conflicts
    "docs/Test-Plan.md",                    # test descriptions reference legacy terms as examples of what to reject
    "docs/decision-log.md",                 # historical record — legitimately references legacy terms in superseded entries
    "docs/code-review-2026-04-07.md",      # code review findings — references legacy terms when documenting violations
    "docs/next-session-todo.md",           # session backlog — references legacy terms in historical context
    "backend/tests/",                       # test code legitimately references legacy terms to verify they're NOT used
    ".git/",
    "__pycache__/",
    "node_modules/",
]

def get_staged_files():
    """Get list of files staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True
    )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

def should_scan(filepath):
    """Return True if this file should be scanned."""
    for skip in SKIP_PATHS:
        if skip in filepath:
            return False
    ext = "." + filepath.rsplit(".", 1)[-1] if "." in filepath else ""
    return ext in SCAN_EXTENSIONS

def check_file(filepath):
    """Check a file for legacy terms. Returns list of (line_num, term, line) tuples."""
    violations = []
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for term in LEGACY_TERMS:
                    if re.search(term, line, re.IGNORECASE):
                        violations.append((line_num, term, line.rstrip()))
    except (OSError, IOError):
        pass
    return violations

def main():
    staged = get_staged_files()
    if not staged:
        print("validate-badge-names: OK - no staged files, skipping.")
        sys.exit(0)

    all_violations = {}
    for filepath in staged:
        if not should_scan(filepath):
            continue
        violations = check_file(filepath)
        if violations:
            all_violations[filepath] = violations

    if not all_violations:
        print("validate-badge-names: OK - No legacy badge vocabulary found.")
        sys.exit(0)

    # Windows console default encoding (cp1252) can't print Unicode chars
    # like check marks, em-dashes, etc. that legitimately appear in our
    # markdown source. Force UTF-8 output for the diagnostic so the hook
    # can report on those files without crashing on its own print().
    def _safe_print(text: str) -> None:
        try:
            print(text)
        except UnicodeEncodeError:
            # Fall back to ASCII, replacing un-encodable chars
            print(text.encode("ascii", errors="replace").decode("ascii"))

    _safe_print("\nCOMMIT BLOCKED -- Legacy badge vocabulary detected:\n")
    for filepath, violations in all_violations.items():
        _safe_print(f"  {filepath}:")
        for line_num, term, line in violations:
            _safe_print(f"    Line {line_num}: matched '{term}'")
            _safe_print(f"    > {line[:120]}")
        _safe_print("")

    _safe_print("Fix the vocabulary above before committing.")
    _safe_print("See docs/Badging-and-Scoring-Reference.md for correct terms.\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
