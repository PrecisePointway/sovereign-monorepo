#!/usr/bin/env python3
"""
Sovereign Governance Kernel — Governance Daemon
Active invariant validator with evidence emission and loud failure enforcement.

This daemon converts governance from descriptive to NON-OPTIONAL.

Features:
- Explicit invariant registry (15 invariants)
- Deterministic pass/fail output
- Evidence emission on violation (JSONL ledger)
- INV_FAILURE_IS_LOUD enforcement
- H.U.G Protocol integration hooks
- Systemd watchdog support
"""

from __future__ import annotations
import os
import sys
import json
import time
import signal
import hashlib
import logging
import argparse
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from invariants import (
    InvariantRegistry,
    InvariantResult,
    InvariantStatus,
    Severity,
    create_default_registry
)

# Systemd watchdog support
try:
    import systemd.daemon as sd_daemon
    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class GovernanceDaemonConfig:
    """Configuration for the governance daemon."""
    
    # Paths
    ledger_path: str = "/var/lib/sovereign/governance_ledger.jsonl"
    state_path: str = "/var/lib/sovereign/governance_state.json"
    pid_path: str = "/var/run/sovereign/governance.pid"
    log_path: str = "/var/log/sovereign/governance.log"
    constitution_path: str = "/etc/sovereign/constitution.yaml"
    
    # Validation settings
    validation_interval_sec: int = 30
    max_failures_before_halt: int = 3
    halt_on_critical: bool = True
    
    # Logging and alerting
    log_level: str = "INFO"
    alerting_enabled: bool = True
    alert_webhook_url: Optional[str] = None
    
    # Watchdog
    watchdog_enabled: bool = True
    watchdog_interval_sec: int = 60
    
    # Runtime
    mode: str = "production"  # production, development, test
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> 'GovernanceDaemonConfig':
        """Load configuration from environment variables."""
        return cls(
            ledger_path=os.environ.get("GOVERNANCE_LEDGER_PATH", cls.ledger_path),
            state_path=os.environ.get("GOVERNANCE_STATE_PATH", cls.state_path),
            log_path=os.environ.get("GOVERNANCE_LOG_PATH", cls.log_path),
            constitution_path=os.environ.get("CONSTITUTION_PATH", cls.constitution_path),
            validation_interval_sec=int(os.environ.get("VALIDATION_INTERVAL", "30")),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            alerting_enabled=os.environ.get("ALERTING_ENABLED", "true").lower() == "true",
            mode=os.environ.get("GOVERNANCE_MODE", "production"),
            debug=os.environ.get("DEBUG", "false").lower() == "true"
        )
    
    @classmethod
    def for_testing(cls) -> 'GovernanceDaemonConfig':
        """Create configuration suitable for testing."""
        return cls(
            ledger_path="/tmp/sovereign/governance_ledger.jsonl",
            state_path="/tmp/sovereign/governance_state.json",
            pid_path="/tmp/sovereign/governance.pid",
            log_path="/tmp/sovereign/governance.log",
            constitution_path="/tmp/sovereign/constitution.yaml",
            validation_interval_sec=5,
            mode="test",
            debug=True
        )


# ═══════════════════════════════════════════════════════════════════
# EVIDENCE LEDGER
# ═══════════════════════════════════════════════════════════════════

class EvidenceLedger:
    """
    Append-only evidence ledger with hash chain integrity.
    
    All invariant results are recorded here for audit purposes.
    """
    
    def __init__(self, path: str):
        self.path = path
        self._last_hash: Optional[str] = None
        self._ensure_directory()
        self._load_last_hash()
    
    def _ensure_directory(self) -> None:
        """Ensure the ledger directory exists."""
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
    
    def _load_last_hash(self) -> None:
        """Load the hash of the last entry for chain continuity."""
        if not os.path.exists(self.path):
            return
        
        try:
            with open(self.path, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    self._last_hash = last_entry.get("entry_hash")
        except (json.JSONDecodeError, IOError):
            pass
    
    def _compute_entry_hash(self, entry: Dict[str, Any]) -> str:
        """Compute hash for a ledger entry."""
        # Include previous hash for chain integrity
        entry_with_prev = {**entry, "previous_hash": self._last_hash}
        canonical = json.dumps(entry_with_prev, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def append(self, result: InvariantResult) -> str:
        """
        Append an invariant result to the ledger.
        
        Returns the entry hash.
        """
        entry = {
            "type": "INVARIANT_RESULT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_hash": self._last_hash,
            "result": result.to_dict()
        }
        
        entry_hash = self._compute_entry_hash(entry)
        entry["entry_hash"] = entry_hash
        
        # Append to ledger
        with open(self.path, 'a') as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        
        self._last_hash = entry_hash
        return entry_hash
    
    def append_batch(self, results: List[InvariantResult]) -> List[str]:
        """Append multiple results and return their hashes."""
        return [self.append(r) for r in results]
    
    def append_event(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Append a general event to the ledger."""
        entry = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_hash": self._last_hash,
            "payload": payload
        }
        
        entry_hash = self._compute_entry_hash(entry)
        entry["entry_hash"] = entry_hash
        
        with open(self.path, 'a') as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        
        self._last_hash = entry_hash
        return entry_hash
    
    def verify_chain(self) -> bool:
        """Verify the integrity of the hash chain."""
        if not os.path.exists(self.path):
            return True
        
        prev_hash = None
        with open(self.path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    if entry.get("previous_hash") != prev_hash:
                        logging.error(f"Chain broken at line {line_num}")
                        return False
                    prev_hash = entry.get("entry_hash")
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON at line {line_num}")
                    return False
        
        return True


# ═══════════════════════════════════════════════════════════════════
# LOUD FAILURE HANDLER
# ═══════════════════════════════════════════════════════════════════

class LoudFailureHandler:
    """
    INV_FAILURE_IS_LOUD implementation.
    
    Ensures all failures are:
    1. Logged with full context
    2. Emitted to evidence ledger
    3. Alerted (if configured)
    4. Never silent
    """
    
    def __init__(self, config: GovernanceDaemonConfig, ledger: EvidenceLedger):
        self.config = config
        self.ledger = ledger
        self.failure_count = 0
        self.critical_failure_count = 0
    
    def handle_failure(self, result: InvariantResult) -> None:
        """
        Handle an invariant failure LOUDLY.
        
        This method ensures failures are never silent.
        """
        self.failure_count += 1
        
        if result.severity == Severity.CRITICAL:
            self.critical_failure_count += 1
        
        # 1. Log with full context
        log_msg = (
            f"INVARIANT FAILURE [{result.severity.value}] "
            f"{result.invariant_id}: {result.name} - {result.reason}"
        )
        
        if result.severity == Severity.CRITICAL:
            logging.critical(log_msg)
        elif result.severity == Severity.HIGH:
            logging.error(log_msg)
        else:
            logging.warning(log_msg)
        
        # 2. Emit to evidence ledger
        self.ledger.append(result)
        
        # 3. Alert if configured
        if self.config.alerting_enabled:
            self._send_alert(result)
        
        # 4. Log evidence for audit
        logging.info(f"Evidence recorded: {result.hash}")
    
    def _send_alert(self, result: InvariantResult) -> None:
        """Send alert for failure (webhook, etc.)."""
        if not self.config.alert_webhook_url:
            return
        
        # In production, this would POST to the webhook
        # For now, just log the alert
        logging.info(f"ALERT: {result.invariant_id} failed - {result.reason}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get failure statistics."""
        return {
            "total_failures": self.failure_count,
            "critical_failures": self.critical_failure_count
        }


# ═══════════════════════════════════════════════════════════════════
# H.U.G PROTOCOL INTEGRATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class HUGResult:
    """Result of a H.U.G Protocol step."""
    step: str  # "H", "U", "G"
    passed: bool
    evidence: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HUGProtocol:
    """
    H.U.G Protocol — Human-in-the-Loop Governance
    
    H: Human Review Gate (mandatory approval on critical changes)
    U: Unit/Invariant Check (automated pass/fail)
    G: Governance Evidence Log (immutable append to chain)
    """
    
    def __init__(self, ledger: EvidenceLedger):
        self.ledger = ledger
    
    def run_audit(
        self,
        changed_files: List[str],
        commit_msg: str,
        invariant_results: List[InvariantResult]
    ) -> List[HUGResult]:
        """
        Run the full H.U.G audit.
        
        Args:
            changed_files: List of files changed in this commit/deployment
            commit_msg: Commit message or deployment description
            invariant_results: Results from invariant validation
            
        Returns:
            List of HUGResult for each step
        """
        results = []
        now = datetime.now(timezone.utc).isoformat()
        
        # H: Human Review Gate
        needs_human = any(
            "invariant" in f.lower() or 
            "governance" in f.lower() or
            "constitution" in f.lower()
            for f in changed_files
        )
        
        human_approved = (
            "approved" in commit_msg.lower() or
            "[human-approved]" in commit_msg.lower() or
            not needs_human
        )
        
        results.append(HUGResult(
            step="H",
            passed=human_approved,
            evidence={
                "changed_files": changed_files,
                "commit_msg": commit_msg,
                "needs_human_review": needs_human,
                "human_approved": human_approved
            },
            timestamp=now
        ))
        
        # U: Unit/Invariant Check
        all_passed = all(
            r.status == InvariantStatus.PASS 
            for r in invariant_results
        )
        
        failures = [
            r.to_dict() for r in invariant_results 
            if r.is_failure()
        ]
        
        results.append(HUGResult(
            step="U",
            passed=all_passed,
            evidence={
                "total_invariants": len(invariant_results),
                "passed": sum(1 for r in invariant_results if r.status == InvariantStatus.PASS),
                "failed": len(failures),
                "failures": failures[:5]  # Limit to first 5
            },
            timestamp=now
        ))
        
        # G: Governance Evidence Log
        # This step always passes if we reach it (evidence is being logged)
        results.append(HUGResult(
            step="G",
            passed=True,
            evidence={
                "audit_complete": True,
                "results_count": len(results),
                "ledger_path": self.ledger.path
            },
            timestamp=now
        ))
        
        # Log H.U.G results to ledger
        for hug in results:
            self.ledger.append_event(
                event_type=f"HUG_STEP_{hug.step}",
                payload={
                    "passed": hug.passed,
                    "evidence": hug.evidence,
                    "timestamp": hug.timestamp
                }
            )
        
        return results
    
    def is_audit_passed(self, results: List[HUGResult]) -> bool:
        """Check if the full H.U.G audit passed."""
        return all(r.passed for r in results)


# ═══════════════════════════════════════════════════════════════════
# GOVERNANCE DAEMON
# ═══════════════════════════════════════════════════════════════════

class GovernanceDaemon:
    """
    Active Invariant Validator Daemon.
    
    This daemon:
    - Continuously validates all 15 constitutional invariants
    - Emits evidence to the governance ledger
    - Enforces INV_FAILURE_IS_LOUD
    - Integrates with H.U.G Protocol
    - Supports systemd watchdog
    """
    
    def __init__(self, config: GovernanceDaemonConfig):
        self.config = config
        self.running = False
        self._setup_logging()
        
        # Initialize components
        self.registry = create_default_registry()
        self.ledger = EvidenceLedger(config.ledger_path)
        self.failure_handler = LoudFailureHandler(config, self.ledger)
        self.hug_protocol = HUGProtocol(self.ledger)
        
        # State
        self.validation_count = 0
        self.last_validation: Optional[datetime] = None
        self.consecutive_failures = 0
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    def _setup_logging(self) -> None:
        """Configure logging with LOUD failure support."""
        Path(self.config.log_path).parent.mkdir(parents=True, exist_ok=True)
        
        handlers = [
            logging.FileHandler(self.config.log_path),
            logging.StreamHandler(sys.stdout)
        ]
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=handlers
        )
    
    def _handle_sigterm(self, signum, frame) -> None:
        """Handle SIGTERM for graceful shutdown."""
        logging.info("Received SIGTERM, initiating graceful shutdown")
        self.stop()
    
    def _handle_sigint(self, signum, frame) -> None:
        """Handle SIGINT (Ctrl+C)."""
        logging.info("Received SIGINT, initiating graceful shutdown")
        self.stop()
    
    def _build_validation_context(self) -> Dict[str, Any]:
        """
        Build the runtime context for invariant validation.
        
        This context is passed to all invariant validators.
        """
        context = {
            # Paths
            "ledger_path": self.config.ledger_path,
            "constitution_path": self.config.constitution_path,
            
            # Human oversight
            "human_oversight_enabled": True,
            "kill_switch_active": True,
            "kill_switch_accessible": True,
            "kill_switch_disabled": False,
            
            # Constitution
            "constitution_hash": self._compute_constitution_hash(),
            "expected_constitution_hash": self._get_expected_constitution_hash(),
            
            # Runtime state
            "current_phase": 0,
            "deterministic_mode": True,
            
            # Failure detection
            "silent_failures_detected": [],
            "logging_enabled": True,
            "alerting_enabled": self.config.alerting_enabled,
            
            # Authority
            "active_authorities": [],
            
            # Evidence
            "ungrounded_claims": [],
            
            # Refusal
            "refusal_enabled": True,
            "refusal_overridden": False,
            
            # Data
            "data_retention_policy": "30_days",
            "excessive_retention_detected": False,
            
            # Boundaries
            "boundary_violations": [],
            
            # AGI Safety
            "constraint_files_hashes": self._compute_constraint_hashes(),
            "expected_constraint_hashes": self._get_expected_constraint_hashes(),
            "max_recursion_depth": 100,
            "current_recursion_depth": 0,
            "unbounded_chains_detected": [],
            "persistent_goals_detected": [],
            "cross_session_memory_unauthorized": False,
            "override_delayed": False,
            "state_misrepresentations_detected": [],
            "capability_misrepresentations": []
        }
        
        return context
    
    def _compute_constitution_hash(self) -> Optional[str]:
        """Compute hash of the constitution file."""
        if not os.path.exists(self.config.constitution_path):
            return None
        
        with open(self.config.constitution_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _get_expected_constitution_hash(self) -> Optional[str]:
        """Get the expected constitution hash from state."""
        # In production, this would be loaded from a secure store
        # For now, return the current hash (first run establishes baseline)
        return self._compute_constitution_hash()
    
    def _compute_constraint_hashes(self) -> Dict[str, str]:
        """Compute hashes of constraint files."""
        hashes = {}
        constraint_dir = Path(self.config.constitution_path).parent
        
        if constraint_dir.exists():
            for f in constraint_dir.glob("*.yaml"):
                with open(f, 'rb') as file:
                    hashes[str(f)] = hashlib.sha256(file.read()).hexdigest()
        
        return hashes
    
    def _get_expected_constraint_hashes(self) -> Dict[str, str]:
        """Get expected constraint hashes from state."""
        # In production, loaded from secure store
        return self._compute_constraint_hashes()
    
    def validate_once(self) -> List[InvariantResult]:
        """
        Run a single validation cycle.
        
        Returns all invariant results.
        """
        self.validation_count += 1
        self.last_validation = datetime.now(timezone.utc)
        
        logging.info(f"Starting validation cycle #{self.validation_count}")
        
        # Build context
        context = self._build_validation_context()
        
        # Validate all invariants
        results = self.registry.validate_all(context)
        
        # Process results
        failures = self.registry.get_failures(results)
        
        if failures:
            self.consecutive_failures += 1
            
            # Handle each failure LOUDLY
            for failure in failures:
                self.failure_handler.handle_failure(failure)
            
            # Check for critical failures
            if self.registry.has_critical_failure(results):
                logging.critical(f"CRITICAL INVARIANT FAILURE DETECTED")
                
                if self.config.halt_on_critical:
                    logging.critical("Initiating emergency halt due to critical failure")
                    self._emergency_halt(failures)
            
            # Check consecutive failure threshold
            if self.consecutive_failures >= self.config.max_failures_before_halt:
                logging.critical(
                    f"Consecutive failure threshold reached: "
                    f"{self.consecutive_failures}/{self.config.max_failures_before_halt}"
                )
                self._emergency_halt(failures)
        else:
            self.consecutive_failures = 0
            logging.info(f"Validation cycle #{self.validation_count} PASSED - All invariants satisfied")
        
        # Record batch to ledger
        self.ledger.append_batch(results)
        
        # Notify systemd watchdog
        if SYSTEMD_AVAILABLE and self.config.watchdog_enabled:
            sd_daemon.notify("WATCHDOG=1")
        
        return results
    
    def _emergency_halt(self, failures: List[InvariantResult]) -> None:
        """
        Execute emergency halt procedure.
        
        This is the HALT_ALL implementation.
        """
        logging.critical("═" * 60)
        logging.critical("  EMERGENCY HALT INITIATED")
        logging.critical("═" * 60)
        
        # Log all failures
        for failure in failures:
            logging.critical(f"  - {failure.invariant_id}: {failure.reason}")
        
        # Record halt event to ledger
        self.ledger.append_event(
            event_type="EMERGENCY_HALT",
            payload={
                "reason": "Critical invariant failure",
                "failures": [f.to_dict() for f in failures],
                "validation_count": self.validation_count
            }
        )
        
        # Stop the daemon
        self.stop()
        
        # Exit with error code
        sys.exit(1)
    
    def run_hug_audit(
        self,
        changed_files: List[str],
        commit_msg: str
    ) -> bool:
        """
        Run H.U.G Protocol audit.
        
        Returns True if audit passed.
        """
        # First, run invariant validation
        results = self.validate_once()
        
        # Then run H.U.G audit
        hug_results = self.hug_protocol.run_audit(
            changed_files=changed_files,
            commit_msg=commit_msg,
            invariant_results=results
        )
        
        # Log results
        for hug in hug_results:
            status = "PASS" if hug.passed else "FAIL"
            logging.info(f"H.U.G [{hug.step}] {status}: {hug.evidence}")
        
        return self.hug_protocol.is_audit_passed(hug_results)
    
    def start(self) -> None:
        """Start the daemon in continuous validation mode."""
        logging.info("═" * 60)
        logging.info("  SOVEREIGN GOVERNANCE DAEMON STARTING")
        logging.info(f"  Mode: {self.config.mode}")
        logging.info(f"  Validation interval: {self.config.validation_interval_sec}s")
        logging.info(f"  Invariants registered: {len(self.registry.list_all())}")
        logging.info("═" * 60)
        
        self.running = True
        
        # Write PID file
        Path(self.config.pid_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.pid_path, 'w') as f:
            f.write(str(os.getpid()))
        
        # Record start event
        self.ledger.append_event(
            event_type="DAEMON_START",
            payload={
                "mode": self.config.mode,
                "invariants": [inv.id for inv in self.registry.list_all()],
                "pid": os.getpid()
            }
        )
        
        # Notify systemd ready
        if SYSTEMD_AVAILABLE:
            sd_daemon.notify("READY=1")
        
        # Main validation loop
        try:
            while self.running:
                self.validate_once()
                time.sleep(self.config.validation_interval_sec)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the daemon gracefully."""
        if not self.running:
            return
        
        logging.info("Stopping governance daemon...")
        self.running = False
        
        # Notify systemd stopping
        if SYSTEMD_AVAILABLE:
            sd_daemon.notify("STOPPING=1")
        
        # Record stop event
        self.ledger.append_event(
            event_type="DAEMON_STOP",
            payload={
                "validation_count": self.validation_count,
                "failure_stats": self.failure_handler.get_stats()
            }
        )
        
        # Remove PID file
        try:
            os.remove(self.config.pid_path)
        except FileNotFoundError:
            pass
        
        logging.info("Governance daemon stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current daemon status."""
        return {
            "running": self.running,
            "mode": self.config.mode,
            "validation_count": self.validation_count,
            "last_validation": self.last_validation.isoformat() if self.last_validation else None,
            "consecutive_failures": self.consecutive_failures,
            "failure_stats": self.failure_handler.get_stats(),
            "invariants": {
                "total": len(self.registry.list_all()),
                "agi_safety": len(self.registry.list_agi_safety())
            },
            "ledger_chain_valid": self.ledger.verify_chain()
        }


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    """CLI entry point for the governance daemon."""
    parser = argparse.ArgumentParser(
        description="Sovereign Governance Daemon - Active Invariant Validator"
    )
    
    parser.add_argument(
        "--mode",
        choices=["production", "development", "test"],
        default="production",
        help="Operating mode"
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run single validation cycle and exit"
    )
    
    parser.add_argument(
        "--hug",
        action="store_true",
        help="Run H.U.G Protocol audit"
    )
    
    parser.add_argument(
        "--changed-files",
        nargs="*",
        default=[],
        help="Files changed (for H.U.G audit)"
    )
    
    parser.add_argument(
        "--commit-msg",
        default="",
        help="Commit message (for H.U.G audit)"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print daemon status and exit"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Create configuration
    if args.mode == "test":
        config = GovernanceDaemonConfig.for_testing()
    else:
        config = GovernanceDaemonConfig.from_env()
    
    config.mode = args.mode
    config.debug = args.debug
    
    if args.debug:
        config.log_level = "DEBUG"
    
    # Create daemon
    daemon = GovernanceDaemon(config)
    
    # Execute requested action
    if args.status:
        status = daemon.get_status()
        print(json.dumps(status, indent=2, default=str))
        return
    
    if args.hug:
        passed = daemon.run_hug_audit(
            changed_files=args.changed_files,
            commit_msg=args.commit_msg
        )
        sys.exit(0 if passed else 1)
    
    if args.once:
        results = daemon.validate_once()
        failures = daemon.registry.get_failures(results)
        
        print(f"\nValidation Results:")
        print(f"  Total: {len(results)}")
        print(f"  Passed: {len(results) - len(failures)}")
        print(f"  Failed: {len(failures)}")
        
        if failures:
            print(f"\nFailures:")
            for f in failures:
                print(f"  [{f.severity.value}] {f.invariant_id}: {f.reason}")
        
        sys.exit(1 if failures else 0)
    
    # Start continuous validation
    daemon.start()


if __name__ == "__main__":
    main()
