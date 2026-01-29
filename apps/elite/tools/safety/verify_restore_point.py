#!/usr/bin/env python3
"""
Verify Restore Point - Sovereign Sanctuary Elite

Verify integrity of a restore point by checking all file hashes.

Version: 2.0.0
Author: Manus AI for Architect

VERIFICATION CHECKS:
- All files in manifest exist
- All file hashes match
- Manifest structure is valid
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

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


def load_manifest(restore_dir: Path) -> Dict[str, Any]:
    """Load and validate manifest from restore point"""
    manifest_path = restore_dir / "MANIFEST.json"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"MANIFEST.json not found in {restore_dir}")
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    # Validate required fields
    required_fields = ["restore_id", "created_utc", "files"]
    for field in required_fields:
        if field not in manifest:
            raise ValueError(f"Manifest missing required field: {field}")
    
    return manifest


def verify_files(restore_dir: Path, files: List[Dict[str, Any]]) -> tuple[int, int, List[str]]:
    """
    Verify all files in the restore point.
    
    Returns:
        Tuple of (passed_count, failed_count, error_messages)
    """
    passed = 0
    failed = 0
    errors = []
    
    for file_info in files:
        file_path = restore_dir / file_info["path"]
        expected_hash = file_info["sha256"]
        
        if not file_path.exists():
            print(f"  ❌ MISSING: {file_info['path']}")
            errors.append(f"Missing file: {file_info['path']}")
            failed += 1
            continue
        
        actual_hash = sha256_file(file_path)
        
        if actual_hash != expected_hash:
            print(f"  ❌ HASH MISMATCH: {file_info['path']}")
            print(f"     Expected: {expected_hash}")
            print(f"     Actual:   {actual_hash}")
            errors.append(f"Hash mismatch: {file_info['path']}")
            failed += 1
        else:
            print(f"  ✅ VERIFIED: {file_info['path']}")
            passed += 1
    
    return passed, failed, errors


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    """
    Verify a restore point.
    
    Usage: python verify_restore_point.py <restore_point_path>
    
    Returns:
        0 if verification passes, 1 otherwise
    """
    if len(sys.argv) < 2:
        print("Usage: python verify_restore_point.py <restore_point_path>")
        print("Example: python verify_restore_point.py RESTORE_POINTS/RESTORE_20260125_120000")
        return 1
    
    restore_dir = Path(sys.argv[1])
    
    print("\n" + "=" * 60)
    print("SOVEREIGN SANCTUARY ELITE - VERIFY RESTORE POINT")
    print("=" * 60)
    print(f"Restore Point: {restore_dir}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z")
    print("-" * 60)
    
    # Check restore point exists
    if not restore_dir.exists():
        print(f"❌ Restore point not found: {restore_dir}")
        return 1
    
    # Load manifest
    try:
        manifest = load_manifest(restore_dir)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"❌ Failed to load manifest: {e}")
        return 1
    
    print(f"Restore ID: {manifest['restore_id']}")
    print(f"Created: {manifest['created_utc']}")
    print(f"Files to verify: {len(manifest['files'])}")
    print("-" * 60)
    
    # Verify files
    passed, failed, errors = verify_files(restore_dir, manifest["files"])
    
    # Print summary
    print("-" * 60)
    print(f"Verification Results:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed == 0:
        print("\n✅ RESTORE POINT VERIFIED - ALL FILES INTACT")
        return 0
    else:
        print("\n❌ RESTORE POINT VERIFICATION FAILED")
        print("Errors:")
        for e in errors:
            print(f"  - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
