<#
.SYNOPSIS
    Collects recent security events from Windows Defender and Sysmon.
.DESCRIPTION
    This script queries the Windows Event Log for malware detections by Windows Defender
    and general system activity from Sysmon within the last 5 minutes.
    It outputs the findings to a standardized text file on the user's Desktop.
.OUTPUTS
    C:\Users\<CurrentUser>\Desktop\detection_log.txt
#>

# --- Configuration ---
# Lấy đường dẫn Desktop của user đang chạy script
$logFile = "$env:USERPROFILE\Desktop\detection_log.txt"

# Định nghĩa khoảng thời gian cần truy vấn (5 phút gần nhất)
$EndTime = Get-Date
$StartTime = $EndTime.AddMinutes(-5)

# --- Main Logic ---

# Xóa file log cũ nếu tồn tại để đảm bảo kết quả luôn mới
if (Test-Path $logFile) {
    Remove-Item $logFile
}

# --- Section 1: Windows Defender Detections ---

# Ghi tiêu đề vào file log
"--- Windows Defender Detections ---`r`n" | Out-File -FilePath $logFile -Encoding utf8

# Truy vấn các Event ID liên quan đến việc phát hiện mã độc
# ID 1116: Malware detection
# ID 1117: Remediation action failed
# ID 1118: Remediation action succeeded
$defenderEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Windows Defender/Operational';
    ID        = 1116, 1117, 1118;
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($null -eq $defenderEvents) {
    "No new detections found in the last 5 minutes.`r`n" | Out-File -FilePath $logFile -Encoding utf8 -Append
} else {
    # Lặp qua từng sự kiện và trích xuất thông tin quan trọng
    foreach ($event in $defenderEvents) {
        # Dữ liệu chi tiết nằm trong định dạng XML, chúng ta cần phân tích nó
        $eventXML = [xml]$event.ToXml()
        $threatName = $eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Threat Name' } | Select-Object -ExpandProperty '#text'
        $filePath = $eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Path' } | Select-Object -ExpandProperty '#text'
        $action = $eventXML.Event.EventData.Data | Where-Object { $_.Name -eq 'Action' } | Select-Object -ExpandProperty '#text'
        
        "Time:     $($event.TimeCreated)" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "Threat:   $threatName" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "File:     $filePath" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "Action:   $action" | Out-File -FilePath $logFile -Encoding utf8 -Append
        "---------------------------------`r`n" | Out-File -FilePath $logFile -Encoding utf8 -Append
    }
}

# --- Section 2: Sysmon Events ---

"`r`n--- Sysmon Behavioral Events (Full Detail) ---`r`n" | Out-File -FilePath $logFile -Encoding utf8 -Append

$sysmonEvents = Get-WinEvent -FilterHashtable @{
    LogName   = 'Microsoft-Windows-Sysmon/Operational';
    StartTime = $StartTime;
} -ErrorAction SilentlyContinue

if ($null -eq $sysmonEvents) {
    "No new Sysmon events found.`r`n" | Out-File -FilePath $logFile -Encoding utf8 -Append
} else {
    # NÂNG CẤP: Sử dụng Format-List để xuất toàn bộ chi tiết của mỗi sự kiện
    # thay vì chỉ lấy dòng đầu tiên.
    ($sysmonEvents | Format-List | Out-String) | Out-File -FilePath $logFile -Encoding utf8 -Append
}

Write-Host "Log collection complete. Output saved to $logFile"