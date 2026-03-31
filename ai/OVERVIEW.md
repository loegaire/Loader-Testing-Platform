# Loader Testing Platform — Project Overview

## What is this?

An **educational research framework** that helps students, red teamers, and blue teamers systematically study shellcode loader techniques.

The malware loader landscape is fragmented — hundreds of techniques scattered across blogs, tools, and repos with no unified structure. This project solves that by decomposing any loader into a **6-stage pipeline model**, making it possible to:

- Study each technique in isolation
- Combine techniques like building blocks
- Map detection opportunities for each technique
- Compare any loader against a common framework

**This is NOT a tool for bypassing AV/EDR.** It is a structured learning and research platform.

## Who is it for?

| Audience | Use case |
|----------|----------|
| Students | Learn how loaders work stage-by-stage, with real code |
| Red Team | Experiment with technique combinations systematically |
| Blue Team | Understand what to detect at each stage, write detection rules |
| Researchers | Map and classify loader techniques using a standard model |

## The Core Idea: 6-Stage Pipeline

Every shellcode loader, no matter how complex, follows this execution pipeline:

```
L0 → L1 → L2 → L3 → L4 → L5

Anti-Analysis → Storage → Allocation → Transformation → Writing → Execution
```

| Stage | Name | What it does | Example |
|-------|------|-------------|---------|
| L0 | Anti-Analysis | Detect sandboxes, debuggers, VMs | `IsDebuggerPresent()` check |
| L1 | Storage | Where the shellcode is stored | Embedded in `.rdata` section |
| L2 | Allocation | Allocate memory for execution | `VirtualAlloc(PAGE_EXECUTE_READWRITE)` |
| L3 | Transformation | Decrypt/decode the shellcode | XOR decryption, AES-128-CTR |
| L4 | Writing | Write shellcode into allocated memory | `memcpy()` to executable region |
| L5 | Execution | Transfer control to shellcode | `CreateThread()`, `EnumDisplayMonitors()` |

Any loader can be described as: `L0.T1 + L1.T1 + L2.T1 + L3.T2 + L4.T1 + L5.T1`

## How the Platform Works

```
User (CLI) → Python Controller → Build C++ Loader → Deploy to VM → Execute → Collect Logs → Analyze
```

1. User picks techniques for each stage via CLI flags (`-t1 rdata -t3 aes -t5 monitors`)
2. Python controller encrypts shellcode and generates C++ header
3. Makefile compiles the loader with appropriate preprocessor flags
4. (Optional) Loader is deployed to VMware VM, executed, and logs are collected

## Project Vision & Roadmap

### Current State
- 6-stage pipeline model defined and implemented
- Basic techniques for each stage (1-2 per stage)
- Automated build system with CLI
- VM orchestration for testing against Windows Defender
- Log collection (Defender events + Sysmon)

### Short-term Goals
- Expand technique library across all stages
- More allocation methods (remote process, new process)
- More execution methods (APC, NtCreateThreadEx, callback abuse)
- More storage methods (file-based, network download)

### Long-term Vision
- **Blue Team Detection Framework**: For every technique, provide:
  - What telemetry it generates (ETW, Sysmon, kernel callbacks)
  - Detection rules (Sigma, YARA, custom)
  - Log analysis methodology
- **Universal Loader Mapping**: Any real-world loader can be decomposed and mapped to this model
- **Academic Research**: Systematic comparison and classification of loader techniques
