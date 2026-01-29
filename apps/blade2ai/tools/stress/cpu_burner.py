import time
import multiprocessing
import os
import sys
import argparse

def burn(duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = 1234 * 5678  # Math operations

def main():
    ap = argparse.ArgumentParser(description="Burn CPU on all cores for a short duration")
    ap.add_argument("duration", nargs="?", type=int, default=15, help="Duration in seconds")
    args = ap.parse_args()

    duration = int(args.duration)
    if duration < 1:
        duration = 1

    print(f"IGNITING CPU STRESS for {duration}s on {multiprocessing.cpu_count()} cores...")

    processes = []
    for _ in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=burn, args=(duration,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("CPU BURN COMPLETE.")

if __name__ == "__main__":
    main()
