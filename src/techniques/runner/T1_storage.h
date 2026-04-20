#pragma once

#include "../context.h"

#ifdef T1_STORAGE_RDATA
#include "../1_storage/storage_rdata.h"
#endif

#ifdef T1_STORAGE_DATA
#include "../1_storage/storage_data.h"
#endif

inline BOOL Run_T1_Storage(TechniqueContext* ctx)
{
#ifdef T1_STORAGE_RDATA
    return Stage1_Storage_Rdata(ctx);
#endif

#ifdef T1_STORAGE_DATA
    return Stage1_Storage_Data(ctx);
#endif

    return FALSE;
}
