#pragma once
#include "../core/win_internals.h"

// Các biến toàn cục để lưu trữ thông tin syscall động
// Chúng sẽ được khởi tạo một lần duy nhất trong hàm main()
extern PVOID g_syscall_addr;
extern DWORD g_ssn_NtAllocateVirtualMemory;
extern DWORD g_ssn_NtCreateThreadEx;
extern DWORD g_ssn_NtWaitForSingleObject;
// ... thêm các SSN khác ở đây

// Khai báo các hàm assembly. Tên hàm giữ nguyên nhưng không cần truyền SSN nữa.
extern "C" {
    NTSTATUS sysNtAllocateVirtualMemory(HANDLE, PVOID*, ULONG_PTR, PSIZE_T, ULONG, ULONG);
    NTSTATUS sysNtCreateThreadEx(PHANDLE, ACCESS_MASK, PVOID, HANDLE, PVOID, PVOID, ULONG, SIZE_T, SIZE_T, SIZE_T, PVOID);
    NTSTATUS sysNtWaitForSingleObject(HANDLE, BOOLEAN, PLARGE_INTEGER);
    // ... thêm các hàm assembly khác ở đây
}