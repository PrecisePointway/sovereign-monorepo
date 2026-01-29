#!/usr/bin/env python3
"""
Safety Guardrail Check - Sovereign Sanctuary Elite

Hard fail if system invariants are violated.
This script MUST pass before snapshot, restore, or takedown.

Version: 2.0.0
Author: Manus AI for Architect

INVARIANTS ENFORCED:
- System status must be GREEN
- Readiness must be 100%
- Governance mode must be ACTIVE

NO OVERRIDE FLAG EXISTS. If this fails, the system is not safe to operate.
"""

import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

STATE_PATH = Path("runtime/state.json")
LEDGER_PATH = Path("evidence/ledger.jsonl")

REQUIRED_INVARIANTS = {
    "status": "GREEN",
    "readiness": 100,
    "governance_mode": "ACTIVE"
}

# ═══════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def load_state() -> Optional[Dict[str, Any]]:
    """Load system state from state.json"""
    if not STATE_PATH.exists():
        return None
    
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ CRITICAL: state.json is corrupted: {e}")
        return None


def sha256_file(path: Path) -> str:
    """Calculate SHA-256 hash of a file"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def log_guardrail_check(passed: bool, violations: list) -> None:
    """Log the guardrail check result to the ledger"""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "event": "GUARDRAIL_CHECK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "violations": violations,
        "state_hash": sha256_file(STATE_PATH) if STATE_PATH.exists() else None
    }
    
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_invariants(state: Dict[str, Any]) -> tuple[bool, list]:
    """
    Check all required invariants against the current state.
    
    Returns:
        Tuple of (all_passed, list_of_violations)
    """
    violations = []
    
    for key, expected in REQUIRED_INVARIANTS.items():
        actual = state.get(key)
        if actual != expected:
            violations.append({
                "invariant": key,
                "expected": expected,
                "actual": actual
            })
    
    return len(violations) == 0, violations


def print_status(state: Dict[str, Any]) -> None:
    """Print current system status"""
    print("\n" + "=" * 60)
    print("SOVEREIGN SANCTUARY ELITE - SAFETY GUARDRAIL CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z")
    print(f"State File: {STATE_PATH}")
    print("-" * 60)
    print("Current State:")
    for key in REQUIRED_INVARIANTS:
        actual = state.get(key, "MISSING")
        expected = REQUIRED_INVARIANTS[key]
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {key}: {actual} (expected: {expected})")
    print("-" * 60)


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    """
    Main entry point.
    
    Returns:
        0 if all guardrails pass, 1 otherwise
    """
    # Check state file exists
    if not STATE_PATH.exists():
        print("❌ CRITICAL: state.json missing")
        print(f"   Expected at: {STATE_PATH.absolute()}")
        print("\nCreate state.json with:")
        print(json.dumps({
            "status": "GREEN",
            "readiness": 100,
            "governance_mode": "ACTIVE"
        }, indent=2))
        log_guardrail_check(False, [{"error": "state.json missing"}])
        return 1
    
    # Load state
    state = load_state()
    if state is None:
        log_guardrail_check(False, [{"error": "state.json corrupted"}])
        return 1
    
    # Print status
    print_status(state)
    
    # Check invariants
    passed, violations = check_invariants(state)
    
    # Log result
    log_guardrail_check(passed, violations)
    
    if passed:
        print("✅ ALL SAFETY GUARDRAILS PASSED")
        print(f"   State Hash: {sha256_file(STATE_PATH)[:16]}...")
        print("\nSystem is SAFE to proceed with operations.")
        return 0
    else:
        print("❌ SAFETY GUARDRAILS FAILED")
        print("\nViolations:")
        for v in violations:
            print(f"  - {v['invariant']}: got {v['actual']}, expected {v['expected']}")
        print("\n⛔ OPERATIONS BLOCKED. Fix violations before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
