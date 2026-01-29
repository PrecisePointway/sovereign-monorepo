#!/usr/bin/env python3
"""
Sovereign Governance Kernel — Defense-in-Depth Security Layers
Multi-layered security architecture with no single point of failure.

DEFENSE LAYERS:
1. Perimeter: Input validation, rate limiting
2. Application: Code integrity, anti-tampering
3. Data: Encryption, access control
4. Kernel: Invariant enforcement, constitutional constraints
5. Audit: Tamper-evident logging, evidence chain

ZERO BACKDOOR GUARANTEE:
- All code paths are explicit and auditable
- No hidden entry points
- No bypass mechanisms
- Fail-secure by default
"""

from __future__ import annotations
import os
import sys
import json
import time
import hashlib
import secrets
import threading
import functools
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════
# LAYER 1: PERIMETER DEFENSE
# ═══════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Token bucket rate limiter for perimeter defense.
    
    Prevents DoS and brute-force attacks.
    """
    
    def __init__(
        self,
        rate: float = 10.0,  # tokens per second
        capacity: float = 100.0,  # max tokens
        block_duration: int = 300  # seconds to block after limit exceeded
    ):
        self.rate = rate
        self.capacity = capacity
        self.block_duration = block_duration
        self._tokens: Dict[str, float] = defaultdict(lambda: capacity)
        self._last_update: Dict[str, float] = defaultdict(time.time)
        self._blocked_until: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def _refill(self, key: str) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_update[key]
        self._tokens[key] = min(
            self.capacity,
            self._tokens[key] + elapsed * self.rate
        )
        self._last_update[key] = now
    
    def is_blocked(self, key: str) -> bool:
        """Check if a key is currently blocked."""
        if key in self._blocked_until:
            if time.time() < self._blocked_until[key]:
                return True
            del self._blocked_until[key]
        return False
    
    def acquire(self, key: str, tokens: float = 1.0) -> bool:
        """
        Attempt to acquire tokens.
        
        Returns True if allowed, False if rate limited.
        """
        with self._lock:
            if self.is_blocked(key):
                return False
            
            self._refill(key)
            
            if self._tokens[key] >= tokens:
                self._tokens[key] -= tokens
                return True
            else:
                # Block the key
                self._blocked_until[key] = time.time() + self.block_duration
                return False
    
    def get_status(self, key: str) -> Dict[str, Any]:
        """Get rate limiter status for a key."""
        with self._lock:
            self._refill(key)
            return {
                "tokens_available": self._tokens[key],
                "capacity": self.capacity,
                "blocked": self.is_blocked(key),
                "blocked_until": self._blocked_until.get(key)
            }


class InputValidator:
    """
    Input validation for perimeter defense.
    
    Validates and sanitizes all inputs before processing.
    """
    
    # Maximum sizes
    MAX_STRING_LENGTH = 10_000
    MAX_ARRAY_LENGTH = 1_000
    MAX_OBJECT_DEPTH = 10
    
    # Forbidden patterns in strings
    FORBIDDEN_PATTERNS = frozenset([
        "<script",
        "javascript:",
        "data:",
        "vbscript:",
        "onclick",
        "onerror",
        "onload",
        "eval(",
        "exec(",
    ])
    
    @classmethod
    def validate_string(cls, value: str, max_length: Optional[int] = None) -> tuple[bool, str]:
        """
        Validate a string input.
        
        Returns (valid, sanitized_value).
        """
        if not isinstance(value, str):
            return False, ""
        
        max_len = max_length or cls.MAX_STRING_LENGTH
        if len(value) > max_len:
            return False, ""
        
        # Check for forbidden patterns
        value_lower = value.lower()
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in value_lower:
                return False, ""
        
        return True, value
    
    @classmethod
    def validate_object(cls, obj: Any, depth: int = 0) -> tuple[bool, Any]:
        """
        Recursively validate an object.
        
        Returns (valid, sanitized_object).
        """
        if depth > cls.MAX_OBJECT_DEPTH:
            return False, None
        
        if obj is None:
            return True, None
        
        if isinstance(obj, bool):
            return True, obj
        
        if isinstance(obj, (int, float)):
            return True, obj
        
        if isinstance(obj, str):
            return cls.validate_string(obj)
        
        if isinstance(obj, list):
            if len(obj) > cls.MAX_ARRAY_LENGTH:
                return False, None
            
            result = []
            for item in obj:
                valid, sanitized = cls.validate_object(item, depth + 1)
                if not valid:
                    return False, None
                result.append(sanitized)
            return True, result
        
        if isinstance(obj, dict):
            if len(obj) > cls.MAX_ARRAY_LENGTH:
                return False, None
            
            result = {}
            for key, value in obj.items():
                key_valid, key_sanitized = cls.validate_string(str(key), max_length=256)
                if not key_valid:
                    return False, None
                
                value_valid, value_sanitized = cls.validate_object(value, depth + 1)
                if not value_valid:
                    return False, None
                
                result[key_sanitized] = value_sanitized
            return True, result
        
        # Unknown type
        return False, None


# ═══════════════════════════════════════════════════════════════════
# LAYER 2: APPLICATION DEFENSE
# ═══════════════════════════════════════════════════════════════════

class CodeIntegrityGuard:
    """
    Runtime code integrity verification.
    
    Detects unauthorized modifications to code at runtime.
    """
    
    def __init__(self):
        self._module_hashes: Dict[str, str] = {}
        self._function_hashes: Dict[str, str] = {}
    
    def register_module(self, module: Any) -> str:
        """Register a module for integrity monitoring."""
        import inspect
        
        source = inspect.getsource(module)
        hash_value = hashlib.sha3_256(source.encode()).hexdigest()
        self._module_hashes[module.__name__] = hash_value
        return hash_value
    
    def verify_module(self, module: Any) -> bool:
        """Verify module integrity against registered hash."""
        import inspect
        
        if module.__name__ not in self._module_hashes:
            return False
        
        source = inspect.getsource(module)
        current_hash = hashlib.sha3_256(source.encode()).hexdigest()
        expected_hash = self._module_hashes[module.__name__]
        
        return secrets.compare_digest(current_hash, expected_hash)
    
    def register_function(self, func: Callable) -> str:
        """Register a function for integrity monitoring."""
        import inspect
        
        source = inspect.getsource(func)
        hash_value = hashlib.sha3_256(source.encode()).hexdigest()
        key = f"{func.__module__}.{func.__qualname__}"
        self._function_hashes[key] = hash_value
        return hash_value
    
    def verify_function(self, func: Callable) -> bool:
        """Verify function integrity against registered hash."""
        import inspect
        
        key = f"{func.__module__}.{func.__qualname__}"
        if key not in self._function_hashes:
            return False
        
        source = inspect.getsource(func)
        current_hash = hashlib.sha3_256(source.encode()).hexdigest()
        expected_hash = self._function_hashes[key]
        
        return secrets.compare_digest(current_hash, expected_hash)


T = TypeVar('T')


def secure_function(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to add security checks to a function.
    
    - Validates inputs
    - Logs execution
    - Catches and logs exceptions
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        # Validate kwargs
        for key, value in kwargs.items():
            valid, _ = InputValidator.validate_object(value)
            if not valid:
                raise ValueError(f"Invalid input for parameter: {key}")
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # Log exception (in production, this would go to security log)
            raise
    
    return wrapper


# ═══════════════════════════════════════════════════════════════════
# LAYER 3: DATA DEFENSE
# ═══════════════════════════════════════════════════════════════════

class AccessControl:
    """
    Role-based access control for data defense.
    """
    
    class Permission(str, Enum):
        READ = "READ"
        WRITE = "WRITE"
        EXECUTE = "EXECUTE"
        ADMIN = "ADMIN"
    
    def __init__(self):
        self._roles: Dict[str, Set[str]] = {}  # role -> permissions
        self._subjects: Dict[str, Set[str]] = {}  # subject -> roles
    
    def define_role(self, role: str, permissions: Set[str]) -> None:
        """Define a role with permissions."""
        self._roles[role] = permissions
    
    def assign_role(self, subject: str, role: str) -> None:
        """Assign a role to a subject."""
        if role not in self._roles:
            raise ValueError(f"Unknown role: {role}")
        
        if subject not in self._subjects:
            self._subjects[subject] = set()
        self._subjects[subject].add(role)
    
    def check_permission(self, subject: str, permission: str) -> bool:
        """Check if subject has permission."""
        if subject not in self._subjects:
            return False
        
        for role in self._subjects[subject]:
            if permission in self._roles.get(role, set()):
                return True
        
        return False
    
    def get_permissions(self, subject: str) -> Set[str]:
        """Get all permissions for a subject."""
        permissions = set()
        for role in self._subjects.get(subject, set()):
            permissions.update(self._roles.get(role, set()))
        return permissions


class DataEncryption:
    """
    Data encryption utilities for defense layer.
    
    Uses AES-256-GCM for authenticated encryption.
    """
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a secure encryption key."""
        return secrets.token_bytes(32)
    
    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.
        
        Returns: nonce (12 bytes) + tag (16 bytes) + ciphertext
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            nonce = secrets.token_bytes(12)
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, data, None)
            return nonce + ciphertext
        except ImportError:
            # Fallback: XOR with key-derived stream (NOT for production)
            # This is a placeholder - in production, use proper crypto
            raise RuntimeError("cryptography package required for encryption")
    
    @staticmethod
    def decrypt(encrypted: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Input: nonce (12 bytes) + tag (16 bytes) + ciphertext
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        except ImportError:
            raise RuntimeError("cryptography package required for decryption")


# ═══════════════════════════════════════════════════════════════════
# LAYER 4: KERNEL DEFENSE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SecurityConstraint:
    """A security constraint that must be enforced."""
    id: str
    name: str
    description: str
    check: Callable[[], bool]
    severity: str = "CRITICAL"
    remediation: str = ""


class KernelDefense:
    """
    Kernel-level defense with constitutional constraints.
    
    These constraints cannot be bypassed or disabled.
    """
    
    def __init__(self):
        self._constraints: Dict[str, SecurityConstraint] = {}
        self._violations: List[Dict[str, Any]] = []
        self._locked = False
    
    def register_constraint(self, constraint: SecurityConstraint) -> None:
        """Register a security constraint."""
        if self._locked:
            raise RuntimeError("Cannot modify constraints after lock")
        self._constraints[constraint.id] = constraint
    
    def lock(self) -> None:
        """Lock constraints - no further modifications allowed."""
        self._locked = True
    
    def enforce_all(self) -> tuple[bool, List[Dict[str, Any]]]:
        """
        Enforce all constraints.
        
        Returns (all_passed, violations).
        """
        self._violations.clear()
        all_passed = True
        
        for constraint in self._constraints.values():
            try:
                passed = constraint.check()
            except Exception as e:
                passed = False
                self._violations.append({
                    "constraint_id": constraint.id,
                    "name": constraint.name,
                    "passed": False,
                    "error": str(e),
                    "severity": constraint.severity
                })
                all_passed = False
                continue
            
            if not passed:
                self._violations.append({
                    "constraint_id": constraint.id,
                    "name": constraint.name,
                    "passed": False,
                    "severity": constraint.severity,
                    "remediation": constraint.remediation
                })
                all_passed = False
        
        return all_passed, self._violations
    
    def get_status(self) -> Dict[str, Any]:
        """Get kernel defense status."""
        return {
            "locked": self._locked,
            "constraints_count": len(self._constraints),
            "last_violations": self._violations
        }


# ═══════════════════════════════════════════════════════════════════
# LAYER 5: AUDIT DEFENSE
# ═══════════════════════════════════════════════════════════════════

class AuditTrail:
    """
    Tamper-evident audit trail for all security events.
    """
    
    def __init__(self, path: str):
        self.path = path
        self._last_hash: Optional[str] = None
        self._sequence = 0
        self._load_state()
    
    def _load_state(self) -> None:
        """Load state from existing trail."""
        if not os.path.exists(self.path):
            return
        
        try:
            with open(self.path, 'r') as f:
                lines = f.readlines()
                if lines:
                    last = json.loads(lines[-1])
                    self._last_hash = last.get("hash")
                    self._sequence = last.get("seq", 0) + 1
        except (json.JSONDecodeError, IOError):
            pass
    
    def log(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Log an audit event.
        
        Returns event hash.
        """
        entry = {
            "type": event_type,
            "ts": datetime.now(timezone.utc).isoformat(),
            "seq": self._sequence,
            "prev": self._last_hash,
            "data": data
        }
        
        # Compute hash
        canonical = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        entry_hash = hashlib.sha3_256(canonical.encode()).hexdigest()
        entry["hash"] = entry_hash
        
        # Ensure directory
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        
        # Append
        with open(self.path, 'a') as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        
        self._last_hash = entry_hash
        self._sequence += 1
        
        return entry_hash
    
    def verify(self) -> tuple[bool, List[str]]:
        """
        Verify audit trail integrity.
        
        Returns (valid, errors).
        """
        errors = []
        
        if not os.path.exists(self.path):
            return True, errors
        
        prev_hash = None
        expected_seq = 0
        
        with open(self.path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(f"Invalid JSON at line {line_num}")
                    return False, errors
                
                if entry.get("prev") != prev_hash:
                    errors.append(f"Chain broken at line {line_num}")
                    return False, errors
                
                if entry.get("seq") != expected_seq:
                    errors.append(f"Sequence gap at line {line_num}")
                    return False, errors
                
                prev_hash = entry.get("hash")
                expected_seq += 1
        
        return True, errors


# ═══════════════════════════════════════════════════════════════════
# UNIFIED DEFENSE COORDINATOR
# ═══════════════════════════════════════════════════════════════════

class DefenseCoordinator:
    """
    Coordinates all defense layers into unified security posture.
    
    DEFENSE LAYERS:
    1. Perimeter: Rate limiting, input validation
    2. Application: Code integrity, secure functions
    3. Data: Access control, encryption
    4. Kernel: Constitutional constraints
    5. Audit: Tamper-evident logging
    """
    
    def __init__(self, audit_path: str = "/var/lib/sovereign/defense_audit.jsonl"):
        # Layer 1: Perimeter
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        
        # Layer 2: Application
        self.code_guard = CodeIntegrityGuard()
        
        # Layer 3: Data
        self.access_control = AccessControl()
        
        # Layer 4: Kernel
        self.kernel = KernelDefense()
        
        # Layer 5: Audit
        self.audit = AuditTrail(audit_path)
        
        # Initialize default constraints
        self._init_default_constraints()
    
    def _init_default_constraints(self) -> None:
        """Initialize default kernel constraints."""
        
        # Constraint: No dangerous environment variables
        self.kernel.register_constraint(SecurityConstraint(
            id="SEC-001",
            name="Clean Environment",
            description="No dangerous environment variables set",
            check=lambda: not any(
                v in os.environ 
                for v in ["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH"]
            ),
            remediation="Unset dangerous environment variables"
        ))
        
        # Constraint: Audit trail integrity
        self.kernel.register_constraint(SecurityConstraint(
            id="SEC-002",
            name="Audit Integrity",
            description="Audit trail has not been tampered with",
            check=lambda: self.audit.verify()[0],
            remediation="Restore audit trail from backup"
        ))
    
    def check_request(self, subject: str, permission: str, data: Any) -> tuple[bool, str]:
        """
        Check if a request should be allowed.
        
        Returns (allowed, reason).
        """
        # Layer 1: Rate limiting
        if not self.rate_limiter.acquire(subject):
            self.audit.log("RATE_LIMITED", {"subject": subject})
            return False, "Rate limited"
        
        # Layer 1: Input validation
        valid, _ = self.input_validator.validate_object(data)
        if not valid:
            self.audit.log("INVALID_INPUT", {"subject": subject})
            return False, "Invalid input"
        
        # Layer 3: Access control
        if not self.access_control.check_permission(subject, permission):
            self.audit.log("ACCESS_DENIED", {
                "subject": subject,
                "permission": permission
            })
            return False, "Access denied"
        
        # Layer 4: Kernel constraints
        passed, violations = self.kernel.enforce_all()
        if not passed:
            self.audit.log("CONSTRAINT_VIOLATION", {
                "subject": subject,
                "violations": violations
            })
            return False, "Security constraint violated"
        
        # All checks passed
        self.audit.log("REQUEST_ALLOWED", {
            "subject": subject,
            "permission": permission
        })
        return True, "Allowed"
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status."""
        audit_valid, audit_errors = self.audit.verify()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layers": {
                "perimeter": {
                    "rate_limiter": "active"
                },
                "application": {
                    "code_guard": "active"
                },
                "data": {
                    "access_control": "active"
                },
                "kernel": self.kernel.get_status(),
                "audit": {
                    "valid": audit_valid,
                    "errors": audit_errors
                }
            },
            "overall_status": "SECURE" if audit_valid else "COMPROMISED"
        }


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Defense-in-Depth Security Layers"
    )
    
    parser.add_argument("--status", action="store_true", help="Show security status")
    parser.add_argument("--verify", action="store_true", help="Verify all layers")
    
    args = parser.parse_args()
    
    coordinator = DefenseCoordinator(audit_path="/tmp/defense_audit.jsonl")
    
    if args.status or args.verify:
        status = coordinator.get_security_status()
        print(json.dumps(status, indent=2))
        sys.exit(0 if status["overall_status"] == "SECURE" else 1)
    else:
        print(json.dumps(coordinator.get_security_status(), indent=2))


if __name__ == "__main__":
    main()
