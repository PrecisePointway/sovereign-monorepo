#!/usr/bin/env python3
"""
HEALTH SPRING PROTOCOL — Logging Stub
======================================
Purpose: Capture health protocol events for later analysis
Philosophy: Data precedes optimization. Log first, automate later.

USAGE:
    python3 health_log.py <event_type> [notes]
    
EVENTS:
    peptides_am     Morning peptides (BPC-157 + TB-500)
    hydration       Hydration + Electrolytes
    breakfast       Breakfast completed
    lunch           Lunch completed
    vitals          Vitals check-in (BP/HR/Mood)
    dinner          Dinner completed
    peptides_pm     Evening peptides/hormones
    winddown        Wind-down + Day Log
    custom          Custom event with notes

OPTIONAL GESTURE TRIGGER:
    Map a gesture (e.g., three_finger_tap) to:
    python3 scripts/health_log.py vitals
"""

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

LOG_DIR = Path(os.getenv("HEALTH_LOG_DIR", "/var/log/health_spring/"))
LOG_FILE = LOG_DIR / "health_log.csv"
JSON_LOG = LOG_DIR / "health_log.json"

# Event definitions from Health_Spring_Protocol.ics
EVENTS = {
    "peptides_am": {
        "name": "Peptides: BPC-157 + TB-500 (± Hexarelin)",
        "scheduled": "07:30",
        "category": "supplementation",
    },
    "hydration": {
        "name": "Hydration + Electrolytes",
        "scheduled": "08:00",
        "category": "nutrition",
    },
    "breakfast": {
        "name": "Breakfast: Protein + Healthy Fats",
        "scheduled": "09:00",
        "category": "nutrition",
    },
    "lunch": {
        "name": "Lunch: Protein + Greens + Complex Carbs",
        "scheduled": "12:30",
        "category": "nutrition",
    },
    "vitals": {
        "name": "Vitals Check-in: Hydrate + BP/HR/Mood",
        "scheduled": "16:00",
        "category": "monitoring",
    },
    "dinner": {
        "name": "Dinner: Light Protein + Greens",
        "scheduled": "18:30",
        "category": "nutrition",
    },
    "peptides_pm": {
        "name": "Peptides/Hormones: BPC-157 + TB-500 (± HGH/Hexarelin)",
        "scheduled": "22:00",
        "category": "supplementation",
    },
    "winddown": {
        "name": "Wind-down + Day Log",
        "scheduled": "22:30",
        "category": "recovery",
    },
    "custom": {
        "name": "Custom Event",
        "scheduled": None,
        "category": "custom",
    },
}

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def ensure_log_dir():
    """Create log directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def init_csv():
    """Initialize CSV file with headers if it doesn't exist."""
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "date",
                "time",
                "event_type",
                "event_name",
                "category",
                "scheduled_time",
                "delta_minutes",
                "notes",
            ])


def calculate_delta(scheduled: Optional[str], actual: datetime) -> Optional[int]:
    """Calculate minutes difference from scheduled time."""
    if not scheduled:
        return None
    
    try:
        scheduled_time = datetime.strptime(scheduled, "%H:%M").time()
        scheduled_dt = datetime.combine(actual.date(), scheduled_time)
        delta = (actual - scheduled_dt).total_seconds() / 60
        return int(delta)
    except ValueError:
        return None


def log_event(event_type: str, notes: str = ""):
    """Log a health protocol event."""
    ensure_log_dir()
    init_csv()
    
    now = datetime.now()
    event = EVENTS.get(event_type, EVENTS["custom"])
    
    if event_type not in EVENTS:
        event["name"] = event_type
    
    delta = calculate_delta(event["scheduled"], now)
    
    record = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "event_type": event_type,
        "event_name": event["name"],
        "category": event["category"],
        "scheduled_time": event["scheduled"],
        "delta_minutes": delta,
        "notes": notes,
    }
    
    # Append to CSV
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            record["timestamp"],
            record["date"],
            record["time"],
            record["event_type"],
            record["event_name"],
            record["category"],
            record["scheduled_time"],
            record["delta_minutes"],
            record["notes"],
        ])
    
    # Append to JSON (line-delimited)
    with open(JSON_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    
    return record


def show_status():
    """Show today's logged events."""
    if not LOG_FILE.exists():
        print("[HEALTH] No logs found")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_events = []
    
    with open(LOG_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                today_events.append(row)
    
    print(f"[HEALTH] Events logged today ({today}): {len(today_events)}")
    print("[HEALTH] " + "-" * 50)
    
    for event in today_events:
        delta_str = ""
        if event["delta_minutes"]:
            delta = int(event["delta_minutes"])
            if delta > 0:
                delta_str = f" (+{delta}m late)"
            elif delta < 0:
                delta_str = f" ({abs(delta)}m early)"
        
        print(f"[HEALTH] {event['time']} | {event['event_type']}{delta_str}")
    
    # Show remaining events
    logged_types = {e["event_type"] for e in today_events}
    remaining = [k for k in EVENTS.keys() if k not in logged_types and k != "custom"]
    
    if remaining:
        print("[HEALTH] " + "-" * 50)
        print(f"[HEALTH] Remaining: {', '.join(remaining)}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("[HEALTH] ============================================")
    print(f"[HEALTH] Health Spring Protocol Logger")
    print(f"[HEALTH] Timestamp: {datetime.now().isoformat()}")
    print("[HEALTH] ============================================")
    
    if len(sys.argv) < 2:
        print("[HEALTH] Usage: health_log.py <event_type> [notes]")
        print(f"[HEALTH] Events: {', '.join(EVENTS.keys())}")
        print("[HEALTH] ")
        show_status()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
        sys.exit(0)
    
    notes = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    
    record = log_event(command, notes)
    
    print(f"[HEALTH] ✓ Logged: {record['event_name']}")
    print(f"[HEALTH]   Time: {record['time']}")
    if record["delta_minutes"] is not None:
        delta = record["delta_minutes"]
        if delta > 0:
            print(f"[HEALTH]   Status: {delta} minutes late")
        elif delta < 0:
            print(f"[HEALTH]   Status: {abs(delta)} minutes early")
        else:
            print(f"[HEALTH]   Status: On time")
    if notes:
        print(f"[HEALTH]   Notes: {notes}")
    
    print("[HEALTH] ============================================")


if __name__ == "__main__":
    main()
