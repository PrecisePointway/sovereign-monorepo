import argparse
import os
import time


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a small evidence write-load (safe-by-default)")
    ap.add_argument("--count", type=int, default=50, help="Number of files to write")
    ap.add_argument(
        "--out-root",
        type=str,
        default="evidence/stress_test",
        help="Root output dir (a timestamped subfolder will be created)",
    )
    ap.add_argument("--delay-ms", type=int, default=100, help="Delay between writes (ms)")
    args = ap.parse_args()

    run_id = time.strftime("%Y%m%d_%H%M%S")
    target_dir = os.path.join(args.out_root, run_id)
    os.makedirs(target_dir, exist_ok=False)

    print(f"INITIATING EVIDENCE FLOOD ({args.count} files) -> {target_dir}")
    start_time = time.time()

    for i in range(int(args.count)):
        fname = os.path.join(target_dir, f"TEST_EVIDENCE_{i:03d}.md")
        with open(fname, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# Stress Test File {i}\nTimestamp: {time.time()}\n")
        time.sleep(max(0.0, float(args.delay_ms) / 1000.0))

    print(f"FLOOD COMPLETE in {time.time() - start_time:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
