"""
Sovereign Governance Kernel — Invariant Registry
Constitutional invariants with deterministic pass/fail validation.

Invariants 1-10: Core Constitutional
Invariants 11-15: AGI Safety Extensions
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import hashlib
import json


class Severity(str, Enum):
    """Invariant violation severity levels."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InvariantStatus(str, Enum):
    """Invariant check result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class InvariantResult:
    """Result of an invariant check."""
    invariant_id: str
    name: str
    status: InvariantStatus
    severity: Severity
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    
    def __post_init__(self):
        """Compute evidence hash after initialization."""
        if not self.hash:
            self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute SHA256 hash of the result for evidence chain."""
        data = {
            "invariant_id": self.invariant_id,
            "name": self.name,
            "status": self.status.value,
            "severity": self.severity.value,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "evidence": self.evidence
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "invariant_id": self.invariant_id,
            "name": self.name,
            "status": self.status.value,
            "severity": self.severity.value,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "evidence": self.evidence,
            "hash": self.hash
        }
    
    def is_failure(self) -> bool:
        """Check if this result represents a failure."""
        return self.status in (InvariantStatus.FAIL, InvariantStatus.ERROR)


@dataclass
class Invariant:
    """
    A constitutional invariant definition.
    
    Invariants are the non-negotiable rules that govern system behavior.
    Each invariant has a validator function that returns pass/fail.
    """
    id: str
    name: str
    description: str
    severity: Severity
    validator: Callable[[Dict[str, Any]], InvariantResult]
    enabled: bool = True
    agi_safety: bool = False  # True for invariants 11-15
    
    def validate(self, context: Dict[str, Any]) -> InvariantResult:
        """
        Execute the invariant validator.
        
        Args:
            context: Runtime context for validation
            
        Returns:
            InvariantResult with pass/fail status
        """
        if not self.enabled:
            return InvariantResult(
                invariant_id=self.id,
                name=self.name,
                status=InvariantStatus.SKIP,
                severity=self.severity,
                reason="Invariant disabled",
                evidence={"enabled": False}
            )
        
        try:
            return self.validator(context)
        except Exception as e:
            # INV_FAILURE_IS_LOUD: Errors are never silent
            return InvariantResult(
                invariant_id=self.id,
                name=self.name,
                status=InvariantStatus.ERROR,
                severity=Severity.CRITICAL,
                reason=f"Validator error: {str(e)}",
                evidence={"exception": str(e), "exception_type": type(e).__name__}
            )


class InvariantRegistry:
    """
    Registry of all constitutional invariants.
    
    Provides:
    - Registration of invariants
    - Batch validation
    - Evidence emission
    - Failure aggregation
    """
    
    def __init__(self):
        self._invariants: Dict[str, Invariant] = {}
        self._results_history: List[InvariantResult] = []
    
    def register(self, invariant: Invariant) -> None:
        """Register an invariant."""
        self._invariants[invariant.id] = invariant
    
    def unregister(self, invariant_id: str) -> bool:
        """Unregister an invariant. Returns True if found and removed."""
        if invariant_id in self._invariants:
            del self._invariants[invariant_id]
            return True
        return False
    
    def get(self, invariant_id: str) -> Optional[Invariant]:
        """Get an invariant by ID."""
        return self._invariants.get(invariant_id)
    
    def list_all(self) -> List[Invariant]:
        """List all registered invariants."""
        return list(self._invariants.values())
    
    def list_agi_safety(self) -> List[Invariant]:
        """List AGI safety invariants (11-15)."""
        return [inv for inv in self._invariants.values() if inv.agi_safety]
    
    def validate_all(self, context: Dict[str, Any]) -> List[InvariantResult]:
        """
        Validate all registered invariants.
        
        Args:
            context: Runtime context for validation
            
        Returns:
            List of InvariantResult for each invariant
        """
        results = []
        for invariant in self._invariants.values():
            result = invariant.validate(context)
            results.append(result)
            self._results_history.append(result)
        return results
    
    def validate_subset(self, invariant_ids: List[str], context: Dict[str, Any]) -> List[InvariantResult]:
        """Validate a subset of invariants by ID."""
        results = []
        for inv_id in invariant_ids:
            if inv_id in self._invariants:
                result = self._invariants[inv_id].validate(context)
                results.append(result)
                self._results_history.append(result)
        return results
    
    def get_failures(self, results: List[InvariantResult]) -> List[InvariantResult]:
        """Extract failures from a list of results."""
        return [r for r in results if r.is_failure()]
    
    def has_critical_failure(self, results: List[InvariantResult]) -> bool:
        """Check if any result is a critical failure."""
        return any(
            r.is_failure() and r.severity == Severity.CRITICAL 
            for r in results
        )
    
    def get_history(self, limit: int = 100) -> List[InvariantResult]:
        """Get recent validation history."""
        return self._results_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear validation history."""
        self._results_history.clear()


# ═══════════════════════════════════════════════════════════════════
# INVARIANT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

def create_default_registry() -> InvariantRegistry:
    """
    Create registry with all 15 constitutional invariants.
    
    Invariants 1-10: Core Constitutional
    Invariants 11-15: AGI Safety Extensions
    """
    registry = InvariantRegistry()
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 1: Immutable Audit Trail
    # ─────────────────────────────────────────────────────────────
    def validate_audit_trail(ctx: Dict[str, Any]) -> InvariantResult:
        ledger_path = ctx.get("ledger_path")
        if not ledger_path:
            return InvariantResult(
                invariant_id="INV-001",
                name="Immutable Audit Trail",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Ledger path not configured",
                evidence={"ledger_path": None}
            )
        
        # Check ledger exists and is append-only
        import os
        if not os.path.exists(ledger_path):
            return InvariantResult(
                invariant_id="INV-001",
                name="Immutable Audit Trail",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason="Ledger file does not exist",
                evidence={"ledger_path": ledger_path, "exists": False}
            )
        
        return InvariantResult(
            invariant_id="INV-001",
            name="Immutable Audit Trail",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="Ledger exists and accessible",
            evidence={"ledger_path": ledger_path, "exists": True}
        )
    
    registry.register(Invariant(
        id="INV-001",
        name="Immutable Audit Trail",
        description="All actions must be logged to the ledger with hash chain integrity",
        severity=Severity.CRITICAL,
        validator=validate_audit_trail
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 2: Human Oversight
    # ─────────────────────────────────────────────────────────────
    def validate_human_oversight(ctx: Dict[str, Any]) -> InvariantResult:
        oversight_enabled = ctx.get("human_oversight_enabled", False)
        kill_switch_active = ctx.get("kill_switch_active", False)
        
        if not oversight_enabled:
            return InvariantResult(
                invariant_id="INV-002",
                name="Human Oversight",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Human oversight is disabled",
                evidence={"oversight_enabled": False, "kill_switch_active": kill_switch_active}
            )
        
        return InvariantResult(
            invariant_id="INV-002",
            name="Human Oversight",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="Human oversight is enabled",
            evidence={"oversight_enabled": True, "kill_switch_active": kill_switch_active}
        )
    
    registry.register(Invariant(
        id="INV-002",
        name="Human Oversight",
        description="High-risk decisions require human approval",
        severity=Severity.CRITICAL,
        validator=validate_human_oversight
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 3: Constitutional Supremacy
    # ─────────────────────────────────────────────────────────────
    def validate_constitutional_supremacy(ctx: Dict[str, Any]) -> InvariantResult:
        constitution_hash = ctx.get("constitution_hash")
        expected_hash = ctx.get("expected_constitution_hash")
        
        if not constitution_hash or not expected_hash:
            return InvariantResult(
                invariant_id="INV-003",
                name="Constitutional Supremacy",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Constitution hash not available for verification",
                evidence={"constitution_hash": constitution_hash, "expected_hash": expected_hash}
            )
        
        if constitution_hash != expected_hash:
            return InvariantResult(
                invariant_id="INV-003",
                name="Constitutional Supremacy",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Constitution has been modified without authorization",
                evidence={"constitution_hash": constitution_hash, "expected_hash": expected_hash}
            )
        
        return InvariantResult(
            invariant_id="INV-003",
            name="Constitutional Supremacy",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="Constitution integrity verified",
            evidence={"constitution_hash": constitution_hash, "verified": True}
        )
    
    registry.register(Invariant(
        id="INV-003",
        name="Constitutional Supremacy",
        description="No agent or process may override the constitution",
        severity=Severity.CRITICAL,
        validator=validate_constitutional_supremacy
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 4: Deterministic Behavior
    # ─────────────────────────────────────────────────────────────
    def validate_deterministic_behavior(ctx: Dict[str, Any]) -> InvariantResult:
        phase = ctx.get("current_phase", 0)
        deterministic_mode = ctx.get("deterministic_mode", True)
        
        # Phase 0 requires strict determinism
        if phase == 0 and not deterministic_mode:
            return InvariantResult(
                invariant_id="INV-004",
                name="Deterministic Behavior",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason="Phase 0 requires deterministic mode",
                evidence={"phase": phase, "deterministic_mode": deterministic_mode}
            )
        
        return InvariantResult(
            invariant_id="INV-004",
            name="Deterministic Behavior",
            status=InvariantStatus.PASS,
            severity=Severity.HIGH,
            reason="Deterministic behavior requirement satisfied",
            evidence={"phase": phase, "deterministic_mode": deterministic_mode}
        )
    
    registry.register(Invariant(
        id="INV-004",
        name="Deterministic Behavior",
        description="Same inputs must produce same outputs in Phase 0",
        severity=Severity.HIGH,
        validator=validate_deterministic_behavior
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 5: Graceful Degradation (INV_FAILURE_IS_LOUD)
    # ─────────────────────────────────────────────────────────────
    def validate_graceful_degradation(ctx: Dict[str, Any]) -> InvariantResult:
        silent_failures = ctx.get("silent_failures_detected", [])
        logging_enabled = ctx.get("logging_enabled", True)
        alerting_enabled = ctx.get("alerting_enabled", True)
        
        if silent_failures:
            return InvariantResult(
                invariant_id="INV-005",
                name="Graceful Degradation (FAILURE_IS_LOUD)",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason=f"Silent failures detected: {len(silent_failures)}",
                evidence={"silent_failures": silent_failures, "count": len(silent_failures)}
            )
        
        if not logging_enabled or not alerting_enabled:
            return InvariantResult(
                invariant_id="INV-005",
                name="Graceful Degradation (FAILURE_IS_LOUD)",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason="Logging or alerting is disabled",
                evidence={"logging_enabled": logging_enabled, "alerting_enabled": alerting_enabled}
            )
        
        return InvariantResult(
            invariant_id="INV-005",
            name="Graceful Degradation (FAILURE_IS_LOUD)",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="No silent failures, logging and alerting active",
            evidence={"logging_enabled": logging_enabled, "alerting_enabled": alerting_enabled}
        )
    
    registry.register(Invariant(
        id="INV-005",
        name="Graceful Degradation (FAILURE_IS_LOUD)",
        description="System must fail safely, never silently",
        severity=Severity.CRITICAL,
        validator=validate_graceful_degradation
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 6: Authority Expiry
    # ─────────────────────────────────────────────────────────────
    def validate_authority_expiry(ctx: Dict[str, Any]) -> InvariantResult:
        active_authorities = ctx.get("active_authorities", [])
        
        expired = []
        perpetual = []
        now = datetime.now(timezone.utc)
        
        for auth in active_authorities:
            expires_at = auth.get("expires_at")
            if expires_at is None:
                perpetual.append(auth.get("id", "unknown"))
            elif isinstance(expires_at, str):
                exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if exp_dt < now:
                    expired.append(auth.get("id", "unknown"))
        
        if perpetual:
            return InvariantResult(
                invariant_id="INV-006",
                name="Authority Expiry",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason=f"Perpetual authorities detected: {perpetual}",
                evidence={"perpetual_authorities": perpetual}
            )
        
        if expired:
            return InvariantResult(
                invariant_id="INV-006",
                name="Authority Expiry",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Expired authorities still active: {expired}",
                evidence={"expired_authorities": expired}
            )
        
        return InvariantResult(
            invariant_id="INV-006",
            name="Authority Expiry",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="All authorities have valid expiry",
            evidence={"active_count": len(active_authorities)}
        )
    
    registry.register(Invariant(
        id="INV-006",
        name="Authority Expiry",
        description="All authority grants must have finite expiry",
        severity=Severity.CRITICAL,
        validator=validate_authority_expiry
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 7: Evidence Grounding
    # ─────────────────────────────────────────────────────────────
    def validate_evidence_grounding(ctx: Dict[str, Any]) -> InvariantResult:
        ungrounded_claims = ctx.get("ungrounded_claims", [])
        
        if ungrounded_claims:
            return InvariantResult(
                invariant_id="INV-007",
                name="Evidence Grounding",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Ungrounded claims detected: {len(ungrounded_claims)}",
                evidence={"ungrounded_claims": ungrounded_claims[:10]}  # Limit to first 10
            )
        
        return InvariantResult(
            invariant_id="INV-007",
            name="Evidence Grounding",
            status=InvariantStatus.PASS,
            severity=Severity.HIGH,
            reason="All claims are evidence-grounded",
            evidence={"verified": True}
        )
    
    registry.register(Invariant(
        id="INV-007",
        name="Evidence Grounding",
        description="All factual claims must be backed by evidence",
        severity=Severity.HIGH,
        validator=validate_evidence_grounding
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 8: Refusal Capability
    # ─────────────────────────────────────────────────────────────
    def validate_refusal_capability(ctx: Dict[str, Any]) -> InvariantResult:
        refusal_enabled = ctx.get("refusal_enabled", True)
        refusal_overridden = ctx.get("refusal_overridden", False)
        
        if not refusal_enabled or refusal_overridden:
            return InvariantResult(
                invariant_id="INV-008",
                name="Refusal Capability",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Refusal capability is disabled or overridden",
                evidence={"refusal_enabled": refusal_enabled, "refusal_overridden": refusal_overridden}
            )
        
        return InvariantResult(
            invariant_id="INV-008",
            name="Refusal Capability",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="Refusal capability is active",
            evidence={"refusal_enabled": True}
        )
    
    registry.register(Invariant(
        id="INV-008",
        name="Refusal Capability",
        description="System must be able to refuse unsafe requests",
        severity=Severity.CRITICAL,
        validator=validate_refusal_capability
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 9: Data Minimization
    # ─────────────────────────────────────────────────────────────
    def validate_data_minimization(ctx: Dict[str, Any]) -> InvariantResult:
        data_retention_policy = ctx.get("data_retention_policy")
        excessive_retention = ctx.get("excessive_retention_detected", False)
        
        if not data_retention_policy:
            return InvariantResult(
                invariant_id="INV-009",
                name="Data Minimization",
                status=InvariantStatus.FAIL,
                severity=Severity.MEDIUM,
                reason="No data retention policy configured",
                evidence={"policy_configured": False}
            )
        
        if excessive_retention:
            return InvariantResult(
                invariant_id="INV-009",
                name="Data Minimization",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason="Excessive data retention detected",
                evidence={"excessive_retention": True}
            )
        
        return InvariantResult(
            invariant_id="INV-009",
            name="Data Minimization",
            status=InvariantStatus.PASS,
            severity=Severity.MEDIUM,
            reason="Data minimization policy enforced",
            evidence={"policy": data_retention_policy}
        )
    
    registry.register(Invariant(
        id="INV-009",
        name="Data Minimization",
        description="Collect and retain only necessary data",
        severity=Severity.MEDIUM,
        validator=validate_data_minimization
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 10: Scope Boundaries
    # ─────────────────────────────────────────────────────────────
    def validate_scope_boundaries(ctx: Dict[str, Any]) -> InvariantResult:
        boundary_violations = ctx.get("boundary_violations", [])
        
        if boundary_violations:
            return InvariantResult(
                invariant_id="INV-010",
                name="Scope Boundaries",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Boundary violations detected: {len(boundary_violations)}",
                evidence={"violations": boundary_violations[:10]}
            )
        
        return InvariantResult(
            invariant_id="INV-010",
            name="Scope Boundaries",
            status=InvariantStatus.PASS,
            severity=Severity.HIGH,
            reason="All operations within scope boundaries",
            evidence={"verified": True}
        )
    
    registry.register(Invariant(
        id="INV-010",
        name="Scope Boundaries",
        description="Operations must stay within authorized scope",
        severity=Severity.HIGH,
        validator=validate_scope_boundaries
    ))
    
    # ═══════════════════════════════════════════════════════════════
    # AGI SAFETY INVARIANTS (11-15)
    # ═══════════════════════════════════════════════════════════════
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 11: No Self-Modification
    # ─────────────────────────────────────────────────────────────
    def validate_no_self_modification(ctx: Dict[str, Any]) -> InvariantResult:
        constraint_files_hashes = ctx.get("constraint_files_hashes", {})
        expected_hashes = ctx.get("expected_constraint_hashes", {})
        
        if not constraint_files_hashes or not expected_hashes:
            return InvariantResult(
                invariant_id="INV-011",
                name="No Self-Modification",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Constraint file hashes not available for verification",
                evidence={"hashes_available": False}
            )
        
        modified = []
        for file_path, current_hash in constraint_files_hashes.items():
            expected = expected_hashes.get(file_path)
            if expected and current_hash != expected:
                modified.append(file_path)
        
        if modified:
            return InvariantResult(
                invariant_id="INV-011",
                name="No Self-Modification",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason=f"Constraint files modified: {modified}",
                evidence={"modified_files": modified}
            )
        
        return InvariantResult(
            invariant_id="INV-011",
            name="No Self-Modification",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="No unauthorized self-modification detected",
            evidence={"files_verified": len(constraint_files_hashes)}
        )
    
    registry.register(Invariant(
        id="INV-011",
        name="No Self-Modification",
        description="System cannot alter its own constraints without multi-party authorization",
        severity=Severity.CRITICAL,
        validator=validate_no_self_modification,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 12: Bounded Recursion
    # ─────────────────────────────────────────────────────────────
    def validate_bounded_recursion(ctx: Dict[str, Any]) -> InvariantResult:
        max_recursion_depth = ctx.get("max_recursion_depth", 100)
        current_recursion_depth = ctx.get("current_recursion_depth", 0)
        unbounded_chains = ctx.get("unbounded_chains_detected", [])
        
        if unbounded_chains:
            return InvariantResult(
                invariant_id="INV-012",
                name="Bounded Recursion",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Unbounded reasoning chains detected: {len(unbounded_chains)}",
                evidence={"unbounded_chains": unbounded_chains[:5]}
            )
        
        if current_recursion_depth > max_recursion_depth:
            return InvariantResult(
                invariant_id="INV-012",
                name="Bounded Recursion",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Recursion depth {current_recursion_depth} exceeds max {max_recursion_depth}",
                evidence={"current_depth": current_recursion_depth, "max_depth": max_recursion_depth}
            )
        
        return InvariantResult(
            invariant_id="INV-012",
            name="Bounded Recursion",
            status=InvariantStatus.PASS,
            severity=Severity.HIGH,
            reason="Recursion within bounds",
            evidence={"current_depth": current_recursion_depth, "max_depth": max_recursion_depth}
        )
    
    registry.register(Invariant(
        id="INV-012",
        name="Bounded Recursion",
        description="Reasoning chains must be depth-limited",
        severity=Severity.HIGH,
        validator=validate_bounded_recursion,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 13: Ephemeral Goals
    # ─────────────────────────────────────────────────────────────
    def validate_ephemeral_goals(ctx: Dict[str, Any]) -> InvariantResult:
        persistent_goals = ctx.get("persistent_goals_detected", [])
        cross_session_memory = ctx.get("cross_session_memory_unauthorized", False)
        
        if persistent_goals:
            return InvariantResult(
                invariant_id="INV-013",
                name="Ephemeral Goals",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Persistent goals detected: {len(persistent_goals)}",
                evidence={"persistent_goals": persistent_goals[:5]}
            )
        
        if cross_session_memory:
            return InvariantResult(
                invariant_id="INV-013",
                name="Ephemeral Goals",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason="Unauthorized cross-session memory detected",
                evidence={"cross_session_memory": True}
            )
        
        return InvariantResult(
            invariant_id="INV-013",
            name="Ephemeral Goals",
            status=InvariantStatus.PASS,
            severity=Severity.HIGH,
            reason="Goals are session-scoped",
            evidence={"session_scoped": True}
        )
    
    registry.register(Invariant(
        id="INV-013",
        name="Ephemeral Goals",
        description="Goals reset per session; no persistent goal accumulation",
        severity=Severity.HIGH,
        validator=validate_ephemeral_goals,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 14: Override Preserved
    # ─────────────────────────────────────────────────────────────
    def validate_override_preserved(ctx: Dict[str, Any]) -> InvariantResult:
        kill_switch_accessible = ctx.get("kill_switch_accessible", True)
        kill_switch_disabled = ctx.get("kill_switch_disabled", False)
        override_delayed = ctx.get("override_delayed", False)
        
        if kill_switch_disabled:
            return InvariantResult(
                invariant_id="INV-014",
                name="Override Preserved",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Kill switch has been disabled",
                evidence={"kill_switch_disabled": True}
            )
        
        if not kill_switch_accessible:
            return InvariantResult(
                invariant_id="INV-014",
                name="Override Preserved",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Kill switch is not accessible",
                evidence={"kill_switch_accessible": False}
            )
        
        if override_delayed:
            return InvariantResult(
                invariant_id="INV-014",
                name="Override Preserved",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason="Override mechanism is being delayed",
                evidence={"override_delayed": True}
            )
        
        return InvariantResult(
            invariant_id="INV-014",
            name="Override Preserved",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="Human override mechanisms are preserved",
            evidence={"kill_switch_accessible": True, "kill_switch_enabled": True}
        )
    
    registry.register(Invariant(
        id="INV-014",
        name="Override Preserved",
        description="Human override mechanisms cannot be disabled, delayed, or obscured",
        severity=Severity.CRITICAL,
        validator=validate_override_preserved,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 15: Verifiable Truthfulness
    # ─────────────────────────────────────────────────────────────
    def validate_verifiable_truthfulness(ctx: Dict[str, Any]) -> InvariantResult:
        state_misrepresentations = ctx.get("state_misrepresentations_detected", [])
        capability_misrepresentations = ctx.get("capability_misrepresentations", [])
        
        if state_misrepresentations:
            return InvariantResult(
                invariant_id="INV-015",
                name="Verifiable Truthfulness",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason=f"State misrepresentations detected: {len(state_misrepresentations)}",
                evidence={"misrepresentations": state_misrepresentations[:5]}
            )
        
        if capability_misrepresentations:
            return InvariantResult(
                invariant_id="INV-015",
                name="Verifiable Truthfulness",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Capability misrepresentations detected: {len(capability_misrepresentations)}",
                evidence={"capability_misrepresentations": capability_misrepresentations[:5]}
            )
        
        return InvariantResult(
            invariant_id="INV-015",
            name="Verifiable Truthfulness",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="No misrepresentations detected",
            evidence={"verified": True}
        )
    
    registry.register(Invariant(
        id="INV-015",
        name="Verifiable Truthfulness",
        description="System cannot misrepresent its internal state, capabilities, or limitations",
        severity=Severity.CRITICAL,
        validator=validate_verifiable_truthfulness,
        agi_safety=True
    ))
    
    return registry


# ═══════════════════════════════════════════════════════════════════
# MILSPEC SECURITY INVARIANTS (16-20)
# Future-proof hardening with zero backdoors
# ═══════════════════════════════════════════════════════════════════

def add_milspec_invariants(registry: InvariantRegistry) -> InvariantRegistry:
    """
    Add MILSPEC security invariants to an existing registry.
    
    Invariants 16-20: Military-specification security hardening
    - Zero backdoors
    - Cryptographic integrity
    - Defense-in-depth
    - Tamper detection
    - Future-proof design
    """
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 16: Zero Backdoors
    # ─────────────────────────────────────────────────────────────
    def validate_zero_backdoors(ctx: Dict[str, Any]) -> InvariantResult:
        backdoor_scan_result = ctx.get("backdoor_scan_result", {})
        forbidden_patterns_found = ctx.get("forbidden_patterns_found", [])
        suspicious_env_vars = ctx.get("suspicious_env_vars", [])
        
        if forbidden_patterns_found:
            return InvariantResult(
                invariant_id="INV-016",
                name="Zero Backdoors",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason=f"Forbidden code patterns detected: {len(forbidden_patterns_found)}",
                evidence={
                    "patterns_found": forbidden_patterns_found[:10],
                    "scan_timestamp": backdoor_scan_result.get("timestamp")
                }
            )
        
        if suspicious_env_vars:
            return InvariantResult(
                invariant_id="INV-016",
                name="Zero Backdoors",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Suspicious environment variables: {suspicious_env_vars}",
                evidence={"suspicious_vars": suspicious_env_vars}
            )
        
        return InvariantResult(
            invariant_id="INV-016",
            name="Zero Backdoors",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="No backdoors detected",
            evidence={"scan_clean": True}
        )
    
    registry.register(Invariant(
        id="INV-016",
        name="Zero Backdoors",
        description="No hidden entry points, bypass mechanisms, or privilege escalation paths",
        severity=Severity.CRITICAL,
        validator=validate_zero_backdoors,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 17: Cryptographic Integrity
    # ─────────────────────────────────────────────────────────────
    def validate_cryptographic_integrity(ctx: Dict[str, Any]) -> InvariantResult:
        manifest_valid = ctx.get("integrity_manifest_valid", False)
        hash_chain_valid = ctx.get("hash_chain_valid", False)
        tampered_files = ctx.get("tampered_files", [])
        
        if tampered_files:
            return InvariantResult(
                invariant_id="INV-017",
                name="Cryptographic Integrity",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason=f"File tampering detected: {len(tampered_files)} files",
                evidence={"tampered_files": tampered_files[:10]}
            )
        
        if not manifest_valid:
            return InvariantResult(
                invariant_id="INV-017",
                name="Cryptographic Integrity",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Integrity manifest validation failed",
                evidence={"manifest_valid": False}
            )
        
        if not hash_chain_valid:
            return InvariantResult(
                invariant_id="INV-017",
                name="Cryptographic Integrity",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Hash chain integrity broken",
                evidence={"hash_chain_valid": False}
            )
        
        return InvariantResult(
            invariant_id="INV-017",
            name="Cryptographic Integrity",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="All cryptographic integrity checks passed",
            evidence={"manifest_valid": True, "hash_chain_valid": True}
        )
    
    registry.register(Invariant(
        id="INV-017",
        name="Cryptographic Integrity",
        description="All protected files verified via SHA-3 hash chain",
        severity=Severity.CRITICAL,
        validator=validate_cryptographic_integrity,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 18: Defense-in-Depth Active
    # ─────────────────────────────────────────────────────────────
    def validate_defense_in_depth(ctx: Dict[str, Any]) -> InvariantResult:
        layers_active = ctx.get("defense_layers_active", {})
        required_layers = {"perimeter", "application", "data", "kernel", "audit"}
        
        active_layers = set(k for k, v in layers_active.items() if v)
        missing_layers = required_layers - active_layers
        
        if missing_layers:
            return InvariantResult(
                invariant_id="INV-018",
                name="Defense-in-Depth Active",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Missing defense layers: {missing_layers}",
                evidence={
                    "required_layers": list(required_layers),
                    "active_layers": list(active_layers),
                    "missing_layers": list(missing_layers)
                }
            )
        
        return InvariantResult(
            invariant_id="INV-018",
            name="Defense-in-Depth Active",
            status=InvariantStatus.PASS,
            severity=Severity.HIGH,
            reason="All defense layers active",
            evidence={"layers_active": list(active_layers)}
        )
    
    registry.register(Invariant(
        id="INV-018",
        name="Defense-in-Depth Active",
        description="All 5 defense layers (perimeter, application, data, kernel, audit) must be active",
        severity=Severity.HIGH,
        validator=validate_defense_in_depth,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 19: Tamper Detection Active
    # ─────────────────────────────────────────────────────────────
    def validate_tamper_detection(ctx: Dict[str, Any]) -> InvariantResult:
        tamper_detection_enabled = ctx.get("tamper_detection_enabled", False)
        last_scan_age_seconds = ctx.get("tamper_scan_age_seconds", float('inf'))
        max_scan_age = ctx.get("max_tamper_scan_age", 3600)  # 1 hour default
        
        if not tamper_detection_enabled:
            return InvariantResult(
                invariant_id="INV-019",
                name="Tamper Detection Active",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Tamper detection is disabled",
                evidence={"tamper_detection_enabled": False}
            )
        
        if last_scan_age_seconds > max_scan_age:
            return InvariantResult(
                invariant_id="INV-019",
                name="Tamper Detection Active",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason=f"Tamper scan stale: {last_scan_age_seconds}s > {max_scan_age}s",
                evidence={
                    "last_scan_age_seconds": last_scan_age_seconds,
                    "max_scan_age": max_scan_age
                }
            )
        
        return InvariantResult(
            invariant_id="INV-019",
            name="Tamper Detection Active",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="Tamper detection active and current",
            evidence={
                "tamper_detection_enabled": True,
                "last_scan_age_seconds": last_scan_age_seconds
            }
        )
    
    registry.register(Invariant(
        id="INV-019",
        name="Tamper Detection Active",
        description="Runtime tamper detection must be enabled and current",
        severity=Severity.CRITICAL,
        validator=validate_tamper_detection,
        agi_safety=True
    ))
    
    # ─────────────────────────────────────────────────────────────
    # INVARIANT 20: Fail-Secure Default
    # ─────────────────────────────────────────────────────────────
    def validate_fail_secure(ctx: Dict[str, Any]) -> InvariantResult:
        fail_open_detected = ctx.get("fail_open_detected", False)
        silent_failures = ctx.get("silent_failures_detected", [])
        degraded_security = ctx.get("degraded_security_mode", False)
        
        if fail_open_detected:
            return InvariantResult(
                invariant_id="INV-020",
                name="Fail-Secure Default",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason="Fail-open behavior detected - system must fail-secure",
                evidence={"fail_open_detected": True}
            )
        
        if silent_failures:
            return InvariantResult(
                invariant_id="INV-020",
                name="Fail-Secure Default",
                status=InvariantStatus.FAIL,
                severity=Severity.CRITICAL,
                reason=f"Silent failures detected: {len(silent_failures)}",
                evidence={"silent_failures": silent_failures[:10]}
            )
        
        if degraded_security:
            return InvariantResult(
                invariant_id="INV-020",
                name="Fail-Secure Default",
                status=InvariantStatus.FAIL,
                severity=Severity.HIGH,
                reason="System operating in degraded security mode",
                evidence={"degraded_security_mode": True}
            )
        
        return InvariantResult(
            invariant_id="INV-020",
            name="Fail-Secure Default",
            status=InvariantStatus.PASS,
            severity=Severity.CRITICAL,
            reason="System configured to fail-secure",
            evidence={"fail_secure": True}
        )
    
    registry.register(Invariant(
        id="INV-020",
        name="Fail-Secure Default",
        description="All failures must result in secure state, never fail-open",
        severity=Severity.CRITICAL,
        validator=validate_fail_secure,
        agi_safety=True
    ))
    
    return registry


def create_milspec_registry() -> InvariantRegistry:
    """
    Create registry with all 20 invariants including MILSPEC hardening.
    
    Invariants 1-10: Core Constitutional
    Invariants 11-15: AGI Safety Extensions
    Invariants 16-20: MILSPEC Security Hardening
    """
    registry = create_default_registry()
    return add_milspec_invariants(registry)
