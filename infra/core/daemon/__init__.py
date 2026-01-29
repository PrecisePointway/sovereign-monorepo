"""
Sovereign Governance Kernel — Daemon Package

This package provides the active invariant validation daemon
for the Sovereign system.

Components:
- invariants: Constitutional invariant registry (15 invariants)
- governance_daemon: Active validator with evidence emission
- hug_protocol: H.U.G Protocol for CI/CD integration

Usage:
    # Run daemon in continuous mode
    python -m daemon.governance_daemon
    
    # Run single validation
    python -m daemon.governance_daemon --once
    
    # Run H.U.G audit
    python -m daemon.hug_protocol --from-git
"""

from .invariants import (
    Invariant,
    InvariantRegistry,
    InvariantResult,
    InvariantStatus,
    Severity,
    create_default_registry
)

from .governance_daemon import (
    GovernanceDaemon,
    GovernanceDaemonConfig,
    EvidenceLedger,
    LoudFailureHandler
)

from .hug_protocol import (
    HUGResult,
    run_hug_audit,
    needs_human_review,
    is_human_approved
)

__all__ = [
    # Invariants
    "Invariant",
    "InvariantRegistry",
    "InvariantResult",
    "InvariantStatus",
    "Severity",
    "create_default_registry",
    
    # Daemon
    "GovernanceDaemon",
    "GovernanceDaemonConfig",
    "EvidenceLedger",
    "LoudFailureHandler",
    
    # H.U.G Protocol
    "HUGResult",
    "run_hug_audit",
    "needs_human_review",
    "is_human_approved"
]

__version__ = "1.0.0"
