"""Start the new Skillable Intelligence app on port 5001.

Run from the project root:
    python run_new.py
"""

import os
import sys

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

# NOW import the app (after env vars are set)
from backend.app_new import app

if __name__ == "__main__":
    print("\n  Skillable Intelligence (new framework)")
    print("  http://localhost:5001\n")
    app.run(debug=True, port=5001, use_reloader=False)
