import logging
import os
import threading
import time

from controller.config import *
from controller.modules.builder import PayloadBuilder
from controller.modules.c2 import C2Listener
from controller.modules.vm_manager import KVMManager

# Setup Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] - %(message)s')


def build_payload(shellcode_path, build_options):
    builder = PayloadBuilder(shellcode_path, build_options)
    return builder.build()


def run_single_test(vm_name, payload_path, build_options,
                    log_dir=None, log_name=None):
    """Revert VM, deploy payload, run, collect telemetry.

    log_dir: directory for the guest telemetry .txt file.
             Defaults to PROJECT_ROOT/test_logs (used by cli.py).
             Batch runners (experiments/run_tests.py) pass a per-batch
             subfolder so one folder contains everything for that batch.
    log_name: filename for the guest telemetry dump within log_dir.
              Defaults to "<vm_name>_<unix_ts>.txt".
    """
    vm_conf = VMS_CONFIG.get(vm_name)
    if not vm_conf:
        return {"status": "ERROR", "log": "VM Config Not Found"}

    if log_dir is None:
        log_dir = os.path.join(PROJECT_ROOT, "test_logs")
    os.makedirs(log_dir, exist_ok=True)
    if log_name is None:
        log_name = f"{vm_name}_{int(time.time())}.txt"

    vm = KVMManager(vm_conf['domain'], vm_conf['guest_ip'])
    c2 = C2Listener(LISTENER_IP, LISTENER_PORT)

    logging.info(f"=== Test cycle: {vm_name} ===")

    # --- boot ---
    if not vm.revert_snapshot(CLEAN_SNAPSHOT_NAME):
        return {"status": "FAILED", "log": "Revert Failed"}
    if not vm.start():
        return {"status": "FAILED", "log": "Start Failed"}
    if not vm.wait_for_guest():
        vm.stop()
        return {"status": "FAILED", "log": "Guest SSH Timeout"}

    status = "UNKNOWN"
    log_data = "N/A"

    try:
        # --- deploy sysmon config (service is already running in snapshot) ---
        # Collector uses a time anchor on ProcessCreate(payload.exe) so we no
        # longer need to wipe the sysmon log here; just push the latest rules.
        if os.path.isfile(SYSMON_CONFIG_HOST):
            if vm.copy_to_guest(SYSMON_CONFIG_HOST, GUEST_SYSMON_CONFIG):
                vm.run_program("sysmon.exe", f"-c {GUEST_SYSMON_CONFIG}")
                time.sleep(1)
            else:
                logging.warning("sysmon config scp failed; guest keeps prior rules")

        # --- deploy collector + payload ---
        collector_script = vm_conf['log_collector_host']
        if not vm.copy_to_guest(collector_script, GUEST_LOG_COLLECTOR):
            return {"status": "FAILED", "log": "Collector copy failed"}

        payload_deployed = vm.copy_to_guest(payload_path, GUEST_PAYLOAD_PATH)

        # --- execute + listen ---
        # Launch via Task Scheduler so the payload runs in the user's
        # interactive session (matches manual console launch). Straight
        # SSH-spawned processes live in the service session, which breaks
        # cross-session OpenProcess calls made by remote-injection loaders.
        if payload_deployed:
            t = threading.Thread(target=c2.listen, args=(30,))
            t.start()
            time.sleep(2)  # let listener bind
            vm.launch_interactive(GUEST_PAYLOAD_PATH)
            t.join()

        # --- classify outcome ---
        if c2.success:
            status = "SUCCESS (Bypass)"
            log_data = "Reverse Shell Established!"
        elif not payload_deployed:
            status = "FAILED (Transfer Blocked - OnWrite)"
            log_data = "Payload blocked/deleted during SCP transfer."
        else:
            status = "FAILED (Execution Blocked)"
            log_data = "Payload copied but no shell received. AV intervened."

        # --- collect telemetry (run regardless of outcome, except TB) ---
        if payload_deployed:
            time.sleep(2)  # let sysmon flush late events
            vm.run_program(
                "powershell.exe",
                f"-ExecutionPolicy Bypass -File {GUEST_LOG_COLLECTOR}"
            )
            time.sleep(5)  # collector writes output

            host_log_path = os.path.join(log_dir, log_name)

            if vm.copy_from_guest(GUEST_LOG_OUTPUT, host_log_path):
                try:
                    with open(host_log_path, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                    log_data += f"\n\n=== DEFENDER/SYSMON LOGS ===\n{log_content}"
                    if "Action:   Quarantine" in log_content:
                        status += " - Verified by Defender Log"
                except Exception as e:
                    log_data += f"\n[WARN] Could not read log file on host: {e}"
            else:
                log_data += "\n[WARN] Failed to copy logs from VM."

    except Exception as e:
        logging.error(f"FATAL during VM cycle: {e}")
        status = "ERROR"
        log_data = f"Python exception: {e}"

    finally:
        vm.stop()

    logging.info(f"=== Result: {status} ===")
    return {"status": status, "log": log_data}
