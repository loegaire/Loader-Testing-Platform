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

inline BOOL MyVirtualProtect(
    PVOID lpAddress,
    SIZE_T dwSize,
    ULONG flNewProtect,
    PULONG lpflOldProtect
) {
#ifdef USE_DIRECT_SYSCALLS
    PVOID baseAddress = lpAddress;
    SIZE_T regionSize = dwSize;

    NTSTATUS status = sysNtProtectVirtualMemory(
        (HANDLE)-1,
        &baseAddress,
        &regionSize,
        flNewProtect,
        lpflOldProtect
    );

    return status == 0;

#else

    return VirtualProtect(
        lpAddress,
        dwSize,
        flNewProtect,
        (PDWORD)lpflOldProtect
    );

#endif
}

inline HANDLE MyCreateThreadEx(
    HANDLE hProcess,
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
        hProcess,
        (PVOID)lpStartAddress,
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

    return CreateRemoteThreadEx(
        hProcess,
        NULL,
        0,
        lpStartAddress,
        lpParameter,
        dwCreationFlags,
        NULL,
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