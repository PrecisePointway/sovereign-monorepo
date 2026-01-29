#!/usr/bin/env python3
"""
METABASE CONTROL — Dashboard Tab Switching & Acknowledgement
=============================================================
Triggered by: double_tap gesture
Purpose: Acknowledge alert or switch Metabase dashboard tab
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional

import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

METABASE_HOST = os.getenv("METABASE_HOST", "http://localhost:3000")
METABASE_SESSION_TOKEN = os.getenv("METABASE_SESSION_TOKEN")
METABASE_USERNAME = os.getenv("METABASE_USERNAME")
METABASE_PASSWORD = os.getenv("METABASE_PASSWORD")

# Dashboard rotation configuration
DASHBOARD_IDS = os.getenv("METABASE_DASHBOARD_IDS", "1,2,3").split(",")
STATE_FILE = "/var/log/manus_gesture/metabase_state.json"

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def load_state() -> dict:
    """Load current dashboard state."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"current_index": 0, "last_switch": None}


def save_state(state: dict):
    """Persist dashboard state."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ============================================================================
# METABASE API
# ============================================================================

class MetabaseClient:
    """Simple Metabase API client."""
    
    def __init__(self, host: str, session_token: Optional[str] = None):
        self.host = host.rstrip("/")
        self.session_token = session_token
        self.session = requests.Session()
        
        if session_token:
            self.session.headers["X-Metabase-Session"] = session_token
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate and obtain session token."""
        try:
            response = self.session.post(
                f"{self.host}/api/session",
                json={"username": username, "password": password},
                timeout=10,
            )
            if response.ok:
                self.session_token = response.json().get("id")
                self.session.headers["X-Metabase-Session"] = self.session_token
                return True
        except requests.exceptions.RequestException:
            pass
        return False
    
    def get_dashboard(self, dashboard_id: int) -> Optional[dict]:
        """Fetch dashboard metadata."""
        try:
            response = self.session.get(
                f"{self.host}/api/dashboard/{dashboard_id}",
                timeout=10,
            )
            if response.ok:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        return None
    
    def get_dashboard_url(self, dashboard_id: int) -> str:
        """Generate dashboard URL."""
        return f"{self.host}/dashboard/{dashboard_id}"


# ============================================================================
# COMMANDS
# ============================================================================

def switch_tab():
    """Switch to next dashboard in rotation."""
    state = load_state()
    
    # Advance to next dashboard
    current_index = state.get("current_index", 0)
    next_index = (current_index + 1) % len(DASHBOARD_IDS)
    
    dashboard_id = DASHBOARD_IDS[next_index].strip()
    dashboard_url = f"{METABASE_HOST}/dashboard/{dashboard_id}"
    
    # Update state
    state["current_index"] = next_index
    state["last_switch"] = datetime.now().isoformat()
    state["current_dashboard"] = dashboard_id
    save_state(state)
    
    print(f"[METABASE] Switched to dashboard {next_index + 1}/{len(DASHBOARD_IDS)}")
    print(f"[METABASE] Dashboard ID: {dashboard_id}")
    print(f"[METABASE] URL: {dashboard_url}")
    
    # Attempt to open in browser (if display available)
    if os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"):
        import subprocess
        try:
            subprocess.run(["xdg-open", dashboard_url], check=False, timeout=5)
        except Exception:
            pass
    
    return True


def acknowledge():
    """Acknowledge current alert/notification."""
    timestamp = datetime.now().isoformat()
    
    # Log acknowledgement
    ack_log = "/var/log/manus_gesture/acknowledgements.log"
    os.makedirs(os.path.dirname(ack_log), exist_ok=True)
    
    with open(ack_log, "a") as f:
        f.write(f"{timestamp} | ACK | Gesture acknowledgement received\n")
    
    print(f"[METABASE] Acknowledgement logged at {timestamp}")
    return True


def status():
    """Show current dashboard state."""
    state = load_state()
    
    print("[METABASE] ============================================")
    print("[METABASE] Current State:")
    print(f"[METABASE]   Dashboard Index: {state.get('current_index', 0) + 1}/{len(DASHBOARD_IDS)}")
    print(f"[METABASE]   Dashboard ID: {state.get('current_dashboard', DASHBOARD_IDS[0])}")
    print(f"[METABASE]   Last Switch: {state.get('last_switch', 'Never')}")
    print("[METABASE] ============================================")
    return True


# ============================================================================
# MAIN
# ============================================================================

COMMANDS = {
    "switch_tab": switch_tab,
    "ack": acknowledge,
    "acknowledge": acknowledge,
    "status": status,
}


def main():
    print("[METABASE] ============================================")
    print(f"[METABASE] Control triggered at {datetime.now().isoformat()}")
    print("[METABASE] ============================================")
    
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "switch_tab"
    
    if command not in COMMANDS:
        print(f"[METABASE] Unknown command: {command}")
        print(f"[METABASE] Available: {', '.join(COMMANDS.keys())}")
        sys.exit(1)
    
    # Execute
    success = COMMANDS[command]()
    
    print("[METABASE] ============================================")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
