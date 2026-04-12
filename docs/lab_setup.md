# Virtual Lab Setup Guide (KVM/Windows)

This guide outlines the standard procedure for provisioning Windows VMs on KVM for automated payload testing. The workflow relies on a **"Golden Image"** architecture to easily scale multiple AV/EDR testing environments.

⚠️ **EXECUTION RULES:** 
- 🐧 **[Linux Host]**: Run these commands in your Linux terminal.
- 🪟 **[Windows Guest]**: Run these commands inside an **Elevated PowerShell (Admin)** on the VM.

---

## Prerequisites (Linux Host)

Install the required KVM packages, utilities, and VirtIO drivers.

🐧 **[Linux Host]**
```bash
# Fedora/RHEL
sudo dnf install -y qemu-kvm libvirt virt-manager virt-install sshpass
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Debian/Ubuntu
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients virtinst virt-manager sshpass
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso
```

---

## Phase 0: Base VM Creation & OS Install

1. Open `virt-manager` and create a new VM (4GB RAM, 2 CPUs, 60GB Disk).
2. **Important:** Before finishing, check *"Customize configuration before install"*.
   - Add the `virtio-win.iso` as a second CDROM.
   - Change the OS Disk bus to **VirtIO**.
   - Change the NIC Device model to **virtio**.
3. **During Windows Install:**
   - Click "Load driver" and browse to `viostor\w11\amd64` to detect the hard drive.
   - To bypass Windows 11 internet requirement: Press `Shift+F10`, type `oobe\bypassnro`, and reboot.
   - Create a local admin account (e.g., `tester` / `password`).
4. **Post-Install:** Download and install [Spice Guest Tools](https://www.spice-space.org/download/windows/spice-guest-tools/spice-guest-tools-latest.exe) to fix display and network drivers automatically.

---

## Phase 1: The "Golden Image" (Do this once)

Boot up your fresh Windows VM. We will configure it to allow automated SSH control and telemetry logging.

### 1. Set Static IP & OpenSSH (Guest VM)
A predictable IP is required for the Python controller.
🪟 **[Windows Guest]**
```powershell
# 1. Set Static IP (Adjust InterfaceAlias and IP as needed)
Remove-NetIPAddress -InterfaceAlias "Ethernet" -Confirm:$false
Remove-NetRoute -InterfaceAlias "Ethernet" -Confirm:$false
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.122.101 -PrefixLength 24 -DefaultGateway 192.168.122.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 8.8.8.8

# 2. Install and Start OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service -Name sshd -StartupType 'Automatic'
Start-Service sshd
```

### 2. Critical OS Tweaks (Guest VM)
Disable UAC restrictions for SSH (crucial for log extraction) and temporarily disable protections.
🪟 **[Windows Guest]**
```powershell
# Disable UAC for Remote/SSH Connections 
reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f

# Disable Windows Firewall & Defender Real-time Protection temporarily
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
Set-MpPreference -DisableRealtimeMonitoring $true
```

### 3. Install Telemetry - Sysmon (Guest VM)
🪟 **[Windows Guest]**
```powershell
Invoke-WebRequest -Uri "https://live.sysinternals.com/Sysmon64.exe" -OutFile "C:\Users\Public\Sysmon64.exe"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml" -OutFile "C:\Users\Public\sysmonconfig.xml"
C:\Users\Public\Sysmon64.exe -accepteula -i C:\Users\Public\sysmonconfig.xml
```

### 4. Create Base Snapshot (Linux Host)
Shut down the VM cleanly from within Windows. Then, take the base snapshot.
🐧 **[Linux Host]**
```bash
# Verify the VM is shut off
virsh -c qemu:///system list --all

# Take the snapshot (Replace 'win11-base' with your VM name)
virsh -c qemu:///system snapshot-create-as --domain win11-base --name "clean_install" --description "Base OS with tools, no AV"
```

---

## Phase 2: The "Test VMs" (Repeat per AV/EDR)

We will clone the Golden Image to create specific testing environments.

### 1. Clone the Golden Image (Linux Host)
🐧 **[Linux Host]**
```bash
virt-clone -c qemu:///system --original win11-base --name win11-defender --auto-clone
virsh -c qemu:///system start win11-defender
```

### 2. Configure Security Product (Guest VM)
Log into the new VM. If setting up **Windows Defender**, re-enable protection but strictly disable OPSEC-leaking features (Cloud, Auto-submission).
🪟 **[Windows Guest]**
```powershell
# 1. Re-enable Protection & Firewall
Set-MpPreference -DisableRealtimeMonitoring $false
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# 2. OPSEC: Disable Cloud Protection & Automatic Sample Submission
Set-MpPreference -MAPSReporting Disable
Set-MpPreference -SubmitSamplesConsent NeverSend
Set-MpPreference -DisableBlockAtFirstSight $true

# 3. Update Virus Definitions
Update-MpSignature
```
*(For 3rd-party EDRs, install their agents manually and disable Cloud/Telemetry via their GUI).*

### 3. Create Testing Snapshot (Linux Host)
Reboot the VM once, then shut it down cleanly. 
🐧 **[Linux Host]**
```bash
# Take the testing snapshot (Must be named EXACTLY 'clean_snapshot')
virsh -c qemu:///system snapshot-create-as --domain win11-defender --name "clean_snapshot" --description "Ready for automated testing"
```

---

## Phase 3: Integration

Register your new VM in the testing framework by editing `controller/config.py`:

```python
# VMs Configuration (KVM)
VMS_CONFIG = {
    "Windows Defender": {
        "domain": "win11-defender",          # virsh domain name
        "guest_ip": "192.168.122.101",       # static IP set in Phase 1
        "log_collector_host": os.path.join(PROJECT_ROOT, "log_collectors", "collect_defender.ps1")
    },
    # Add cloned VMs here:
    # "Kaspersky": {
    #     "domain": "win11-kaspersky",
    #     "guest_ip": "192.168.122.102",
    #     ...
    # },
}
```