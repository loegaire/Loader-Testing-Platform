; src/api/syscall.asm - Viết cho NASM, định dạng Win64

; Khai báo các biến toàn cục mà file C++ sẽ cung cấp
extern g_syscall_addr
extern g_ssn_NtAllocateVirtualMemory
extern g_ssn_NtCreateThreadEx
extern g_ssn_NtWaitForSingleObject
; ...

; Khai báo các hàm để C++ có thể gọi
global sysNtAllocateVirtualMemory
global sysNtCreateThreadEx
global sysNtWaitForSingleObject
; ...

section .text

sysNtAllocateVirtualMemory:
    mov r10, rcx
    ; --- THAY ĐỔI QUAN TRỌNG ---
    ; Sử dụng Rip-Relative Addressing
    mov eax, dword [rel g_ssn_NtAllocateVirtualMemory]
    jmp qword [rel g_syscall_addr]
    ret

sysNtCreateThreadEx:
    mov r10, rcx
    ; --- THAY ĐỔI QUAN TRỌNG ---
    mov eax, dword [rel g_ssn_NtCreateThreadEx]
    jmp qword [rel g_syscall_addr]
    ret

sysNtWaitForSingleObject:
    mov r10, rcx
    ; --- THAY ĐỔI QUAN TRỌNG ---
    mov eax, dword [rel g_ssn_NtWaitForSingleObject]
    jmp qword [rel g_syscall_addr]
    ret

; ... các hàm syscall khác theo cùng mẫu ...