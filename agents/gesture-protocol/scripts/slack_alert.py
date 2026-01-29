#!/usr/bin/env python3
"""
SLACK ALERT — Compliance P1 Notification
=========================================
Triggered by: thumb_circle gesture
Purpose: Send compliance Slack alert (predefined P1 category)
"""

import json
import os
import sys
from datetime import datetime

import requests

# ============================================================================
# CONFIGURATION — Load from environment (NEVER hardcode webhooks)
# ============================================================================

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "#compliance-alerts")
OPERATOR_NAME = os.getenv("OPERATOR_NAME", "Architect")

# ============================================================================
# ALERT TEMPLATES
# ============================================================================

ALERT_TEMPLATES = {
    "P1_COMPLIANCE": {
        "emoji": ":warning:",
        "color": "#FF0000",
        "title": "P1 Compliance Alert",
        "text": "Manual review triggered via gesture interface.",
        "priority": "Critical",
    },
    "P2_REVIEW": {
        "emoji": ":eyes:",
        "color": "#FFA500",
        "title": "P2 Review Required",
        "text": "Scheduled compliance review initiated.",
        "priority": "High",
    },
}

# ============================================================================
# MAIN
# ============================================================================

def send_slack_alert(template_key: str = "P1_COMPLIANCE") -> bool:
    """Send formatted Slack alert using webhook."""
    
    if not SLACK_WEBHOOK:
        print("[SLACK] ERROR: SLACK_WEBHOOK_URL not configured")
        print("[SLACK] Set environment variable: export SLACK_WEBHOOK_URL='https://hooks.slack.com/...'")
        return False
    
    template = ALERT_TEMPLATES.get(template_key, ALERT_TEMPLATES["P1_COMPLIANCE"])
    timestamp = datetime.now().isoformat()
    
    payload = {
        "channel": ALERT_CHANNEL,
        "username": "Sovereign Ops",
        "icon_emoji": template["emoji"],
        "attachments": [
            {
                "color": template["color"],
                "title": template["title"],
                "text": template["text"],
                "fields": [
                    {"title": "Priority", "value": template["priority"], "short": True},
                    {"title": "Triggered By", "value": OPERATOR_NAME, "short": True},
                    {"title": "Timestamp", "value": timestamp, "short": False},
                    {"title": "Source", "value": "Manus Pro Gesture Interface", "short": False},
                ],
                "footer": "Sovereign Elite OS",
                "ts": int(datetime.now().timestamp()),
            }
        ],
    }
    
    try:
        response = requests.post(
            SLACK_WEBHOOK,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[SLACK] Request failed: {e}")
        return False


def main():
    print("[SLACK] ============================================")
    print(f"[SLACK] Alert triggered at {datetime.now().isoformat()}")
    print("[SLACK] ============================================")
    
    # Default to P1 compliance alert
    template = sys.argv[1] if len(sys.argv) > 1 else "P1_COMPLIANCE"
    
    success = send_slack_alert(template)
    
    if success:
        print("[SLACK] ✓ Alert sent successfully")
    else:
        print("[SLACK] ✗ Alert failed")
    
    print("[SLACK] ============================================")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
