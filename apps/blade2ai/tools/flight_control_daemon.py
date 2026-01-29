#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from dataclasses import dataclass


WATCH_ROOTS = ["evidence"]
EXTENSIONS = {".md", ".mmd"}
IGNORE_SUFFIXES = {".sha256.txt"}
POLL_SECONDS = float(os.environ.get("FC_DAEMON_POLL_SECONDS", "2"))
QUIET_SECONDS = float(os.environ.get("FC_DAEMON_QUIET_SECONDS", "0.5"))


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def should_track(path: str) -> bool:
    norm = path.replace("\\", "/")
    if "/.git/" in norm:
        return False
    for suf in IGNORE_SUFFIXES:
        if norm.endswith(suf):
            return False
    _, ext = os.path.splitext(norm)
    return ext.lower() in EXTENSIONS


def iter_tracked_files() -> list[str]:
    out: list[str] = []
    for root in WATCH_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {".git"}]
            for name in filenames:
                p = os.path.join(dirpath, name)
                if os.path.isfile(p) and should_track(p):
                    out.append(p)
    return out


@dataclass(frozen=True)
class FileStamp:
    mtime_ns: int
    size: int


def snapshot() -> dict[str, FileStamp]:
    snap: dict[str, FileStamp] = {}
    for path in iter_tracked_files():
        try:
            st = os.stat(path)
            snap[path] = FileStamp(mtime_ns=getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9)), size=st.st_size)
        except OSError:
            continue
    return snap


def diff(prev: dict[str, FileStamp], cur: dict[str, FileStamp]) -> list[str]:
    changed: list[str] = []
    for p, st in cur.items():
        if p not in prev or prev[p] != st:
            changed.append(p)
    return sorted(changed)


def seal_paths(paths: list[str]) -> int:
    for p in paths:
        rc = run([sys.executable, "tools/seal_file.py", p])
        if rc != 0:
            return rc
    return 0


def engage_autopilot() -> int:
    return run([sys.executable, "tools/autopilot.py"])


def try_watchdog() -> int:
    try:
        from watchdog.events import FileSystemEventHandler  # type: ignore
        from watchdog.observers import Observer  # type: ignore
    except Exception:
        return 2

    class Handler(FileSystemEventHandler):
        def __init__(self) -> None:
            super().__init__()
            self.last_event = 0.0

        def _mark(self) -> None:
            self.last_event = time.time()

        def on_modified(self, event):
            self._mark()

        def on_created(self, event):
            self._mark()

        def on_moved(self, event):
            self._mark()

        def on_deleted(self, event):
            self._mark()

    handler = Handler()
    observer = Observer()

    for root in WATCH_ROOTS:
        if os.path.isdir(root):
            observer.schedule(handler, root, recursive=True)

    observer.start()
    print("DAEMON: watchdog mode")

    try:
        while True:
            time.sleep(POLL_SECONDS)
            if handler.last_event == 0.0:
                continue
            if (time.time() - handler.last_event) < QUIET_SECONDS:
                continue
            handler.last_event = 0.0
            # In watchdog mode we don't have a specific path list; seal all tracked files.
            snap = snapshot()
            rc = seal_paths(sorted(snap.keys()))
            if rc != 0:
                return rc
            rc = engage_autopilot()
            if rc != 0:
                return rc
    finally:
        observer.stop()
        observer.join()


def main() -> int:
    # Prefer watchdog if available; fall back to polling.
    rc = try_watchdog()
    if rc != 2:
        return rc

    print("DAEMON: polling mode (watchdog not installed)")
    prev = snapshot()
    while True:
        time.sleep(POLL_SECONDS)
        cur = snapshot()
        changed = diff(prev, cur)
        if changed:
            rc = seal_paths(changed)
            if rc != 0:
                return rc
            rc = engage_autopilot()
            if rc != 0:
                return rc
            prev = snapshot()
        else:
            prev = cur


if __name__ == "__main__":
    raise SystemExit(main())
