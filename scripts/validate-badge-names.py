#!/usr/bin/env python3
"""
validate-badge-names.py
Pre-commit hook: blocks commits that introduce legacy badge vocabulary.
Run via: python scripts/validate-badge-names.py
Or as a git hook: called automatically on git commit.
"""

import subprocess
import sys
import re

# Legacy terms that must never appear in committed files
LEGACY_TERMS = [
    "Technical Orchestrability",
    "Product Complexity",           # as a dimension name
    "Training Ecosystem",
    "Lab Maturity",
    "Market Readiness",             # renamed to Market Fit
    "Strategic Fit",
    "Path A1",
    "Path A2",
    "Path B",
    "Path C",
    r"\bYellow\b",                  # badge color (Amber is correct)
    "Gate 1",                       # legacy gate labels
    "Gate 2",
    "Gate 3",
    "Gate 4",
    "No Deployment Method.*simulation",  # misuse: using No Deployment when Simulation applies
]

# Files to check (only scan these extensions)
SCAN_EXTENSIONS = {".md", ".txt", ".py", ".html", ".js"}

# Files/paths to skip
SKIP_PATHS = [
    "scripts/validate-badge-names.py",  # skip this file itself
    "CLAUDE.md",                         # locked vocab table lists legacy terms intentionally
    "docs/Badging-Framework-Core.md",    # "Never this" column lists legacy terms intentionally
    "backend/prompts/product_scoring.txt",  # scoring prompt references path names in context
    "docs/Scoring-Framework-Core.md",       # references legacy terms in explanatory context
    "docs/intelligence-platform.md",        # references legacy terms in explanatory context
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
        print("validate-badge-names: no staged files, skipping.")
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

    print("\nCOMMIT BLOCKED -- Legacy badge vocabulary detected:\n")
    for filepath, violations in all_violations.items():
        print(f"  {filepath}:")
        for line_num, term, line in violations:
            print(f"    Line {line_num}: matched '{term}'")
            print(f"    > {line[:120]}")
        print()

    print("Fix the vocabulary above before committing.")
    print("See docs/Badging-Framework-Core.md for correct terms.\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
