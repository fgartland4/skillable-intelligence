"""Shared test configuration for Skillable Intelligence backend tests.

Adds both the project root and backend directory to sys.path so tests can
import modules the same way they're imported when Flask runs.
"""

import os
import sys

# Add project root (for `from backend import ...` style imports)
_project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, _project_root)

# Add backend/ (for direct `import scoring_config` style imports)
_backend_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _backend_dir)
