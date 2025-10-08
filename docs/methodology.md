# Evasion Techniques Research Methodology

This document outlines the core methodology for analyzing, implementing, and evaluating evasion techniques within the project's shellcode loader. Instead of focusing on **named techniques (e.g., "Process Hollowing")**, this research adopts a systematic approach by deconstructing the loader's lifecycle into **primitive stages**.

This model enables a modular and structured analysis, allowing for the independent evaluation of each primitive and its various implementations.

---

## 1. The 4-Stage Loader Lifecycle Model

Every shellcode loader executes a sequence of four fundamental stages. Bypassing AV/EDR solutions is achieved by selecting stealthy methods for each stage.

### **Stage 1: Storage**
-   **Question:** Where and in what form is the shellcode stored on disk or before execution?
-   **Evasion Goal:** Evade static signature-based scanning. The on-disk payload should appear as benign or random data.
-   **Methods Under Study:**
    -   `S1` (Baseline): Embedded as a C++ byte array in the `.data` or `.rdata` section.
    -   `S2` (Advanced): Stored within the PE file's resource section (`.rsrc`).
    -   `S3` (Remote): Fetched from a remote server over HTTP/S.

### **Stage 2: Allocation**
-   **Question:** How is memory requested from the OS to hold the executable shellcode?
-   **Evasion Goal:** Avoid detection when allocating executable memory (RWX), a heavily monitored behavior.
-   **Methods Under Study:**
    -   `A1` (Local): Allocating memory within the loader's own process (`VirtualAlloc`).
    -   `A2` (Remote): Allocating memory in a remote process (`VirtualAllocEx`).
    -   `A3` (Advanced): Reusing existing memory regions (e.g., module stomping, memory mapping).

### **Stage 3: Writing / Transformation**
-   **Question:** How is the shellcode moved from *Storage* into the *Allocated* memory region?
-   **Evasion Goal:** Ensure the plaintext, executable shellcode exists in memory for the shortest possible duration and in a form that resists memory scanning.
-   **Methods Under Study:**
    -   **Transformation (Decryption):**
        -   `T1` (Baseline): **XOR** decryption.
        -   `T2` (Advanced): **AES-256** decryption.
    -   **Writing (Memory Copy):**
        -   `W1` (Local): Direct memory copy (`memcpy`, `RtlMoveMemory`).
        -   `W2` (Remote): Writing to a remote process's memory (`WriteProcessMemory`).

### **Stage 4: Execution**
-   **Question:** How is CPU control transferred to the allocated shellcode?
-   **Evasion Goal:** Avoid loud and easily monitored execution methods like `CreateRemoteThread`.
-   **Methods Under Study:**
    -   `E1` (Local): Creating a new local thread (`CreateThread`).
    -   `E2` (Remote): Creating a new remote thread (`CreateRemoteThread`).
    -   `E3` (Stealthy): Queuing an Asynchronous Procedure Call (`QueueUserAPC`).
    -   `E4` (Stealthy): Hijacking an existing thread (`SetThreadContext`).

---

## 2. Mapping Methodology to Code Architecture

The project's source code is structured to directly reflect this 4-stage model.

-   **`src/techniques/T_encryption.h`**: Implements methods for the **Transformation** stage (`T1`, `T2`, etc.).
-   **`src/techniques/T_injection.h`**: Contains complete "recipes," where each recipe is a combination of methods from the `Allocation`, `Writing`, and `Execution` stages.
-   **`src/api/api_wrappers.h`**: Provides an abstraction layer for **how** each method is implemented. For instance, the `A1 (VirtualAlloc)` method can be executed via a standard WinAPI call or a Direct Syscall.

---

## 3. The Test Matrix

The primary research objective is to construct and execute a test matrix, comparing the effectiveness of different primitive combinations against various AV/EDR environments.

**Example Matrix Row:**

| Test ID | Storage | Allocation | Transform | Execution | API Method | Target AV | Result | Sysmon Log Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-001 | S1 | A1 | T1 (XOR) | E1 (CreateThread) | WinAPI | Defender | FAILED | `payload.exe` detected making outbound network connection. |
| T-002 | S1 | A2 | T1 (XOR) | E4 (SetThreadContext)| WinAPI | Defender | SUCCESS | `svchost.exe` made outbound connection; behavior not flagged. |
| T-003 | S1 | A2 | T1 (XOR) | E4 (SetThreadContext)| Syscall | Defender | SUCCESS | Same as T-002, but no API calls from `kernel32.dll` logged. |

By populating this matrix, the project will provide quantitative and detailed insights into the efficacy of individual evasion techniques and methodologies.