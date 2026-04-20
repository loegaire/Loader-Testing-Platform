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
import collections
import csv
import hashlib
import logging
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, REPO_ROOT)

from controller import core_engine  # noqa: E402 — import after sys.path tweak
from controller.config import VMS_CONFIG, PROJECT_ROOT, LOGS_DIR  # noqa: E402


# ---------------------------------------------------------------------------
# Logging setup (overrides core_engine's basicConfig default of INFO)
# ---------------------------------------------------------------------------

def configure_logging(verbose_count):
    """
    verbose_count == 0 -> WARNING (quiet, default)
    verbose_count == 1 -> INFO    (-v)
    verbose_count >= 2 -> DEBUG   (-vv)
    """
    level = logging.WARNING
    if verbose_count == 1:
        level = logging.INFO
    elif verbose_count >= 2:
        level = logging.DEBUG

    root = logging.getLogger()
    root.setLevel(level)
    for h in root.handlers:
        h.setLevel(level)


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


def _remote_factorial(prefix, t2_value):
    """Helper: factorial for a remote-style L2 + remote write/execute chain."""
    configs = []
    idx = 1
    for t3 in ["none", "xor", "aes"]:
        for api in ["winapi", "syscalls"]:
            configs.append((
                f"{prefix}{idx}",
                _baseline(t2=t2_value, t4="remote", t5="remote_thread",
                          t3=t3, api_method=api),
                1,
            ))
            idx += 1
    return configs


def phase_e():
    """Remote injection into existing explorer.exe (T2.3 + T4.3 + T5.4).

    Generates Event 10 ProcessAccess (payload -> explorer) and Event 8
    CreateRemoteThread (cross-process). No Event 1 for explorer (already
    running). Distinct from local chains.
    """
    return _remote_factorial("E", "remote")


def phase_f():
    """Spawn-and-inject chain (T2.4 + T4.3 + T5.4).

    Spawns notepad.exe suspended, then runs the same remote write/execute
    path. Adds Event 1 ProcessCreate (parent=payload, child=notepad) on
    top of the Phase E signal, exercising a different part of the
    detection surface (suspended process creation).
    """
    return _remote_factorial("F", "spawn")


PHASES = {
    "A": phase_a, "B": phase_b, "C": phase_c,
    "D": phase_d, "E": phase_e, "F": phase_f,
}


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
    summarize_csv(out_csv)
    return out_csv


# ---------------------------------------------------------------------------
# Summary (used both at end of batch and via --summarize)
# ---------------------------------------------------------------------------

def summarize_csv(csv_path):
    if not os.path.isfile(csv_path):
        print(f"[!] CSV not found: {csv_path}")
        return

    by_phase = collections.defaultdict(collections.Counter)
    by_phase_time = collections.defaultdict(float)
    total_time = 0.0
    total_runs = 0
    reps_per_id = collections.defaultdict(list)

    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            phase = row["id"][0] if row["id"] else "?"
            code = row["code"]
            by_phase[phase][code] += 1
            try:
                t = float(row["wall_time_s"])
            except (ValueError, TypeError):
                t = 0.0
            by_phase_time[phase] += t
            total_time += t
            total_runs += 1
            reps_per_id[row["id"]].append(code)

    print("\n" + "=" * 60)
    print(" Experiment summary")
    print("=" * 60)

    phase_names = {
        "A": "Sanity", "B": "Main (RWX)", "C": "W^X",
        "D": "Antidebug", "E": "Remote (existing)", "F": "Spawn (suspended)",
    }
    for phase in sorted(by_phase):
        counts = by_phase[phase]
        total = sum(counts.values())
        t = by_phase_time[phase]
        pretty = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        name = phase_names.get(phase, phase)
        print(f"Phase {phase} ({name:<12}): {total:2d} runs | {pretty:<32s} | {t/60:5.1f} min")

    # Flag disagreements within a config id (only meaningful if rep>1)
    disagreements = [
        (cid, codes) for cid, codes in reps_per_id.items()
        if len(codes) > 1 and len(set(codes)) > 1
    ]
    if disagreements:
        print("\n[!] Non-deterministic outcomes within same config id:")
        for cid, codes in disagreements:
            print(f"    {cid}: {codes}")

    m = int(total_time // 60)
    s = int(total_time % 60)
    print(f"\nTotal runs: {total_runs}  |  Total wall time: {m}m {s}s")
    print(f"CSV: {csv_path}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("-s", "--shellcode",
                        help="Path to shellcode .bin (relative to repo or absolute). "
                             "Required unless --dry-run or --summarize is used.")
    parser.add_argument("--vm", default="Windows Defender",
                        help="VM name from controller/config.py (default: 'Windows Defender')")
    parser.add_argument("--phases", default="A,B,C,D,E,F",
                        help="Comma-separated phase keys (A/B/C/D/E/F). Default: all.")
    parser.add_argument("--resume", metavar="CSV",
                        help="Existing CSV to resume; rows already in CSV are skipped.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the test plan and exit without running.")
    parser.add_argument("--summarize", metavar="CSV",
                        help="Print summary of an existing experiment CSV and exit "
                             "(no new runs).")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase log verbosity: -v for INFO, -vv for DEBUG. "
                             "Default is WARNING only.")
    args = parser.parse_args()

    configure_logging(args.verbose)

    # --summarize: re-analyze existing CSV and exit
    if args.summarize:
        summarize_csv(args.summarize)
        return

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

    # From here on, we actually execute runs — require shellcode + valid VM.
    if not args.shellcode:
        parser.error("--shellcode is required unless --dry-run or --summarize is given.")
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
