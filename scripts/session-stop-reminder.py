#!/usr/bin/env python3
"""
session-stop-reminder.py
Stop hook: outputs a reminder to update decision-log.md before ending the session.
Claude Code calls this automatically when the session stops.
"""

import json
import sys

message = {
    "systemMessage": (
        "⚠️ SESSION ENDING — Before this session closes:\n"
        "1. Have all decisions made today been written to memory/decision-log.md?\n"
        "2. Have any new badge names or scoring rules been added to Badging-Framework-Core.md?\n"
        "3. Does product_scoring.txt still match Badging-Framework-Core.md?\n"
        "If any decisions were made and not yet logged, write them now."
    )
}

print(json.dumps(message))
sys.exit(0)
