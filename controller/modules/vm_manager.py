import subprocess
import time
import logging
import os
from controller.config import GUEST_USER, GUEST_PASS

class VMwareManager:
    def __init__(self, vmx_path):
        self.vmx_path = vmx_path
        self.user = GUEST_USER
        self.passwd = GUEST_PASS
        self.logger = logging.getLogger("VMware")

    def _run(self, args, timeout=120):
        cmd = ["vmrun"] + args
        # self.logger.debug(f"Exec: {' '.join(cmd)}")
        try:
            return subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
        except Exception as e:
            self.logger.error(f"VM Command Failed: {cmd} -> {e}")
            return None

    def revert_snapshot(self, snapshot_name):
        self.logger.info(f"Reverting to snapshot: {snapshot_name}")
        return self._run(["revertToSnapshot", self.vmx_path, snapshot_name]) is not None

    def start(self):
        self.logger.info("Starting VM...")
        return self._run(["-T", "ws", "start", self.vmx_path, "nogui"]) is not None

    def stop(self):
        self.logger.info("Stopping VM...")
        return self._run(["stop", self.vmx_path]) is not None

    def copy_to_guest(self, host_path, guest_path):
        self.logger.info(f"Deploying: {os.path.basename(host_path)} -> {guest_path}")
        return self._run(["-gu", self.user, "-gp", self.passwd, "copyFileToGuest", self.vmx_path, host_path, guest_path]) is not None

    def copy_from_guest(self, guest_path, host_path):
        return self._run(["-gu", self.user, "-gp", self.passwd, "copyFileFromGuest", self.vmx_path, guest_path, host_path]) is not None

    def run_program(self, program_path, args="", no_wait=False):
        cmd_args = ["-gu", self.user, "-gp", self.passwd, "runProgramInGuest", self.vmx_path]
        if no_wait: cmd_args.append("-noWait")
        cmd_args.append(program_path)
        if args: cmd_args.append(args)
        return self._run(cmd_args) is not None

    def list_processes(self):
        return self._run(["-gu", self.user, "-gp", self.passwd, "listProcessesInGuest", self.vmx_path], timeout=10) is not None

    def wait_for_tools(self, timeout=120):
        self.logger.info("Waiting for VMware Tools...")
        start = time.time()
        while time.time() - start < timeout:
            if self.list_processes():
                self.logger.info("VM is Ready!")
                return True
            time.sleep(5)
        return False