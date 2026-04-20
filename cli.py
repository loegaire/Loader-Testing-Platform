import argparse
import os
import sys
import time

# Force UTF-8 stdout so box-drawing characters render on Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from controller.modules.definitions import STAGE_FLAGS

# --- MÀU SẮC CHO TERMINAL (ANSI Codes) ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- SETUP PATH & IMPORTS ---
# Thêm thư mục hiện tại vào sys.path để Python nhận diện package 'controller'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from controller import core_engine
    from controller.config import VMS_CONFIG, PROJECT_ROOT, OUTPUT_DIR, BUILD_DIR, LOGS_DIR
except ImportError as e:
    print(f"{Colors.FAIL}[!] Error importing modules: {e}{Colors.ENDC}")
    print(f"{Colors.WARNING}Ensure you are running 'python cli.py' from the project root and that 'controller/__init__.py' exists.{Colors.ENDC}")
    sys.exit(1)


def print_pipeline_banner(options, shellcode_path):
    s0_status  = f"{Colors.GREEN}[ ENABLED ]{Colors.ENDC}"  if options.get('anti_evasion') \
                 else f"{Colors.WARNING}[ DISABLED ]{Colors.ENDC}"
    s1_method  = options.get('t1', 'rdata').upper()
    s2_alloc   = options.get('t2', 'local').upper()
    s3_algo    = options.get('t3', 'none').upper()
    s3_color   = Colors.GREEN if s3_algo != "NONE" else Colors.FAIL
    s4_write   = options.get('t4', 'local').upper()
    s5_exec    = options.get('t5', 'classic').upper()
    api_mode   = options.get('api_method', 'winapi').upper()
    api_color  = Colors.CYAN if "SYSCALL" in api_mode else Colors.FAIL

    sc_name = os.path.basename(shellcode_path)

    print(f"\n{Colors.BOLD}{Colors.HEADER}=== EVASION ENGINEERING PIPELINE (6-STAGE MODEL) ==={Colors.ENDC}")
    print(f"Payload Source: {Colors.CYAN}{sc_name}{Colors.ENDC}")
    print("│")
    print(f"├── {Colors.BOLD}Stage 0: Anti-Analysis{Colors.ENDC}")
    print(f"│   └── Checks:       {s0_status}")
    print("│")
    print(f"├── {Colors.BOLD}Stage 1: Storage{Colors.ENDC}")
    print(f"│   └── Location:     {s1_method}")
    print("│")
    print(f"├── {Colors.BOLD}Stage 2: Allocation{Colors.ENDC} {api_color}[{api_mode}]{Colors.ENDC}")
    print(f"│   └── Strategy:     {s2_alloc}")
    print("│")
    print(f"├── {Colors.BOLD}Stage 3: Transformation{Colors.ENDC}")
    print(f"│   └── Algorithm:    {s3_color}{s3_algo}{Colors.ENDC}")
    print("│")
    print(f"├── {Colors.BOLD}Stage 4: Writing{Colors.ENDC} {api_color}[{api_mode}]{Colors.ENDC}")
    print(f"│   └── Method:       {s4_write}")
    print("│")
    print(f"└── {Colors.BOLD}Stage 5: Execution{Colors.ENDC} {api_color}[{api_mode}]{Colors.ENDC}")
    print(f"    └── Technique:    {Colors.GREEN}{s5_exec}{Colors.ENDC}")
    print("")

def main():
    parser = argparse.ArgumentParser(
        description="FUD Loader - Evasion Engineering Platform",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=40)    )

    # --- REQUIRED ---
    parser.add_argument("-s", "--shellcode", required=True, metavar="PATH",
                        help="Path to raw shellcode (.bin)")

    # --- STAGE FLAGS ---
    parser.add_argument("-t0", dest="t0", metavar="TECH", default="none",
                        choices=["none", "antidebug"],
                        help="Stage 0 - Anti-Analysis")

    parser.add_argument("-t1", dest="t1", metavar="TECH", default="rdata",
                        choices=list(STAGE_FLAGS['t1'].keys()),
                        help=f"Stage 1 - Storage ({', '.join(STAGE_FLAGS['t1'].keys())})")

    parser.add_argument("-t2", dest="t2", metavar="TECH", default="local",
                        choices=list(STAGE_FLAGS['t2'].keys()),
                        help=f"Stage 2 - Storage ({', '.join(STAGE_FLAGS['t2'].keys())})")

    parser.add_argument("-t3", dest="t3", metavar="TECH", default="none",
                        choices=list(STAGE_FLAGS['t3'].keys()),
                        help=f"Stage 3 - Storage ({', '.join(STAGE_FLAGS['t3'].keys())})")

    parser.add_argument("-t4", dest="t4", metavar="TECH", default="local",
                        choices=list(STAGE_FLAGS['t4'].keys()),
                        help=f"Stage 4 - Storage ({', '.join(STAGE_FLAGS['t4'].keys())})")

    parser.add_argument("-t5", dest="t5", metavar="TECH", default="local",
                        choices=list(STAGE_FLAGS['t5'].keys()),
                        help=f"Stage 5 - Storage ({', '.join(STAGE_FLAGS['t5'].keys())})")

    # --- API LAYER ---
    parser.add_argument("--api", dest="api_method", metavar="MODE", default="winapi",
                        choices=["winapi", "syscalls"],
                        help="API Layer:                   winapi | syscalls")

    # --- MISC ---
    parser.add_argument("-v", "--vms", nargs='*', metavar="VM",
                        help="Target VMs for testing")
    parser.add_argument("--build-only", action="store_true",
                        help="Build only, skip test")
    parser.add_argument("--debug", action="store_true",
                        help="Enable DEBUG_MODE in payload")

    args = parser.parse_args()

    if not args.build_only and not args.vms:
        parser.error("Specify target VMs with -v/--vms OR use --build-only.")

    shellcode_path = args.shellcode if os.path.isabs(args.shellcode) \
                     else os.path.join(PROJECT_ROOT, args.shellcode)
                     
    build_options = {
        "t0":         args.t0,
        "t1":         args.t1,
        "t2":         args.t2,
        "t3":         args.t3,       # builder dùng key này cho encrypt
        "t4":         args.t4,
        "t5":         args.t5,
        "api_method": args.api_method,
        "debug":      args.debug,
    }

    # --- DISPLAY BANNER ---
    print_pipeline_banner(build_options, shellcode_path)
    
    # --- BUILD ---
    payload_path = core_engine.build_payload(shellcode_path, build_options)

    if not payload_path:
        print(f"\n{Colors.FAIL}[!] Payload build failed. Aborting.{Colors.ENDC}")
        return
    
    print(f"\n{Colors.GREEN}[SUCCESS] Payload built at: {payload_path}{Colors.ENDC}")

    if args.build_only:
        return

    # --- TEST ---
    for vm_name in args.vms:
        if vm_name not in VMS_CONFIG:
            print(f"{Colors.FAIL}[!] Error: VM '{vm_name}' not defined in controller/config.py.{Colors.ENDC}")
            print(f"    Available VMs: {list(VMS_CONFIG.keys())}")
            continue

        result = core_engine.run_single_test(vm_name, payload_path, build_options)
        
        # Report
        status = result.get('status', 'UNKNOWN')
        color = Colors.GREEN if "SUCCESS" in status else Colors.FAIL
        
        print(f"\n{Colors.BOLD}--- Result for {vm_name} ---{Colors.ENDC}")
        print(f"Status: {color}{status}{Colors.ENDC}")
        
        if 'FAILED' in status or 'ERROR' in status:
            print(f"{Colors.WARNING}Log Preview:{Colors.ENDC}")
            logs = result.get('log', '').split('\n')
            # In tối đa 10 dòng log để preview
            count = 0
            for line in logs:
                if line.strip(): 
                    print(f"  > {line}")
                    count += 1
                if count >= 10: break
            print(f"  > (See full logs in test_logs/)")

if __name__ == "__main__":
    # Tạo các thư mục output nếu chưa có
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    main()