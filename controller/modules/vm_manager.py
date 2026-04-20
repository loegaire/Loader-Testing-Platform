import logging
import os
import subprocess
import time

from controller.config import GUEST_USER, GUEST_PASSWORD


def win_to_sftp_path(path: str) -> str:
    # C:\Users\tester\Desktop\file.txt -> /C:/Users/tester/Desktop/file.txt
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

    # ---------------------------------------------------------------
    # Low-level helpers
    # ---------------------------------------------------------------
    def _virsh(self, args, timeout=120):
        cmd = ["virsh", "-c", "qemu:///system"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result
        self.logger.error(
            f"virsh failed: {' '.join(cmd)} (rc={result.returncode}) "
            f"stderr={result.stderr.strip()}"
        )
        return None

    def _ssh_cmd(self, remote_cmd, timeout=120, quiet=False):
        """Run a command on the guest via SSH.

        quiet=True suppresses the per-call error log on failure (used during
        wait_for_guest polling where failures are expected).
        """
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
            return result
        if not quiet:
            self.logger.error(
                f"SSH failed: {remote_cmd} (rc={result.returncode}) "
                f"stderr={result.stderr.strip()}"
            )
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
        self.logger.error(
            f"SCP to guest failed: {host_path} (rc={result.returncode}) "
            f"stderr={result.stderr.strip()}"
        )
        return None

    def _scp_from_guest(self, guest_path, host_path, timeout=120):
        guest_path_sftp = win_to_sftp_path(guest_path).replace(" ", "\\ ")
        cmd = [
            "sshpass", "-p", self.password,
            "scp",
            "-o", "StrictHostKeyChecking=no",
            f"{self.user}@{self.guest_ip}:{guest_path_sftp}",
            host_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result
        self.logger.error(
            f"SCP from guest failed: {guest_path_sftp} (rc={result.returncode}) "
            f"stderr={result.stderr.strip()}"
        )
        return None

    # ---------------------------------------------------------------
    # VM lifecycle
    # ---------------------------------------------------------------
    def revert_snapshot(self, snapshot_name):
        self.logger.info(f"[vm] revert -> {snapshot_name}")
        return self._virsh(["snapshot-revert", self.domain, snapshot_name]) is not None

    def start(self):
        self.logger.info("[vm] start")
        return self._virsh(["start", self.domain]) is not None

    def stop(self):
        self.logger.info("[vm] stop")
        return self._virsh(["shutdown", self.domain]) is not None

    def wait_for_guest(self, timeout=120):
        self.logger.info("[vm] waiting for SSH...")
        start = time.time()
        while time.time() - start < timeout:
            if self._ssh_cmd("echo ok", timeout=10, quiet=True):
                self.logger.info(f"[vm] SSH ready ({int(time.time() - start)}s)")
                return True
            time.sleep(5)
        self.logger.error("[vm] SSH timeout")
        return False

    # ---------------------------------------------------------------
    # Guest interaction
    # ---------------------------------------------------------------
    def copy_to_guest(self, host_path, guest_path):
        if self._scp_to_guest(host_path, guest_path):
            self.logger.info(f"[scp] {os.path.basename(host_path)} -> guest")
            return True
        return False

    def copy_from_guest(self, guest_path, host_path):
        return self._scp_from_guest(guest_path, host_path) is not None

    def run_program(self, program_path, args="", no_wait=False):
        if no_wait:
            # Detach so SSH returns immediately
            remote_cmd = f'Start-Process -FilePath "{program_path}"'
            if args:
                remote_cmd += f' -ArgumentList "{args}"'
            remote_cmd = f"powershell -Command {remote_cmd}"
        else:
            remote_cmd = f'"{program_path}"'
            if args:
                remote_cmd += f" {args}"
        return self._ssh_cmd(remote_cmd) is not None
