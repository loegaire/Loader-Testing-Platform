#!/usr/bin/env python3
"""
experiments/run_tests.py — Automated test-matrix runner for the paper.

Drives the core_engine (build + VM cycle) over a defined experiment plan:

  Phase A — sanity check  : 1 config x 3 reps to confirm determinism.
  Phase B — main factorial: 18 configs, L2/L4 = (local RWX, memcpy),
                            L3 x L5 x API.
  Phase C — W^X factorial : 18 configs, L2/L4 = (local_rw, local_rx),
                            L3 x L5 x API.
  Phase D — antidebug spot: 2 configs, L0 = antidebug baseline vs stealth.

Per-run output:
  - CSV row appended to test_logs/experiment_matrix_<timestamp>.csv
  - Full raw log saved to   test_logs/run_<id>_<rep>_<timestamp>.log

Usage:
  python experiments/run_tests.py -s shellcodes/payload.bin
  python experiments/run_tests.py -s ... --phases A       # sanity only
  python experiments/run_tests.py -s ... --phases B,C     # skip sanity+antidebug
  python experiments/run_tests.py -s ... --dry-run        # print plan only
  python experiments/run_tests.py -s ... --resume CSV     # skip done rows
"""

import argparse
import csv
import hashlib
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, REPO_ROOT)

from controller import core_engine
from controller.config import VMS_CONFIG, PROJECT_ROOT, LOGS_DIR


# ---------------------------------------------------------------------------
# Test plan
# ---------------------------------------------------------------------------

def _baseline(**overrides):
    cfg = {
        "t0": "none", "t1": "rdata",
        "t2": "local", "t4": "local",
        "t3": "none", "t5": "local",
        "api_method": "winapi", "debug": False,
    }
    cfg.update(overrides)
    return cfg


def phase_a():
    return [("A1", _baseline(), 3)]


def _factorial(prefix, t2, t4):
    configs = []
    idx = 1
    for t3 in ["none", "xor", "aes"]:
        for t5 in ["local", "monitors", "fiber"]:
            for api in ["winapi", "syscalls"]:
                configs.append((
                    f"{prefix}{idx}",
                    _baseline(t2=t2, t4=t4, t3=t3, t5=t5, api_method=api),
                    1,
                ))
                idx += 1
    return configs


def phase_b():
    return _factorial("B", "local", "local")


def phase_c():
    return _factorial("C", "local_rw", "local_rx")


def phase_d():
    return [
        ("D1", _baseline(t0="antidebug"), 1),
        ("D2", _baseline(t0="antidebug", t3="aes", api_method="syscalls"), 1),
    ]


PHASES = {"A": phase_a, "B": phase_b, "C": phase_c, "D": phase_d}


# ---------------------------------------------------------------------------
# Outcome classification
# ---------------------------------------------------------------------------

def classify(raw_status):
    """Map core_engine status to paper outcome code.

    S       : callback received
    TB      : deleted during file transfer
    BLOCKED : copied but execution blocked; SD vs RD requires manual log review
    ERROR   : infrastructure failure
    UNKNOWN : unparseable
    """
    s = (raw_status or "").upper()
    if "SUCCESS" in s:
        return "S"
    if "TRANSFER BLOCKED" in s:
        return "TB"
    if "EXECUTION BLOCKED" in s:
        return "BLOCKED"
    if "BUILD_FAILED" in s or "EXCEPTION" in s or "ERROR" in s or "FAILED" in s:
        return "ERROR"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def short_name(cfg):
    return (
        f"t0={cfg['t0']} t2={cfg['t2']} t3={cfg['t3']} "
        f"t4={cfg['t4']} t5={cfg['t5']} api={cfg['api_method']}"
    )


def sha256_short(path, n=16):
    if not path or not os.path.isfile(path):
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def build_plan(phase_keys):
    runs = []
    for key in phase_keys:
        if key not in PHASES:
            print(f"[!] Unknown phase: {key}. Valid: {list(PHASES.keys())}")
            continue
        runs.extend(PHASES[key]())
    return runs


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "id", "rep", "started_at",
    "t0", "t1", "t2", "t3", "t4", "t5", "api",
    "payload_sha256", "raw_status", "code", "wall_time_s", "log_file",
]


def load_done_keys(csv_path):
    done = set()
    if not csv_path or not os.path.isfile(csv_path):
        return done
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add((row["id"], str(row["rep"])))
    return done


def run_all(shellcode_path, vm_name, phase_keys, resume_csv=None):
    os.makedirs(LOGS_DIR, exist_ok=True)
    done = load_done_keys(resume_csv)

    if resume_csv and os.path.isfile(resume_csv):
        out_csv = resume_csv
        mode = "a"
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_csv = os.path.join(LOGS_DIR, f"experiment_matrix_{stamp}.csv")
        mode = "w"

    runs = build_plan(phase_keys)
    total = sum(reps for _, _, reps in runs)
    print(f"[plan] {total} runs across phases {','.join(phase_keys)}")
    print(f"[csv]  {out_csv}")
    print(f"[vm]   {vm_name}")
    print(f"[shellcode] {shellcode_path}  sha256={sha256_short(shellcode_path)}")

    f_csv = open(out_csv, mode, newline="", encoding="utf-8")
    writer = csv.DictWriter(f_csv, fieldnames=FIELDNAMES)
    if mode == "w":
        writer.writeheader()
        f_csv.flush()

    idx = 0
    try:
        for cfg_id, cfg, reps in runs:
            for rep in range(1, reps + 1):
                idx += 1
                key = (cfg_id, str(rep))
                if key in done:
                    print(f"[{idx}/{total}] SKIP {cfg_id}/{rep} (in resume CSV)")
                    continue

                started = datetime.now().strftime("%Y%m%d_%H%M%S")
                print(f"\n[{idx}/{total}] {cfg_id}/{rep}  {short_name(cfg)}")
                t0 = time.time()

                raw_status = "UNKNOWN"
                log_body = ""
                payload_path = None
                try:
                    payload_path = core_engine.build_payload(shellcode_path, cfg)
                    if not payload_path:
                        raw_status = "BUILD_FAILED"
                        log_body = "core_engine.build_payload returned None"
                    else:
                        result = core_engine.run_single_test(vm_name, payload_path, cfg)
                        raw_status = result.get("status", "UNKNOWN")
                        log_body = result.get("log", "") or ""
                except Exception as exc:
                    raw_status = f"EXCEPTION: {exc}"
                    log_body = f"Python exception: {exc}"

                wall = round(time.time() - t0, 1)
                code = classify(raw_status)

                # Persist per-run log
                log_name = f"run_{cfg_id}_{rep}_{started}.log"
                log_path = os.path.join(LOGS_DIR, log_name)
                with open(log_path, "w", encoding="utf-8", errors="replace") as lf:
                    lf.write(f"id={cfg_id} rep={rep}\n")
                    lf.write(f"config={cfg}\n")
                    lf.write(f"raw_status={raw_status}\n")
                    lf.write(f"code={code}\n")
                    lf.write(f"wall_time_s={wall}\n")
                    lf.write(f"payload={payload_path}\n")
                    lf.write("---\n")
                    lf.write(log_body)

                writer.writerow({
                    "id": cfg_id,
                    "rep": rep,
                    "started_at": started,
                    "t0": cfg["t0"], "t1": cfg["t1"], "t2": cfg["t2"],
                    "t3": cfg["t3"], "t4": cfg["t4"], "t5": cfg["t5"],
                    "api": cfg["api_method"],
                    "payload_sha256": sha256_short(payload_path),
                    "raw_status": raw_status,
                    "code": code,
                    "wall_time_s": wall,
                    "log_file": log_name,
                })
                f_csv.flush()
                print(f"       -> code={code}  ({wall}s)  raw={raw_status}")
    finally:
        f_csv.close()

    print(f"\n[done] matrix: {out_csv}")
    return out_csv


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("-s", "--shellcode", required=True,
                        help="Path to shellcode .bin (relative to repo or absolute)")
    parser.add_argument("-v", "--vm", default="Windows Defender",
                        help="VM name from controller/config.py (default: 'Windows Defender')")
    parser.add_argument("--phases", default="A,B,C,D",
                        help="Comma-separated phase keys (A/B/C/D). Default: all.")
    parser.add_argument("--resume", metavar="CSV",
                        help="Existing CSV to resume; rows already in CSV are skipped.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the test plan and exit without running.")
    args = parser.parse_args()

    phase_keys = [p.strip().upper() for p in args.phases.split(",") if p.strip()]
    for k in phase_keys:
        if k not in PHASES:
            print(f"[!] Unknown phase '{k}'. Valid: {list(PHASES.keys())}")
            sys.exit(1)

    if args.dry_run:
        runs = build_plan(phase_keys)
        total = 0
        for cfg_id, cfg, reps in runs:
            for rep in range(1, reps + 1):
                total += 1
                print(f"{cfg_id:<4} rep={rep}  {short_name(cfg)}")
        print(f"\nTotal: {total} runs")
        return

    if args.vm not in VMS_CONFIG:
        print(f"[!] VM '{args.vm}' not in controller/config.py")
        print(f"    Available: {list(VMS_CONFIG.keys())}")
        sys.exit(1)

    shellcode = args.shellcode
    if not os.path.isabs(shellcode):
        shellcode = os.path.join(PROJECT_ROOT, shellcode)
    if not os.path.isfile(shellcode):
        print(f"[!] Shellcode not found: {shellcode}")
        sys.exit(1)

    run_all(shellcode, args.vm, phase_keys, resume_csv=args.resume)


if __name__ == "__main__":
    main()
