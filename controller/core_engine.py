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
    vm_conf = VMS_CONFIG.get(vm_name)
    if not vm_conf: return {"status": "ERROR", "log": "VM Config Not Found"}

    vm = KVMManager(vm_conf['domain'], vm_conf['guest_ip'])
    c2 = C2Listener(LISTENER_IP, LISTENER_PORT)

    logging.info(f"=== Starting Test Cycle on {vm_name} ===")

    # 2. Prepare Environment
    if not vm.revert_snapshot(CLEAN_SNAPSHOT_NAME): return {"status": "FAILED", "log": "Revert Failed"}
    if not vm.start(): return {"status": "FAILED", "log": "Start Failed"}
    if not vm.wait_for_guest():
        vm.stop() # Force tắt nếu không boot lên được
        return {"status": "FAILED", "log": "Guest SSH Timeout"}

    status = "UNKNOWN"
    log_data = "N/A"

    # ĐƯA VÀO TRY-FINALLY ĐỂ ĐẢM BẢO LUÔN CLEANUP VM DÙ CÓ LỖI GÌ XẢY RA
    try:
        # 3a. Apply latest Sysmon config from host. We clear the Sysmon
        # event log first, then apply the config, then verify rules loaded.
        # Clearing the log ensures the collect step only sees events from
        # THIS run, not from boot-time noise retained in the snapshot.
        if os.path.isfile(SYSMON_CONFIG_HOST):
            if vm.copy_to_guest(SYSMON_CONFIG_HOST, GUEST_SYSMON_CONFIG):
                # Wipe residual boot-time Sysmon events from the snapshot
                vm.run_program(
                    "powershell.exe",
                    "-Command \"wevtutil cl Microsoft-Windows-Sysmon/Operational\""
                )
                # Apply new rules
                vm.run_program("sysmon.exe", f"-c {GUEST_SYSMON_CONFIG}")
                time.sleep(2)  # settle before payload events
            else:
                logging.warning("Sysmon config SCP failed; guest keeps prior ruleset")
        else:
            logging.warning(f"Sysmon config not found at {SYSMON_CONFIG_HOST}; skipping update")

        # 3b. Connection Test & Prep
        collector_script = vm_conf['log_collector_host']
        if not vm.copy_to_guest(collector_script, GUEST_LOG_COLLECTOR):
            status, log_data = "FAILED", "Connection Test Failed (Copy Collector)"
            return {"status": status, "log": log_data}

        # 4. Deploy Payload
        payload_deployed = vm.copy_to_guest(payload_path, GUEST_PAYLOAD_PATH)

        if payload_deployed:
            # 5. Execute & Listen
            t = threading.Thread(target=c2.listen, args=(30,)) 
            t.start()
            time.sleep(2) # Chờ port C2 mở hẳn

            vm.run_program(GUEST_PAYLOAD_PATH, no_wait=True)
            t.join() # Chờ C2 listener kết thúc (tối đa 30s)

        # 6. Determine run status
        if c2.success:
            status = "SUCCESS (Bypass)"
            log_data = "Reverse Shell Established!"
        elif not payload_deployed:
            status = "FAILED (Transfer Blocked - OnWrite)"
            log_data = "Payload blocked/deleted during SCP transfer."
        else:
            status = "FAILED (Execution Blocked)"
            log_data = "Payload copied but no shell received. AV intervened."

        # 7. Collect telemetry — run regardless of outcome so that Sysmon
        #    events are available for stage-level analysis. Only skip if
        #    the payload never reached the guest (TB case above).
        if payload_deployed:
            logging.info(f"Collecting telemetry (status so far: {status})")

            # Small settle time so Sysmon can flush late events from execution
            time.sleep(2)

            vm.run_program(
                r"powershell.exe",
                f"-ExecutionPolicy Bypass -File {GUEST_LOG_COLLECTOR}"
            )
            time.sleep(5)  # wait for the collector to finish writing output

            host_log_path = os.path.join(
                PROJECT_ROOT, "test_logs",
                f"{vm_name}_{int(time.time())}.txt"
            )

            if vm.copy_from_guest(GUEST_LOG_OUTPUT, host_log_path):
                try:
                    with open(host_log_path, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                        log_data += f"\n\n=== DEFENDER/SYSMON LOGS ===\n{log_content}"

                        # Hint: Defender quarantine action marker in log
                        if "Action:   Quarantine" in log_content:
                            status += " - Verified by Defender Log"
                except Exception as e:
                    log_data += f"\n[WARNING] Could not read log file on Host: {e}"
            else:
                log_data += "\n[WARNING] Failed to copy logs from VM (network-isolated by EDR/AV?)."

    except Exception as e:
        logging.error(f"FATAL ERROR during VM cycle: {e}")
        status = "ERROR"
        log_data = f"Python Exception occurred: {str(e)}"

    finally:
        # 7. Cleanup
        logging.info("Cleaning up VM state...")
        vm.stop()
        
    return {"status": status, "log": log_data}