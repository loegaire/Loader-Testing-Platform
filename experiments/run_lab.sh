#!/usr/bin/env bash
set -euo pipefail

# Loader Testing Platform helper wrapper
# - full matrix runs (A-F)
# - phase subset runs
# - single technique chain runs via cli.py
# - summarize existing CSV

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_VM="Windows Defender"
DEFAULT_SHELLCODE="shellcodes/defaul_192-168-122-1_4444.bin"

log() { printf "[run_lab] %s\n" "$*"; }
warn() { printf "[run_lab][WARN] %s\n" "$*" >&2; }
err() { printf "[run_lab][ERROR] %s\n" "$*" >&2; }

die() {
  err "$*"
  exit 1
}

usage() {
  cat <<'USAGE'
Usage:
  experiments/run_lab.sh full [options]
  experiments/run_lab.sh phase --phases A,B [options]
  experiments/run_lab.sh single [single options]
  experiments/run_lab.sh summarize --csv PATH

Commands:
  full         Run full experiment matrix (A,B,C,D,E,F) with run_tests.py
  phase        Run only selected phases with run_tests.py
  single       Run one specific technique chain via cli.py
  summarize    Summarize an existing matrix CSV via run_tests.py --summarize

Common options (full/phase):
  -s, --shellcode PATH     Shellcode path (default: shellcodes/defaul_192-168-122-1_4444.bin)
  --vm NAME                VM name key from controller/config.py (default: Windows Defender)
  --clean                  Delete stale matrix/log files before run
  --resume CSV             Resume an existing matrix CSV
  --dry-run                Print planned matrix only, do not execute
  -v, --verbose            Pass -v to run_tests.py (repeat: -vv for debug logs)
  --no-preflight           Skip virsh/ssh preflight checks

Phase options:
  --phases A,B,C           Required for phase command

Single options (via cli.py):
  -s, --shellcode PATH     Shellcode path
  --vm NAME                VM name key (omit + use --build-only to compile only)
  --build-only             Build payload only, no VM interaction
  --debug                  Enable payload debug mode
  --api winapi|syscalls    API path (default: winapi)
  -t0 none|antidebug|sleep_skew
  -t1 rdata|data
  -t2 local|local_rw|remote|spawn
  -t3 none|xor|aes|rc4|chacha20|bitwise
  -t4 local|local_rx|remote
  -t5 local|monitors|fiber|remote_thread

Examples:
  experiments/run_lab.sh full --clean
  experiments/run_lab.sh phase --phases B,C --clean
  experiments/run_lab.sh phase --phases A --dry-run
  experiments/run_lab.sh single -t0 antidebug -t1 rdata -t2 local_rw -t3 aes -t4 local_rx -t5 fiber --api syscalls --vm "Windows Defender"
  experiments/run_lab.sh summarize --csv test_logs/experiment_matrix_20260420_161211.csv
USAGE
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

abs_path() {
  local p="$1"
  if [[ "$p" = /* ]]; then
    printf "%s\n" "$p"
  else
    printf "%s/%s\n" "$REPO_ROOT" "$p"
  fi
}

setup_uv_env() {
  require_cmd uv
  cd "$REPO_ROOT"
  if [[ ! -d .venv ]]; then
    log "Creating .venv with uv"
    uv venv .venv
  fi
  log "Installing Python dependencies with uv"
  uv pip install -r requirements.txt >/dev/null
}

resolve_vm_fields() {
  local vm_name="$1"
  local out
  out="$(uv run python - "$vm_name" <<'PY'
import sys
from controller.config import VMS_CONFIG
vm = sys.argv[1]
cfg = VMS_CONFIG.get(vm)
if not cfg:
    print("MISSING")
    sys.exit(0)
print(cfg.get("domain", ""))
print(cfg.get("guest_ip", ""))
PY
)"
  if [[ "$out" == "MISSING" ]]; then
    die "VM key '$vm_name' not found in controller/config.py"
  fi

  VM_DOMAIN="$(printf "%s\n" "$out" | sed -n '1p')"
  VM_IP="$(printf "%s\n" "$out" | sed -n '2p')"

  [[ -n "$VM_DOMAIN" ]] || die "VM '$vm_name' has empty domain in config"
  [[ -n "$VM_IP" ]] || die "VM '$vm_name' has empty guest_ip in config"
}

preflight_vm() {
  local vm_name="$1"

  require_cmd virsh
  require_cmd sshpass
  resolve_vm_fields "$vm_name"

  log "Preflight VM='$vm_name' domain='$VM_DOMAIN' ip='$VM_IP'"

  if ! virsh -c qemu:///system list --all | awk '{print $2}' | grep -Fxq "$VM_DOMAIN"; then
    die "Libvirt domain '$VM_DOMAIN' not found. Check controller/config.py vs 'virsh list --all'."
  fi

  if ! ip route | grep -q '192.168.122.0/24'; then
    warn "No route for 192.168.122.0/24 found. Guest network may be unreachable."
  fi

  if ! ping -c 1 -W 1 "$VM_IP" >/dev/null 2>&1; then
    warn "Guest IP $VM_IP did not respond to ping yet (may still boot after snapshot)."
  fi

  # SSH probe is informative only; run_tests has its own wait loop.
  if ! sshpass -p "$(uv run python - <<'PY'
from controller.config import GUEST_PASSWORD
print(GUEST_PASSWORD)
PY
)" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$(uv run python - <<'PY'
from controller.config import GUEST_USER
print(GUEST_USER)
PY
)@${VM_IP}" "echo ok" >/dev/null 2>&1; then
    warn "SSH probe failed. This can be transient during guest boot."
  fi
}

clean_logs() {
  cd "$REPO_ROOT"
  mkdir -p test_logs
  rm -f test_logs/run_*.log test_logs/experiment_matrix_*.csv
  log "Deleted stale run logs and matrix CSV files under test_logs"
}

validate_shellcode() {
  local shellcode="$1"
  [[ -f "$shellcode" ]] || die "Shellcode not found: $shellcode"
}

run_matrix() {
  local shellcode="$1"
  local vm_name="$2"
  local phases="$3"
  local resume_csv="$4"
  local dry_run="$5"
  local verbose_count="$6"

  local args=(experiments/run_tests.py -s "$shellcode" --vm "$vm_name" --phases "$phases")

  if [[ -n "$resume_csv" ]]; then
    args+=(--resume "$resume_csv")
  fi

  if [[ "$dry_run" == "1" ]]; then
    args+=(--dry-run)
  fi

  if [[ "$verbose_count" -ge 1 ]]; then
    args+=(-v)
  fi
  if [[ "$verbose_count" -ge 2 ]]; then
    args+=(-v)
  fi

  cd "$REPO_ROOT"
  log "Running matrix: phases=$phases vm=$vm_name shellcode=$shellcode"
  uv run "${args[@]}"
}

run_single() {
  local shellcode="$1"
  local vm_name="$2"
  local build_only="$3"
  local debug_mode="$4"
  local api="$5"
  local t0="$6"
  local t1="$7"
  local t2="$8"
  local t3="$9"
  local t4="${10}"
  local t5="${11}"

  validate_shellcode "$shellcode"

  cd "$REPO_ROOT"
  local args=(cli.py -s "$shellcode" -t0 "$t0" -t1 "$t1" -t2 "$t2" -t3 "$t3" -t4 "$t4" -t5 "$t5" --api "$api")

  if [[ "$build_only" == "1" ]]; then
    args+=(--build-only)
  else
    [[ -n "$vm_name" ]] || die "single mode without --build-only requires --vm NAME"
    args+=(-v "$vm_name")
  fi

  if [[ "$debug_mode" == "1" ]]; then
    args+=(--debug)
  fi

  log "Running single chain: t0=$t0 t1=$t1 t2=$t2 t3=$t3 t4=$t4 t5=$t5 api=$api"
  uv run "${args[@]}"
}

run_summarize() {
  local csv_path="$1"
  [[ -f "$csv_path" ]] || die "CSV not found: $csv_path"
  cd "$REPO_ROOT"
  uv run experiments/run_tests.py --summarize "$csv_path"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

MODE="$1"
shift

SHELLCODE_REL="$DEFAULT_SHELLCODE"
VM_NAME="$DEFAULT_VM"
PHASES="A,B,C,D,E,F"
RESUME_CSV=""
DRY_RUN="0"
VERBOSE_COUNT=0
DO_CLEAN="0"
DO_PREFLIGHT="1"

# single defaults
S_BUILD_ONLY="0"
S_DEBUG="0"
S_API="winapi"
S_T0="none"
S_T1="rdata"
S_T2="local"
S_T3="none"
S_T4="local"
S_T5="local"
SUMMARIZE_CSV=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--shellcode)
      SHELLCODE_REL="$2"; shift 2;;
    --vm)
      VM_NAME="$2"; shift 2;;
    --phases)
      PHASES="$2"; shift 2;;
    --resume)
      RESUME_CSV="$2"; shift 2;;
    --dry-run)
      DRY_RUN="1"; shift;;
    -v|--verbose)
      VERBOSE_COUNT=$((VERBOSE_COUNT + 1)); shift;;
    --clean)
      DO_CLEAN="1"; shift;;
    --no-preflight)
      DO_PREFLIGHT="0"; shift;;
    --build-only)
      S_BUILD_ONLY="1"; shift;;
    --debug)
      S_DEBUG="1"; shift;;
    --api)
      S_API="$2"; shift 2;;
    -t0)
      S_T0="$2"; shift 2;;
    -t1)
      S_T1="$2"; shift 2;;
    -t2)
      S_T2="$2"; shift 2;;
    -t3)
      S_T3="$2"; shift 2;;
    -t4)
      S_T4="$2"; shift 2;;
    -t5)
      S_T5="$2"; shift 2;;
    --csv)
      SUMMARIZE_CSV="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      die "Unknown option: $1";;
  esac
done

SHELLCODE_ABS="$(abs_path "$SHELLCODE_REL")"
[[ -z "$RESUME_CSV" ]] || RESUME_CSV="$(abs_path "$RESUME_CSV")"
[[ -z "$SUMMARIZE_CSV" ]] || SUMMARIZE_CSV="$(abs_path "$SUMMARIZE_CSV")"

setup_uv_env

case "$MODE" in
  full)
    validate_shellcode "$SHELLCODE_ABS"
    if [[ "$DO_CLEAN" == "1" ]]; then
      clean_logs
    fi
    if [[ "$DO_PREFLIGHT" == "1" && "$DRY_RUN" == "0" ]]; then
      preflight_vm "$VM_NAME"
    fi
    run_matrix "$SHELLCODE_ABS" "$VM_NAME" "A,B,C,D,E,F" "$RESUME_CSV" "$DRY_RUN" "$VERBOSE_COUNT"
    ;;
  phase)
    validate_shellcode "$SHELLCODE_ABS"
    [[ -n "$PHASES" ]] || die "phase mode requires --phases"
    if [[ "$DO_CLEAN" == "1" ]]; then
      clean_logs
    fi
    if [[ "$DO_PREFLIGHT" == "1" && "$DRY_RUN" == "0" ]]; then
      preflight_vm "$VM_NAME"
    fi
    run_matrix "$SHELLCODE_ABS" "$VM_NAME" "$PHASES" "$RESUME_CSV" "$DRY_RUN" "$VERBOSE_COUNT"
    ;;
  single)
    if [[ "$S_BUILD_ONLY" == "0" && "$DO_PREFLIGHT" == "1" ]]; then
      preflight_vm "$VM_NAME"
    fi
    run_single "$SHELLCODE_ABS" "$VM_NAME" "$S_BUILD_ONLY" "$S_DEBUG" "$S_API" "$S_T0" "$S_T1" "$S_T2" "$S_T3" "$S_T4" "$S_T5"
    ;;
  summarize)
    [[ -n "$SUMMARIZE_CSV" ]] || die "summarize mode requires --csv PATH"
    run_summarize "$SUMMARIZE_CSV"
    ;;
  *)
    usage
    die "Unknown mode: $MODE"
    ;;
esac
