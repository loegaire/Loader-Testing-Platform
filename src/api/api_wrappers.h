#pragma once
#include "syscall.h"

// --- WRAPPER for VirtualAllocEx ---
inline PVOID MyVirtualAllocEx(
    HANDLE hProcess,
    PVOID lpAddress,
    SIZE_T dwSize,
    ULONG flAllocationType,
    ULONG flProtect
) {
#ifdef USE_DIRECT_SYSCALLS
    PVOID baseAddress = NULL;
    SIZE_T regionSize = dwSize;

    NTSTATUS status = sysNtAllocateVirtualMemory(
        hProcess, 
        &baseAddress, 
        0, 
        &regionSize, 
        flAllocationType, 
        flProtect
    );

    if (status != 0) return NULL;
    return baseAddress;

#else

    return VirtualAllocEx(
        hProcess,
        lpAddress,
        dwSize,
        flAllocationType,
        flProtect
    );
    
#endif
}

inline HANDLE MyCreateThread(
    LPTHREAD_START_ROUTINE lpStartAddress,
    LPVOID lpParameter,
    DWORD dwCreationFlags
) {
#ifdef USE_DIRECT_SYSCALLS

    HANDLE hThread = NULL;

    NTSTATUS status = sysNtCreateThreadEx(
        &hThread,
        GENERIC_ALL,
        NULL,
        (HANDLE)-1,          // current process
        lpStartAddress,
        lpParameter,
        dwCreationFlags,
        0,
        0,
        0,
        NULL
    );

    if (status != 0)
        return NULL;

    return hThread;

#else

    return CreateThread(
        NULL,
        0,
        lpStartAddress,
        lpParameter,
        dwCreationFlags,
        NULL
    );

#endif
}

inline DWORD MyWaitForSingleObject(
    HANDLE hObject,
    DWORD dwMilliseconds
) {
#ifdef USE_DIRECT_SYSCALLS

    LARGE_INTEGER timeout;
    PLARGE_INTEGER pTimeout = NULL;

    if (dwMilliseconds != INFINITE) {
        timeout.QuadPart = -(10 * 1000 * (LONGLONG)dwMilliseconds);
        pTimeout = &timeout;
    }

    return sysNtWaitForSingleObject(
        hObject,
        FALSE,
        pTimeout
    );

#else

    return WaitForSingleObject(
        hObject,
        dwMilliseconds
    );

#endif
}