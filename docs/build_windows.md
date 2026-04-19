# Building on Windows

The project targets Windows PE output. On Linux you cross-compile with MinGW-w64; on Windows you compile natively with the same toolchain via **MSYS2**.

Git Bash alone does **not** include `make`, `nasm`, or a MinGW-w64 C++ compiler — install MSYS2 separately.

---

## 1. Install MSYS2

1. Download the installer from <https://www.msys2.org> and run it.
2. Accept the default install path (`C:\msys64`).
3. From Start Menu, launch **"MSYS2 MinGW64"** (the green-icon shell) — **not** "MSYS2 MSYS".
4. Run `pacman -Syu` once to sync the package database. Close and re-open the shell if prompted.

All `pacman` commands below run inside the MSYS2 MinGW64 shell.

## 2. Install Toolchain

```bash
pacman -S --needed \
    mingw-w64-x86_64-gcc \
    mingw-w64-x86_64-nasm \
    make \
    mingw-w64-x86_64-python \
    mingw-w64-x86_64-python-pip
```

## 3. Verify

```bash
x86_64-w64-mingw32-g++ --version    # or: g++ --version
nasm --version
make --version
python --version
```

If `x86_64-w64-mingw32-g++` is missing but `g++` works (some MSYS2 revisions drop the prefixed alias), either symlink it:

```bash
ln -sf /mingw64/bin/g++.exe /mingw64/bin/x86_64-w64-mingw32-g++.exe
```

or override when building:

```bash
export CC=g++
```

The Makefile uses `CC ?= x86_64-w64-mingw32-g++` so environment overrides take effect.

## 4. Install Python Dependencies

**Use a virtual environment.** MSYS2 Python enforces PEP 668 and blocks system-wide `pip install`. Even with system Python, a venv keeps project deps isolated.

From the project root:

```bash
# MSYS2 MinGW64 shell or Git Bash
cd /c/Users/<you>/Documents/GitHub/Loader-Testing-Platform
python -m venv .venv
source .venv/Scripts/activate       # Bash-style activation
pip install -r requirements.txt
```

```powershell
# PowerShell
cd C:\Users\<you>\Documents\GitHub\Loader-Testing-Platform
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```cmd
:: cmd.exe
cd C:\Users\<you>\Documents\GitHub\Loader-Testing-Platform
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

On future sessions, just re-activate the venv before building — don't re-run `pip install`.

> If you see `error: externally-managed-environment` you're calling MSYS2 `pip` outside a venv. Create the venv as above.

## 5. Build

```bash
python cli.py -s shellcodes/dummy.bin --build-only
```

Output: `build/bin/payload_<timestamp>.exe`.

Full flags work the same as on Linux (see main [README](../README.md)).

## 6. Running Outside MSYS2 Shell

You don't have to stay in the MSYS2 MinGW64 shell. The toolchain is just `.exe` files in known directories — you can build from **Git Bash, PowerShell, or cmd** as long as those directories are on `PATH`.

**Per-session (Git Bash):**

```bash
export PATH=$PATH:/c/msys64/mingw64/bin:/c/msys64/usr/bin
python cli.py -s shellcodes/dummy.bin --build-only
```

**Per-session (PowerShell):**

```powershell
$env:Path += ";C:\msys64\mingw64\bin;C:\msys64\usr\bin"
python cli.py -s shellcodes/dummy.bin --build-only
```

**Persistent (Windows system PATH):** *Start → Edit environment variables for your account → Path → Edit → New →* add `C:\msys64\mingw64\bin` and `C:\msys64\usr\bin`. Any shell spawned afterwards (including Python `subprocess`) sees the tools.

**Persistent (Git Bash only):** append the `export PATH=...` line to `~/.bashrc`.

Recommended: persistent Windows PATH. MSYS2 Python won't be added (good — keep system/venv Python priority), but `make`/`nasm`/`x86_64-w64-mingw32-g++` become globally available.

---

## Local Smoke Test (no VM)

To verify the build end-to-end on the same Windows host — no KVM required:

1. **Prepare a localhost shellcode.** The shipped `shellcodes/default_localhost.bin` is a reverse TCP shell to `127.0.0.1:4444`.

2. **Start a listener.** MSYS2 can install `ncat` via nmap:
   ```bash
   pacman -S --needed mingw-w64-x86_64-nmap
   ncat -lvp 4444
   ```
   Or pure-Python fallback (no extra packages):
   ```bash
   python -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',4444)); s.listen(1); c,_=s.accept(); print('[+] Connected:', c.getpeername()); \
   import sys; sys.stdout.flush()
   while True:
       d=c.recv(4096)
       if not d: break
       sys.stdout.buffer.write(d); sys.stdout.flush()"
   ```

3. **Build + run:**
   ```bash
   python cli.py -s shellcodes/default_localhost.bin --build-only -t3 aes
   ./build/bin/payload_<timestamp>.exe
   ```

   A callback on the listener means the full pipeline (encrypt → decrypt → exec) works.

---

## VM Testing on Windows

`controller/modules/vm_manager.py` drives VMs via `virsh` (KVM/libvirt), which is Linux-only. Options on a Windows host:

- Build locally, transfer the .exe to a Linux host for VM testing.
- Run the whole platform inside WSL2 — VM cycle won't work (no nested KVM on WSL), but build + manual execution in Windows does.
- Use a Linux VM as the controller host.

A native Hyper-V / VMware backend is not currently implemented.

---

## Common Issues

| Symptom | Fix |
|---------|-----|
| `make: command not found` | Wrong shell. Use **MSYS2 MinGW64**, not Git Bash or MSYS2 MSYS. |
| `x86_64-w64-mingw32-g++: command not found` | `export CC=g++` or create the symlink above. |
| `UnicodeEncodeError: 'charmap' codec ...` | Already fixed in `cli.py` (stdout forced to UTF-8). If still failing, set `export PYTHONIOENCODING=utf-8`. |
| `No module named 'tinyaes'` | `pip install -r requirements.txt` for the *same* Python that runs `cli.py`. Verify with `which python`. |
| Build succeeds but `.exe` does nothing | Check the shellcode is valid PE-independent position-independent code. Try `--debug` flag and look at `DEBUG_MSG` output. |
