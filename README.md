Here is the English translation of your repository documentation, formatted as a **README.md** file suitable for GitHub.

-----

# Automated FUD Payload Testing Platform

*(Research & Education Only)*

## 🎯 Project Goals

This is a **research and educational** project designed to build an **automated platform** for testing and evaluating the effectiveness of **evasion techniques** used in **shellcode loaders**.

**Key Objectives:**

1.  **Evaluate detection capabilities** of **Antivirus (AV)** and **Endpoint Detection & Response (EDR)** solutions against various encryption and injection techniques.
2.  Provide a **dashboard** that helps **Red Teams** quickly test evasion techniques and assists **Blue Teams** in collecting logs and analyzing behavior.

> ⚠️ **Warning:** This tool is strictly for **research and training purposes** within an **isolated lab environment**. Do not use it for any unauthorized offensive activities.

-----

## 💡 Benefits for Red & Blue Teams

  * **For Red Teams:**
      * Rapidly test multiple **obfuscation and injection** techniques on the same shellcode.
      * Measure the success rate of specific techniques to optimize **AV/EDR bypass** tactics.
  * **For Blue Teams:**
      * Automate the collection of alert logs and analyze the actual behavior of loaders.
      * Improve detection capabilities and tune monitoring policies and signatures.

-----

## 🏗️ System Architecture

The system operates as an **Internal Dashboard**, consisting of 4 main components:

```
[Web Dashboard] → [Core Engine] → [Loader Builder] → [VMware VMs]
```

| Component | Role |
| :--- | :--- |
| **Web Interface (Frontend)** | Flask-based local UI for uploading shellcode, selecting techniques, and choosing VMs. |
| **Core Engine** | Python module (`core_engine.py`) that orchestrates the workflow: build, deploy, execute, log. |
| **Loader Builder** | C++/MinGW-64 source code that packages the shellcode + techniques into an `.exe` file. |
| **VMware Hypervisor** | Runs target Windows VMs with AV/EDR, providing snapshots for state resets. |

-----

## ⚡ Workflow

1.  **Configure & Upload:** User uploads a shellcode file (`.bin`) and selects options via the Dashboard.
2.  **Build Payload:** The Core Engine calls the `builder` to compile the C++ loader into a unique executable.
3.  **Deploy & Execute:** The payload is automatically transferred to the selected VMs and executed.
4.  **Collect & Report:** The system gathers detection logs and execution status, then generates a report on the Dashboard.

-----

## 📂 Directory Structure

```
FUD_Testing_Platform/
├── app.py              # Flask Backend for Web UI
├── core_engine.py      # Main logic: build, deploy, log
├── requirements.txt    # Python dependencies
├── Makefile            # C++ compilation configuration
├── .gitignore          # Ignored files
├── src/                # C++ loader source code
├── templates/          # HTML templates for Flask
├── shellcodes/         # Sample shellcodes
├── uploads/            # User uploaded shellcodes
├── output/             # Compiled .exe payloads
└── test_logs/          # Result logs from VMs
```

-----

## 🔧 Technologies Used

  * **Python 3.8+:** Flask web dashboard, Core Engine automation.
  * **C++ (MinGW-w64):** Loader development, utilizing Windows APIs.
  * **HTML/Jinja2:** Simple user interface.
  * **VMware Workstation/Player:** Manages target Windows VMs.
  * **vmrun CLI:** Controls snapshots, file uploads, and command execution within VMs.

-----

## ⚙️ Prerequisites

1.  **Python 3.8+** and `pip`.
2.  **VMware Workstation/Player** and the `vmrun` CLI tool (included with VMware installation).
3.  **MinGW-w64** for compiling the C++ loader.
4.  **Virtual Machines (VMs):**
      * Windows OS (10/11) with **VMware Tools** installed.
      * Target **AV/EDR** installed (Defender, SentinelOne, CrowdStrike, OpenEDR, etc.).
      * Each VM must have a snapshot named **`clean_snapshot`** to reset state after tests.
5.  **Storage:** Minimum **100 GB** recommended to store multiple VMs and snapshots.

-----

## 🚀 Installation Guide

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd FUD_Testing_Platform
    ```
2.  **Create virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # On Windows
    pip install -r requirements.txt
    ```
3.  **Configure Virtual Machines:**
      * Prepare Windows VMs and snapshots as described above.
      * Update `.vmx` paths and login credentials in `core_engine.py` or a separate config file.
      * **Disable "Sample Submission"** in the AV to prevent leaking payloads.

-----

## 💻 Usage

1.  **Start the Dashboard:**
    ```bash
    python app.py
    ```
    Open your browser and navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)
2.  **On the Interface:**
      * Upload a `.bin` shellcode file.
      * Select encryption & injection techniques.
      * Select the target VMs.
      * Click **Run Test**.
3.  **View Results:**
      * The Dashboard will display the status (SUCCESS/FAILED) and detailed logs for each environment.
      * Logs are also saved in the `test_logs/` directory for later analysis.

-----

## 📅 Roadmap

The project is divided into key phases, focusing on platform foundation, technique research, and advanced analysis.

### ✅ Phase 1: Platform Foundation (Completed)

This phase focused on building the core framework and automation pipeline.

  * **Control Engine (`core_engine.py`):** Logic for `vmrun` management (revert, start, stop), payload building, and a simple C2 Listener.
  * **CLI (`cli.py`):** Command-line interface for flexible testing configuration.
  * **Basic Loader (C++):** Implemented **XOR Encryption** and **Classic Injection (`CreateThread`)**.
  * **Initial Lab Environment:** Configured **Windows Defender** + **Sysmon** with automated log collection scripts.
  * **Pipeline Automation:** Fully automated chain: **Build → Revert VM → Start VM → Deploy → Execute → Collect Logs → Report**.

### 🚀 Phase 2: Technique Research & Lab Expansion (Next Steps)

Focuses on developing and evaluating new evasion techniques.

  * **🔬 Evasion Technique R\&D:**
      * **Encryption:** Integrate **AES-256**.
      * **Injection:** Implement **Process Hollowing** and **APC Injection**.
      * **Anti-Analysis:** Implement **Anti-Sandbox** (RAM/CPU checks, `Sleep`) and **API Hashing**.
  * **🧪 Lab Expansion:**
      * Configure a VM with a **third-party EDR** (e.g., SentinelOne, Bitdefender).
      * Develop custom log collection scripts for the new EDR environment.
  * **🖥️ UI/UX Development:**
      * Build a basic Flask **Web Dashboard** for configuration.
      * Design a results page for visual data presentation.

### 🌟 Phase 3: Advanced Analysis (Long-term Vision)

Focuses on actionable insights and platform maturity.

  * **📊 Analysis & Reporting:**
      * Enhance log collection for granular event details.
      * Build a **rule-based analysis engine** to identify behavior patterns.
      * Data visualization (charts comparing technique effectiveness).
  * **🖥️ Platform Upgrades:**
      * Real-time progress tracking via AJAX/JS.
      * History management to compare past test results.

-----

## 🔒 Scope & Limitations

  * All testing is performed **strictly within an internal environment**.
  * Generated payloads **must not be distributed** to the Internet.
  * This is **not an attack tool**; it serves only defensive research (Blue Team) and testing (Red Team) purposes.

-----

## References

### I. Overview of Evasion & Malware Development

  * **MITRE ATT\&CK® – Defense Evasion**
    [https://attack.mitre.org/tactics/TA0005/](https://attack.mitre.org/tactics/TA0005/)
    The definitive knowledge base for attack tactics. The *Defense Evasion* section is essential reading.
  * **ired.team – Code Injection**
    [https://www.ired.team/offensive-security/code-injection-process-injection](https://www.ired.team/offensive-security/code-injection-process-injection)
    Comprehensive collection of code injection techniques with concise examples.
  * **Windows Internals, Part 2 – Mark Russinovich et al.**
    Deep dive into how Windows manages processes, threads, memory, and APC queues.

### II. Injection Techniques

  * **Process Hollowing – A Technical Analysis**
    [https://www.elastic.co/blog/a-technical-analysis-of-process-hollowing](https://www.elastic.co/blog/a-technical-analysis-of-process-hollowing)
    Step-by-step analysis of creating suspended processes and overwriting memory.
  * **Asynchronous Procedure Calls (APC) Injection**
    [https://www.ired.team/offensive-security/code-injection-process-injection/apc-injection-for-dll-injection](https://www.ired.team/offensive-security/code-injection-process-injection/apc-injection-for-dll-injection)
    Explains abusing thread APC queues for indirect code execution.
  * **Microsoft Documentation (Classic Injection)**
      * [CreateRemoteThread](https://docs.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createremotethread)
      * [VirtualAllocEx](https://docs.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualallocex)

### III. Obfuscation & Evasion

  * **API Hashing – Maldev Academy**
    [https://maldevacademy.com/posts/api-hashing/](https://maldevacademy.com/posts/api-hashing/)
    Detailed guide on API Hashing to avoid IAT hooking and static analysis.
  * **Anti-Sandbox & Anti-Analysis Techniques**
    [The Ultimate Anti-Reversing Reference (PDF)](https://anti-reversing.com/Downloads/Anti-Reversing/The_Ultimate_Anti-Reversing_Reference.pdf)
    Extensive list of techniques to detect debuggers, VMs, and sandboxes.
  * **Advanced Encryption Standard (AES) – FIPS 197**
    [https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.197.pdf](https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.197.pdf)

### IV. Monitoring & Logging (Sysmon)

  * **Sysmon – Microsoft Sysinternals**
    [https://docs.microsoft.com/en-us/sysinternals/downloads/sysmon](https://docs.microsoft.com/en-us/sysinternals/downloads/sysmon)
  * **Sysmon Configuration Project – SwiftOnSecurity**
    [https://github.com/SwiftOnSecurity/sysmon-config](https://github.com/SwiftOnSecurity/sysmon-config)
    Widely used configuration repo for hunting and detection.
  * **SANS DFIR – Sysmon Cheatsheet**
    [https://www.sans.org/posters/sysmon-threat-hunting-cheatsheet/](https://www.sans.org/posters/sysmon-threat-hunting-cheatsheet/)
