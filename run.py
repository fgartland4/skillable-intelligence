"""Start the Skillable Intelligence app on port 5001.

Run from the project root:
    python run.py
"""

import logging
import os
import sys

# Force unbuffered stdout/stderr so we see logs immediately on Windows
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load .env file BEFORE any imports that read os.environ
for env_path in [
    os.path.join(os.path.dirname(__file__), "backend", ".env"),
    os.path.join(os.path.dirname(__file__), ".env"),
]:
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        break

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging BEFORE importing the app so all loggers (including werkzeug) inherit
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
# Make sure werkzeug request logs and our backend logs both show
logging.getLogger("werkzeug").setLevel(logging.INFO)
logging.getLogger("backend").setLevel(logging.INFO)

# NOW import the app (after env vars are set)
from backend.app import app

if __name__ == "__main__":
    print("\n  Skillable Intelligence")
    print("  http://localhost:5001\n", flush=True)
    app.run(debug=True, port=5001, use_reloader=False)
