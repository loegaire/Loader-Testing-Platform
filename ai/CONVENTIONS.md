# Coding Conventions & Contribution Guide

## Language

- Loader implementation: **C++ (C-style)** compiled with MinGW-w64
- Orchestration/automation: **Python 3.8+**
- Build system: **GNU Make**
- Assembly (syscalls): **NASM** (win64 format)

## Naming Conventions

### Technique Files
- Location: `src/techniques/<stage_number>_<stage_name>/<technique_name>.h`
- Example: `src/techniques/5_execution/exec_display_monitors.h`

### Technique Functions
- Pattern: `Stage<N>_<Action>_<Name>(TechniqueContext* ctx)`
- Examples:
  - `Stage1_Storage_Rdata(ctx)`
  - `Stage2_Alloc_Local(ctx)`
  - `Stage3_Transform_XOR(ctx)`
  - `Stage5_Exec_DisplayMonitors(ctx)`

### Preprocessor Flags
- Pattern: `-DT<N>_<STAGE>_<TECHNIQUE>`
- Examples:
  - `-DT1_STORAGE_RDATA`
  - `-DT3_TRANSFORM_AES`
  - `-DT5_EXEC_DISPLAY_MONITORS`

### Technique IDs
- Format: `L<stage>.T<number>` (in documentation)
- Example: `L3.T2` = AES decryption (Stage 3, Technique 2)

## Adding a New Technique — Step by Step

### Step 1: Write the technique (.h file)

```c
// src/techniques/2_allocation/alloc_remote.h
#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"
#include "../context.h"

inline BOOL Stage2_Alloc_Remote(TechniqueContext* ctx)
{
    // Implementation here
    // Use ctx-> fields for input/output
    // Return BOOL for success/failure
}
```

### Step 2: Add to runner dispatcher

```c
// src/techniques/runner/T2_allocation.h
#ifdef T2_ALLOC_REMOTE
#include "../2_allocation/alloc_remote.h"
#endif

// In the Run_T2_Allocation function:
#ifdef T2_ALLOC_REMOTE
    return Stage2_Alloc_Remote(ctx);
#endif
```

### Step 3: Register the preprocessor flag

```python
# controller/modules/definitions.py
STAGE_FLAGS = {
    't2': {
        'local':  '-DT2_ALLOC_LOCAL',
        'remote': '-DT2_ALLOC_REMOTE',   # ← add here
    },
}
```

### Step 4: (Optional) Add documentation

Create `docs/techniques/<stage>/<technique_name>.md` with:
- What the technique does
- How it works (API calls, behavior)
- Detection surface (what telemetry it generates)
- References

## Code Style

- Header-only C++ (`.h` files with `inline` functions)
- Always include `#pragma once`
- Always null-check `ctx` and required fields
- Use `#ifdef DEBUG_MODE` for debug output
- Use `DEBUG_MSG(stage, format, ...)` macro for logging
- Keep each technique self-contained in a single file
