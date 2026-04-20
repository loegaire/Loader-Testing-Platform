<#
.SYNOPSIS
    One-time setup script to prepare a Windows guest for the Loader
    Testing Platform. Run INSIDE the guest before taking the clean
    snapshot. Must run as Administrator.

.DESCRIPTION
    After this script completes:
      1. Shutdown the guest cleanly.
      2. Take a snapshot and name it 'clean_snapshot' (see
         CLEAN_SNAPSHOT_NAME in controller/config.py).
      3. From then on, every test run reverts to this snapshot.

    Idempotent: safe to re-run if you need to update baseline settings.

.CONFIGURATION
    GUEST_USER and GUEST_PASSWORD must match controller/config.py.
#>

[CmdletBinding()]
param(
    [string]$TesterUser = "tester",
    [string]$TesterPassword = "123456"
)

$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Msg) Write-Host "[setup] $Msg" -ForegroundColor Cyan }

# --- 1. Auto-login -----------------------------------------------------------
# The payload launcher (vm_manager.launch_interactive) schedules the payload
# into the logged-in user's interactive session. Auto-login ensures that
# session exists immediately after snapshot revert, with no manual login.
Write-Step "Enabling auto-login for '$TesterUser'"

$winlogon = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
Set-ItemProperty -Path $winlogon -Name "AutoAdminLogon"     -Value "1"
Set-ItemProperty -Path $winlogon -Name "DefaultUserName"    -Value $TesterUser
Set-ItemProperty -Path $winlogon -Name "DefaultPassword"    -Value $TesterPassword
# Clear any stale domain so WinLogon treats DefaultUserName as local
Set-ItemProperty -Path $winlogon -Name "DefaultDomainName"  -Value ""


# --- 2. Sysmon service -------------------------------------------------------
# Platform keeps Sysmon running across reboots; per-run config updates are
# applied by the harness. Confirm the service exists and is set to autostart.
Write-Step "Ensuring Sysmon service is installed and autostart"

if (-not (Get-Service -Name Sysmon -ErrorAction SilentlyContinue)) {
    Write-Warning "Sysmon service is not installed."
    Write-Warning "On Windows 11 24H2+ / Server 2025: enable 'System Monitor' in Optional Features,"
    Write-Warning "or install classic Sysinternals Sysmon manually."
} else {
    Set-Service Sysmon -StartupType Automatic
    Start-Service Sysmon -ErrorAction SilentlyContinue
}


# --- 3. Baseline Sysmon rules -----------------------------------------------
# Apply the shipped rules as baseline so a bare snapshot revert already has
# sane filters. Each test run still pushes the latest config from host.
$sysmonCfg = "C:\Users\$TesterUser\Desktop\sysmon_loader_config.xml"
if (Test-Path $sysmonCfg) {
    Write-Step "Applying baseline Sysmon config"
    & sysmon.exe -c $sysmonCfg | Out-Null
} else {
    Write-Warning "Sysmon config not found at $sysmonCfg. Skipping baseline apply."
    Write-Warning "Copy log_collectors/sysmon_loader_config.xml to that path, then re-run."
}


# --- 4. Defender cloud / sample submission ----------------------------------
# Prevent cloud-driven signature drift across test sessions: a sample that
# succeeds at t1 would otherwise leak to Microsoft cloud and potentially be
# caught at t2 with the same technique. Also disables automatic sample
# submission so our test binaries never leave the host.
Write-Step "Disabling Defender MAPS + sample submission"

try {
    Set-MpPreference -MAPSReporting Disabled -ErrorAction Stop
    Set-MpPreference -SubmitSamplesConsent NeverSend -ErrorAction Stop
    Write-Host "       Defender cloud lookup: off"
    Write-Host "       Sample submission:     off"
} catch {
    Write-Warning "Failed to set Defender preferences: $_"
    Write-Warning "You may need to disable Tamper Protection or run as SYSTEM."
}


# --- 5. Record baseline for paper reproducibility ---------------------------
# Write Defender/Sysmon versions to a text file on the desktop for later
# reference. Section 5.4 (Reproducibility) of the paper refers to these
# identifiers to pin a run to a specific telemetry configuration.
Write-Step "Recording guest fingerprint"

$fingerprint = "C:\Users\$TesterUser\Desktop\guest_fingerprint.txt"
$lines = @()
$lines += "--- Guest fingerprint (captured $(Get-Date -Format o)) ---"
$lines += "Windows build:      $([System.Environment]::OSVersion.Version)"
try {
    $mp = Get-MpComputerStatus
    $lines += "Defender engine:    $($mp.AMEngineVersion)"
    $lines += "Defender platform:  $($mp.AMProductVersionNumber)"
    $lines += "Signature version:  $($mp.AntivirusSignatureVersion)"
    $lines += "Signature date:     $($mp.AntivirusSignatureLastUpdated)"
} catch {
    $lines += "Defender status:    not available"
}
try {
    $sm = Get-Service Sysmon -ErrorAction Stop
    $lines += "Sysmon service:     $($sm.Status)"
} catch {
    $lines += "Sysmon service:     not installed"
}
$lines | Set-Content -Path $fingerprint -Encoding UTF8


Write-Host ""
Write-Host "[setup] Done. Next steps:" -ForegroundColor Green
Write-Host "  1. Shutdown this VM"
Write-Host "  2. virsh snapshot-create-as <domain> clean_snapshot"
Write-Host "  3. From Linux host, run a test cycle to verify"
