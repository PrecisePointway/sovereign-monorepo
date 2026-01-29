#!/usr/bin/env python3
"""
AIRBYTE SYNC — Manual Pipeline Trigger
=======================================
Triggered by: two_finger_swipe_up gesture
Purpose: Manually sync data pipeline via Airbyte connector set
"""

import json
import os
import sys
from datetime import datetime

import requests

# ============================================================================
# CONFIGURATION — Load from environment or .env
# ============================================================================

AIRBYTE_HOST = os.getenv("AIRBYTE_HOST", "http://localhost:8000")
AIRBYTE_API = f"{AIRBYTE_HOST}/api/v1/connections/sync"
CONNECTION_ID = os.getenv("AIRBYTE_CONNECTION_ID", "")  # Set via environment variable

# Optional: Multiple connections to sync
CONNECTION_IDS = os.getenv("AIRBYTE_CONNECTION_IDS", CONNECTION_ID).split(",")

# ============================================================================
# MAIN
# ============================================================================

def sync_connection(connection_id: str) -> dict:
    """Trigger sync for a single Airbyte connection."""
    payload = {"connectionId": connection_id.strip()}
    
    try:
        response = requests.post(
            AIRBYTE_API,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        return {
            "connection_id": connection_id,
            "status_code": response.status_code,
            "success": response.status_code in (200, 201, 202),
            "response": response.json() if response.ok else response.text,
        }
    except requests.exceptions.RequestException as e:
        return {
            "connection_id": connection_id,
            "status_code": None,
            "success": False,
            "error": str(e),
        }


def main():
    print("[AIRBYTE] ============================================")
    print(f"[AIRBYTE] Sync triggered at {datetime.now().isoformat()}")
    print(f"[AIRBYTE] Target: {AIRBYTE_HOST}")
    print(f"[AIRBYTE] Connections: {len(CONNECTION_IDS)}")
    print("[AIRBYTE] ============================================")
    
    results = []
    for conn_id in CONNECTION_IDS:
        if not conn_id.strip():
            continue
        print(f"[AIRBYTE] Syncing: {conn_id}...")
        result = sync_connection(conn_id)
        results.append(result)
        
        if result["success"]:
            print(f"[AIRBYTE] ✓ {conn_id}: {result['status_code']}")
        else:
            print(f"[AIRBYTE] ✗ {conn_id}: {result.get('error', result.get('status_code'))}")
    
    # Summary
    success_count = sum(1 for r in results if r["success"])
    print("[AIRBYTE] ============================================")
    print(f"[AIRBYTE] Complete: {success_count}/{len(results)} successful")
    print("[AIRBYTE] ============================================")
    
    # Exit with error if any failed
    sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
