#pragma once

#include "../context.h"

#ifdef T1_STORAGE_RDATA
#include "../1_storage/storage_rdata.h"
#endif

inline BOOL Run_T1_Storage(TechniqueContext* ctx)
{
#ifdef T1_STORAGE_RDATA
    return Stage1_Storage_Rdata(ctx);
#endif

    return FALSE;
}
