import os

# Paths
CONTROLLER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CONTROLLER_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'build', 'bin')
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build', 'src')
SHELLCODE_DIR = os.path.join(PROJECT_ROOT, "shellcodes")
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
LOGS_DIR = os.path.join(PROJECT_ROOT, "test_logs")

# Guest Paths
GUEST_USER = "test"
GUEST_PASS = "test"
GUEST_DESKTOP = f"C:\\Users\\{GUEST_USER}\\Desktop"
GUEST_PAYLOAD_PATH = f"{GUEST_DESKTOP}\\payload.exe"
GUEST_LOG_COLLECTOR = f"{GUEST_DESKTOP}\\collect_logs.ps1"
GUEST_LOG_OUTPUT = f"{GUEST_DESKTOP}\\detection_log.txt"

# Infrastructure
CLEAN_SNAPSHOT_NAME = "clean_snapshot"
LISTENER_IP = "192.168.142.1"
LISTENER_PORT = 4444

# VMs Configuration
VMS_CONFIG = {
    "Windows Defender": {
        "vmx_path": r"C:\Users\Duy\Documents\Virtual_Machines\Windows_11_01.vmx",
        "log_collector_host": os.path.join(PROJECT_ROOT, "log_collectors", "collect_defender.ps1")
    },
    # Thêm VM khác vào đây
}