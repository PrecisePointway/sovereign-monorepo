#!/usr/bin/env python3
"""
Verify Snapshot Safety - Sovereign Sanctuary Elite

Snapshot integrity + temporal consistency check.
External-facing verification tool.

Version: 2.0.0
Author: Manus AI for Architect

VERIFICATION CHECKS:
- All files in manifest exist
- All file hashes match
- Temporal consistency (files not modified after snapshot)
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

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


def load_manifest(snapshot_dir: Path) -> Dict[str, Any]:
    """Load manifest from snapshot"""
    manifest_path = snapshot_dir / "MANIFEST.json"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"MANIFEST.json not found in {snapshot_dir}")
    
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp string"""
    # Handle various ISO formats
    ts_str = ts_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        # Fallback for formats without timezone
        return datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    """
    Verify a snapshot's integrity and safety.
    
    Usage: python verify_snapshot_safety.py <snapshot_path>
    
    Returns:
        0 if verification passes, 1 otherwise
    """
    if len(sys.argv) < 2:
        print("Usage: python verify_snapshot_safety.py <snapshot_path>")
        print("Example: python verify_snapshot_safety.py EVIDENCE_SNAPSHOTS/SNAPSHOT_20260125_120000")
        return 1
    
    snapshot_dir = Path(sys.argv[1])
    
    print("\n" + "=" * 60)
    print("SOVEREIGN SANCTUARY ELITE - VERIFY SNAPSHOT SAFETY")
    print("=" * 60)
    print(f"Snapshot: {snapshot_dir}")
    print(f"Verification Time: {datetime.now(timezone.utc).isoformat()}Z")
    print("-" * 60)
    
    # Check snapshot exists
    if not snapshot_dir.exists():
        print(f"❌ Snapshot not found: {snapshot_dir}")
        return 1
    
    # Load manifest
    try:
        manifest = load_manifest(snapshot_dir)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Failed to load manifest: {e}")
        return 1
    
    snapshot_id = manifest.get("snapshot_id", "UNKNOWN")
    creation_time = manifest.get("creation_timestamp", "UNKNOWN")
    
    print(f"Snapshot ID: {snapshot_id}")
    print(f"Created: {creation_time}")
    print(f"Files: {len(manifest.get('files', []))}")
    print("-" * 60)
    
    # Parse creation timestamp
    try:
        creation_dt = parse_timestamp(creation_time)
    except Exception:
        creation_dt = None
        print("⚠️  Could not parse creation timestamp")
    
    # Verify files
    passed = 0
    failed = 0
    warnings = 0
    
    print("Verifying files...")
    
    for file_info in manifest.get("files", []):
        file_name = file_info.get("name", file_info.get("path", "UNKNOWN"))
        file_path = snapshot_dir / file_name
        expected_hash = file_info.get("sha256", "")
        
        # Check existence
        if not file_path.exists():
            print(f"  ❌ MISSING: {file_name}")
            failed += 1
            continue
        
        # Check hash
        actual_hash = sha256_file(file_path)
        if actual_hash != expected_hash:
            print(f"  ❌ HASH MISMATCH: {file_name}")
            print(f"     Expected: {expected_hash}")
            print(f"     Actual:   {actual_hash}")
            failed += 1
            continue
        
        # Check temporal consistency (file not modified after snapshot)
        if creation_dt:
            file_mtime = datetime.fromtimestamp(
                file_path.stat().st_mtime, tz=timezone.utc
            )
            if file_mtime > creation_dt:
                print(f"  ⚠️  TEMPORAL WARNING: {file_name}")
                print(f"     File modified after snapshot creation")
                warnings += 1
        
        print(f"  ✅ VERIFIED: {file_name}")
        passed += 1
    
    # Print summary
    print("-" * 60)
    print("Verification Results:")
    print(f"  ✅ Passed:   {passed}")
    print(f"  ❌ Failed:   {failed}")
    print(f"  ⚠️  Warnings: {warnings}")
    
    # Calculate manifest hash for reference
    manifest_path = snapshot_dir / "MANIFEST.json"
    manifest_hash = sha256_file(manifest_path)
    print(f"\nManifest Hash: {manifest_hash}")
    
    if failed == 0:
        print("\n✅ SNAPSHOT VERIFIED - ALL FILES INTACT")
        if warnings > 0:
            print(f"   ({warnings} temporal warnings - review if concerned)")
        return 0
    else:
        print("\n❌ SNAPSHOT VERIFICATION FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
