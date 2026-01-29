#!/usr/bin/env python3
"""
Module Registry Validator
=========================
Validates module registry files against schema and business rules.
"""

import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "module.schema.json"
VALID_STATUS = ["Draft", "Active", "Parked", "Deprecated"]
VALID_APPLIES_TO = ["Cooperative", "Community", "Municipal", "Personal", "Enterprise", "All"]


def load_json(path: Path) -> dict | list:
    """Load and parse JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def validate_module(module: dict, index: int) -> list[str]:
    """Validate a single module entry. Returns list of errors."""
    errors = []
    
    # Required fields
    required = ["name", "purpose", "applies_to", "status", "last_used"]
    for field in required:
        if field not in module:
            errors.append(f"[{index}] Missing required field: {field}")
    
    # Name validation
    if "name" in module:
        name = module["name"]
        if not isinstance(name, str) or len(name) < 1 or len(name) > 64:
            errors.append(f"[{index}] 'name' must be string 1-64 chars")
    
    # Purpose validation
    if "purpose" in module:
        purpose = module["purpose"]
        if not isinstance(purpose, str) or len(purpose) < 1 or len(purpose) > 128:
            errors.append(f"[{index}] 'purpose' must be string 1-128 chars")
    
    # Status validation
    if "status" in module:
        if module["status"] not in VALID_STATUS:
            errors.append(f"[{index}] Invalid status: {module['status']}")
    
    # Applies_to validation
    if "applies_to" in module:
        applies = module["applies_to"]
        if not isinstance(applies, list) or len(applies) < 1:
            errors.append(f"[{index}] 'applies_to' must be non-empty array")
        else:
            for item in applies:
                if item not in VALID_APPLIES_TO:
                    errors.append(f"[{index}] Invalid applies_to value: {item}")
    
    # Last_used validation (null or ISO date)
    if "last_used" in module:
        last_used = module["last_used"]
        if last_used is not None:
            try:
                datetime.fromisoformat(last_used)
            except ValueError:
                errors.append(f"[{index}] 'last_used' must be ISO date or null")
    
    # No extra fields
    allowed = set(required)
    extra = set(module.keys()) - allowed
    if extra:
        errors.append(f"[{index}] Extra fields not allowed: {extra}")
    
    return errors


def validate_registry(modules: list, env: str = "dev") -> list[str]:
    """Validate entire registry. Returns list of errors."""
    errors = []
    
    if not isinstance(modules, list):
        return ["Registry must be a JSON array"]
    
    # Validate each module
    for i, module in enumerate(modules):
        errors.extend(validate_module(module, i))
    
    # Check unique names
    names = [m.get("name") for m in modules if "name" in m]
    if len(names) != len(set(names)):
        errors.append("Duplicate module names detected")
    
    # Prod-specific: no Draft status
    if env == "prod":
        for i, module in enumerate(modules):
            if module.get("status") == "Draft":
                errors.append(f"[{i}] Draft status not allowed in prod")
    
    return errors


def compute_hash(path: Path) -> str:
    """Compute SHA256 hash of file."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    if len(sys.argv) < 2:
        print("Usage: validate.py <path> [env]")
        print("  env: 'dev' (default) or 'prod'")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    env = sys.argv[2] if len(sys.argv) > 2 else "dev"
    
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    
    try:
        modules = load_json(path)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)
    
    errors = validate_registry(modules, env)
    
    if errors:
        print(f"VALIDATION FAILED ({len(errors)} errors):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        file_hash = compute_hash(path)
        print(f"VALIDATION PASSED")
        print(f"  Modules: {len(modules)}")
        print(f"  Environment: {env}")
        print(f"  SHA256: {file_hash[:16]}...")
        sys.exit(0)


if __name__ == "__main__":
    main()
