import subprocess
import time
import logging
import os
from controller.config import GUEST_USER, GUEST_PASSWORD

def win_to_sftp_path(path: str) -> str:
    # C:\Users\tester\Desktop\file.txt
    drive = path[0].upper()
    rest = path[3:].replace("\\", "/")
    return f"/{drive}:/{rest}"

class KVMManager:
    def __init__(self, domain_name, guest_ip):
        self.domain = domain_name
        self.guest_ip = guest_ip
        self.user = GUEST_USER
        self.password = GUEST_PASSWORD
        self.logger = logging.getLogger("KVM")

    def _virsh(self, args, timeout=120):
        cmd = ["virsh", "-c", "qemu:///system"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result
        else:
            self.logger.error(f"virsh command failed: {' '.join(cmd)} -> returncode: {result.returncode}, stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
            return None

    def _ssh_cmd(self, remote_cmd, timeout=120):
        cmd = [
            "sshpass", "-p", self.password,
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"{self.user}@{self.guest_ip}",
            remote_cmd,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            self.logger.info(f"SSH command succeeded: {remote_cmd}")
            return result
        else:
            self.logger.error(f"SSH command failed: {remote_cmd} -> returncode: {result.returncode}, stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
            return None

    def _scp_to_guest(self, host_path, guest_path, timeout=120):
        cmd = [
            "sshpass", "-p", self.password,
            "scp",
            "-o", "StrictHostKeyChecking=no",
            host_path,
            f"{self.user}@{self.guest_ip}:{guest_path}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result
        else:
            self.logger.error(f"SCP to guest failed: {host_path} -> returncode: {result.returncode}, stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
            return None

    def _scp_from_guest(self, guest_path, host_path, timeout=120):
        guest_path_sftp = win_to_sftp_path(guest_path)
        guest_path_sftp = guest_path_sftp.replace(" ", "\\ ")

        cmd = [
            "sshpass", "-p", self.password,
            "scp",
            "-o", "StrictHostKeyChecking=no",
            f'{self.user}@{self.guest_ip}:{guest_path_sftp}',
            host_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result
        else:
            self.logger.error(
                f"SCP from guest failed: {guest_path_sftp} -> returncode: {result.returncode}, "
                f"stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}"
            )
            return None

    # --- VM lifecycle (virsh) ---

    def revert_snapshot(self, snapshot_name):
        self.logger.info(f"Reverting to snapshot: {snapshot_name}")
        return self._virsh(["snapshot-revert", self.domain, snapshot_name]) is not None

    def start(self):
        self.logger.info("Starting VM...")
        return self._virsh(["start", self.domain]) is not None

    def stop(self):
        self.logger.info("Stopping VM...")
        return self._virsh(["shutdown", self.domain]) is not None

    # --- Guest interaction (SSH/SCP) ---

    def copy_to_guest(self, host_path, guest_path):
        self.logger.info(f"[DEPLOY] {host_path} -> {guest_path}")
        result = self._scp_to_guest(host_path, guest_path)

        if result:
            self.logger.info("[DEPLOY] SUCCESS")
        else:
            self.logger.error("[DEPLOY] FAILED")

        return result is not None

    def copy_from_guest(self, guest_path, host_path):
        return self._scp_from_guest(guest_path, host_path) is not None

    def run_program(self, program_path, args="", no_wait=False):
        remote_cmd = f'"{program_path}"'
        if args:
            remote_cmd += f" {args}"
        if no_wait:
            # Detach process so SSH returns immediately
            remote_cmd = f'Start-Process -FilePath "{program_path}"'
            if args:
                remote_cmd += f' -ArgumentList "{args}"'
            remote_cmd = f"powershell -Command {remote_cmd}"
        return self._ssh_cmd(remote_cmd) is not None

    def wait_for_guest(self, timeout=120):
        self.logger.info("Waiting for guest SSH...")
        start = time.time()
        while time.time() - start < timeout:
            result = self._ssh_cmd("echo ok", timeout=10)
            if result:
                self.logger.info("VM is ready!")
                return True
            time.sleep(5)
        self.logger.error("Guest SSH timeout")
        return False
