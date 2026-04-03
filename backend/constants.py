"""Shared constants for the Skillable Intelligence Platform.

Single source of truth for score thresholds, verdict labels, color palette,
and composite weights.  All Python modules, templates, and export logic
should reference these constants instead of hardcoding values.

Changes here propagate everywhere.  If a threshold or color changes,
update it once in this file.
"""

# ---------------------------------------------------------------------------
# Composite score weights — 40 / 30 / 20 / 10
# Canonical definition: docs/Scoring-Framework-Core.md
# ---------------------------------------------------------------------------

WEIGHT_PRODUCT_LABABILITY = 40
WEIGHT_INSTRUCTIONAL_VALUE = 30
WEIGHT_ORGANIZATIONAL_READINESS = 20
WEIGHT_MARKET_READINESS = 10

# ---------------------------------------------------------------------------
# Verdict thresholds and labels
# Canonical definition: docs/Scoring-Framework-Core.md
# ---------------------------------------------------------------------------

VERDICT_STRONG_FIT = 70   # score >= 70
VERDICT_PURSUE = 45       # score >= 45
VERDICT_MONITOR = 20      # score >= 20
# score < 20 → Pass

VERDICT_LABELS = {
    "strong_fit": "Strong Fit",
    "pursue": "Pursue",
    "monitor": "Monitor",
    "pass": "Pass",
}

# ---------------------------------------------------------------------------
# Labability tier thresholds (same breakpoints as verdicts)
# ---------------------------------------------------------------------------

TIER_HIGHLY_LIKELY = 70   # score >= 70
TIER_LIKELY = 45          # score >= 45
TIER_LESS_LIKELY = 20     # score >= 20
# score < 20 → not_likely

TIER_LABELS = {
    "highly_likely": "Highly Likely",
    "likely": "Likely",
    "less_likely": "Less Likely",
    "not_likely": "Not Likely",
}

# ---------------------------------------------------------------------------
# Prospector path thresholds
# ---------------------------------------------------------------------------

PATH_LABABLE_THRESHOLD = 50     # lab_score >= 50 → "Labable"
PATH_SIMULATION_THRESHOLD = 20  # lab_score >= 20 → "Simulations"
# lab_score < 20 → "Do Not Pursue"

# ---------------------------------------------------------------------------
# Technical fit multiplier breakpoints
# Applied in models.compute_labability_total()
# ---------------------------------------------------------------------------

MULTIPLIER_FULL = 32       # tech >= 32 → 1.0x (any method)
MULTIPLIER_DATACENTER = 24 # tech >= 24 → 1.0x (datacenter only), 0.75x (cloud-only)
MULTIPLIER_REDUCED = 19    # tech >= 19 → 0.75x
MULTIPLIER_LOW = 10        # tech >= 10 → 0.40x
# tech < 10 → 0.15x

MULTIPLIER_VALUES = {
    "full": 1.0,
    "datacenter": 1.0,
    "cloud_reduced": 0.75,
    "low": 0.40,
    "minimal": 0.15,
}

# Datacenter method prefixes that qualify for the 1.0x multiplier at tech >= 24
DATACENTER_PREFIXES = ("Hyper-V", "ESX", "Container", "Azure VM", "AWS VM")

# ---------------------------------------------------------------------------
# Score color thresholds — used by templates and exports
# ---------------------------------------------------------------------------

SCORE_COLOR_HIGH = 70   # score >= 70 → green
SCORE_COLOR_MID = 40    # score >= 40 → amber
# score < 40 → red

# ---------------------------------------------------------------------------
# Color palette — brand colors used across all templates and exports
# Canonical definition: CLAUDE.md color palette table
# ---------------------------------------------------------------------------

# Brand greens
COLOR_SIDEBAR = "#0A3E28"         # Deep forest — sidebar background
COLOR_PRIMARY = "#136945"         # Dark green — headings, table headers, borders
COLOR_ACCENT = "#24ED9B"          # Bright green — interactive, scores, links
COLOR_ACCENT_MUTED = "#7dd8b8"    # Muted green — secondary scores (Pursue tier)

# Score colors
COLOR_SCORE_HIGH = "#24ED9B"      # Green — Strong Fit / high scores
COLOR_SCORE_MID = "#f59e0b"       # Amber — Monitor / mid scores
COLOR_SCORE_LOW = "#e05252"       # Red — Pass / low scores
COLOR_SCORE_LOW_SOFT = "#f87171"  # Soft red — used in some templates

# Evidence qualifier colors
COLOR_BLOCKER = "#e05252"         # Red — Blocker labels
COLOR_RISK = "#f59e0b"            # Amber — Risk labels
COLOR_STRENGTH = "#24ED9B"        # Green — Strength/Opportunity labels

# Dark theme (Inspector, Prospector)
COLOR_BG_DARK = "#060f0b"         # Page background
COLOR_SURFACE_DARK = "#0c1f19"    # Card/box background
COLOR_BORDER_DARK = "#1e3329"     # Borders
COLOR_TEXT_PRIMARY = "#e8f5f0"    # Primary text
COLOR_TEXT_SECONDARY = "#c8ddd6"  # Body text
COLOR_TEXT_MUTED = "#6b9e88"      # Muted labels
COLOR_TEXT_DIM = "#4a7060"        # Eyebrow/meta text

# Light theme (Designer)
COLOR_BG_LIGHT = "#f7f8fa"        # Page background
COLOR_SURFACE_LIGHT = "#ffffff"   # Card/surface
COLOR_BORDER_LIGHT = "#e2e5ea"    # Borders
COLOR_TEXT_DARK = "#1f2937"       # Body text

# Export colors (ARGB format for openpyxl)
EXCEL_GREEN_HI = "FF24ED9B"
EXCEL_GREEN_MID = "FF6b9e88"
EXCEL_AMBER = "FFF59E0B"
EXCEL_RED_SOFT = "FFF87171"
EXCEL_BG_HEADER = "FF06100C"
EXCEL_BG_ROW = "FF0D1A14"
EXCEL_TEXT_WHITE = "FFE8F5F0"
EXCEL_TEXT_MUTED = "FF3d6655"

# ---------------------------------------------------------------------------
# Concurrency limits
# ---------------------------------------------------------------------------

MAX_SCORING_WORKERS = 6       # Max parallel Claude API calls for product scoring
MAX_SEARCH_WORKERS = 12       # Max parallel web searches
MAX_FETCH_WORKERS = 10        # Max parallel page fetches
MAX_PROSPECTOR_WORKERS = 6    # Max parallel company analyses in Prospector batch
COMPANY_TIMEOUT_SECS = 180    # Per-company timeout in Prospector batch (3 min)
SCORING_TIMEOUT_SECS = 300    # Per-product scoring timeout (5 min)

# ---------------------------------------------------------------------------
# Cache TTL
# ---------------------------------------------------------------------------

CACHE_TTL_DAYS = 45           # Analysis and discovery cache lifetime
