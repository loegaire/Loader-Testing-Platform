| | |
| :--- | :--- |
| **ID** | AO1 (API Obfuscation 1) |
| **Category** | API Call Obfuscation |
| **Complexity** | Medium |
| **Primary Use** | Hide Windows API imports from the static import table (IAT). |

### Goal
To resolve the memory addresses of Windows API functions **at runtime**, rather than linking to them at compile time. This prevents function names (e.g., "VirtualAlloc", "CreateThread") from appearing in the loader's Import Address Table (IAT), a primary source for static malware detection.

### Mechanism
This technique manually replicates the job of the Windows loader. The loader, upon starting, becomes responsible for finding its own required functions.

**1. Locate Target DLL:**
The loader first needs to find the base address of the required DLL (e.g., `kernel32.dll`) in its own memory space. This is achieved by traversing the **Process Environment Block (PEB)**, an internal Windows structure.
   - The PEB's address is found at a fixed offset from the `GS` segment register on x64 systems.
   - The loader then navigates `PEB -> Ldr -> InLoadOrderModuleList`, which is a linked list of all modules loaded into the process.
   - By walking this list and comparing module names, it can find the base address of any loaded DLL.

**2. Parse the DLL's Export Table:**
Once the DLL's base address is found, the loader parses its **Export Address Table (EAT)**. The EAT is a part of the PE file format that lists all functions a DLL "exports" for other programs to use.
   - The EAT contains three key arrays: function names, function addresses, and function ordinals.
   - The loader iterates through the list of function names, comparing each one to the target function name (e.g., "VirtualAlloc").

**3. Retrieve and Call the Function:**
When a name match is found, the loader uses the index of that name to look up the corresponding function address from the address array. This address is then stored in a function pointer and can be called like a normal function.

```cpp
// Simplified example from the project's api_wrappers.h
typedef PVOID (WINAPI *pVirtualAlloc)(PVOID, SIZE_T, DWORD, DWORD);

// GetApiAddr is a helper that performs steps 1 and 2
pVirtualAlloc fnVirtualAlloc = (pVirtualAlloc)GetApiAddr(L"kernel32.dll", "VirtualAlloc");

// Call the function via the resolved pointer
fnVirtualAlloc(NULL, size, MEM_COMMIT, PAGE_EXECUTE_READWRITE);
```

### Analysis

#### Strengths
*   **Evades IAT-Based Detection:** This is the technique's primary benefit. Static analysis tools and security products often flag a program as malicious simply for importing suspicious functions. By resolving these dynamically, the loader's IAT can appear completely benign, containing only a few basic imports.
*   **Foundation for Other Techniques:** The ability to parse the PEB and EAT is a foundational skill required for more advanced techniques like API Hashing and Direct Syscalls.

#### Weaknesses
*   **Revealing String Literals:** The function names ("VirtualAlloc", "CreateThread") still exist as **string literals** within the binary's `.rdata` section. An analyst can run the `strings` utility on the executable, see these names, and immediately understand the program's capabilities. (This weakness is addressed by `Code Obfuscation - String Encryption`).
*   **Does Not Evade Behavioral Detection:** This technique only hides the *static link* to the API; it does **not** hide the *call* to it. Any EDR that has placed a hook on `kernel32!VirtualAlloc` will still trigger an alert when the function is eventually called via the resolved pointer.

### Summary
Dynamic API Resolution is an essential technique for defeating static analysis based on the Import Address Table. It forces analysts and automated tools to move beyond simple IAT inspection. However, it provides **no protection against behavioral analysis or EDRs that hook user-land functions**. It serves as a crucial first layer of API obfuscation.