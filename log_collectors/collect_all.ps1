<#
.SYNOPSIS
    Collects detection telemetry from Windows Defender and Sysmon,
    organized by pipeline stage for the Loader Testing Platform.
.DESCRIPTION
    Queries Windows Event Log for:
    - Windows Defender detections (Event 1116/1117/1118)
    - Sysmon events mapped to loader pipeline stages:
      L1 (Storage):   Event 11 (FileCreate), Event 3 (NetworkConnect), Event 22 (DNS)
      L2 (Allocation): Event 10 (ProcessAccess)
      L5 (Execution): Event 1 (ProcessCreate), Event 8 (CreateRemoteThread), Event 25 (ProcessTampering)
    Outputs structured text and CSV for automated parsing.
.OUTPUTS
    C:\Users\<CurrentUser>\Desktop\detection_log.txt  (human-readable)
    C:\Users\<CurrentUser>\Desktop\detection_log.csv  (machine-parseable)
#>

param(
    [int]$Minutes = 5
)

# --- Configuration ---
$logFile = "$env:USERPROFILE\Desktop\detection_log.txt"
$csvFile = "$env:USERPROFILE\Desktop\detection_log.csv"

$EndTime = Get-Date
$StartTime = $EndTime.AddMinutes(-$Minutes)

# Clean previous logs
if (Test-Path $logFile) { Remove-Item $logFile }
if (Test-Path $csvFile) { Remove-Item $csvFile }

# CSV header
"Timestamp,Source,EventID,Stage,Description,Details" | Out-File -FilePath $csvFile -Encoding utf8

# --- Helper function ---
function Write-Log {
    param([string]$Text)
    $Text | Out-File -FilePath $logFile -Encoding utf8 -Append
}

function Write-Csv {
    param([string]$Timestamp, [string]$Source, [int]$EventID, [string]$Stage, [string]$Description, [string]$Details)
    $escaped = $Details -replace '"','""'
    "`"$Timestamp`",`"$Source`",$EventID,`"$Stage`",`"$Description`",`"$escaped`"" | Out-File -FilePath $csvFile -Encoding utf8 -Append
}

# =====================================================================
# Section 1: Windows Defender Detections
# =====================================================================

Write-Log "=== WINDOWS DEFENDER DETECTIONS ==="
Write-Log ""

$defenderEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Windows Defender/Operational';
    ID        = 1116, 1117, 1118;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($null -eq $defenderEvents) {
    Write-Log "No Defender detections in last $Minutes minutes."
} else {
    foreach ($event in $defenderEvents) {
        $eventXML = [xml]$event.ToXml()
        $threatName = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Threat Name' }).'#text'
        $filePath   = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Path' }).'#text'
        $action     = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Action' }).'#text'
        $severity   = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Severity Name' }).'#text'

        Write-Log "Time:     $($event.TimeCreated)"
        Write-Log "EventID:  $($event.Id)"
        Write-Log "Threat:   $threatName"
        Write-Log "Severity: $severity"
        Write-Log "File:     $filePath"
        Write-Log "Action:   $action"
        Write-Log "---------------------------------"
        Write-Log ""

        Write-Csv $event.TimeCreated "Defender" $event.Id "AV" $threatName $filePath
    }
}

# =====================================================================
# Section 2: Sysmon Events by Pipeline Stage
# =====================================================================

# --- L1: Storage ---
Write-Log ""
Write-Log "=== SYSMON: L1 STORAGE EVENTS ==="
Write-Log ""

# Event 11: FileCreate
$fileCreateEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Sysmon/Operational';
    ID        = 11;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($fileCreateEvents) {
    foreach ($event in $fileCreateEvents) {
        $eventXML = [xml]$event.ToXml()
        $image   = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Image' }).'#text'
        $target  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'TargetFilename' }).'#text'

        Write-Log "[FileCreate] $($event.TimeCreated)"
        Write-Log "  Process: $image"
        Write-Log "  File:    $target"
        Write-Log ""

        Write-Csv $event.TimeCreated "Sysmon" 11 "L1" "FileCreate" "$image -> $target"
    }
} else {
    Write-Log "No FileCreate events."
}

# Event 3: NetworkConnect
$netEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Sysmon/Operational';
    ID        = 3;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($netEvents) {
    foreach ($event in $netEvents) {
        $eventXML = [xml]$event.ToXml()
        $image   = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Image' }).'#text'
        $destIP  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'DestinationIp' }).'#text'
        $destPort= ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'DestinationPort' }).'#text'

        Write-Log "[NetworkConnect] $($event.TimeCreated)"
        Write-Log "  Process: $image"
        Write-Log "  Dest:    ${destIP}:${destPort}"
        Write-Log ""

        Write-Csv $event.TimeCreated "Sysmon" 3 "L1" "NetworkConnect" "$image -> ${destIP}:${destPort}"
    }
} else {
    Write-Log "No NetworkConnect events."
}

# --- L2: Allocation + L4: Writing ---
Write-Log ""
Write-Log "=== SYSMON: L2/L4 ALLOCATION & WRITING EVENTS ==="
Write-Log ""

# Event 10: ProcessAccess (covers both VirtualAllocEx and WriteProcessMemory)
$accessEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Sysmon/Operational';
    ID        = 10;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($accessEvents) {
    foreach ($event in $accessEvents) {
        $eventXML = [xml]$event.ToXml()
        $srcImage  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'SourceImage' }).'#text'
        $tgtImage  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'TargetImage' }).'#text'
        $access    = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'GrantedAccess' }).'#text'
        $callTrace = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'CallTrace' }).'#text'

        Write-Log "[ProcessAccess] $($event.TimeCreated)"
        Write-Log "  Source:  $srcImage"
        Write-Log "  Target:  $tgtImage"
        Write-Log "  Access:  $access"
        Write-Log "  Trace:   $callTrace"
        Write-Log ""

        Write-Csv $event.TimeCreated "Sysmon" 10 "L2/L4" "ProcessAccess($access)" "$srcImage -> $tgtImage"
    }
} else {
    Write-Log "No ProcessAccess events."
}

# --- L5: Execution ---
Write-Log ""
Write-Log "=== SYSMON: L5 EXECUTION EVENTS ==="
Write-Log ""

# Event 8: CreateRemoteThread
$threadEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Sysmon/Operational';
    ID        = 8;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($threadEvents) {
    foreach ($event in $threadEvents) {
        $eventXML = [xml]$event.ToXml()
        $srcImage  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'SourceImage' }).'#text'
        $tgtImage  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'TargetImage' }).'#text'
        $startAddr = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'StartAddress' }).'#text'
        $startMod  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'StartModule' }).'#text'
        $startFunc = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'StartFunction' }).'#text'

        Write-Log "[CreateRemoteThread] $($event.TimeCreated)"
        Write-Log "  Source:    $srcImage"
        Write-Log "  Target:    $tgtImage"
        Write-Log "  StartAddr: $startAddr"
        Write-Log "  Module:    $startMod"
        Write-Log "  Function:  $startFunc"
        Write-Log ""

        Write-Csv $event.TimeCreated "Sysmon" 8 "L5" "CreateRemoteThread" "$srcImage -> $tgtImage @ $startAddr"
    }
} else {
    Write-Log "No CreateRemoteThread events."
}

# Event 1: ProcessCreate (for hollowing detection - suspicious parent/child)
$procEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Sysmon/Operational';
    ID        = 1;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($procEvents) {
    # Only log processes related to payload or shellcode-spawned children.
    # Includes 'explorer' to catch cmd/powershell spawns from shellcode that
    # was injected into explorer.exe via the remote chain (T2.3 + T4.3 + T5.4).
    $filtered = $procEvents | Where-Object {
        $xml = [xml]$_.ToXml()
        $img = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq 'Image' }).'#text'
        $parent = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq 'ParentImage' }).'#text'
        ($img -match 'Desktop') -or
        ($parent -match 'Desktop') -or
        ($parent -match 'payload') -or
        ($parent -match 'explorer')
    }

    if ($filtered) {
        foreach ($event in $filtered) {
            $eventXML = [xml]$event.ToXml()
            $image   = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Image' }).'#text'
            $parent  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'ParentImage' }).'#text'
            $cmdline = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'CommandLine' }).'#text'

            Write-Log "[ProcessCreate] $($event.TimeCreated)"
            Write-Log "  Process: $image"
            Write-Log "  Parent:  $parent"
            Write-Log "  CmdLine: $cmdline"
            Write-Log ""

            Write-Csv $event.TimeCreated "Sysmon" 1 "L5" "ProcessCreate" "$parent -> $image"
        }
    } else {
        Write-Log "No suspicious ProcessCreate events."
    }
} else {
    Write-Log "No ProcessCreate events."
}

# Event 25: ProcessTampering
$tamperEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Sysmon/Operational';
    ID        = 25;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($tamperEvents) {
    foreach ($event in $tamperEvents) {
        $eventXML = [xml]$event.ToXml()
        $image = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Image' }).'#text'
        $type  = ($eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Type' }).'#text'

        Write-Log "[ProcessTampering] $($event.TimeCreated)"
        Write-Log "  Process: $image"
        Write-Log "  Type:    $type"
        Write-Log ""

        Write-Csv $event.TimeCreated "Sysmon" 25 "L5" "ProcessTampering($type)" $image
    }
} else {
    Write-Log "No ProcessTampering events."
}

# --- Summary ---
Write-Log ""
Write-Log "=== COLLECTION COMPLETE ==="
Write-Log "Time range: $StartTime to $EndTime ($Minutes minutes)"
Write-Log "Text log:   $logFile"
Write-Log "CSV log:    $csvFile"

Write-Host "Log collection complete."
Write-Host "  Text: $logFile"
Write-Host "  CSV:  $csvFile"
