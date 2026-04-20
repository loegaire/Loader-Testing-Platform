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
              -t2 local|local_rw \
              -t3 none|xor|aes \
              -t4 local|local_rx \
              -t5 local|monitors|fiber \
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
- `syscalls` — direct syscall via NASM stubs. Covers `NtAllocateVirtualMemory`, `NtProtectVirtualMemory`, `NtCreateThreadEx`, `NtWaitForSingleObject`.

Wrapped functions: `MyVirtualAllocEx`, `MyVirtualProtect`, `MyCreateThreadEx`, `MyWaitForSingleObject`.

### Test Execution (VM)

`controller/core_engine.py` manages the full test cycle: revert VM snapshot → start → deploy payload → listen for C2 callback (`controller/modules/c2.py`) → execute → collect Defender/Sysmon logs → report result. VM config lives in `controller/config.py`. VM backend is KVM/libvirt via `virsh` — Linux host only.

## Current Technique Inventory

| Stage | Option | Define | Notes |
|-------|--------|--------|-------|
| L0 | `none` | `T0_ANTIANALYSIS_NONE` | No-op |
| L0 | `antidebug` | `T0_ANTIANALYSIS_DEBUG` | PEB.BeingDebugged check |
| L1 | `rdata` | `T1_STORAGE_RDATA` | Payload in `.rdata` as C array |
| L2 | `local` | `T2_ALLOC_LOCAL` | VirtualAlloc `PAGE_EXECUTE_READWRITE` (RWX) |
| L2 | `local_rw` | `T2_ALLOC_LOCAL_RW` | VirtualAlloc `PAGE_READWRITE` (pair with L4 `local_rx`) |
| L3 | `none` | `T3_TRANSFORM_NONE` | No decryption |
| L3 | `xor` | `T3_TRANSFORM_XOR` | XOR-key |
| L3 | `aes` | `T3_TRANSFORM_AES` | AES-128-CTR via `aes.c` |
| L4 | `local` | `T4_WRITE_LOCAL` | memcpy only (assumes RWX allocation) |
| L4 | `local_rx` | `T4_WRITE_LOCAL_RX` | memcpy + `VirtualProtect` to `PAGE_EXECUTE_READ` |
| L5 | `local` | `T5_EXEC_LOCAL` | `CreateThread` on shellcode entry |
| L5 | `monitors` | `T5_EXEC_DISPLAY_MONITORS` | `EnumDisplayMonitors` callback trick |
| L5 | `fiber` | `T5_EXEC_FIBER` | `ConvertThreadToFiber` + `CreateFiber` + `SwitchToFiber` |

**Paired techniques**: `-t2 local_rw` only makes sense with `-t4 local_rx` (plain `local_rw + local` will crash because the buffer never gets the execute bit). No chain validator yet — users are expected to pair correctly.

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
