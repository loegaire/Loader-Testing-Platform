#pragma once
#include "syscall.h"

// --- WRAPPER for VirtualAlloc ---
inline PVOID MyVirtualAlloc(SIZE_T dwSize) {
#ifdef USE_DIRECT_SYSCALLS
    PVOID baseAddress = NULL;
    SIZE_T regionSize = dwSize;
    NTSTATUS status = sysNtAllocateVirtualMemory(GetCurrentProcess(), &baseAddress, 0, &regionSize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (status != 0) return NULL;
    return baseAddress;
#else
    return VirtualAlloc(NULL, dwSize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
#endif
}

// --- WRAPPER CHO CreateThread ---
inline HANDLE MyCreateThread(LPVOID lpStartAddress) {
#ifdef USE_DIRECT_SYSCALLS
    HANDLE hThread = NULL;
    NTSTATUS status = sysNtCreateThreadEx(&hThread, GENERIC_ALL, NULL, GetCurrentProcess(), lpStartAddress, NULL, 0, 0, 0, 0, NULL);
    if (status != 0) return NULL;
    return hThread;
#else
    return CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)lpStartAddress, NULL, 0, NULL);
#endif
}

// --- WRAPPER CHO WaitForSingleObject ---
inline void MyWaitForSingleObject(HANDLE hObject) {
#ifdef USE_DIRECT_SYSCALLS
    LARGE_INTEGER timeout;
    timeout.QuadPart = -1; // Chờ vô hạn
    sysNtWaitForSingleObject(hObject, FALSE, &timeout);
#else
    WaitForSingleObject(hObject, INFINITE);
#endif
}