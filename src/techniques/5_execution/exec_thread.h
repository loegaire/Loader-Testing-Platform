#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"

void Stage5_Exec_LocalThread(LPVOID address) {
    HANDLE hThread = MyCreateThread(address);
    if (hThread) {
        MyWaitForSingleObject(hThread);
        CloseHandle(hThread);
    }
}