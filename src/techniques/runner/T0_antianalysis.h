#pragma once
#include "../context.h"

#ifdef T0_ANTIANALYSIS_DEBUG
#include "../0_anti_analysis/anti_debug.h"
#endif

inline BOOL Run_T0_AntiAnalysis(TechniqueContext* ctx)
{
#ifdef T0_ANTIANALYSIS_NONE
    (void)ctx;
    return TRUE;
#endif

#ifdef T0_ANTIANALYSIS_DEBUG
    return Stage0_AntiAnalysis_Debug(ctx);
#endif

    return TRUE;
}
