#pragma once
#include "../context.h"

#ifdef T0_ANTIANALYSIS_DEBUG
#include "../0_anti_analysis/anti_debug.h"
#endif

#ifdef T0_ANTIANALYSIS_SLEEP_SKEW
#include "../0_anti_analysis/random_sleep_skew.h"
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

#ifdef T0_ANTIANALYSIS_SLEEP_SKEW
    return Stage0_AntiAnalysis_SleepSkew(ctx);
#endif

    return TRUE;
}
