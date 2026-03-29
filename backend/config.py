"""Configuration for the Labability Intelligence Engine."""

import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Optional: Serper.dev API key for Google search results (serper.dev/dashboard)
# When set, all web searches use Serper instead of DuckDuckGo.
# Add SERPER_API_KEY=your_key to .env
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "results")
os.makedirs(DATA_DIR, exist_ok=True)
