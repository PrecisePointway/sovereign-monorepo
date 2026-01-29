#!/usr/bin/env python3
"""
Mirror Takedown Protocol - Sovereign Sanctuary Elite

Controlled takedown of mirror deployments.
DEFAULT = DRY RUN - Nothing destructive without explicit confirmation.

Version: 2.0.0
Author: Manus AI for Architect

SAFETY GUARANTEES:
- Default is DRY RUN (no changes)
- Requires hash-matched confirmation
- Requires explicit --execute flag
- All actions logged to ledger
- Manual steps enforced for destructive operations
"""

import argparse
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

STATE_PATH = Path("runtime/state.json")
LEDGER_PATH = Path("evidence/ledger.jsonl")

SUPPORTED_MODES = ["local", "github", "ipfs", "s3", "all"]

# ═══════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def sha256_file(path: Path) -> str:
    """Calculate SHA-256 hash of a file"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def log_takedown(mode: str, executed: bool, state_hash: str) -> None:
    """Log the takedown operation to the ledger"""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "event": "MIRROR_TAKEDOWN",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "executed": executed,
        "state_hash": state_hash,
        "dry_run": not executed
    }
    
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def execute_local_takedown(dry_run: bool) -> None:
    """Execute local mirror takedown"""
    print("\n[LOCAL TAKEDOWN]")
    if dry_run:
        print("  Would remove local mirror directories")
        print("  Affected paths:")
        print("    - ./EVIDENCE_SNAPSHOTS/")
        print("    - ./public_mirror/")
    else:
        print("  ⚠️  MANUAL STEP REQUIRED")
        print("  Execute the following commands manually:")
        print("    rm -rf ./public_mirror/")
        print("  (Evidence snapshots preserved for audit)")


def execute_github_takedown(dry_run: bool) -> None:
    """Execute GitHub mirror takedown"""
    print("\n[GITHUB TAKEDOWN]")
    if dry_run:
        print("  Would archive GitHub repository")
        print("  Repository: sovereign-sanctuary-elite")
    else:
        print("  ⚠️  MANUAL STEP REQUIRED")
        print("  Execute the following:")
        print("    gh repo archive <owner>/sovereign-sanctuary-elite --yes")
        print("  Or use GitHub web interface to archive/delete")


def execute_ipfs_takedown(dry_run: bool) -> None:
    """Execute IPFS mirror takedown"""
    print("\n[IPFS TAKEDOWN]")
    if dry_run:
        print("  Would unpin IPFS CID")
        print("  Note: Content may persist on other nodes")
    else:
        print("  ⚠️  MANUAL STEP REQUIRED")
        print("  Execute the following:")
        print("    ipfs pin rm <CID>")
        print("  Contact pinning service to remove from their nodes")


def execute_s3_takedown(dry_run: bool) -> None:
    """Execute S3 mirror takedown"""
    print("\n[S3 TAKEDOWN]")
    if dry_run:
        print("  Would delete S3 bucket contents")
        print("  Bucket: sovereign-evidence-mirror")
    else:
        print("  ⚠️  MANUAL STEP REQUIRED")
        print("  Execute the following:")
        print("    aws s3 rm s3://sovereign-evidence-mirror --recursive")
        print("  Then delete bucket if desired")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    """
    Execute mirror takedown protocol.
    
    Returns:
        0 on success, 1 on failure
    """
    parser = argparse.ArgumentParser(
        description="Mirror takedown protocol with failsafe defaults"
    )
    parser.add_argument(
        "--mode",
        choices=SUPPORTED_MODES,
        required=True,
        help="Takedown mode: local, github, ipfs, s3, or all"
    )
    parser.add_argument(
        "--confirm-hash",
        required=True,
        help="SHA-256 hash of state.json for confirmation"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute takedown (default is dry run)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip state file check (dangerous)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("SOVEREIGN SANCTUARY ELITE - MIRROR TAKEDOWN PROTOCOL")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Execute: {args.execute}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z")
    print("-" * 60)
    
    # Verify state file exists
    if not STATE_PATH.exists() and not args.force:
        print(f"❌ State file not found: {STATE_PATH}")
        print("   Use --force to skip this check (dangerous)")
        return 1
    
    # Calculate state hash
    if STATE_PATH.exists():
        actual_hash = sha256_file(STATE_PATH)
    else:
        actual_hash = "FORCED_NO_STATE"
    
    # Verify hash confirmation
    if actual_hash != args.confirm_hash:
        print("❌ HASH CONFIRMATION FAILED")
        print(f"   Expected: {args.confirm_hash}")
        print(f"   Actual:   {actual_hash}")
        print("\nTo get current hash:")
        print(f"   sha256sum {STATE_PATH}")
        return 1
    
    print("✅ Hash confirmation passed")
    
    # Determine if dry run
    dry_run = not args.execute
    
    if dry_run:
        print("\n" + "=" * 60)
        print("⚠️  DRY RUN MODE - NO CHANGES WILL BE MADE")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("🚨 EXECUTION MODE - MANUAL STEPS WILL BE SHOWN")
        print("=" * 60)
    
    # Execute takedown based on mode
    modes_to_execute = SUPPORTED_MODES[:-1] if args.mode == "all" else [args.mode]
    
    for mode in modes_to_execute:
        if mode == "local":
            execute_local_takedown(dry_run)
        elif mode == "github":
            execute_github_takedown(dry_run)
        elif mode == "ipfs":
            execute_ipfs_takedown(dry_run)
        elif mode == "s3":
            execute_s3_takedown(dry_run)
    
    # Log the operation
    log_takedown(args.mode, args.execute, actual_hash)
    
    # Print summary
    print("\n" + "-" * 60)
    if dry_run:
        print("✅ DRY RUN COMPLETE")
        print("\nTo execute takedown, add --execute flag:")
        print(f"   python mirror_takedown.py --mode {args.mode} --confirm-hash {actual_hash} --execute")
    else:
        print("✅ TAKEDOWN INSTRUCTIONS GENERATED")
        print("\nFollow the manual steps above to complete takedown.")
        print("All actions have been logged to the ledger.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
