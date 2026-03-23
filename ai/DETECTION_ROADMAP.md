# Detection & Blue Team Roadmap

## Current State

- Log collection: `collect_defender.ps1` collects Windows Defender events (1116/1117/1118) and Sysmon events
- Detection analysis: Manual review of collected logs
- No structured detection rules yet

## Vision: Technique ↔ Detection Mapping

For **every technique** in the framework, the blue team side should provide:

```
Technique: L2.T1 — VirtualAlloc (Local)
├── Telemetry Sources
│   ├── Sysmon Event ID 10 (Process Access)
│   ├── ETW: Microsoft-Windows-Kernel-Memory
│   └── Kernel Callback: PsSetCreateThreadNotifyRoutine
├── Detection Indicators
│   ├── RWX memory allocation from non-system process
│   ├── Large allocation size matching common shellcode sizes
│   └── Allocation followed by thread creation in same region
├── Detection Rules
│   ├── Sigma: proc_access_rwx_alloc.yml
│   ├── YARA: rwx_section_in_memory.yar
│   └── Custom: PowerShell log query
└── References
    ├── MITRE ATT&CK: T1055.001
    └── Elastic Detection Rules: ...
```

## Proposed Structure

```
detection/
├── rules/
│   ├── sigma/                    # Sigma detection rules
│   │   ├── L2_T1_virtual_alloc.yml
│   │   ├── L5_T1_create_thread.yml
│   │   └── L5_T2_callback_execution.yml
│   ├── yara/                     # YARA rules for static analysis
│   └── custom/                   # Custom detection scripts
│
├── telemetry/
│   ├── sysmon_config.xml         # Optimized Sysmon config for loader detection
│   └── etw_providers.md          # Relevant ETW providers per stage
│
├── analysis/
│   ├── L0_anti_analysis.md       # Detection surface for anti-analysis techniques
│   ├── L1_storage.md
│   ├── L2_allocation.md
│   ├── L3_transformation.md
│   ├── L4_writing.md
│   └── L5_execution.md
│
└── mapping/
    └── technique_detection_matrix.md   # Complete mapping table
```

## Detection Surface by Stage

| Stage | Key Detection Points | Primary Telemetry |
|-------|---------------------|-------------------|
| L0 — Anti-Analysis | Timing anomalies, API call patterns | ETW, API hooking |
| L1 — Storage | File on disk (static scan), network download | Defender scan, Sysmon Event 11/3 |
| L2 — Allocation | RWX memory allocation | Sysmon Event 10, ETW kernel memory |
| L3 — Transformation | Entropy analysis, crypto API usage | Static analysis, YARA |
| L4 — Writing | Process memory modification | Sysmon Event 10, WriteProcessMemory hooking |
| L5 — Execution | Thread creation, callback invocation | Sysmon Event 8, ETW thread events |

## Priority

1. Start with detection docs per stage (what to look for)
2. Write Sigma rules for existing techniques
3. Expand Sysmon config to capture relevant events
4. Build the technique ↔ detection matrix
5. Add automated detection analysis to the testing pipeline
