# Automated Loader Testing Platform
*(Research & Educational Use Only)*

## Overview

Automated testing platform for evaluating shellcode loader techniques against AV/EDR solutions.

The platform automates the full testing workflow: **build loader** → **deploy to VM** → **execute** → **collect detection logs** → **report results**.

Built on a [6-stage loader model](./docs/methodology.md) where each stage (anti-analysis, storage, allocation, transformation, writing, execution) can be independently swapped at compile time.

---

## Quick Start

### 1. Install Host Dependencies

**Linux (recommended — required for VM testing):**

```bash
# Fedora
sudo dnf install -y mingw64-gcc-c++ nasm python3 python3-pip make sshpass \
    qemu-kvm libvirt virt-manager virt-install

# Debian/Ubuntu
sudo apt install -y mingw-w64 nasm python3 python3-pip make sshpass \
    qemu-kvm libvirt-daemon-system libvirt-clients virtinst virt-manager
```

**Windows (build only, no VM testing):** See [Windows build guide](./docs/build_windows.md) — requires MSYS2.

### 2. Clone & Install Python Dependencies

```bash
git clone <repo-url> && cd Loader-Testing-Platform
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Build Only (No VM Needed)

```bash
# Create a dummy shellcode for testing the build pipeline
printf '\x90\x90\x90\x90' > shellcodes/dummy.bin

python3 cli.py -s shellcodes/dummy.bin --build-only
# Output: build/bin/payload_<timestamp>.exe
```

### 4. Build + Test on VM

Requires a Windows VM set up according to [Lab Setup Guide](./docs/lab_setup.md).

```bash
python3 cli.py -s shellcodes/payload.bin -t3 xor -t5 local -v "Windows Defender" --debug
```

---

## CLI Usage

```bash
python3 cli.py -s <shellcode.bin> [stage flags] [options]
```

### Stage Flags

| Flag | Stage | Options | Default |
|------|-------|---------|---------|
| `-t0` | Anti-Analysis | `none`, `antidebug` | `none` |
| `-t1` | Storage | `rdata` | `rdata` |
| `-t2` | Allocation | `local` | `local` |
| `-t3` | Transformation | `none`, `xor`, `aes` | `none` |
| `-t4` | Writing | `local` | `local` |
| `-t5` | Execution | `local`, `monitors` | `local` |
| `--api` | API Layer | `winapi`, `indirect`, `syscalls` | `winapi` |

### Options

| Flag | Description |
|------|-------------|
| `--build-only` | Build payload without running on VM |
| `-v VM1 VM2` | Target VMs (names from `config.py`) |
| `--debug` | Enable debug output in payload |

### Examples

```bash
# Build only, AES encryption
python3 cli.py -s shellcodes/payload.bin --build-only -t3 aes -t5 monitors

# Build + test on VM, XOR encryption, direct syscalls
python3 cli.py -s shellcodes/payload.bin -t3 xor -t5 local --api syscalls -v "Windows Defender"

# Full options
python3 cli.py -s shellcodes/payload.bin -t0 antidebug -t1 rdata -t2 local \
    -t3 aes -t4 local -t5 local --api indirect -v "Windows Defender" --debug
```

---

## Architecture

```
                    ┌─────────────┐
                    │   cli.py    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ core_engine │
                    └──┬───────┬──┘
                       │       │
              ┌────────▼──┐ ┌──▼──────────┐
              │  builder  │ │ vm_manager  │
              │           │ │  (KVM/SSH)  │
              └─────┬─────┘ └──┬───────┬──┘
                    │          │       │
               build/bin/   virsh   ssh/scp
              payload.exe     │       │
                           ┌──▼───────▼──┐
                           │  Windows VM │
                           │  (KVM/QEMU) │
                           └─────────────┘
```

| Component | Description |
|-----------|-------------|
| `cli.py` | CLI entry point, parses flags |
| `core_engine.py` | Orchestrates build → deploy → execute → collect |
| `builder.py` | Encrypts shellcode, generates C++ header, calls `make` |
| `vm_manager.py` | Controls VM via `virsh`, interacts via SSH/SCP (`sshpass`) |
| `c2.py` | TCP listener that waits for reverse shell callback |
| `config.py` | VM definitions, paths, credentials |
| `definitions.py` | Maps CLI flags to C++ preprocessor defines |

### Test Cycle

When run with `-v`, the engine performs:

1. **Revert** VM to `clean_snapshot` (`virsh snapshot-revert`)
2. **Start** VM (`virsh start`)
3. **Wait** for SSH to become available
4. **Deploy** payload via SCP
5. **Execute** payload via SSH
6. **Listen** for C2 callback (30s timeout)
7. **Collect** Defender/Sysmon logs if detection occurred
8. **Shutdown** VM

---

## Project Structure

```
.
├── cli.py                          # CLI entry point
├── Makefile                        # C++ build rules (MinGW + NASM)
├── requirements.txt                # Python dependencies (tinyaes)
│
├── controller/
│   ├── config.py                   # VM config, paths, credentials
│   ├── core_engine.py              # Test orchestration
│   └── modules/
│       ├── builder.py              # Payload build pipeline
│       ├── crypto_utils.py         # XOR/AES encryption
│       ├── definitions.py          # CLI flag → preprocessor define mapping
│       └── vm_manager.py           # KVM/SSH VM management
│
├── src/
│   ├── main.cpp                    # Loader entry point (template)
│   ├── api/
│   │   ├── api_wrappers.h          # NT API abstraction (winapi/indirect/syscalls)
│   │   ├── syscall.asm             # Direct syscall stubs (NASM)
│   │   └── syscall.h               # Syscall declarations
│   ├── core/
│   │   ├── utils.h                 # DEBUG_MSG macro, utilities
│   │   └── win_internals.h         # Windows internal structures
│   └── techniques/
│       ├── context.h               # TechniqueContext struct (shared state)
│       ├── runner/                  # Stage dispatcher headers (#ifdef routing)
│       │   ├── T1_storage.h
│       │   ├── T2_allocation.h
│       │   ├── T3_transformation.h
│       │   ├── T4_writing.h
│       │   └── T5_execution.h
│       ├── 0_anti_analysis/        # L0 techniques
│       ├── 1_storage/              # L1 techniques
│       ├── 2_allocation/           # L2 techniques
│       ├── 3_transformation/       # L3 techniques (XOR, AES)
│       ├── 4_writing/              # L4 techniques
│       └── 5_execution/            # L5 techniques
│
├── log_collectors/                 # PowerShell scripts for log collection
├── shellcodes/                     # Input shellcode files (.bin)
├── build/                          # Build artifacts (generated)
├── test_logs/                      # Collected detection logs
└── docs/                           # Documentation
    ├── lab_setup.md                # VM setup guide
    ├── methodology.md              # 6-stage framework design
    └── techniques/                 # Per-technique documentation
```

---

## Requirements

| Component | Purpose |
|-----------|---------|
| Python 3.8+ | Orchestration |
| MinGW-w64 (`x86_64-w64-mingw32-g++`) | Cross-compile loader for Windows |
| NASM | Assemble direct syscall stubs |
| KVM/QEMU + libvirt | VM hypervisor |
| `virt-manager` | VM creation (GUI) |
| `sshpass` | Password-based SSH automation |
| Windows 10/11 VM | Test target |

Recommended host: Linux with 8GB+ RAM, 100GB+ disk.

---

## Documentation

- [Lab Setup Guide](./docs/lab_setup.md) — how to create Windows VMs for testing
- [Windows Build Guide](./docs/build_windows.md) — MSYS2 toolchain setup for Windows hosts
- [Framework Methodology](./docs/methodology.md) — 6-stage loader model design
- [Technique Docs](./docs/techniques/) — per-technique documentation

---

## Research Scope

This platform is strictly for **security research and defensive analysis** in isolated lab environments. Generated payloads must never be distributed or executed outside controlled systems.

## Reference

- [Shhhloader](https://github.com/icyguider/Shhhloader/tree/main) — shellcode loader used for technique mapping reference
