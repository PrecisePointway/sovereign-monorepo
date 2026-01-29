import argparse
import json
import os
import time
from pathlib import Path


DEAD_IP = "192.0.2.0"  # TEST-NET-1 reserved (non-routable)


def main() -> int:
    ap = argparse.ArgumentParser(description="Simulate a PC2_* node failure by sabotaging its IP (safe-by-default)")
    ap.add_argument("--config", type=str, default="config/swarm_config.json", help="Path to swarm config")
    ap.add_argument("--node-prefix", type=str, default="PC2_", help="Node key prefix to target")
    ap.add_argument("--duration", type=int, default=70, help="Seconds to hold the sabotage")
    ap.add_argument("--apply", action="store_true", help="Actually modify the config (otherwise dry-run)")
    args = ap.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        return 2

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", {}) if isinstance(data.get("nodes", {}), dict) else {}
    target_key = None
    for k in nodes.keys():
        if str(k).startswith(str(args.node_prefix)):
            target_key = str(k)
            break

    if not target_key:
        print(f"No node found with prefix {args.node_prefix!r}. Available: {', '.join(map(str, nodes.keys()))}")
        return 2

    original_ip = str((nodes.get(target_key, {}) or {}).get("ip", ""))
    print(f"Target node: {target_key} (ip={original_ip!r})")
    print(f"Sabotage ip -> {DEAD_IP!r} for {int(args.duration)}s")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to actually modify the config.")
        return 0

    backup_path = config_path.with_suffix(config_path.suffix + f".bak.{time.strftime('%Y%m%d_%H%M%S')}")
    backup_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    try:
        nodes[target_key]["ip"] = DEAD_IP
        data["nodes"] = nodes
        with open(config_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        print("Sabotage applied. Waiting...")
        time.sleep(max(1, int(args.duration)))
    finally:
        os.replace(str(backup_path), str(config_path))
        print("Simulation ended. Config restored.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
