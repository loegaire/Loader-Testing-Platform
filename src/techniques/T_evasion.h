#pragma once
#include <windows.h>

// Hàm kiểm tra sandbox bằng cách đo thời gian Sleep
BOOL IsSandboxed_Sleep() {
    DWORD start = GetTickCount();
    Sleep(2000); // Yêu cầu ngủ 2 giây
    DWORD end = GetTickCount();
    // Nếu thời gian trôi qua ít hơn 1.5 giây, có thể sandbox đã tua nhanh hàm Sleep
    if ((end - start) < 1500) {
        return TRUE;
    }
    return FALSE;
}