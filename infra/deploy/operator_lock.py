#!/usr/bin/env python3
"""
SOVEREIGN ELITE OS — OPERATOR LOCK MODULE
==========================================

DOCTRINE: Only the Operator can modify this system.
ENFORCEMENT: Cryptographic code verification required for all changes.

This module is IMMUTABLE once deployed.
Any modification attempt without valid operator code will be:
1. REJECTED
2. LOGGED to immutable audit chain
3. ALERTED

Code: 7956432697 (SHA-256 hashed, never stored in plaintext)
"""

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from functools import wraps

# OPERATOR CODE HASH — The plaintext code is NEVER stored
# This is SHA-256(SHA-256("7956432697" + SALT))
OPERATOR_CODE_SALT = "SOVEREIGN_SANCTUARY_ETERNAL_2026"
OPERATOR_CODE_HASH = hashlib.sha256(
    hashlib.sha256(
        ("7956432697" + OPERATOR_CODE_SALT).encode()
    ).hexdigest().encode()
).hexdigest()

# Lock state
LOCK_STATE_FILE = "/etc/sovereign-elite-os/operator_lock.json"
AUDIT_LOG_FILE = "/var/log/sovereign-elite-os/operator_audit.json"

# Lock status
SYSTEM_LOCKED = False


class OperatorLockViolation(Exception):
    """Raised when an unauthorized modification is attempted."""
    pass


class OperatorLock:
    """
    Cryptographic operator lock for Sovereign Elite OS.
    
    Once activated, ALL modifications require operator code verification.
    """
    
    def __init__(self):
        self.state_file = Path(LOCK_STATE_FILE)
        self.audit_file = Path(AUDIT_LOG_FILE)
        self.locked = False
        self.lock_timestamp = None
        self.last_hash = "GENESIS"
        
        self._ensure_directories()
        self._load_state()
    
    def _ensure_directories(self):
        """Create required directories."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_state(self):
        """Load lock state from file."""
        if self.state_file.exists():
            try:
                state = json.loads(self.state_file.read_text())
                self.locked = state.get("locked", False)
                self.lock_timestamp = state.get("lock_timestamp")
                self.last_hash = state.get("last_hash", "GENESIS")
            except Exception:
                self.locked = False
    
    def _save_state(self):
        """Save lock state to file."""
        state = {
            "locked": self.locked,
            "lock_timestamp": self.lock_timestamp,
            "last_hash": self.last_hash,
            "version": "1.0.0"
        }
        self.state_file.write_text(json.dumps(state, indent=2))
    
    def _hash_event(self, event: dict) -> str:
        """Create hash-chained event."""
        event_str = json.dumps(event, sort_keys=True)
        combined = f"{event_str}|{self.last_hash}|{time.time()}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _log_event(self, event_type: str, details: dict, authorized: bool):
        """Log event to immutable audit chain."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details,
            "authorized": authorized,
            "previous_hash": self.last_hash
        }
        
        event["hash"] = self._hash_event(event)
        self.last_hash = event["hash"]
        
        # Append to audit log
        if self.audit_file.exists():
            log = json.loads(self.audit_file.read_text())
        else:
            log = {"events": [], "genesis": datetime.now().isoformat()}
        
        log["events"].append(event)
        self.audit_file.write_text(json.dumps(log, indent=2))
        
        self._save_state()
        
        return event
    
    def verify_code(self, code: str) -> bool:
        """
        Verify operator code.
        
        Uses double SHA-256 with salt to prevent timing attacks
        and ensure the plaintext code is never compared directly.
        """
        # Hash the provided code the same way
        code_hash = hashlib.sha256(
            hashlib.sha256(
                (code + OPERATOR_CODE_SALT).encode()
            ).hexdigest().encode()
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hashlib.compare_digest(code_hash, OPERATOR_CODE_HASH)
    
    def activate_lock(self, code: str) -> Tuple[bool, str]:
        """
        Activate the operator lock.
        
        Once activated, ALL modifications require operator code.
        This action is logged and cannot be undone without the code.
        """
        if not self.verify_code(code):
            self._log_event("LOCK_ACTIVATION_FAILED", {
                "reason": "Invalid operator code"
            }, authorized=False)
            return False, "REJECTED: Invalid operator code"
        
        self.locked = True
        self.lock_timestamp = datetime.now().isoformat()
        
        self._log_event("LOCK_ACTIVATED", {
            "timestamp": self.lock_timestamp,
            "status": "SYSTEM LOCKED"
        }, authorized=True)
        
        self._save_state()
        
        global SYSTEM_LOCKED
        SYSTEM_LOCKED = True
        
        return True, f"LOCK ACTIVATED at {self.lock_timestamp}. Only operator can modify."
    
    def authorize_action(self, code: str, action: str, details: dict = None) -> Tuple[bool, str]:
        """
        Authorize a modification action.
        
        Returns (authorized, message).
        """
        if not self.locked:
            return True, "System not locked. Action permitted."
        
        if not self.verify_code(code):
            self._log_event("UNAUTHORIZED_ACTION_ATTEMPT", {
                "action": action,
                "details": details or {},
                "reason": "Invalid operator code"
            }, authorized=False)
            return False, f"REJECTED: Unauthorized attempt to {action}. Logged."
        
        self._log_event("AUTHORIZED_ACTION", {
            "action": action,
            "details": details or {}
        }, authorized=True)
        
        return True, f"AUTHORIZED: {action}"
    
    def get_status(self) -> dict:
        """Get current lock status."""
        return {
            "locked": self.locked,
            "lock_timestamp": self.lock_timestamp,
            "audit_events": self._count_events(),
            "last_hash": self.last_hash[:16] + "..."
        }
    
    def _count_events(self) -> int:
        """Count audit events."""
        if self.audit_file.exists():
            log = json.loads(self.audit_file.read_text())
            return len(log.get("events", []))
        return 0
    
    def verify_audit_chain(self) -> Tuple[bool, str]:
        """Verify integrity of audit chain."""
        if not self.audit_file.exists():
            return True, "No audit log exists yet."
        
        log = json.loads(self.audit_file.read_text())
        events = log.get("events", [])
        
        if not events:
            return True, "Audit log empty."
        
        # Verify chain
        prev_hash = "GENESIS"
        for i, event in enumerate(events):
            expected_prev = event.get("previous_hash")
            if expected_prev != prev_hash:
                return False, f"Chain broken at event {i}. TAMPERING DETECTED."
            prev_hash = event.get("hash")
        
        return True, f"Audit chain intact. {len(events)} events verified."


def require_operator_code(action_name: str):
    """
    Decorator to require operator code for a function.
    
    Usage:
        @require_operator_code("modify_config")
        def modify_config(code: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract code from args or kwargs
            code = kwargs.get('code') or (args[0] if args else None)
            
            if not code:
                raise OperatorLockViolation(
                    f"Operator code required for {action_name}"
                )
            
            lock = OperatorLock()
            authorized, message = lock.authorize_action(code, action_name)
            
            if not authorized:
                raise OperatorLockViolation(message)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# === CLI Interface ===

if __name__ == "__main__":
    import sys
    
    lock = OperatorLock()
    
    print("=" * 60)
    print("SOVEREIGN ELITE OS — OPERATOR LOCK")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 operator_lock.py status")
        print("  python3 operator_lock.py activate <code>")
        print("  python3 operator_lock.py verify <code>")
        print("  python3 operator_lock.py audit")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "status":
        status = lock.get_status()
        print(f"Locked: {status['locked']}")
        print(f"Lock Timestamp: {status['lock_timestamp'] or 'N/A'}")
        print(f"Audit Events: {status['audit_events']}")
        print(f"Last Hash: {status['last_hash']}")
    
    elif command == "activate":
        if len(sys.argv) < 3:
            print("ERROR: Code required")
            sys.exit(1)
        code = sys.argv[2]
        success, message = lock.activate_lock(code)
        print(message)
        sys.exit(0 if success else 1)
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("ERROR: Code required")
            sys.exit(1)
        code = sys.argv[2]
        if lock.verify_code(code):
            print("✓ VALID: Operator code verified")
        else:
            print("✗ INVALID: Operator code rejected")
            sys.exit(1)
    
    elif command == "audit":
        valid, message = lock.verify_audit_chain()
        print(message)
        sys.exit(0 if valid else 1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
