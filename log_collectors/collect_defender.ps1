<#
.SYNOPSIS
    Collects recent security events from Windows Defender.
.DESCRIPTION
    This script queries the Windows Event Log for malware detections by Windows Defender
    within the last 5 minutes.
    It outputs the findings to a standardized text file on the user's Desktop.
#>

# --- 1. Check Administrator Rights ---
# Bắt buộc phải có quyền Admin mới đọc được Security Event Logs
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "LỖI: Bạn phải mở PowerShell bằng quyền Administrator (Run as Administrator) để chạy script này!"
    exit
}

# --- 2. Configuration ---
$logFile = "$env:USERPROFILE\Desktop\detection_log.txt"

$EndTime = Get-Date
$StartTime = $EndTime.AddMinutes(-5)

# Reset file log cũ nếu có
if (Test-Path $logFile) {
    Remove-Item $logFile
}

# --- 3. Windows Defender Detections ---
"--- Windows Defender Detections ---`r`n" | Out-File -FilePath $logFile -Encoding utf8

try {
    # FIX LỖI: Sử dụng @() để định nghĩa mảng ID giúp tránh lỗi "parameter is incorrect"
    $defenderEvents = Get-WinEvent -FilterHashtable @{
        LogName   = 'Microsoft-Windows-Windows Defender/Operational';
        ID        = @(1116, 1117, 1118);
        StartTime = $StartTime;
    } -ErrorAction Stop

    # Nếu có log, lặp qua từng sự kiện và trích xuất thông tin bằng XML
    foreach ($event in $defenderEvents) {
        $eventXML = [xml]$event.ToXml()
        
        # Bắt lỗi null trong trường hợp log không có đủ field
        $threatName = $eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Threat Name' } | Select-Object -ExpandProperty '#text' -ErrorAction SilentlyContinue
        $filePath = $eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Path' } | Select-Object -ExpandProperty '#text' -ErrorAction SilentlyContinue
        $action = $eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Action' } | Select-Object -ExpandProperty '#text' -ErrorAction SilentlyContinue
        
        "Time:     $($event.TimeCreated)" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "Threat:   $threatName" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "File:     $filePath" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "Action:   $action" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "---------------------------------`r`n" | Out-File -FilePath $logFile -Encoding utf8 -Append
    }
}
catch {
    # Nếu không có malware nào trong 5 phút qua, Get-WinEvent sẽ quăng lỗi thay vì trả về Null.
    # Dùng try...catch để bắt lỗi này và ghi vào file log một cách mượt mà.
    "No new Defender detections found in the last 5 minutes.`r`n" | Out-File -FilePath $logFile -Encoding utf8 -Append
}

Write-Host "Log collection complete. Output saved to $logFile" -ForegroundColor Green