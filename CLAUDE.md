# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Educational shellcode loader testing platform. Automates: build → deploy to VM → execute → collect detection logs. **Not** an AV/EDR bypass tool — it's for studying how loaders work and mapping detection surfaces.

## Build & Run Commands

```bash
# Build only (no VM testing)
python cli.py -s shellcodes/payload.bin --build-only -t3 aes -t5 monitors

# Build and test on VMs
python cli.py -s shellcodes/payload.bin -t3 xor -t5 local -v "VM_NAME"

# Full flags
python cli.py -s PATH -t0 none|antidebug -t1 rdata -t2 local -t3 none|xor|aes \
              -t4 local -t5 local|monitors --api winapi|indirect|syscalls \
              -v VM1 VM2 --debug

# Manual make (rarely needed — builder.py calls this)
make build SRC=generated_loader.cpp OUT=payload.exe DEFINES="-DT3_TRANSFORM_AES"

# Clean build artifacts
make clean
```

Requirements: Python 3.8+, MinGW-w64 (`x86_64-w64-mingw32-g++`), NASM, VMware with `vmrun` CLI.

## Architecture

### 6-Stage Loader Pipeline

Every loader is decomposed into 6 compile-time selectable stages:

```
L0: Anti-Analysis → L1: Storage → L2: Allocation → L3: Transformation → L4: Writing → L5: Execution
```

Stages communicate through a single `TechniqueContext` struct (`src/techniques/context.h`) passed as a pointer through all stages.

### Compile-Time Technique Selection

Techniques are **not** selected at runtime. The flow is:

1. CLI flag (e.g., `-t3 aes`) → Python maps to preprocessor define (`-DT3_TRANSFORM_AES`) via `controller/modules/definitions.py`
2. Runner files (`src/techniques/runner/T<N>_*.h`) use `#ifdef` to include the selected technique
3. Each technique is a self-contained header file with one `inline` function

### Build Pipeline

```
shellcode.bin
  → Python encrypts + generates build/src/payload_data.h (C array)
  → Copies src/main.cpp → build/src/generated_loader.cpp
  → make build with -D flags
  → build/bin/payload_TIMESTAMP.exe
```

Orchestrated by `controller/modules/builder.py`. The Makefile compiles C++ (MinGW), assembles NASM (`src/api/syscall.asm`), and links.

### API Abstraction

`src/api/api_wrappers.h` wraps NT API calls with three modes selected via `--api`:
- `winapi` (default) — standard Windows API
- `indirect` — resolve through ntdll
- `syscalls` — direct syscall via NASM stubs (`src/api/syscall.asm`)

### Test Execution (VM)

`controller/core_engine.py` manages the full test cycle: revert VM snapshot → start → deploy payload → listen for C2 callback (`controller/modules/c2.py`) → execute → collect Defender/Sysmon logs → report result. VM config lives in `controller/config.py`.

## Adding a New Technique

1. Create `src/techniques/<stage_number>_<stage_name>/<technique>.h` with function `Stage<N>_<Action>_<Name>(TechniqueContext* ctx)`
2. Add `#ifdef` block in `src/techniques/runner/T<N>_*.h`
3. Register preprocessor flag in `controller/modules/definitions.py` under `STAGE_FLAGS`
4. CLI picks up new choices automatically from `STAGE_FLAGS`

## Naming Conventions

- Technique functions: `Stage<N>_<Action>_<Name>(TechniqueContext* ctx)`
- Preprocessor flags: `-DT<N>_<STAGE>_<TECHNIQUE>` (e.g., `-DT5_EXEC_DISPLAY_MONITORS`)
- Technique files: `src/techniques/<stage_number>_<stage_name>/<technique_name>.h`
- Documentation IDs: `L<stage>.T<number>` (e.g., `L3.T2` = AES)

## Code Style

- C++ loader code is header-only (`.h` with `inline` functions), C-style
- Every technique file needs `#pragma once` and null-checks on `ctx`
- Debug output uses `DEBUG_MSG(stage, format, ...)` macro, gated by `#ifdef DEBUG_MODE`
- Each technique must be self-contained in a single file
