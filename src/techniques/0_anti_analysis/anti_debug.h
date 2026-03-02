#pragma once
#include "../../core/utils.h"

BOOL IsDebugged() {
#ifdef EVASION_CHECKS_ENABLED
    // Kiểm tra cờ BeingDebugged trong PEB
    PPEB pPeb = GetPeb();
    if (pPeb->BeingDebugged) {
        #ifdef DEBUG_MODE
            DEBUG_MSG("Anti-Analysis", "Debugger detected via PEB!");
        #endif
        return TRUE;
    }
#endif
    return FALSE;
}