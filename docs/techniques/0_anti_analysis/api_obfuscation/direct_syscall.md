| | |
| :--- | :--- |
| **ID** | AO2 (API Obfuscation 2) |
| **Category** | API Call Obfuscation / EDR Evasion |
| **Complexity** | High |
| **Primary Use** | Bypass user-land EDR hooks by invoking kernel functions directly. |

### Goal
To execute system functions by communicating directly with the Windows kernel, completely bypassing the standard user-land DLLs (`kernel32.dll`) and their corresponding EDR hooks.

### Mechanism
Most user-land WinAPI functions (e.g., `kernel32!CreateThread`) are simply wrappers around a corresponding function in `ntdll.dll` (e.g., `ntdll!NtCreateThreadEx`). The `ntdll` function then prepares for and executes a `syscall` instruction to transition into kernel mode. EDRs often place "hooks" on the `kernel32` or `ntdll` functions to monitor their usage. Direct Syscalls bypasses these hooks.

The process involves three key steps:

**1. Dynamic SSN Resolution:**
The System Service Number (SSN), or syscall number, is a unique ID for each kernel function. These numbers can change between Windows versions, so they must be found at runtime.
   - The address of the target `ntdll` function (e.g., `NtCreateThreadEx`) is found by parsing `ntdll.dll`'s Export Table.
   - The loader then reads the first few bytes of this function's machine code. On modern Windows x64, this code follows a predictable pattern (the "syscall stub"):
     ```assembly
     mov r10, rcx
     mov eax, <SSN>  ; The SSN is hardcoded here by the OS loader!
     ```
   - The loader extracts the 4-byte SSN directly from this `mov eax, ...` instruction.

**2. Find `syscall` Instruction Address:**
The loader continues scanning a few bytes forward from the start of the `ntdll` function to find the memory address of the `syscall` instruction (`0F 05`). This address is the same for all functions in `ntdll` and acts as the gateway to the kernel.

**3. Execute Syscall via Assembly Stub:**
The loader uses a small, custom piece of assembly code to perform the syscall.
   - It sets up the function arguments according to the x64 calling convention.
   - It moves the dynamically resolved SSN (from Step 1) into the `EAX` register.
   - It `jmp`s to the address of the `syscall` instruction (from Step 2).

```cpp
// C++ wrapper calling the assembly stub
// The SSN and syscall address have been resolved and stored in global variables.
NTSTATUS status = sysNtCreateThreadEx(&hThread, ...); // sysNtCreateThreadEx is an assembly function
```

### Analysis

#### Strengths
*   **Bypasses All User-Land Hooks:** This is the most significant advantage. Since the loader never calls the functions in `kernel32.dll` or the hooked entry points in `ntdll.dll`, the EDR's primary monitoring mechanism in user-land is completely circumvented.
*   **High Stealth:** From a user-land monitoring perspective, the program's execution flow appears to "vanish" at the assembly stub and then reappear in the kernel, leaving no direct trace of which `ntdll` function was invoked.

#### Weaknesses
*   **Vulnerable to Kernel-Level Monitoring:** This technique is **not** a silver bullet. Advanced EDRs operate at the kernel level. They can monitor system calls directly via kernel callbacks (e.g., `PsSetCreateThreadNotifyRoutine`) or by monitoring the System Service Dispatch Table (SSDT). Direct Syscalls offers no protection against this layer of defense.
*   **Implementation Fragility:** The SSN resolution method relies on the predictable "stub" pattern of `ntdll` functions. A future Windows update could change this pattern, breaking the loader and requiring it to be updated.
*   **Complexity:** The technique is complex, architecture-specific, and requires careful handling of assembly code and undocumented structures.

### Summary
Direct Syscalls is a powerful and highly effective technique for bypassing the majority of EDRs that rely on user-land API hooking. It represents a significant escalation in evasion capabilities compared to Dynamic API Resolution. However, it is detectable by kernel-level security solutions and its implementation can be fragile across different Windows versions.