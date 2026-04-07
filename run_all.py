#!/usr/bin/env python3
"""
Burgerreich-watch v3 — Run all collectors + merge in one shot.
Designed for cron / systemd timer on self-hosted (Pi4, VPS, etc.)

Usage:
    python run_all.py          # run all collectors
    python run_all.py --quick  # skip slow scrapers (commanders, doomsday)
"""

import importlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add collectors/ to Python path so intra-package imports (utils, collector_base) work
_collectors_dir = str(Path(__file__).resolve().parent / "collectors")
if _collectors_dir not in sys.path:
    sys.path.insert(0, _collectors_dir)

COLLECTORS = [
    ("collect_centcom",    "collect",  "CENTCOM"),
    ("collect_eucom",      "collect",  "EUCOM"),
    ("collect_indopacom",  "collect",  "INDOPACOM"),
    ("collect_africom",    "collect",  "AFRICOM"),
    ("collect_stratcom",   "collect",  "STRATCOM"),
    ("collect_osint",      "collect",  "OSINT"),
    ("collect_fleet",      "collect",  "Fleet"),
    ("collect_casualties", "collect",  "Casualties"),
    ("collect_losses",     "collect",  "Losses"),
    ("collect_posture",    "collect",  "Posture"),
]

SLOW_COLLECTORS = [
    ("collect_commanders", "collect",  "Commanders"),
    ("collect_doomsday",   "collect",  "Doomsday"),
]

MERGER = ("merge_feeds", "merge", "Merge")


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
