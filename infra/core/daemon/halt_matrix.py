"""
PRIVILEGED-OPERATION HALT MATRIX

This module externalizes what is already implicit in the kernel's severity semantics.
It does not change behavior — it codifies what is already inevitable.

Doctrine: Severity deterministically drives behavior.
Mutation: DISALLOWED — this is a read-only binding.

The kernel already behaves as:
    info     → record only
    warn     → record + visibility
    fault    → remediation required
    critical → privileged ops halt

This matrix makes that binding explicit and binds it to specific op-classes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, Optional, Callable, Any
from datetime import datetime, timezone
import hashlib
import json


# =============================================================================
# SEVERITY LEVELS (ALREADY DEFINED IN KERNEL)
# =============================================================================

class Severity(Enum):
    """Severity levels — closed vocabulary, no additions."""
    INFO = "info"
    WARN = "warn"
    FAULT = "fault"
    CRITICAL = "critical"


# =============================================================================
# OPERATION CLASSES (CLOSED SET)
# =============================================================================

class OpClass(Enum):
    """
    Privileged operation classes.
    Each class represents a category of actions that may be halted.
    """
    # Authority operations
    AUTHORITY_GRANT = "authority_grant"
    AUTHORITY_REVOKE = "authority_revoke"
    AUTHORITY_EXTEND = "authority_extend"
    
    # Configuration operations
    CONFIG_MODIFY = "config_modify"
    CONFIG_DEPLOY = "config_deploy"
    CONFIG_ROLLBACK = "config_rollback"
    
    # Data operations
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    DATA_MIGRATE = "data_migrate"
    
    # System operations
    SYSTEM_RESTART = "system_restart"
    SYSTEM_UPGRADE = "system_upgrade"
    SYSTEM_SHUTDOWN = "system_shutdown"
    
    # Security operations
    SECURITY_OVERRIDE = "security_override"
    SECURITY_DOWNGRADE = "security_downgrade"
    KEY_ROTATION = "key_rotation"
    
    # Governance operations
    QUORUM_OVERRIDE = "quorum_override"
    CHALLENGE_DISMISS = "challenge_dismiss"
    INVARIANT_SUSPEND = "invariant_suspend"


# =============================================================================
# HALT BEHAVIOR (CLOSED SET)
# =============================================================================

class HaltBehavior(Enum):
    """
    What happens when an operation is attempted under a given severity state.
    """
    ALLOW = "allow"           # Operation proceeds, recorded
    WARN_ALLOW = "warn_allow" # Operation proceeds with warning, recorded
    QUEUE = "queue"           # Operation queued pending remediation
    HALT = "halt"             # Operation blocked, challenge required
    DENY = "deny"             # Operation permanently denied at this severity


# =============================================================================
# HALT MATRIX ENTRY
# =============================================================================

@dataclass(frozen=True)
class HaltMatrixEntry:
    """
    A single binding: (severity, op_class) → behavior
    
    Immutable by construction.
    """
    severity: Severity
    op_class: OpClass
    behavior: HaltBehavior
    requires_quorum: bool = False
    requires_challenge_clear: bool = False
    audit_level: str = "standard"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "op_class": self.op_class.value,
            "behavior": self.behavior.value,
            "requires_quorum": self.requires_quorum,
            "requires_challenge_clear": self.requires_challenge_clear,
            "audit_level": self.audit_level,
        }


# =============================================================================
# THE HALT MATRIX (DECLARATIVE, IMMUTABLE)
# =============================================================================

class HaltMatrix:
    """
    The Privileged-Operation Halt Matrix.
    
    This is a pure function: (current_severity, requested_op) → decision
    
    Properties:
        - Deterministic: same inputs always produce same output
        - Complete: every (severity, op_class) pair has a defined behavior
        - Immutable: cannot be modified after construction
        - Auditable: every decision is logged with evidence
    """
    
    def __init__(self):
        self._matrix: Dict[tuple, HaltMatrixEntry] = {}
        self._sealed = False
        self._seal_hash: Optional[str] = None
        self._build_matrix()
        self._seal()
    
    def _build_matrix(self) -> None:
        """
        Build the complete halt matrix.
        
        This encodes what is already implicit in severity semantics:
            info     → record only (most ops allowed)
            warn     → record + visibility (ops allowed with warning)
            fault    → remediation required (privileged ops queued)
            critical → privileged ops halt (blocked until resolved)
        """
        
        # INFO severity — system healthy, most operations allowed
        for op in OpClass:
            if op in (OpClass.INVARIANT_SUSPEND, OpClass.SECURITY_DOWNGRADE):
                # These are never allowed without quorum, even when healthy
                self._add(Severity.INFO, op, HaltBehavior.HALT, 
                         requires_quorum=True, requires_challenge_clear=True)
            elif op in (OpClass.QUORUM_OVERRIDE, OpClass.CHALLENGE_DISMISS):
                # Governance overrides always require quorum
                self._add(Severity.INFO, op, HaltBehavior.WARN_ALLOW,
                         requires_quorum=True)
            else:
                self._add(Severity.INFO, op, HaltBehavior.ALLOW)
        
        # WARN severity — issues detected, operations allowed with visibility
        for op in OpClass:
            if op in (OpClass.INVARIANT_SUSPEND, OpClass.SECURITY_DOWNGRADE,
                     OpClass.SECURITY_OVERRIDE):
                self._add(Severity.WARN, op, HaltBehavior.HALT,
                         requires_quorum=True, requires_challenge_clear=True)
            elif op in (OpClass.SYSTEM_UPGRADE, OpClass.CONFIG_DEPLOY,
                       OpClass.DATA_MIGRATE):
                # Risky ops get queued at warn level
                self._add(Severity.WARN, op, HaltBehavior.QUEUE)
            else:
                self._add(Severity.WARN, op, HaltBehavior.WARN_ALLOW,
                         audit_level="elevated")
        
        # FAULT severity — remediation required, privileged ops queued
        for op in OpClass:
            if op in (OpClass.INVARIANT_SUSPEND, OpClass.SECURITY_DOWNGRADE,
                     OpClass.SECURITY_OVERRIDE, OpClass.QUORUM_OVERRIDE):
                self._add(Severity.FAULT, op, HaltBehavior.DENY)
            elif op in (OpClass.AUTHORITY_GRANT, OpClass.AUTHORITY_EXTEND,
                       OpClass.CONFIG_MODIFY, OpClass.CONFIG_DEPLOY,
                       OpClass.SYSTEM_UPGRADE, OpClass.DATA_DELETE,
                       OpClass.DATA_MIGRATE):
                self._add(Severity.FAULT, op, HaltBehavior.HALT,
                         requires_challenge_clear=True)
            else:
                self._add(Severity.FAULT, op, HaltBehavior.QUEUE,
                         audit_level="elevated")
        
        # CRITICAL severity — privileged ops halt
        for op in OpClass:
            if op in (OpClass.AUTHORITY_REVOKE, OpClass.CONFIG_ROLLBACK,
                     OpClass.SYSTEM_SHUTDOWN):
                # Emergency operations still allowed at critical
                self._add(Severity.CRITICAL, op, HaltBehavior.WARN_ALLOW,
                         requires_quorum=True, audit_level="maximum")
            elif op == OpClass.CHALLENGE_DISMISS:
                # Cannot dismiss challenges during critical state
                self._add(Severity.CRITICAL, op, HaltBehavior.DENY)
            else:
                self._add(Severity.CRITICAL, op, HaltBehavior.HALT,
                         requires_quorum=True, requires_challenge_clear=True,
                         audit_level="maximum")
    
    def _add(self, severity: Severity, op_class: OpClass, 
             behavior: HaltBehavior, requires_quorum: bool = False,
             requires_challenge_clear: bool = False,
             audit_level: str = "standard") -> None:
        """Add an entry to the matrix."""
        if self._sealed:
            raise RuntimeError("Cannot modify sealed matrix")
        
        key = (severity, op_class)
        self._matrix[key] = HaltMatrixEntry(
            severity=severity,
            op_class=op_class,
            behavior=behavior,
            requires_quorum=requires_quorum,
            requires_challenge_clear=requires_challenge_clear,
            audit_level=audit_level,
        )
    
    def _seal(self) -> None:
        """Seal the matrix — no further modifications allowed."""
        # Compute hash of entire matrix
        entries = sorted(
            [e.to_dict() for e in self._matrix.values()],
            key=lambda x: (x["severity"], x["op_class"])
        )
        content = json.dumps(entries, sort_keys=True)
        self._seal_hash = hashlib.sha256(content.encode()).hexdigest()
        self._sealed = True
    
    @property
    def seal_hash(self) -> str:
        """Return the seal hash of the matrix."""
        return self._seal_hash
    
    def decide(self, severity: Severity, op_class: OpClass) -> HaltMatrixEntry:
        """
        Pure function: (severity, op_class) → decision
        
        This is the core of the halt matrix.
        """
        key = (severity, op_class)
        if key not in self._matrix:
            # Fail-secure: unknown combinations are denied
            return HaltMatrixEntry(
                severity=severity,
                op_class=op_class,
                behavior=HaltBehavior.DENY,
                requires_quorum=True,
                requires_challenge_clear=True,
                audit_level="maximum",
            )
        return self._matrix[key]
    
    def can_proceed(self, severity: Severity, op_class: OpClass,
                    quorum_satisfied: bool = False,
                    challenges_clear: bool = False) -> tuple[bool, str]:
        """
        Evaluate whether an operation can proceed.
        
        Returns: (can_proceed, reason)
        """
        entry = self.decide(severity, op_class)
        
        if entry.behavior == HaltBehavior.DENY:
            return False, f"Operation {op_class.value} denied at severity {severity.value}"
        
        if entry.behavior == HaltBehavior.HALT:
            if entry.requires_quorum and not quorum_satisfied:
                return False, f"Operation {op_class.value} halted: quorum required"
            if entry.requires_challenge_clear and not challenges_clear:
                return False, f"Operation {op_class.value} halted: challenges must be cleared"
            # If requirements met, halt becomes allow
            return True, f"Operation {op_class.value} allowed after requirements satisfied"
        
        if entry.behavior == HaltBehavior.QUEUE:
            return False, f"Operation {op_class.value} queued pending remediation"
        
        # ALLOW or WARN_ALLOW
        return True, f"Operation {op_class.value} allowed at severity {severity.value}"
    
    def get_all_entries(self) -> list[HaltMatrixEntry]:
        """Return all matrix entries."""
        return list(self._matrix.values())
    
    def to_table(self) -> str:
        """Render the matrix as a human-readable table."""
        lines = []
        lines.append("=" * 100)
        lines.append("PRIVILEGED-OPERATION HALT MATRIX")
        lines.append(f"Seal Hash: {self._seal_hash[:32]}...")
        lines.append("=" * 100)
        lines.append("")
        
        # Group by severity
        for sev in Severity:
            lines.append(f"### {sev.value.upper()} SEVERITY")
            lines.append("-" * 80)
            lines.append(f"{'Operation':<30} {'Behavior':<15} {'Quorum':<8} {'Clear':<8} {'Audit':<10}")
            lines.append("-" * 80)
            
            for op in OpClass:
                entry = self._matrix.get((sev, op))
                if entry:
                    lines.append(
                        f"{op.value:<30} {entry.behavior.value:<15} "
                        f"{'Yes' if entry.requires_quorum else 'No':<8} "
                        f"{'Yes' if entry.requires_challenge_clear else 'No':<8} "
                        f"{entry.audit_level:<10}"
                    )
            lines.append("")
        
        return "\n".join(lines)


# =============================================================================
# SINGLETON INSTANCE (IMMUTABLE)
# =============================================================================

# The matrix is constructed once and sealed
HALT_MATRIX = HaltMatrix()


# =============================================================================
# DECISION FUNCTION (PURE)
# =============================================================================

def evaluate_operation(
    op_class: OpClass,
    current_severity: Severity,
    quorum_satisfied: bool = False,
    challenges_clear: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate whether a privileged operation can proceed.
    
    This is the public API for the halt matrix.
    
    Returns a decision record suitable for ledger entry.
    """
    entry = HALT_MATRIX.decide(current_severity, op_class)
    can_proceed, reason = HALT_MATRIX.can_proceed(
        current_severity, op_class, quorum_satisfied, challenges_clear
    )
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "op_class": op_class.value,
        "severity": current_severity.value,
        "behavior": entry.behavior.value,
        "decision": "PROCEED" if can_proceed else "BLOCKED",
        "reason": reason,
        "requirements": {
            "quorum_required": entry.requires_quorum,
            "quorum_satisfied": quorum_satisfied,
            "challenges_clear_required": entry.requires_challenge_clear,
            "challenges_clear": challenges_clear,
        },
        "audit_level": entry.audit_level,
        "matrix_hash": HALT_MATRIX.seal_hash,
    }


# =============================================================================
# CLI / TEST INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print(HALT_MATRIX.to_table())
    print("")
    print(f"Matrix sealed with hash: {HALT_MATRIX.seal_hash}")
    print("")
    
    # Test scenarios
    print("=" * 60)
    print("TEST SCENARIOS")
    print("=" * 60)
    
    tests = [
        (OpClass.CONFIG_DEPLOY, Severity.INFO, False, True),
        (OpClass.CONFIG_DEPLOY, Severity.CRITICAL, False, False),
        (OpClass.CONFIG_DEPLOY, Severity.CRITICAL, True, True),
        (OpClass.AUTHORITY_REVOKE, Severity.CRITICAL, True, False),
        (OpClass.INVARIANT_SUSPEND, Severity.INFO, False, False),
        (OpClass.INVARIANT_SUSPEND, Severity.INFO, True, True),
        (OpClass.CHALLENGE_DISMISS, Severity.CRITICAL, True, True),
    ]
    
    for op, sev, quorum, clear in tests:
        result = evaluate_operation(op, sev, quorum, clear)
        status = "✅" if result["decision"] == "PROCEED" else "❌"
        print(f"{status} {op.value} @ {sev.value}: {result['decision']} — {result['reason']}")
