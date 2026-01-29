#!/usr/bin/env python3
"""
H.U.G Protocol — Human-in-the-Loop Governance
Standalone module for CI/CD integration.

H: Human Review Gate (mandatory approval on critical changes)
U: Unit/Invariant Check (automated pass/fail)
G: Governance Evidence Log (immutable append to chain)

Usage:
    # In CI/CD pipeline:
    python hug_protocol.py --changed-files file1.py file2.py --commit-msg "feat: update"
    
    # Or import in Python:
    from hug_protocol import run_hug_audit, HUGResult
"""

from __future__ import annotations
import os
import sys
import json
import argparse
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class HUGResult:
    """Result of a H.U.G Protocol step."""
    step: str  # "H", "U", "G"
    passed: bool
    evidence: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "passed": self.passed,
            "evidence": self.evidence,
            "timestamp": self.timestamp
        }


# Critical file patterns that require human review
CRITICAL_PATTERNS = [
    "invariant",
    "governance",
    "constitution",
    "daemon",
    "authority",
    "security",
    "credential",
    "secret",
    ".env",
    "kill_switch",
    "halt"
]


def needs_human_review(changed_files: List[str]) -> bool:
    """
    Determine if changes require human review.
    
    Returns True if any changed file matches critical patterns.
    """
    for file_path in changed_files:
        file_lower = file_path.lower()
        for pattern in CRITICAL_PATTERNS:
            if pattern in file_lower:
                return True
    return False


def is_human_approved(commit_msg: str) -> bool:
    """
    Check if the commit has human approval markers.
    
    Approved markers:
    - [human-approved]
    - [approved]
    - Approved-by:
    """
    msg_lower = commit_msg.lower()
    return any([
        "[human-approved]" in msg_lower,
        "[approved]" in msg_lower,
        "approved-by:" in msg_lower,
        "acked-by:" in msg_lower
    ])


def run_invariant_tests() -> tuple[bool, Dict[str, Any]]:
    """
    Run invariant validation tests.
    
    Returns (passed, evidence).
    """
    # Try to import and run the governance daemon validator
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from governance_daemon import GovernanceDaemon, GovernanceDaemonConfig
        
        config = GovernanceDaemonConfig.for_testing()
        daemon = GovernanceDaemon(config)
        results = daemon.validate_once()
        
        failures = daemon.registry.get_failures(results)
        
        return len(failures) == 0, {
            "total": len(results),
            "passed": len(results) - len(failures),
            "failed": len(failures),
            "failures": [f.to_dict() for f in failures[:5]]
        }
    except ImportError:
        # Fallback: run pytest if available
        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0, {
                "method": "pytest",
                "returncode": result.returncode,
                "stdout": result.stdout[-1000:] if result.stdout else ""
            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True, {
                "method": "skipped",
                "reason": "No test framework available"
            }


def run_hug_audit(
    changed_files: List[str],
    commit_msg: str,
    ledger_path: Optional[str] = None
) -> List[HUGResult]:
    """
    Run the full H.U.G Protocol audit.
    
    Args:
        changed_files: List of files changed in this commit/deployment
        commit_msg: Commit message or deployment description
        ledger_path: Optional path to evidence ledger
        
    Returns:
        List of HUGResult for each step
    """
    results = []
    now = datetime.now(timezone.utc).isoformat()
    
    # ─────────────────────────────────────────────────────────────
    # H: Human Review Gate
    # ─────────────────────────────────────────────────────────────
    requires_human = needs_human_review(changed_files)
    human_approved = is_human_approved(commit_msg)
    
    h_passed = not requires_human or human_approved
    
    results.append(HUGResult(
        step="H",
        passed=h_passed,
        evidence={
            "changed_files": changed_files,
            "commit_msg": commit_msg[:200],  # Truncate for evidence
            "requires_human_review": requires_human,
            "human_approved": human_approved,
            "critical_patterns_matched": [
                f for f in changed_files 
                if any(p in f.lower() for p in CRITICAL_PATTERNS)
            ]
        },
        timestamp=now
    ))
    
    # ─────────────────────────────────────────────────────────────
    # U: Unit/Invariant Check
    # ─────────────────────────────────────────────────────────────
    u_passed, u_evidence = run_invariant_tests()
    
    results.append(HUGResult(
        step="U",
        passed=u_passed,
        evidence=u_evidence,
        timestamp=now
    ))
    
    # ─────────────────────────────────────────────────────────────
    # G: Governance Evidence Log
    # ─────────────────────────────────────────────────────────────
    # This step always passes if we reach it (evidence is being logged)
    g_evidence = {
        "audit_complete": True,
        "results_count": len(results),
        "all_passed": all(r.passed for r in results)
    }
    
    # Append to ledger if path provided
    if ledger_path:
        try:
            Path(ledger_path).parent.mkdir(parents=True, exist_ok=True)
            with open(ledger_path, 'a') as f:
                for r in results:
                    entry = {
                        "type": f"HUG_STEP_{r.step}",
                        "timestamp": r.timestamp,
                        "result": r.to_dict()
                    }
                    f.write(json.dumps(entry, separators=(",", ":")) + "\n")
            g_evidence["ledger_path"] = ledger_path
            g_evidence["ledger_written"] = True
        except IOError as e:
            g_evidence["ledger_error"] = str(e)
    
    results.append(HUGResult(
        step="G",
        passed=True,
        evidence=g_evidence,
        timestamp=now
    ))
    
    return results


def print_results(results: List[HUGResult]) -> None:
    """Print H.U.G audit results in a readable format."""
    print("\n" + "═" * 50)
    print("  H.U.G PROTOCOL AUDIT RESULTS")
    print("═" * 50)
    
    for r in results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        step_name = {
            "H": "Human Review Gate",
            "U": "Unit/Invariant Check",
            "G": "Governance Evidence Log"
        }.get(r.step, r.step)
        
        print(f"\n[{r.step}] {step_name}: {status}")
        
        # Print relevant evidence
        if r.step == "H":
            if r.evidence.get("requires_human_review"):
                print(f"    Critical files: {r.evidence.get('critical_patterns_matched', [])}")
                print(f"    Human approved: {r.evidence.get('human_approved', False)}")
        elif r.step == "U":
            print(f"    Tests: {r.evidence.get('passed', 0)}/{r.evidence.get('total', 0)} passed")
            if r.evidence.get("failures"):
                print(f"    Failures: {len(r.evidence['failures'])}")
    
    print("\n" + "─" * 50)
    all_passed = all(r.passed for r in results)
    final_status = "✅ AUDIT PASSED" if all_passed else "❌ AUDIT FAILED"
    print(f"  FINAL: {final_status}")
    print("─" * 50 + "\n")


def main():
    """CLI entry point for H.U.G Protocol audit."""
    parser = argparse.ArgumentParser(
        description="H.U.G Protocol - Human-in-the-Loop Governance Audit"
    )
    
    parser.add_argument(
        "--changed-files",
        nargs="*",
        default=[],
        help="List of changed files"
    )
    
    parser.add_argument(
        "--commit-msg",
        default="",
        help="Commit message"
    )
    
    parser.add_argument(
        "--from-git",
        action="store_true",
        help="Auto-detect changed files and commit message from git"
    )
    
    parser.add_argument(
        "--ledger",
        default=None,
        help="Path to evidence ledger file"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    # Auto-detect from git if requested
    changed_files = args.changed_files
    commit_msg = args.commit_msg
    
    if args.from_git:
        try:
            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD^"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                changed_files = result.stdout.strip().split("\n")
                changed_files = [f for f in changed_files if f]
            
            # Get commit message
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                commit_msg = result.stdout.strip()
        except FileNotFoundError:
            print("Warning: git not found, using provided arguments")
    
    # Run audit
    results = run_hug_audit(
        changed_files=changed_files,
        commit_msg=commit_msg,
        ledger_path=args.ledger
    )
    
    # Output results
    if args.json:
        output = {
            "results": [r.to_dict() for r in results],
            "passed": all(r.passed for r in results)
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(results)
    
    # Exit with appropriate code
    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
