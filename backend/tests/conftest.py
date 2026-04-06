"""Shared test configuration for Skillable Intelligence backend tests.

Adds the backend directory to sys.path so tests can import scoring_config,
prompt_generator, and other backend modules directly.
"""

import os
import sys

# Add backend/ to path so imports work the same as when Flask runs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
