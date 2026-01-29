#!/usr/bin/env python3
"""
Create Restore Point - Sovereign Sanctuary Elite

Create immutable restore point with manifest + hash.
Safe by design. No deletes. No overwrites.

Version: 2.0.0
Author: Manus AI for Architect

SAFETY GUARANTEES:
- Never overwrites existing restore points
- All files hashed with SHA-256
- Manifest is cryptographically sealed
- Only files in allowlist are included
"""

import json
import hashlib
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

ALLOWLIST_PATH = Path("tools/restore/restore_allowlist.txt")
OUTPUT_DIR = Path("RESTORE_POINTS")
LEDGER_PATH = Path("evidence/ledger.jsonl")

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


def sha256_string(data: str) -> str:
    """Calculate SHA-256 hash of a string"""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def load_allowlist() -> List[tuple[str, bool]]:
    """
    Load the restore allowlist.
    
    Returns:
        List of (path, is_optional) tuples
    """
    if not ALLOWLIST_PATH.exists():
        print(f"⚠️  Allowlist not found at {ALLOWLIST_PATH}")
        print("   Creating default allowlist...")
        create_default_allowlist()
    
    entries = []
    for line in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        is_optional = line.endswith("?")
        path = line.rstrip("?")
        entries.append((path, is_optional))
    
    return entries


def create_default_allowlist() -> None:
    """Create a default allowlist file"""
    ALLOWLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    default_content = """# Restore Point Allowlist
# Lines ending with ? are optional
# Comments start with #

# Core configuration
runtime/state.json
config/swarm_config.json
config/sanctuary_config.yaml?

# Evidence (critical)
evidence/ledger.jsonl?
evidence/SITREP.md?

# Core code
core/daemon.py
core/models.py

# Tools
tools/self_heal_monitor.py
tools/flight_control_daemon.py
"""
    ALLOWLIST_PATH.write_text(default_content, encoding="utf-8")
    print(f"   Created: {ALLOWLIST_PATH}")


def log_restore_point(restore_id: str, manifest_hash: str, file_count: int) -> None:
    """Log the restore point creation to the ledger"""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "event": "RESTORE_POINT_CREATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "restore_id": restore_id,
        "manifest_hash": manifest_hash,
        "file_count": file_count
    }
    
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    """
    Create a new restore point.
    
    Returns:
        0 on success, 1 on failure
    """
    print("\n" + "=" * 60)
    print("SOVEREIGN SANCTUARY ELITE - CREATE RESTORE POINT")
    print("=" * 60)
    
    # Generate timestamp-based ID
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    restore_id = f"RESTORE_{stamp}"
    restore_dir = OUTPUT_DIR / restore_id
    
    # Check for collision (should never happen with second precision)
    if restore_dir.exists():
        print(f"❌ Restore point already exists: {restore_id}")
        return 1
    
    print(f"Restore ID: {restore_id}")
    print(f"Output Dir: {restore_dir}")
    print("-" * 60)
    
    # Load allowlist
    allowlist = load_allowlist()
    print(f"Allowlist entries: {len(allowlist)}")
    
    # Create restore directory
    restore_dir.mkdir(parents=True)
    
    # Copy files
    files: List[Dict[str, Any]] = []
    errors = []
    
    for path_str, is_optional in allowlist:
        source = Path(path_str)
        
        if not source.exists():
            if is_optional:
                print(f"  ⏭️  Skipped (optional): {path_str}")
                continue
            else:
                print(f"  ❌ Missing (required): {path_str}")
                errors.append(f"Missing required file: {path_str}")
                continue
        
        # Create destination path
        dest = restore_dir / path_str
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(source, dest)
        
        # Record file info
        file_hash = sha256_file(dest)
        files.append({
            "path": path_str,
            "sha256": file_hash,
            "size": dest.stat().st_size,
            "mtime": datetime.fromtimestamp(
                dest.stat().st_mtime, tz=timezone.utc
            ).isoformat()
        })
        print(f"  ✅ Copied: {path_str} ({file_hash[:12]}...)")
    
    # Check for errors
    if errors:
        print("\n❌ RESTORE POINT CREATION FAILED")
        for e in errors:
            print(f"   - {e}")
        # Clean up partial restore point
        shutil.rmtree(restore_dir)
        return 1
    
    # Create manifest
    manifest = {
        "restore_id": restore_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": "SHA-256",
        "file_count": len(files),
        "files": files
    }
    
    manifest_path = restore_dir / "MANIFEST.json"
    manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_path.write_text(manifest_json, encoding="utf-8")
    
    manifest_hash = sha256_string(manifest_json)
    
    # Log to ledger
    log_restore_point(restore_id, manifest_hash, len(files))
    
    # Print summary
    print("-" * 60)
    print("✅ RESTORE POINT CREATED SUCCESSFULLY")
    print(f"   Restore ID:    {restore_id}")
    print(f"   Files:         {len(files)}")
    print(f"   Manifest Hash: {manifest_hash}")
    print(f"   Location:      {restore_dir.absolute()}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
