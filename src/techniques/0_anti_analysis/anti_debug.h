#pragma once
#include "../../core/utils.h"
#include "../context.h"

inline BOOL Stage0_AntiAnalysis_Debug(TechniqueContext* ctx)
{
    (void)ctx;

    PEB* pPeb = GetPeb();
    if (pPeb && pPeb->BeingDebugged) {
#ifdef DEBUG_MODE
        DEBUG_MSG("Stage0", "Debugger detected via PEB!");
#endif
        return FALSE;
    }

    return TRUE;
}
