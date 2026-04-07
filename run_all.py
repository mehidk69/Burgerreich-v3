#!/usr/bin/env python3
"""
Burgerreich-watch v3 — Run all collectors + merge in one shot.
Designed for cron / systemd timer on self-hosted (Pi4, VPS, etc.)

Usage:
    python run_all.py          # run all collectors
    python run_all.py --quick  # skip slow scrapers (commanders, doomsday)
"""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
COLLECTORS_DIR = PROJECT_ROOT / "collectors"
PYTHON = sys.executable

COLLECTORS = [
    ("collect_centcom.py",    "CENTCOM"),
    ("collect_eucom.py",      "EUCOM"),
    ("collect_indopacom.py",  "INDOPACOM"),
    ("collect_africom.py",    "AFRICOM"),
    ("collect_stratcom.py",   "STRATCOM"),
    ("collect_osint.py",      "OSINT"),
    ("collect_fleet.py",      "Fleet"),
    ("collect_casualties.py", "Casualties"),
    ("collect_losses.py",     "Losses"),
    ("collect_posture.py",    "Posture"),
]

SLOW_COLLECTORS = [
    ("collect_commanders.py", "Commanders"),
    ("collect_doomsday.py",   "Doomsday"),
]

MERGER = ("merge_feeds.py", "Merge")


def run_collector(script: str, label: str) -> bool:
    """Run a collector script as a subprocess from the collectors/ directory."""
    script_path = COLLECTORS_DIR / script
    try:
        result = subprocess.run(
            [PYTHON, str(script_path)],
            cwd=str(COLLECTORS_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.stderr:
            # Print collector's log output (they log to stderr)
            for line in result.stderr.strip().splitlines():
                print(f"  {line}")
        if result.returncode != 0:
            print(f"  [{label}] FAILED (exit {result.returncode})")
            if result.stdout:
                print(f"  {result.stdout.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  [{label}] TIMEOUT (120s)")
        return False
    except Exception as e:
        print(f"  [{label}] FAILED: {e}")
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

    for script, label in all_collectors:
        print(f"[>] {label}...")
        ok = run_collector(script, label)
        results[label] = ok

    # Always run merger
    print(f"[>] {MERGER[1]}...")
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
