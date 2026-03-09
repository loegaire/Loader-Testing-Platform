#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"

void Stage5_Exec_LocalThread(LPVOID address) {
    DEBUG_MSG("Stage 5", "Execute on new thread");
    HANDLE hThread = MyCreateThread(
        (LPTHREAD_START_ROUTINE)address,
        NULL,
        0
    );
    if (hThread) {
        MyWaitForSingleObject(hThread, INFINITE);
        CloseHandle(hThread);
    }
}