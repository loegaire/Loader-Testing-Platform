# Lab Setup Guide — Windows VM on KVM

This guide walks through creating a Windows VM for automated payload testing. The platform uses **KVM/libvirt** for VM management and **SSH** (via `sshpass`) for guest interaction.

**End result:** a Windows VM with OpenSSH Server, registered in `config.py`, with a `clean_snapshot` that the test engine can revert to.

**Time required:** ~30 minutes.

---

## Prerequisites

A Linux host with:

- CPU virtualization enabled (VT-x / AMD-V), should have Desktop GUI (I used mate)
- KVM, libvirt, virt-manager installed
- `sshpass` installed
- A Windows 10/11 ISO
- VirtIO drivers ISO

Install everything:

```bash
# Fedora
sudo dnf install -y qemu-kvm libvirt virt-manager virt-install sshpass

# Debian/Ubuntu
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients \
    virtinst virt-manager sshpass
```

Download VirtIO drivers:

```bash
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso
```

Ensure KVM networking is active:

```bash
virsh -c qemu:///system net-list
# Should show "default" as active. If not:
# virsh -c qemu:///system net-start default
# virsh -c qemu:///system net-autostart default
```

> **Important:** Always use `virsh -c qemu:///system` (not plain `virsh`), because VMs created through `virt-manager` use the system connection. Plain `virsh` defaults to `qemu:///session` and won't see your VMs.

---

## Step 1: Create VM in virt-manager

1. Open **virt-manager** → **Create a new virtual machine**
2. Select **Local install media (ISO)** → browse to your Windows ISO
3. Set **RAM: 4096 MB**, **CPUs: 2**
4. Set **Disk: 60 GB**
5. **Check "Customize configuration before install"** before clicking Finish

In the customization screen:

- **Add Hardware → Storage → Device type: CDROM** → select `virtio-win.iso`
- Click on the main **Disk** → change **Disk bus** to **VirtIO**
- Click on **NIC** → change **Device model** to **virtio**
- Click **Begin Installation**

---

## Step 2: Install Windows

### Load VirtIO drivers during install

When Windows asks you to select a drive, it won't see the VirtIO disk:

1. Click **"Load driver"** → **Browse**
2. Navigate to the VirtIO CD → `viostor\w11\amd64` (or `w10` for Win10)
3. Select and load → the disk appears
4. Continue installation normally

### Bypass OOBE network requirement (Win11)

Windows 11 forces you to connect to the internet during setup. To skip:

1. Press **Shift + F10** to open Command Prompt
2. Type `oobe\bypassnro` and press Enter
3. PC reboots → now you'll see **"I don't have internet"** → **"Continue with limited setup"**

### Create the test user

- Create a **Local Account** (not Microsoft account)
- Username: `tester`, Password: `123456` (or whatever you set in `config.py`)
- This account will have Administrator privileges by default on a fresh install

---

## Step 3: Install VirtIO network driver

After Windows boots, you'll have no network because the VirtIO NIC driver isn't loaded yet.

1. Open **Device Manager** (right-click Start → Device Manager)
2. Find **Ethernet Controller** with a yellow warning icon
3. Right-click → **Update driver** → **Browse my computer for drivers**
4. Browse to the VirtIO CD → select `NetKVM\w11\amd64` (or `w10`)
5. Install the driver

Verify: open PowerShell and run `ipconfig` — you should now see an Ethernet adapter with a DHCP address.

> **Tip:** You can also install all VirtIO drivers at once by running `virtio-win-gt-x64.msi` from the VirtIO CD.

---

## Step 4: Set a static IP

The test engine needs a predictable IP. Open PowerShell (Admin):

```powershell
# Check your adapter name first
Get-NetAdapter
# Usually "Ethernet" — adjust below if different

# Remove existing DHCP config
Remove-NetIPAddress -InterfaceAlias "Ethernet" -Confirm:$false
Remove-NetRoute -InterfaceAlias "Ethernet" -Confirm:$false

# Set static IP
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.122.101 -PrefixLength 24 -DefaultGateway 192.168.122.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 8.8.8.8
```

Verify from host:

```bash
ping 192.168.122.101
```

---

## Step 5: Install & configure OpenSSH Server

On the Windows VM, PowerShell (Admin):

```powershell
# Install OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start and enable on boot
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

# Allow SSH through firewall
New-NetFirewallRule -Name "SSH" -DisplayName "OpenSSH Server" `
    -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

Verify from host:

```bash
sshpass -p '123456' ssh -o StrictHostKeyChecking=no tester@192.168.122.101 "echo hello"
# Should print "hello" with no errors
```

If it doesn't work, check:
- Is `sshd` running? (`Get-Service sshd` on VM)
- Is firewall rule active? (`Get-NetFirewallRule -Name SSH` on VM)
- Can you ping the VM? (`ping 192.168.122.101` from host)

---

## Step 6: Install Sysmon (optional, recommended)

Sysmon provides detailed execution logs for detection analysis.

On the VM, PowerShell (Admin):

```powershell
Invoke-WebRequest -Uri "https://download.sysinternals.com/files/Sysmon.zip" -OutFile "$env:TEMP\Sysmon.zip"
Expand-Archive "$env:TEMP\Sysmon.zip" -DestinationPath "$env:TEMP\Sysmon" -Force
& "$env:TEMP\Sysmon\sysmon64.exe" -accepteula -i
```

---

## Step 7: Configure security products

**For a Defender-only VM:**

- Ensure Windows Defender Real-time Protection is **ON**
- Run Windows Update to get latest signatures
- Keep Windows Firewall on (SSH rule from Step 5 will persist)

**For third-party AV/EDR:**

- Install the product
- Update virus definitions

**For all VMs — disable sample submission:**

- **Automatic Sample Submission** → OFF
- **Cloud Protection** → OFF
- **Telemetry / Data Sharing** → OFF

This prevents your test payloads from being uploaded to vendor cloud services.

---

## Step 8: Create snapshot

Shut down the VM cleanly, then create the snapshot:

```bash
virsh -c qemu:///system shutdown <domain-name>
# Wait for VM to fully shut down
virsh -c qemu:///system list --all
# Confirm state is "shut off"

virsh -c qemu:///system snapshot-create-as <domain-name> clean_snapshot "Ready for testing"
```

> Replace `<domain-name>` with your VM name (e.g., `win11-01`). Check with `virsh -c qemu:///system list --all`.

---

## Step 9: Register VM in config.py

Edit `controller/config.py`:

```python
# Guest SSH
GUEST_USER = "tester"
GUEST_PASSWORD = "123456"

# VMs Configuration (KVM)
VMS_CONFIG = {
    "Windows Defender": {
        "domain": "win11-01",                # virsh domain name
        "guest_ip": "192.168.122.101",       # static IP set in Step 4
        "log_collector_host": os.path.join(PROJECT_ROOT, "log_collectors", "collect_defender.ps1")
    },
    # Add more VMs here, e.g.:
    # "Kaspersky": {
    #     "domain": "win11-kaspersky",
    #     "guest_ip": "192.168.122.102",
    #     "log_collector_host": os.path.join(PROJECT_ROOT, "log_collectors", "collect_all.ps1")
    # },
}
```

---

## Step 10: Test the full pipeline

```bash
python3 cli.py -s shellcodes/dummy.bin -t3 none -t5 local -v "Windows Defender" --debug
```

Expected output:

```
[INFO] - Compiling with flags: ...
[INFO] - Build Success: build/bin/payload_XXXXX.exe
[INFO] - === Starting Test Cycle on Windows Defender ===
[INFO] - Reverting to snapshot: clean_snapshot
[INFO] - Starting VM...
[INFO] - Waiting for guest SSH...
[INFO] - VM is ready!
[INFO] - Deploying: payload_XXXXX.exe -> C:\Users\tester\Desktop\payload.exe
...
```

---

## Adding More VMs

To test against multiple AV products:

1. Clone an existing VM: `virt-clone -c qemu:///system --original win11-01 --name win11-kaspersky --auto-clone`
2. Start it, change the static IP (e.g., `192.168.122.102`)
3. Install the AV/EDR product
4. Disable sample submission
5. Shut down and snapshot: `virsh -c qemu:///system snapshot-create-as win11-kaspersky clean_snapshot`
6. Add to `VMS_CONFIG` in `config.py`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `virsh list` shows nothing | Use `virsh -c qemu:///system list --all` |
| VM has no network adapter | Install VirtIO NIC driver from `NetKVM\w11\amd64` on VirtIO CD |
| Can't attach CDROM to running VM | Shut down VM first, then add CDROM, then start |
| Windows OOBE requires internet | Press Shift+F10, type `oobe\bypassnro` |
| `ping` VM doesn't work | Check static IP is set, check VM has network driver |
| SSH connection refused | Check `sshd` service is running, firewall rule exists for port 22 |
| SSH `Connection reset by peer` | Run `sshd -d` on VM for debug output, check host keys exist |
| `sshpass: command not found` | Install: `sudo dnf install sshpass` or `sudo apt install sshpass` |
| `virsh snapshot-revert` fails | Check snapshot exists: `virsh -c qemu:///system snapshot-list <domain>` |
| SCP file gets deleted on arrival | AV blocked it — this is a valid test result ("Transfer Blocked") |
