#pragma once
#include "../../core/utils.h"
#include "../context.h"
#include <stdlib.h>

inline BOOL Stage0_AntiAnalysis_SleepSkew(TechniqueContext* ctx)
{
    (void)ctx;

    static BOOL seeded = FALSE;
    if (!seeded) {
        srand((unsigned int)(GetTickCount() ^ GetCurrentProcessId()));
        seeded = TRUE;
    }

    const DWORD kSamples = 3;
    const DWORD kBaseMs = 150;
    const DWORD kJitterMs = 350;
    const DWORD kToleranceMs = 45;

    for (DWORD i = 0; i < kSamples; ++i) {
        DWORD target = kBaseMs + (DWORD)(rand() % kJitterMs);
        ULONGLONG start = GetTickCount64();
        Sleep(target);
        ULONGLONG elapsed = GetTickCount64() - start;

        if ((elapsed + kToleranceMs) < target) {
#ifdef DEBUG_MODE
            DEBUG_MSG("Stage0", "Sleep skew detected: target=%lu elapsed=%llu",
                      target, (unsigned long long)elapsed);
#endif
            return FALSE;
        }
    }

    return TRUE;
}
