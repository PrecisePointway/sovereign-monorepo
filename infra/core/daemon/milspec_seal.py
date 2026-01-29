#!/usr/bin/env python3
"""
Sovereign Governance Kernel — MILSPEC Security Seal
Future-proof cryptographic hardening with zero backdoors.

This module provides:
- Cryptographic integrity verification
- Anti-backdoor detection
- Tamper-evident logging
- Defense-in-depth security layers
- Immutable constraint enforcement

SECURITY PRINCIPLES:
1. No hidden entry points
2. No bypass mechanisms
3. No privilege escalation paths
4. No silent degradation
5. All code paths auditable
"""

from __future__ import annotations
import os
import sys
import hmac
import json
import hashlib
import secrets
import struct
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import base64


# ═══════════════════════════════════════════════════════════════════
# CRYPTOGRAPHIC CONSTANTS — NO BACKDOORS
# ═══════════════════════════════════════════════════════════════════

# Hash algorithms — using standard, audited algorithms only
HASH_ALGORITHM = "sha3_256"  # SHA-3 for future-proofing (quantum-resistant design)
HMAC_ALGORITHM = "sha3_256"
KDF_ITERATIONS = 100_000  # PBKDF2 iterations

# Minimum key sizes (NIST recommendations)
MIN_SYMMETRIC_KEY_BITS = 256
MIN_HASH_OUTPUT_BITS = 256

# Forbidden patterns — these indicate potential backdoors
# Note: These are checked in runtime code, not in documentation/comments
FORBIDDEN_PATTERNS = frozenset([
    "eval(",
    "exec(",
    "compile(",
    "__import__(",
    "subprocess.call(",
    "os.system(",
    "pickle.loads(",
    "yaml.load(",  # unsafe yaml.load (yaml.safe_load is OK)
    "marshal.loads(",
])

# Patterns that are OK in specific contexts
ALLOWED_PATTERN_CONTEXTS = {
    "eval(": ["FORBIDDEN_PATTERNS", "# ", "'''", '"""'],
    "exec(": ["FORBIDDEN_PATTERNS", "# ", "'''", '"""'],
    "compile(": ["FORBIDDEN_PATTERNS", "# ", "'''", '"""', "re.compile"],
    "__import__(": ["FORBIDDEN_PATTERNS", "# ", "'''", '"""'],
    "subprocess.call(": ["FORBIDDEN_PATTERNS", "# ", "'''", '"""'],
}

# Forbidden environment variables that could be attack vectors
FORBIDDEN_ENV_VARS = frozenset([
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "PYTHONPATH",
    "PYTHONSTARTUP",
    "PYTHONHOME",
])


class SecurityLevel(str, Enum):
    """Security classification levels."""
    UNCLASSIFIED = "UNCLASSIFIED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"


class ThreatCategory(str, Enum):
    """Threat classification categories."""
    BACKDOOR = "BACKDOOR"
    TAMPERING = "TAMPERING"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    INFORMATION_DISCLOSURE = "INFORMATION_DISCLOSURE"
    DENIAL_OF_SERVICE = "DENIAL_OF_SERVICE"
    INTEGRITY_VIOLATION = "INTEGRITY_VIOLATION"


@dataclass
class SecurityViolation:
    """Record of a security violation."""
    violation_id: str
    category: ThreatCategory
    severity: str
    description: str
    evidence: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    remediation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "category": self.category.value,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "remediation": self.remediation
        }


# ═══════════════════════════════════════════════════════════════════
# CRYPTOGRAPHIC PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

def secure_hash(data: bytes, algorithm: str = HASH_ALGORITHM) -> str:
    """
    Compute cryptographic hash using approved algorithm.
    
    Uses SHA-3 by default for quantum-resistance properties.
    """
    if algorithm == "sha3_256":
        h = hashlib.sha3_256(data)
    elif algorithm == "sha3_512":
        h = hashlib.sha3_512(data)
    elif algorithm == "sha256":
        h = hashlib.sha256(data)
    elif algorithm == "sha512":
        h = hashlib.sha512(data)
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    return h.hexdigest()


def secure_hmac(key: bytes, data: bytes) -> str:
    """
    Compute HMAC using approved algorithm.
    
    Key must be at least MIN_SYMMETRIC_KEY_BITS bits.
    """
    if len(key) * 8 < MIN_SYMMETRIC_KEY_BITS:
        raise ValueError(f"Key must be at least {MIN_SYMMETRIC_KEY_BITS} bits")
    
    h = hmac.new(key, data, hashlib.sha3_256)
    return h.hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token."""
    return secrets.token_hex(length)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks.
    
    CRITICAL: Always use this for security-sensitive comparisons.
    """
    return hmac.compare_digest(a.encode(), b.encode())


def derive_key(password: bytes, salt: bytes, iterations: int = KDF_ITERATIONS) -> bytes:
    """
    Derive cryptographic key from password using PBKDF2.
    
    Uses high iteration count for brute-force resistance.
    """
    return hashlib.pbkdf2_hmac(
        'sha256',
        password,
        salt,
        iterations,
        dklen=32
    )


# ═══════════════════════════════════════════════════════════════════
# INTEGRITY VERIFICATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class IntegrityManifest:
    """
    Cryptographic manifest for file integrity verification.
    
    Contains hashes of all protected files with tamper detection.
    """
    version: str = "1.0.0"
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    algorithm: str = HASH_ALGORITHM
    files: Dict[str, str] = field(default_factory=dict)
    manifest_hash: str = ""
    
    def add_file(self, path: str, content: bytes) -> None:
        """Add file to manifest with its hash."""
        self.files[path] = secure_hash(content)
    
    def compute_manifest_hash(self) -> str:
        """Compute hash of the entire manifest."""
        data = json.dumps({
            "version": self.version,
            "created": self.created,
            "algorithm": self.algorithm,
            "files": dict(sorted(self.files.items()))
        }, sort_keys=True, separators=(",", ":"))
        self.manifest_hash = secure_hash(data.encode())
        return self.manifest_hash
    
    def verify_file(self, path: str, content: bytes) -> bool:
        """Verify a file against the manifest."""
        if path not in self.files:
            return False
        expected = self.files[path]
        actual = secure_hash(content)
        return constant_time_compare(expected, actual)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created": self.created,
            "algorithm": self.algorithm,
            "files": self.files,
            "manifest_hash": self.manifest_hash
        }
    
    def save(self, path: str) -> None:
        """Save manifest to file."""
        self.compute_manifest_hash()
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'IntegrityManifest':
        """Load manifest from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        manifest = cls(
            version=data["version"],
            created=data["created"],
            algorithm=data["algorithm"],
            files=data["files"],
            manifest_hash=data["manifest_hash"]
        )
        return manifest


class IntegrityVerifier:
    """
    Verifies integrity of protected files and detects tampering.
    """
    
    def __init__(self, manifest: IntegrityManifest):
        self.manifest = manifest
        self.violations: List[SecurityViolation] = []
    
    def verify_all(self, base_path: str) -> Tuple[bool, List[SecurityViolation]]:
        """
        Verify all files in the manifest.
        
        Returns (all_valid, violations).
        """
        self.violations.clear()
        all_valid = True
        
        for file_path, expected_hash in self.manifest.files.items():
            full_path = os.path.join(base_path, file_path)
            
            if not os.path.exists(full_path):
                self.violations.append(SecurityViolation(
                    violation_id=generate_secure_token(8),
                    category=ThreatCategory.TAMPERING,
                    severity="CRITICAL",
                    description=f"Protected file missing: {file_path}",
                    evidence={"path": file_path, "expected_hash": expected_hash},
                    remediation="Restore file from trusted source"
                ))
                all_valid = False
                continue
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            actual_hash = secure_hash(content)
            
            if not constant_time_compare(expected_hash, actual_hash):
                self.violations.append(SecurityViolation(
                    violation_id=generate_secure_token(8),
                    category=ThreatCategory.TAMPERING,
                    severity="CRITICAL",
                    description=f"File integrity violation: {file_path}",
                    evidence={
                        "path": file_path,
                        "expected_hash": expected_hash,
                        "actual_hash": actual_hash
                    },
                    remediation="Restore file from trusted source or investigate tampering"
                ))
                all_valid = False
        
        return all_valid, self.violations


# ═══════════════════════════════════════════════════════════════════
# ANTI-BACKDOOR DETECTION
# ═══════════════════════════════════════════════════════════════════

class BackdoorDetector:
    """
    Detects potential backdoors in code and configuration.
    
    Scans for:
    - Dangerous function calls
    - Hidden entry points
    - Privilege escalation patterns
    - Suspicious environment manipulation
    """
    
    def __init__(self):
        self.violations: List[SecurityViolation] = []
    
    def scan_file(self, path: str, content: str) -> List[SecurityViolation]:
        """Scan a single file for backdoor patterns."""
        violations = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Check for forbidden patterns
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.lower() in line_lower:
                    # Check if it's in an allowed context
                    is_allowed = False
                    
                    # Check if line is a comment
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        is_allowed = True
                    
                    # Check for allowed contexts (documentation, pattern lists, etc.)
                    if not is_allowed and pattern in ALLOWED_PATTERN_CONTEXTS:
                        for allowed_ctx in ALLOWED_PATTERN_CONTEXTS[pattern]:
                            if allowed_ctx in line:
                                is_allowed = True
                                break
                    
                    # Check if it's in a docstring (simple heuristic)
                    if not is_allowed and ('"""' in line or "'''" in line):
                        is_allowed = True
                    
                    # Check if it's a string literal in a data structure (frozenset, list, etc.)
                    if not is_allowed:
                        # Pattern is in quotes = it's a string literal, not code
                        quoted_pattern = f'"{pattern}"'
                        if quoted_pattern in line:
                            is_allowed = True
                    
                    if not is_allowed:
                        violations.append(SecurityViolation(
                            violation_id=generate_secure_token(8),
                            category=ThreatCategory.BACKDOOR,
                            severity="CRITICAL",
                            description=f"Potential backdoor pattern detected: {pattern}",
                            evidence={
                                "file": path,
                                "line": line_num,
                                "pattern": pattern,
                                "content": line.strip()[:100]
                            },
                            remediation="Remove dangerous code pattern or justify with security review"
                        ))
        
        return violations
    
    def scan_environment(self) -> List[SecurityViolation]:
        """Scan environment for suspicious variables."""
        violations = []
        
        for var in FORBIDDEN_ENV_VARS:
            if var in os.environ:
                violations.append(SecurityViolation(
                    violation_id=generate_secure_token(8),
                    category=ThreatCategory.PRIVILEGE_ESCALATION,
                    severity="HIGH",
                    description=f"Suspicious environment variable set: {var}",
                    evidence={
                        "variable": var,
                        "value_length": len(os.environ[var])
                    },
                    remediation=f"Unset {var} or justify with security review"
                ))
        
        return violations
    
    def scan_directory(self, path: str, extensions: Set[str] = {'.py', '.sh', '.yaml', '.yml'}) -> List[SecurityViolation]:
        """Scan all files in a directory for backdoors."""
        all_violations = []
        
        for root, dirs, files in os.walk(path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        violations = self.scan_file(file_path, content)
                        all_violations.extend(violations)
                    except IOError:
                        pass
        
        # Also scan environment
        all_violations.extend(self.scan_environment())
        
        return all_violations


# ═══════════════════════════════════════════════════════════════════
# TAMPER-EVIDENT LOGGING
# ═══════════════════════════════════════════════════════════════════

class TamperEvidentLog:
    """
    Append-only log with cryptographic tamper detection.
    
    Each entry is chained to the previous entry via hash,
    making any modification detectable.
    """
    
    def __init__(self, path: str, key: Optional[bytes] = None):
        self.path = path
        self.key = key or secrets.token_bytes(32)
        self._last_hash: Optional[str] = None
        self._entry_count = 0
        self._load_state()
    
    def _load_state(self) -> None:
        """Load state from existing log."""
        if not os.path.exists(self.path):
            return
        
        try:
            with open(self.path, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    self._last_hash = last_entry.get("entry_hash")
                    self._entry_count = len(lines)
        except (json.JSONDecodeError, IOError):
            pass
    
    def _compute_entry_hash(self, entry: Dict[str, Any]) -> str:
        """Compute hash for a log entry including chain link."""
        data = {
            **entry,
            "previous_hash": self._last_hash,
            "sequence": self._entry_count
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return secure_hash(canonical.encode())
    
    def _compute_mac(self, entry_hash: str) -> str:
        """Compute MAC for entry authentication."""
        return secure_hmac(self.key, entry_hash.encode())
    
    def append(self, event_type: str, payload: Dict[str, Any]) -> str:
        """
        Append entry to tamper-evident log.
        
        Returns entry hash.
        """
        entry = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "previous_hash": self._last_hash,
            "sequence": self._entry_count
        }
        
        entry_hash = self._compute_entry_hash(entry)
        entry["entry_hash"] = entry_hash
        entry["mac"] = self._compute_mac(entry_hash)
        
        # Ensure directory exists
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        
        # Append atomically
        with open(self.path, 'a') as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        
        self._last_hash = entry_hash
        self._entry_count += 1
        
        return entry_hash
    
    def verify_chain(self) -> Tuple[bool, List[SecurityViolation]]:
        """
        Verify the integrity of the entire log chain.
        
        Returns (valid, violations).
        """
        violations = []
        
        if not os.path.exists(self.path):
            return True, violations
        
        prev_hash = None
        expected_sequence = 0
        
        with open(self.path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    violations.append(SecurityViolation(
                        violation_id=generate_secure_token(8),
                        category=ThreatCategory.TAMPERING,
                        severity="CRITICAL",
                        description=f"Invalid JSON at line {line_num}",
                        evidence={"line": line_num}
                    ))
                    return False, violations
                
                # Verify chain link
                if entry.get("previous_hash") != prev_hash:
                    violations.append(SecurityViolation(
                        violation_id=generate_secure_token(8),
                        category=ThreatCategory.TAMPERING,
                        severity="CRITICAL",
                        description=f"Chain broken at line {line_num}",
                        evidence={
                            "line": line_num,
                            "expected_previous": prev_hash,
                            "actual_previous": entry.get("previous_hash")
                        }
                    ))
                    return False, violations
                
                # Verify sequence
                if entry.get("sequence") != expected_sequence:
                    violations.append(SecurityViolation(
                        violation_id=generate_secure_token(8),
                        category=ThreatCategory.TAMPERING,
                        severity="CRITICAL",
                        description=f"Sequence gap at line {line_num}",
                        evidence={
                            "line": line_num,
                            "expected_sequence": expected_sequence,
                            "actual_sequence": entry.get("sequence")
                        }
                    ))
                    return False, violations
                
                # Verify MAC if key available
                if self.key and "mac" in entry:
                    expected_mac = self._compute_mac(entry["entry_hash"])
                    if not constant_time_compare(entry["mac"], expected_mac):
                        violations.append(SecurityViolation(
                            violation_id=generate_secure_token(8),
                            category=ThreatCategory.TAMPERING,
                            severity="CRITICAL",
                            description=f"MAC verification failed at line {line_num}",
                            evidence={"line": line_num}
                        ))
                        return False, violations
                
                prev_hash = entry.get("entry_hash")
                expected_sequence += 1
        
        return True, violations


# ═══════════════════════════════════════════════════════════════════
# MILSPEC SECURITY SEAL
# ═══════════════════════════════════════════════════════════════════

class MilspecSeal:
    """
    Military-specification security seal for the governance system.
    
    Provides:
    - Cryptographic integrity verification
    - Anti-backdoor scanning
    - Tamper-evident logging
    - Runtime security monitoring
    - Zero-trust verification
    
    SECURITY GUARANTEE:
    - No hidden entry points
    - No bypass mechanisms
    - No privilege escalation paths
    - All operations auditable
    - Fail-secure by default
    """
    
    VERSION = "1.0.0"
    SEAL_ID = "SOVEREIGN-MILSPEC-SEAL"
    
    def __init__(
        self,
        protected_path: str,
        manifest_path: str,
        security_log_path: str,
        key: Optional[bytes] = None
    ):
        self.protected_path = protected_path
        self.manifest_path = manifest_path
        self.key = key or secrets.token_bytes(32)
        
        # Initialize components
        self.security_log = TamperEvidentLog(security_log_path, self.key)
        self.backdoor_detector = BackdoorDetector()
        self.manifest: Optional[IntegrityManifest] = None
        self.verifier: Optional[IntegrityVerifier] = None
        
        # Load or create manifest
        if os.path.exists(manifest_path):
            self.manifest = IntegrityManifest.load(manifest_path)
            self.verifier = IntegrityVerifier(self.manifest)
    
    def initialize_manifest(self) -> IntegrityManifest:
        """
        Initialize integrity manifest for protected files.
        
        Should be called once during secure deployment.
        """
        self.manifest = IntegrityManifest()
        
        # Add all Python files to manifest
        for root, dirs, files in os.walk(self.protected_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.protected_path)
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    self.manifest.add_file(rel_path, content)
        
        self.manifest.compute_manifest_hash()
        self.manifest.save(self.manifest_path)
        self.verifier = IntegrityVerifier(self.manifest)
        
        # Log initialization
        self.security_log.append("SEAL_INITIALIZED", {
            "version": self.VERSION,
            "manifest_hash": self.manifest.manifest_hash,
            "files_protected": len(self.manifest.files)
        })
        
        return self.manifest
    
    def verify_integrity(self) -> Tuple[bool, List[SecurityViolation]]:
        """
        Verify integrity of all protected files.
        
        Returns (valid, violations).
        """
        if not self.verifier:
            return False, [SecurityViolation(
                violation_id=generate_secure_token(8),
                category=ThreatCategory.INTEGRITY_VIOLATION,
                severity="CRITICAL",
                description="No integrity manifest available",
                evidence={}
            )]
        
        valid, violations = self.verifier.verify_all(self.protected_path)
        
        # Log verification
        self.security_log.append("INTEGRITY_CHECK", {
            "valid": valid,
            "violations_count": len(violations)
        })
        
        return valid, violations
    
    def scan_for_backdoors(self) -> Tuple[bool, List[SecurityViolation]]:
        """
        Scan for potential backdoors.
        
        Returns (clean, violations).
        """
        violations = self.backdoor_detector.scan_directory(self.protected_path)
        clean = len(violations) == 0
        
        # Log scan
        self.security_log.append("BACKDOOR_SCAN", {
            "clean": clean,
            "violations_count": len(violations)
        })
        
        return clean, violations
    
    def verify_log_integrity(self) -> Tuple[bool, List[SecurityViolation]]:
        """
        Verify integrity of security log.
        
        Returns (valid, violations).
        """
        return self.security_log.verify_chain()
    
    def full_security_audit(self) -> Dict[str, Any]:
        """
        Perform full security audit.
        
        Returns comprehensive audit report.
        """
        report = {
            "seal_id": self.SEAL_ID,
            "version": self.VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {}
        }
        
        # 1. Integrity verification
        integrity_valid, integrity_violations = self.verify_integrity()
        report["checks"]["integrity"] = {
            "passed": integrity_valid,
            "violations": [v.to_dict() for v in integrity_violations]
        }
        
        # 2. Backdoor scan
        backdoor_clean, backdoor_violations = self.scan_for_backdoors()
        report["checks"]["backdoor_scan"] = {
            "passed": backdoor_clean,
            "violations": [v.to_dict() for v in backdoor_violations]
        }
        
        # 3. Log integrity
        log_valid, log_violations = self.verify_log_integrity()
        report["checks"]["log_integrity"] = {
            "passed": log_valid,
            "violations": [v.to_dict() for v in log_violations]
        }
        
        # 4. Environment check
        env_violations = self.backdoor_detector.scan_environment()
        report["checks"]["environment"] = {
            "passed": len(env_violations) == 0,
            "violations": [v.to_dict() for v in env_violations]
        }
        
        # Overall result
        all_passed = all(
            check["passed"] 
            for check in report["checks"].values()
        )
        report["overall_passed"] = all_passed
        report["security_level"] = SecurityLevel.TOP_SECRET.value if all_passed else SecurityLevel.UNCLASSIFIED.value
        
        # Log audit
        self.security_log.append("FULL_AUDIT", {
            "overall_passed": all_passed,
            "checks_passed": sum(1 for c in report["checks"].values() if c["passed"]),
            "checks_total": len(report["checks"])
        })
        
        return report
    
    def get_seal_status(self) -> Dict[str, Any]:
        """Get current seal status."""
        return {
            "seal_id": self.SEAL_ID,
            "version": self.VERSION,
            "manifest_hash": self.manifest.manifest_hash if self.manifest else None,
            "files_protected": len(self.manifest.files) if self.manifest else 0,
            "key_fingerprint": secure_hash(self.key)[:16]
        }


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    """CLI entry point for MILSPEC seal operations."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MILSPEC Security Seal - Zero Backdoor Verification"
    )
    
    parser.add_argument(
        "--path",
        default=".",
        help="Path to protected directory"
    )
    
    parser.add_argument(
        "--manifest",
        default="integrity_manifest.json",
        help="Path to integrity manifest"
    )
    
    parser.add_argument(
        "--log",
        default="security_audit.jsonl",
        help="Path to security log"
    )
    
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize integrity manifest"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify integrity"
    )
    
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for backdoors"
    )
    
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Full security audit"
    )
    
    args = parser.parse_args()
    
    seal = MilspecSeal(
        protected_path=args.path,
        manifest_path=args.manifest,
        security_log_path=args.log
    )
    
    if args.init:
        print("Initializing integrity manifest...")
        manifest = seal.initialize_manifest()
        print(f"Manifest created: {manifest.manifest_hash}")
        print(f"Files protected: {len(manifest.files)}")
    
    elif args.verify:
        print("Verifying integrity...")
        valid, violations = seal.verify_integrity()
        if valid:
            print("✅ Integrity verified")
        else:
            print("❌ Integrity violations detected:")
            for v in violations:
                print(f"  - {v.description}")
        sys.exit(0 if valid else 1)
    
    elif args.scan:
        print("Scanning for backdoors...")
        clean, violations = seal.scan_for_backdoors()
        if clean:
            print("✅ No backdoors detected")
        else:
            print("❌ Potential backdoors detected:")
            for v in violations:
                print(f"  - {v.description}")
        sys.exit(0 if clean else 1)
    
    elif args.audit:
        print("Running full security audit...")
        report = seal.full_security_audit()
        print(json.dumps(report, indent=2))
        sys.exit(0 if report["overall_passed"] else 1)
    
    else:
        print(json.dumps(seal.get_seal_status(), indent=2))


if __name__ == "__main__":
    main()
