#pragma once
#include "../core/win_internals.h"
#include "../core/utils.h"

#ifdef DEBUG_MODE
    #define DEBUG_MSG(title, msg) MessageBoxA(NULL, msg, title, MB_OK | MB_ICONINFORMATION)
#else
    #define DEBUG_MSG(title, msg)
#endif

// --- CÁC HÀM KIỂM TRA LẺ (Primitives) ---

BOOL Check_Sleep_Acceleration() {
    // ... code kiểm tra Sleep ...
    return FALSE; // Giả sử an toàn
}

BOOL Check_Low_Resources() {
    // ... code kiểm tra RAM/CPU ...
    return FALSE; 
}

// --- STAGE 0 COMPOSITE (Hàm tổng hợp) ---

BOOL Stage0_Environment_Check() {
    DEBUG_MSG("Stage 0", "Checking environment safety...");

    if (Check_Sleep_Acceleration()) {
        DEBUG_MSG("Stage 0 [FAIL]", "Sandbox detected (Sleep Patching)!");
        return FALSE;
    }

    if (Check_Low_Resources()) {
        DEBUG_MSG("Stage 0 [FAIL]", "Sandbox detected (Low Specs)!");
        return FALSE;
    }

    DEBUG_MSG("Stage 0 [PASS]", "Environment looks clean.");
    return TRUE;
}