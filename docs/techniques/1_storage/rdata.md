# Storage Technique: .rdata section

| | |
| :--- | :--- |
| **ID** | S1 |
| **Category** | Payload Storage |
| **Complexity** | Low |
| **Primary Use** | Embed the payload directly into the loader executable. |

### Goal
To store the shellcode payload within the compiled executable file itself, making the loader a self-contained, single-file implant.

### Mechanism
This technique leverages how compilers handle initialized global constant data.

**1. At Build Time (in `core_engine.py`):**
The Python script reads the shellcode (which is often encrypted first) and converts it into a C++ byte array declaration.

```python
# Example: Converting binary data to a C++ array
# shellcode_data = b"\xDE\xAD\xBE\xEF..."
shell_array = "unsigned char shellcode[] = {"
shell_array += ", ".join([f"0x{byte:02x}" for byte in shellcode_data])
shell_array += "};"
```

This generated code is then inserted into the source file before compilation.

**2. During Compilation:**
The compiler sees the `unsigned char shellcode[] = {...};` declaration. Because it is a global, initialized array, the compiler places the entire byte array into one of the PE file's data sections.
-   If declared as `const`, it goes into the **`.rdata` (Read-Only Data)** section.
-   If not `const`, it typically goes into the **`.data` (Initialized Data)** section.

The result is that the shellcode becomes a static part of the final `.exe` file.

**3. At Runtime (in the C++ Loader):**
The loader can access the shellcode simply by referencing the `shellcode` array variable. The program's memory manager automatically loads the `.rdata` or `.data` section into memory when the executable is launched.

```cpp
// The shellcode is directly accessible
// Decrypt it (if needed)
DecryptXOR(shellcode, sizeof(shellcode), key);

// Pass it to an injection function
Inject_Classic(shellcode, sizeof(shellcode));
```

### Analysis

#### Strengths
*   **Self-Contained & Portable:** The loader is a single `.exe` file that contains everything it needs. There are no external dependencies, making it easy to deploy and execute. This is the most common and reliable storage method.
*   **Simple & Reliable:** Accessing the payload is as simple as referencing a variable. There is no need for complex API calls to read from resources or remote locations, which reduces potential points of failure.

#### Weaknesses
*   **Vulnerable to Static Analysis (if unencrypted):** If the raw, unencrypted shellcode is stored this way, it is trivial for an AV scanner to find its signature by scanning the `.rdata` or `.data` section of the file.
*   **Increases File Size:** The size of the final executable increases directly with the size of the shellcode.
*   **Inflexible:** To update the shellcode, the entire loader must be recompiled. This is less flexible than methods that load the payload from an external source (like a resource file or a remote URL).

### Summary
Storing the payload in the `.rdata` or `.data` section is the **foundational storage technique** for most shellcode loaders. It is simple, reliable, and creates a portable, self-contained executable.

However, it **must** be paired with a transformation technique like **XOR or AES encryption (T1, T2)**. Storing an unencrypted payload in this manner is the easiest way to get caught by static antivirus signatures. Its primary role is to provide a container for the *encrypted* payload within the executable file.