#!/usr/bin/env python3
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request


# ============================================================
#  CORE_GENESIS_Verifier — Constitutional Hygiene Ritual
#  Sealed Implementation v1.1 (deterministic, Windows-safe)
# ============================================================

# -----------------------------
# Configuration
# -----------------------------
CAPSULE_DIR = r"C:\Governance\CoreGenesis\Capsule"
LEDGER_DIR = r"C:\Governance\CoreGenesis"

PINNED_HASH_FILE = os.path.join(LEDGER_DIR, "pinned_capsule_hash.txt")
PINNED_SIGNATURE_FILE = os.path.join(LEDGER_DIR, "pinned_capsule_signature.asc")
PUBLIC_KEY_FILE = os.path.join(LEDGER_DIR, "public_key.asc")

# Local deterministic GPG home (no pollution of user's keyring)
GPG_HOME = os.path.join(LEDGER_DIR, "gnupg_home")

# Notification hooks (optional)
WEBHOOK_URL = os.environ.get("DRIFT_WEBHOOK_URL")
EMAIL_TO = os.environ.get("DRIFT_EMAIL_TO")
SMTP_HOST = os.environ.get("DRIFT_SMTP_HOST", "localhost")


# -----------------------------
# Utility: deterministic hashing of directory tree (chunked)
# -----------------------------
def hash_directory(path: str) -> str:
    sha = hashlib.sha256()
    base = os.path.abspath(path)

    for root, dirs, files in os.walk(base):
        dirs.sort()
        files.sort()
        for fn in files:
            full = os.path.join(root, fn)
            if not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, base).replace("\\", "/")
            sha.update(rel.encode("utf-8"))
            sha.update(b"\n")
            with open(full, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    sha.update(chunk)
            sha.update(b"\n")
    return sha.hexdigest()


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def gpg_cmd() -> list[str]:
    return ["gpg", "--homedir", GPG_HOME, "--batch", "--yes"]


def have_gpg() -> bool:
    try:
        r = subprocess.run(["gpg", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode == 0
    except Exception:
        return False


# -----------------------------
# Utility: verify GPG signature (detached signature of PINNED_HASH_FILE)
# -----------------------------
def verify_signature() -> tuple[bool, str]:
    if not have_gpg():
        return False, "Missing gpg executable"

    if not os.path.exists(PUBLIC_KEY_FILE):
        return False, "Missing public key"

    if not os.path.exists(PINNED_SIGNATURE_FILE):
        return False, "Missing pinned signature"

    if not os.path.exists(PINNED_HASH_FILE):
        return False, "Missing pinned hash file"

    ensure_dir(GPG_HOME)

    # Import key into local deterministic home
    subprocess.run(
        gpg_cmd() + ["--import", PUBLIC_KEY_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Verify detached signature against the pinned hash file
    result = subprocess.run(
        gpg_cmd() + ["--verify", PINNED_SIGNATURE_FILE, PINNED_HASH_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ok = result.returncode == 0
    msg = result.stderr.decode("utf-8", "replace")
    return ok, msg


# -----------------------------
# Ledger rotation + chain reading (cross-month)
# -----------------------------
def ledger_path_for(dt: datetime.datetime) -> str:
    return os.path.join(LEDGER_DIR, f"truth_ledger_{dt.year:04d}-{dt.month:02d}.jsonl")


def list_ledgers() -> list[str]:
    p = pathlib.Path(LEDGER_DIR)
    return sorted(str(x) for x in p.glob("truth_ledger_????-??.jsonl"))


def read_last_entry_any_ledger() -> dict | None:
    ledgers = list_ledgers()
    if not ledgers:
        return None
    for lp in reversed(ledgers):
        try:
            last = None
            with open(lp, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    last = json.loads(line)
            if last:
                return last
        except Exception:
            continue
    return None


def verify_entry_hash(entry: dict) -> bool:
    # entry_hash is sha256 of canonical JSON of entry without entry_hash.
    if not isinstance(entry, dict):
        return False
    entry_hash = entry.get("entry_hash")
    if not isinstance(entry_hash, str) or not entry_hash:
        return False

    copy = dict(entry)
    copy.pop("entry_hash", None)
    entry_str = json.dumps(copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    computed = hashlib.sha256(entry_str).hexdigest()
    return computed == entry_hash


# -----------------------------
# Notification hook (stdlib-only)
# -----------------------------
def notify_drift(message: str) -> None:
    if WEBHOOK_URL:
        try:
            data = json.dumps({"text": message}).encode("utf-8")
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5).read()
        except Exception:
            pass

    if EMAIL_TO:
        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(message)
            msg["Subject"] = "CORE_GENESIS Drift Detected"
            msg["To"] = EMAIL_TO
            msg["From"] = "core-genesis@localhost"
            s = smtplib.SMTP(SMTP_HOST)
            s.send_message(msg)
            s.quit()
        except Exception:
            pass


# -----------------------------
# Windows-safe append with basic lock
# -----------------------------
def append_line_locked(path: str, line: str) -> None:
    ensure_dir(os.path.dirname(path))
    try:
        import msvcrt

        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            fh.write(line + "\n")
            fh.flush()
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    except Exception:
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")


def main() -> int:
    now = datetime.datetime.utcnow().replace(microsecond=0)
    timestamp = now.isoformat() + "Z"
    drift_reasons: list[str] = []

    # Capsule existence
    if not os.path.exists(CAPSULE_DIR):
        drift_reasons.append("Capsule directory missing")
        capsule_hash = None
    else:
        capsule_hash = hash_directory(CAPSULE_DIR)

    # Load pinned hash
    pinned_hash = None
    if not os.path.exists(PINNED_HASH_FILE):
        drift_reasons.append("Pinned capsule hash missing")
    else:
        pinned_hash = open(PINNED_HASH_FILE, "r", encoding="utf-8").read().strip()
        if pinned_hash and not (len(pinned_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in pinned_hash)):
            drift_reasons.append("Pinned hash is not a valid sha256 hex")

    # Compare hashes
    if pinned_hash and capsule_hash and capsule_hash != pinned_hash:
        drift_reasons.append("Capsule hash mismatch")

    # Signature validation
    sig_ok, sig_msg = verify_signature()
    if not sig_ok:
        drift_reasons.append("Signature validation failed")

    # Ledger chain read
    last = read_last_entry_any_ledger()
    prev_hash = last.get("entry_hash") if isinstance(last, dict) else None

    if isinstance(last, dict) and last:
        if not verify_entry_hash(last):
            drift_reasons.append("Previous ledger entry hash invalid")

        last_ts = last.get("timestamp")
        if isinstance(last_ts, str) and last_ts >= timestamp:
            drift_reasons.append("Timestamp not monotonic")

    # Construct entry
    entry = {
        "timestamp": timestamp,
        "capsule_hash": capsule_hash,
        "pinned_capsule_hash": pinned_hash,
        "signature_ok": sig_ok,
        "signature_msg": sig_msg[:5000],
        "drift_reasons": drift_reasons,
        "prev_entry_hash": prev_hash,
    }

    # Compute entry hash
    entry_str = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
    entry_hash = hashlib.sha256(entry_str).hexdigest()
    entry["entry_hash"] = entry_hash

    ledger_path = ledger_path_for(now)
    append_line_locked(ledger_path, json.dumps(entry, separators=(",", ":"), ensure_ascii=False))

    status = "OK" if not drift_reasons else "DRIFT"
    print(json.dumps({"status": status, "timestamp": timestamp}, separators=(",", ":")))

    if drift_reasons:
        notify_drift(f"CORE_GENESIS drift detected: {drift_reasons}")
        return 1

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"status": "ERROR", "error": str(e)}, separators=(",", ":")))
        raise SystemExit(2)
