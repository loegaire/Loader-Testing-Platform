import os

# Paths
CONTROLLER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CONTROLLER_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'build', 'bin')
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build', 'src')
SHELLCODE_DIR = os.path.join(PROJECT_ROOT, "shellcodes")
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
LOGS_DIR = os.path.join(PROJECT_ROOT, "test_logs")

# Guest SSH
GUEST_USER = "tester"
GUEST_PASSWORD = "123456"  # dùng sshpass cho password auth

# Guest Paths (Windows)
GUEST_DESKTOP = f"C:\\Users\\{GUEST_USER}\\Desktop"
GUEST_PAYLOAD_PATH = f"{GUEST_DESKTOP}\\payload.exe"
GUEST_LOG_COLLECTOR = f"{GUEST_DESKTOP}\\collect_logs.ps1"
GUEST_LOG_OUTPUT = f"{GUEST_DESKTOP}\\detection_log.txt"
GUEST_SYSMON_CONFIG = f"{GUEST_DESKTOP}\\sysmon.xml"

# Sysmon config on host — applied to guest's pre-installed built-in Sysmon
# before each test run. Edit the XML freely; changes are picked up next run.
SYSMON_CONFIG_HOST = os.path.join(
    PROJECT_ROOT, "log_collectors", "sysmon_loader_config.xml"
)

# Infrastructure
CLEAN_SNAPSHOT_NAME = "clean_snapshot"
LISTENER_IP = "192.168.122.1"  # Default KVM virbr0 gateway
LISTENER_PORT = 4444

# VMs Configuration (KVM)
VMS_CONFIG = {
    "Windows Defender": {
        "domain": "Win11_Defender",             # virsh domain name
        "guest_ip": "192.168.122.101",    # Static IP of Windows guest
        "log_collector_host": os.path.join(PROJECT_ROOT, "log_collectors", "collect_all.ps1")
    },
    # Add more VMs here
}
