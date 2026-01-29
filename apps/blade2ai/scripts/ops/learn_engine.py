#!/usr/bin/env python3
"""Compat entrypoint: scripts/ops/learn_engine.py

This repo's canonical implementation lives in tools/learn_engine.py.
This wrapper exists to match the Phase 3 file layout without duplicating logic.
"""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    script = os.path.join(repo_root, "tools", "learn_engine.py")
    return subprocess.call([sys.executable, script] + sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
