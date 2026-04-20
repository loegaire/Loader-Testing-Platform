# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Educational shellcode loader testing platform. Automates: build → deploy to VM → execute → collect detection logs. **Not** an AV/EDR bypass tool — it's for studying how loaders work and mapping detection surfaces.

## Build & Run Commands

```bash
# Build only (no VM testing)
python cli.py -s shellcodes/payload.bin --build-only -t3 aes -t5 monitors

# Build and test on VMs (requires Linux host with KVM)
python cli.py -s shellcodes/payload.bin -t3 xor -t5 local -v "VM_NAME"

# Full flags
python cli.py -s PATH \
              -t0 none|antidebug \
              -t1 rdata \
              -t2 local|local_rw|remote|spawn \
              -t3 none|xor|aes \
              -t4 local|local_rx|remote \
              -t5 local|monitors|fiber|remote_thread \
              --api winapi|syscalls \
              -v VM1 VM2 --debug

# Manual make (rarely needed — builder.py calls this)
make build SRC=generated_loader.cpp OUT=payload.exe DEFINES="-DT3_TRANSFORM_AES"

# Clean build artifacts
make clean
```

Requirements:

- Python 3.8+, `tinyaes` via `pip install -r requirements.txt`
- MinGW-w64 (`x86_64-w64-mingw32-g++`), NASM, GNU Make
- **Linux host**: `qemu-kvm`, `libvirt`, `virsh`, `sshpass` — required for VM testing
- **Windows host**: MSYS2 with `mingw-w64-x86_64-gcc`, `mingw-w64-x86_64-nasm`, `make` — supports build only (no VM backend). See `docs/build_windows.md`.

## Architecture

### 6-Stage Loader Pipeline

Every loader is decomposed into 6 compile-time selectable stages:

```
L0: Anti-Analysis → L1: Storage → L2: Allocation → L3: Transformation → L4: Writing → L5: Execution
```

Each stage has a runner header `src/techniques/runner/T<N>_*.h` that `#ifdef`-selects one technique. `src/main.cpp` calls `Run_T0_AntiAnalysis` through `Run_T5_Execute` in order, aborting on any `FALSE` return. Stages communicate through a single `TechniqueContext` struct (`src/techniques/context.h`) passed as a pointer through all stages.

### Compile-Time Technique Selection

Techniques are **not** selected at runtime. The flow is:

1. CLI flag (e.g., `-t3 aes`) → Python maps to preprocessor define (`-DT3_TRANSFORM_AES`) via `controller/modules/definitions.py`
2. Runner files (`src/techniques/runner/T<N>_*.h`) use `#ifdef` to include and dispatch to the selected technique
3. Each technique is a self-contained header file with one `inline BOOL Stage<N>_*(TechniqueContext*)` function

### Build Pipeline

```
shellcode.bin
  → Python encrypts + generates build/src/payload_data.h (C array)
  → Copies src/main.cpp → build/src/generated_loader.cpp
  → make build with -D flags
  → build/bin/payload_TIMESTAMP.exe
```

Orchestrated by `controller/modules/builder.py`. The Makefile compiles C++ (MinGW), assembles NASM (`src/api/syscall.asm`), and links. `CC` and `AS` use `ifeq origin default` so env/command-line overrides work (e.g. `CC=g++` on MSYS2).

### API Abstraction

`src/api/api_wrappers.h` wraps NT API calls with two modes selected via `--api`:
- `winapi` (default) — standard Windows API
- `syscalls` — direct syscall via NASM stubs. Covers `NtAllocateVirtualMemory`, `NtProtectVirtualMemory`, `NtCreateThreadEx`, `NtWaitForSingleObject`, `NtWriteVirtualMemory`.

Wrapped functions: `MyVirtualAllocEx`, `MyVirtualProtect`, `MyCreateThreadEx`, `MyWaitForSingleObject`, `MyWriteProcessMemory`.

### Test Execution (VM)

`controller/core_engine.py` manages the full test cycle: revert VM snapshot → start → deploy payload → listen for C2 callback (`controller/modules/c2.py`) → execute → collect Defender/Sysmon logs → report result. VM config lives in `controller/config.py`. VM backend is KVM/libvirt via `virsh` — Linux host only.

**Payload launch goes through `vm.launch_interactive()`, not SSH `Start-Process`.** SSH-spawned processes live in the sshd service session (often Session 0). A remote-injection loader that calls `OpenProcess` on `explorer.exe` (user's interactive Session 1) fails cross-session even though the same code works when launched manually from the desktop. `launch_interactive()` registers a one-shot Task Scheduler task with `-LogonType Interactive -RunLevel Limited`, which runs the payload in the logged-in user's session at Medium integrity. This requires the guest to have an active interactive session of the test user at boot — set up by `log_collectors/setup_guest.ps1` (enables autologin).

**Privilege split**: loader runs at Medium integrity (standard-user token); no loader technique in this repo needs `SeDebugPrivilege` because all cross-process operations are same-user. Admin is required only for the harness itself (Sysmon config apply, event log reading).

### Guest Snapshot Setup

`log_collectors/setup_guest.ps1` is run inside the VM **once** before taking `clean_snapshot`. It:
1. Enables autologin for `tester` so an interactive session exists at boot (required for Task Scheduler interactive launch).
2. Ensures Sysmon service is autostart; applies baseline `sysmon_loader_config.xml`.
3. Disables Defender MAPS + sample submission (prevents cloud signature drift between runs — a config that succeeded at `t1` would otherwise be blocked at `t2` with no code change).
4. Writes `guest_fingerprint.txt` (Defender engine/signature versions, Windows build) to the desktop for paper reproducibility.

**To update `clean_snapshot` after changing guest state:** `virsh snapshot-create-as` does NOT overwrite an existing same-name snapshot; delete first. Sequence: shutdown guest → `virsh snapshot-delete <domain> clean_snapshot` → `virsh snapshot-create-as <domain> clean_snapshot`.

### Telemetry Collection

`log_collectors/collect_all.ps1` is copied to the guest and run at the end of each test cycle. It anchors its event window to the `ProcessCreate` event for `payload.exe` (with a 5-second lookback), falling back to a fixed minute-window if the payload never ran. This scopes the collected log to the current run's events without needing to wipe the Sysmon log between runs.

`log_collectors/sysmon_loader_config.xml` (schema 4.91) scopes Sysmon rules to loader-relevant activity. Key design rules:
- `ProcessAccess` includes only `SourceImage contains \Desktop\` — a broader `GrantedAccess` filter matches every service-to-service call and drowns the payload signal.
- `ProcessCreate` excludes shellcode-spawned `cmd.exe` and `conhost.exe` — those are payload behavior, not loader behavior (per the shellcode-vs-loader scope boundary in the paper).
- `FileCreate` narrows to `\Desktop\` and excludes the harness's own output files (`detection_log.*`, `sysmon.xml`, `collect_logs.ps1`).
- `NetworkConnect` includes Desktop-sourced connections plus `DestinationPort=4444` (C2 port) as a control marker for successful shellcode execution.
- `CreateRemoteThread` excludes boot-time system processes (`csrss`, `services`, `svchost`, `MsMpEng`, `vmtoolsd`, `winlogon`, `wininit`, `smss`, `dwm`, `lsass`).

### Batch Runs

`experiments/run_tests.py` runs the full phase matrix (A sanity, B main RWX, C W^X, D antidebug, E remote-existing, F spawn-suspended). Output goes to `experiments/runs/<batch_timestamp>/` containing `matrix.csv`, `run_<id>_<rep>.log` (harness trace), and `guest_<id>_<rep>.txt` (raw Defender+Sysmon telemetry). `core_engine.run_single_test()` accepts `log_dir` and `log_name` parameters for this redirection; `cli.py` single runs still write to `test_logs/`.

## Current Technique Inventory

| Stage | Option | Define | Notes |
|-------|--------|--------|-------|
| L0 | `none` | `T0_ANTIANALYSIS_NONE` | No-op |
| L0 | `antidebug` | `T0_ANTIANALYSIS_DEBUG` | PEB.BeingDebugged check |
| L1 | `rdata` | `T1_STORAGE_RDATA` | Payload in `.rdata` as C array |
| L2 | `local` | `T2_ALLOC_LOCAL` | VirtualAlloc `PAGE_EXECUTE_READWRITE` (RWX) |
| L2 | `local_rw` | `T2_ALLOC_LOCAL_RW` | VirtualAlloc `PAGE_READWRITE` (pair with L4 `local_rx`) |
| L2 | `remote` | `T2_ALLOC_REMOTE` | Find existing `explorer.exe` + `OpenProcess` + `VirtualAllocEx` |
| L2 | `spawn` | `T2_ALLOC_SPAWN` | `CreateProcess(notepad.exe, CREATE_SUSPENDED)` + `VirtualAllocEx` |
| L3 | `none` | `T3_TRANSFORM_NONE` | No decryption |
| L3 | `xor` | `T3_TRANSFORM_XOR` | XOR-key |
| L3 | `aes` | `T3_TRANSFORM_AES` | AES-128-CTR via `aes.c` |
| L4 | `local` | `T4_WRITE_LOCAL` | memcpy only (assumes RWX allocation) |
| L4 | `local_rx` | `T4_WRITE_LOCAL_RX` | memcpy + `VirtualProtect` to `PAGE_EXECUTE_READ` |
| L4 | `remote` | `T4_WRITE_REMOTE` | `WriteProcessMemory` into target process buffer |
| L5 | `local` | `T5_EXEC_LOCAL` | `CreateThread` on shellcode entry |
| L5 | `monitors` | `T5_EXEC_DISPLAY_MONITORS` | `EnumDisplayMonitors` callback trick |
| L5 | `fiber` | `T5_EXEC_FIBER` | `ConvertThreadToFiber` + `CreateFiber` + `SwitchToFiber` |
| L5 | `remote_thread` | `T5_EXEC_REMOTE_THREAD` | `CreateRemoteThreadEx` (or `NtCreateThreadEx` syscall) into target |

**Paired techniques**:
- `-t2 local_rw` only makes sense with `-t4 local_rx` (plain `local_rw + local` will crash because the buffer never gets the execute bit).
- `-t2 remote` and `-t2 spawn` both require `-t4 remote` and `-t5 remote_thread` (the cross-process chains share `target_process` through the context). The two L2 variants differ only in how `target_process` is obtained: `remote` opens an existing `explorer.exe`, `spawn` creates a fresh `notepad.exe` suspended. Mixing either remote-style L2 with local L4/L5 leaves `target_process` set but unused, and the local L4/L5 write to a non-existent local buffer.
- No chain validator yet — users are expected to pair correctly.

## Adding a New Technique

Each new technique currently touches 3–4 places:

1. Create `src/techniques/<stage_number>_<stage_name>/<technique>.h` with function `inline BOOL Stage<N>_<Action>_<Name>(TechniqueContext* ctx)`
2. Add `#ifdef` block (include + dispatch) in `src/techniques/runner/T<N>_*.h`
3. Register preprocessor flag in `controller/modules/definitions.py` under `STAGE_FLAGS`
4. If the technique needs an extra compile unit (e.g. an `.asm` or `.c` file), add the object to `OBJS` in the `Makefile`

A registry-based refactor that would cut this down to 2 touches is designed but not yet implemented.

## Naming Conventions

- Technique functions: `Stage<N>_<Action>_<Name>(TechniqueContext* ctx)` returning `BOOL` (TRUE = success, FALSE = abort pipeline)
- Preprocessor flags: `-DT<N>_<STAGE>_<TECHNIQUE>` (e.g., `-DT5_EXEC_DISPLAY_MONITORS`, `-DT0_ANTIANALYSIS_DEBUG`)
- Technique files: `src/techniques/<stage_number>_<stage_name>/<technique_name>.h`
- Documentation IDs: `L<stage>.T<number>` (e.g., `L3.T2` = AES)

## Code Style

- C++ loader code is header-only (`.h` with `inline` functions), C-style
- Every technique file needs `#pragma once` and null-checks on `ctx`
- Every `Stage<N>_*` function returns `BOOL`; main.cpp aborts the loader on `FALSE`
- Debug output uses `DEBUG_MSG(stage, format, ...)` macro, gated by `#ifdef DEBUG_MODE`
- Each technique must be self-contained in a single file
- NT API calls go through `src/api/api_wrappers.h` wrappers (`MyVirtualAllocEx`, `MyVirtualProtect`, …) — never call the raw Windows or NT function directly, otherwise `--api syscalls` becomes contaminated
