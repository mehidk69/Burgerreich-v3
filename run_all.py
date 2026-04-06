#!/usr/bin/env python3
"""
Burgerreich-watch v3 — Run all collectors + merge in one shot.
Designed for cron / systemd timer on self-hosted (Pi4, VPS, etc.)

Usage:
    python run_all.py          # run all collectors
    python run_all.py --quick  # skip slow scrapers (commanders, doomsday)
"""

import importlib
import sys
import time
from datetime import datetime, timezone

COLLECTORS = [
    ("collectors.collect_centcom",    "collect",  "CENTCOM"),
    ("collectors.collect_eucom",      "collect",  "EUCOM"),
    ("collectors.collect_indopacom",  "collect",  "INDOPACOM"),
    ("collectors.collect_africom",    "collect",  "AFRICOM"),
    ("collectors.collect_stratcom",   "collect",  "STRATCOM"),
    ("collectors.collect_osint",      "collect",  "OSINT"),
    ("collectors.collect_fleet",      "collect",  "Fleet"),
    ("collectors.collect_casualties", "collect",  "Casualties"),
    ("collectors.collect_losses",     "collect",  "Losses"),
    ("collectors.collect_posture",    "collect",  "Posture"),
]

SLOW_COLLECTORS = [
    ("collectors.collect_commanders", "collect",  "Commanders"),
    ("collectors.collect_doomsday",   "collect",  "Doomsday"),
]

MERGER = ("collectors.merge_feeds", "merge", "Merge")


def run_collector(module_path: str, func_name: str, label: str) -> bool:
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        func()
        return True
    except Exception as e:
        print(f"  [{label}] FAILED: {e}", file=sys.stderr)
        return False


def main():
    quick = "--quick" in sys.argv
    start = time.time()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"\n{'='*60}")
    print(f"  BURGERREICH_watch v3 — Collector Run")
    print(f"  {ts}")
    print(f"  Mode: {'QUICK' if quick else 'FULL'}")
    print(f"{'='*60}\n")

    results = {}

    all_collectors = COLLECTORS if quick else COLLECTORS + SLOW_COLLECTORS

    for module_path, func_name, label in all_collectors:
        print(f"[>] {label}...")
        ok = run_collector(module_path, func_name, label)
        results[label] = ok

    # Always run merger
    print(f"[>] {MERGER[2]}...")
    run_collector(*MERGER)

    elapsed = time.time() - start
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    print(f"\n{'='*60}")
    print(f"  Done in {elapsed:.1f}s — {passed} OK, {failed} failed")
    if failed:
        for label, ok in results.items():
            if not ok:
                print(f"    FAILED: {label}")
    print(f"{'='*60}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
