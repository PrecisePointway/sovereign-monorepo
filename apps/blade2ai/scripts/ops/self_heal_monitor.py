#!/usr/bin/env python3
"""Compat entrypoint: scripts/ops/self_heal_monitor.py

This repo's canonical implementation lives in tools/self_heal_monitor.py.
This wrapper exists to match the Phase 2 file layout without duplicating logic.
"""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    script = os.path.join(repo_root, "tools", "self_heal_monitor.py")

    # Pass through args (plus default config if not provided)
    args = [sys.executable, script]
    if "--config" not in sys.argv:
        args += ["--config", os.path.join(repo_root, "config", "swarm_config.json")]
    args += sys.argv[1:]

    return subprocess.call(args)


if __name__ == "__main__":
    raise SystemExit(main())
