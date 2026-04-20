#pragma once
#include "../context.h"

#ifdef T2_ALLOC_LOCAL
#include "../2_allocation/alloc_local.h"
#endif

#ifdef T2_ALLOC_LOCAL_RW
#include "../2_allocation/alloc_local_rw.h"
#endif

#ifdef T2_ALLOC_REMOTE
#include "../2_allocation/alloc_remote.h"
#endif

#ifdef T2_ALLOC_SPAWN
#include "../2_allocation/alloc_spawn.h"
#endif

inline BOOL Run_T2_Allocation(TechniqueContext* ctx)
{
#ifdef T2_ALLOC_LOCAL
    return Stage2_Alloc_Local(ctx);
#endif

#ifdef T2_ALLOC_LOCAL_RW
    return Stage2_Alloc_Local_RW(ctx);
#endif

#ifdef T2_ALLOC_REMOTE
    return Stage2_Alloc_Remote(ctx);
#endif

#ifdef T2_ALLOC_SPAWN
    return Stage2_Alloc_Spawn(ctx);
#endif

    return FALSE;
}
