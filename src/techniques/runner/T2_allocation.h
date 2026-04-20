#pragma once
#include "../context.h"

#ifdef T2_ALLOC_LOCAL
#include "../2_allocation/alloc_local.h"
#endif

#ifdef T2_ALLOC_LOCAL_RW
#include "../2_allocation/alloc_local_rw.h"
#endif

inline BOOL Run_T2_Allocation(TechniqueContext* ctx)
{
#ifdef T2_ALLOC_LOCAL
    return Stage2_Alloc_Local(ctx);
#endif

#ifdef T2_ALLOC_LOCAL_RW
    return Stage2_Alloc_Local_RW(ctx);
#endif

    return FALSE;
}
