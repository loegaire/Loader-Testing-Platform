# Architecture & Codebase Guide

## Repository Structure

```
.
├── ai/                          # AI context files (this folder)
├── src/                         # C++ loader source code
│   ├── main.cpp                 # Entry point — calls each stage runner sequentially
│   ├── api/
│   │   ├── api_wrappers.h       # Abstraction layer: WinAPI / Indirect / Direct Syscall
│   │   ├── syscall.asm          # NASM assembly for direct syscalls
│   │   └── syscall.h            # Syscall initialization and SSN resolution
│   ├── core/
│   │   ├── utils.h              # Debug macros, helper functions
│   │   └── win_internals.h      # Windows internal structures (PEB, TEB, etc.)
│   └── techniques/
│       ├── context.h             # TechniqueContext struct — shared state between stages
│       ├── 0_anti_analysis/      # L0 techniques
│       ├── 1_storage/            # L1 techniques
│       ├── 2_allocation/         # L2 techniques
│       ├── 3_transformation/     # L3 techniques (+ aes.c/aes.h for AES impl)
│       ├── 4_writing/            # L4 techniques
│       ├── 5_execution/          # L5 techniques
│       └── runner/               # Stage dispatchers (T1_storage.h → T5_execution.h)
│                                 # Each runner uses #ifdef to select the active technique
│
├── controller/                  # Python orchestration layer
│   ├── config.py                # Paths, VM configs, credentials
│   ├── core_engine.py           # Main workflow: build → deploy → execute → collect logs
│   └── modules/
│       ├── definitions.py       # Maps CLI flags to C++ preprocessor defines
│       ├── builder.py           # Reads shellcode, encrypts, generates header, compiles
│       ├── crypto_utils.py      # XOR/AES encryption at build time
│       ├── c2.py                # Simple TCP listener to verify shellcode execution
│       └── vm_manager.py        # VMware vmrun wrapper
│
├── log_collectors/
│   └── collect_defender.ps1     # PowerShell: collects Defender + Sysmon events
│
├── docs/                        # Research documentation
│   ├── methodology.md           # The 6-stage pipeline model (theory)
│   ├── lab_setup.md             # VM environment setup guide
│   └── techniques/              # Per-technique documentation
│
├── cli.py                       # CLI entry point
├── Makefile                     # Build system (MinGW + NASM)
└── requirements.txt             # Python dependencies
```

## Key Design Patterns

### 1. Technique Selection via Preprocessor

Techniques are selected at **compile time** using C preprocessor defines:

```
CLI flag: -t3 aes
  → Python maps to: -DT3_TRANSFORM_AES
    → C++ runner/T3_transformation.h:
        #ifdef T3_TRANSFORM_AES
        #include "../3_transformation/crypto_aes.h"
        #endif
```

This means each technique is a self-contained `.h` file with a single function.

### 2. TechniqueContext — Shared State

All stages communicate through a single `TechniqueContext` struct:

```c
typedef struct {
    unsigned char* data;           // raw/encrypted shellcode
    SIZE_T length;
    unsigned char* key;            // encryption key
    SIZE_T key_len;
    unsigned char* nonce;          // nonce (for AES-CTR)
    SIZE_T nonce_len;
    unsigned char* transformed;    // decrypted buffer
    unsigned char* allocated_mem;  // executable memory
    HANDLE target_process;         // for remote injection
} TechniqueContext;
```

Stage 1 populates `data/key/nonce` → Stage 2 allocates `allocated_mem` → Stage 3 decrypts `data` in-place → Stage 4 copies to `allocated_mem` → Stage 5 executes from `allocated_mem`.

### 3. API Abstraction Layer

API calls are wrapped to support three modes:
- **WinAPI** (default): Standard Windows API calls
- **Indirect Syscall**: Resolve and call through ntdll
- **Direct Syscall**: Custom assembly syscall stubs (NASM)

Selected via `--api winapi|indirect|syscalls`.

### 4. Build Pipeline

```
shellcode.bin
    ↓ (Python: encrypt + generate payload_data.h)
payload_data.h (contains encrypted shellcode as C array)
    ↓ (copy main.cpp → build/src/generated_loader.cpp)
    ↓ (make build DEFINES="-DT1_STORAGE_RDATA -DT3_TRANSFORM_AES ...")
payload_TIMESTAMP.exe
```

## Currently Implemented Techniques

| Stage | ID | Name | File | Description |
|-------|----|------|------|-------------|
| L0 | T0.1 | Anti-Debug | `anti_debug.h` | `IsDebuggerPresent()` check |
| L1 | T1.1 | .rdata Storage | `storage_rdata.h` | Shellcode embedded in binary, copied to heap |
| L2 | T2.1 | Local Alloc | `alloc_local.h` | `VirtualAlloc` in current process (RWX) |
| L3 | T3.0 | None | — | No encryption |
| L3 | T3.1 | XOR | `crypto_xor.h` | Single-byte/multi-byte XOR |
| L3 | T3.2 | AES-128-CTR | `crypto_aes.h` | AES decryption (tiny-AES-c) |
| L4 | T4.1 | Local Write | `write_local.h` | `memcpy` to allocated region |
| L5 | T5.1 | Local Thread | `exec_local.h` | `CreateThread` + `WaitForSingleObject` |
| L5 | T5.2 | DisplayMonitors | `exec_display_monitors.h` | `EnumDisplayMonitors` callback abuse |

## How to Add a New Technique

1. Create a `.h` file in the appropriate `src/techniques/<stage>/` folder
2. Implement a function following the naming convention: `Stage<N>_<Name>(TechniqueContext* ctx)`
3. Add `#ifdef` block in the corresponding `runner/T<N>_*.h`
4. Add the preprocessor flag in `controller/modules/definitions.py` under `STAGE_FLAGS`
5. The CLI automatically picks up new choices from `STAGE_FLAGS`
