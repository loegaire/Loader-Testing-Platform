#pragma once
#include "../context.h"

#ifdef T4_WRITE_LOCAL
#include "../4_writing/write_local.h"
#endif

#ifdef T4_WRITE_LOCAL_RX
#include "../4_writing/write_local_rx.h"
#endif

inline BOOL Run_T4_Write(TechniqueContext* ctx)
{
#ifdef T4_WRITE_LOCAL
    return Stage4_Write_Local(ctx);
#endif

#ifdef T4_WRITE_LOCAL_RX
    return Stage4_Write_Local_RX(ctx);
#endif

    return FALSE;
}
