#!/usr/bin/env python3
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sh(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return out.decode("utf-8", "replace").strip()
    except Exception:
        return ""


def try_git_head() -> str:
    return sh(["git", "rev-parse", "HEAD"])


def try_git_dirty() -> str:
    return "dirty" if sh(["git", "status", "--porcelain"]) else "clean"


def relpath_from_cwd(path: str) -> str:
    try:
        rel = os.path.relpath(os.path.abspath(path), os.getcwd())
        return rel.replace("\\", "/")
    except Exception:
        return path.replace("\\", "/")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/seal_file.py <path-to-file>")
        return 2

    target = sys.argv[1]
    if not os.path.exists(target) or not os.path.isfile(target):
        print(f"ERROR: file not found: {target}")
        return 2

    digest = sha256_file(target)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    head = try_git_head()
    dirty = try_git_dirty()

    rel = relpath_from_cwd(target)
    size = os.path.getsize(target)

    sha_out = f"{target}.sha256.txt"
    lines = [
        f"{digest}  {rel}",
        f"bytes: {size}",
        f"timestamp_utc: {ts}",
        f"git_state: {dirty}",
    ]
    if head:
        lines.append(f"git_head: {head}")

    with open(sha_out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"SEALED: {sha_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
