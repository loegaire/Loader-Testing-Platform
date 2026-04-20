#pragma once
#include "../context.h"

#ifdef T5_EXEC_LOCAL
#include "../5_execution/exec_local.h"
#endif

#ifdef T5_EXEC_DISPLAY_MONITORS
#include "../5_execution/exec_display_monitors.h"
#endif

#ifdef T5_EXEC_FIBER
#include "../5_execution/exec_fiber.h"
#endif

#ifdef T5_EXEC_REMOTE_THREAD
#include "../5_execution/exec_remote_thread.h"
#endif


inline BOOL Run_T5_Execute(TechniqueContext* ctx)
{

#ifdef T5_EXEC_LOCAL
    return Stage5_Exec_LocalThread(ctx);
#endif

#ifdef T5_EXEC_DISPLAY_MONITORS
    return Stage5_Exec_DisplayMonitors(ctx);
#endif

#ifdef T5_EXEC_FIBER
    return Stage5_Exec_Fiber(ctx);
#endif

#ifdef T5_EXEC_REMOTE_THREAD
    return Stage5_Exec_RemoteThread(ctx);
#endif

    return FALSE;
}
