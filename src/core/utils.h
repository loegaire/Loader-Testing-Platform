#pragma once
#include "win_internals.h"
#include <windows.h>
#include <iostream>
#include <tlhelp32.h>

// =================================================================
//                      UTILITY FUNCTIONS
// =================================================================

#ifdef DEBUG_MODE
    #define DEBUG_MSG(title, msg) MessageBoxA(NULL, msg, title, MB_OK)
#else
    #define DEBUG_MSG(title, msg)
#endif

__forceinline PEB* GetPeb()
{
#ifdef _WIN64
    return (PEB*)__readgsqword(0x60);
#else
    return (PEB*)__readfsdword(0x30);
#endif
}

void sprintf_address(char* buffer, size_t buffer_size, const void* address) {
    sprintf_s(buffer, buffer_size, "0x%p", address);
}

// Khai báo lại các biến extern để file này có thể sử dụng
extern PVOID g_syscall_addr;
extern DWORD g_ssn_NtAllocateVirtualMemory;
extern DWORD g_ssn_NtCreateThreadEx;
extern DWORD g_ssn_NtWaitForSingleObject;

DWORD GetProcessIdByName(LPCUWSTR procname) {
    DWORD pid = 0;
    HANDLE hProcSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hProcSnap == INVALID_HANDLE_VALUE) {
        return 0;
    }

    PROCESSENTRY32W pe32;
    pe32.dwSize = sizeof(pe32);

    if (!Process32FirstW(hProcSnap, &pe32)) {
        CloseHandle(hProcSnap);
        return 0;
    }

    while (Process32NextW(hProcSnap, &pe32)) {
        if (lstrcmpiW(procname, pe32.szExeFile) == 0) {
            pid = pe32.th32ProcessID;
            break;
        }
    }

    CloseHandle(hProcSnap);
    return pid;
}

BOOL IsStringEqual(IN LPCWSTR Str1, IN LPCWSTR Str2) {
    WCHAR lStr1[MAX_PATH], lStr2[MAX_PATH];
    int len1 = lstrlenW(Str1), len2 = lstrlenW(Str2);
    int i = 0;

    // Checking length
    if (len1 >= MAX_PATH || len2 >= MAX_PATH) {
        return FALSE;
    }

    // Converting Str1 to lower case string
    for (i = 0; i < len1; i++) {
        lStr1[i] = (WCHAR)tolower(Str1[i]);
    }
    lStr1[i] = L'\0'; // Null terminating

    // Converting Str2 to lower case
    for (i = 0; i < len2; i++) {
        lStr2[i] = (WCHAR)tolower(Str2[i]);
    }
    lStr2[i] = L'\0'; // Null terminating

    return (lstrcmpiW(lStr1, lStr2) == 0);
}

HMODULE CustomGetModuleHandle(IN LPCWSTR moduleName) {

#ifdef _WIN64
    PEB * ProcEnvBlk = (PEB *) __readgsdword(0x60);
#elif _WIN32
    PEB * ProcEnvBlk = (PEB *)__readgsqword(0x30);
#endif

    // return base address of a calling module
    if (moduleName == NULL) 
        return (HMODULE) (ProcEnvBlk->ImageBaseAddress);

    PEB_LDR_DATA * Ldr = ProcEnvBlk->Ldr;
    LIST_ENTRY * ModuleList = NULL;
    
    ModuleList = &Ldr->InMemoryOrderModuleList;
    LIST_ENTRY *  pStartListEntry = ModuleList->Flink;

    for (LIST_ENTRY *  pListEntry  = pStartListEntry;       // start from beginning of InMemoryOrderModuleList
                       pListEntry != ModuleList;            // walk all list entries
                       pListEntry  = pListEntry->Flink) {
        
        // get current Data Table Entry
        LDR_DATA_TABLE_ENTRY * pEntry = (LDR_DATA_TABLE_ENTRY *) ((BYTE *) pListEntry - sizeof(LIST_ENTRY));

        // check if module is found and return its base address
        if (strcmp((const char *) pEntry->BaseDllName.Buffer, (const char *) moduleName) == 0)
            return (HMODULE) pEntry->DllBase;
    }

    // otherwise:
    return NULL;

}

FARPROC CustomGetProcProcess(IN HMODULE hMod, IN LPCSTR funcName) {
    
    char * pBaseAddr = (char *) hMod;

    // get pointers to main headers/structures
    IMAGE_DOS_HEADER * pDosHdr = (IMAGE_DOS_HEADER *) pBaseAddr;
    IMAGE_NT_HEADERS * pNTHdr = (IMAGE_NT_HEADERS *) (pBaseAddr + pDosHdr->e_lfanew);
    IMAGE_OPTIONAL_HEADER * pOptionalHdr = &pNTHdr->OptionalHeader;
    IMAGE_DATA_DIRECTORY * pExportDataDir = (IMAGE_DATA_DIRECTORY *) (&pOptionalHdr->DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT]);
    IMAGE_EXPORT_DIRECTORY * pExportDirAddr = (IMAGE_EXPORT_DIRECTORY *) (pBaseAddr + pExportDataDir->VirtualAddress);

    // resolve addresses to Export Address Table, table of function names and "table of ordinals"
    DWORD * pEAT = (DWORD *) (pBaseAddr + pExportDirAddr->AddressOfFunctions);
    DWORD * pFuncNameTbl = (DWORD *) (pBaseAddr + pExportDirAddr->AddressOfNames);
    WORD * pHintsTbl = (WORD *) (pBaseAddr + pExportDirAddr->AddressOfNameOrdinals);

    // function address we're looking for
    FARPROC pProcAddr = NULL;

    // resolve function by ordinal
    if (((DWORD_PTR)funcName >> 16) == 0) {
        WORD ordinal = (WORD)((uintptr_t)funcName & 0xFFFF);   // convert to WORD
        DWORD Base = pExportDirAddr->Base;          // first ordinal number

        // check if ordinal is not out of scope
        if (ordinal < Base || ordinal >= Base + pExportDirAddr->NumberOfFunctions)
            return NULL;

        // get the function virtual address = RVA + BaseAddr
        pProcAddr = (FARPROC) (pBaseAddr + (DWORD_PTR) pEAT[ordinal - Base]);
    }
    // resolve function by name
    else {
        // parse through table of function names
        for (DWORD i = 0; i < pExportDirAddr->NumberOfNames; i++) {
            char * sTmpFuncName = (char *) pBaseAddr + (DWORD_PTR) pFuncNameTbl[i];
    
            if (strcmp(funcName, sTmpFuncName) == 0)   {
                // found, get the function virtual address = RVA + BaseAddr
                pProcAddr = (FARPROC) ((ULONG_PTR)pBaseAddr + (DWORD_PTR) pEAT[pHintsTbl[i]]);
                break;
            }
        }
    }

    return (FARPROC) pProcAddr;
}

// Hàm tìm địa chỉ của stub syscall và lệnh "syscall"
BOOL FindSyscall(const char* funcName, DWORD& syscallId, PVOID& syscallInstAddr) {

    std::cerr << funcName;

    HMODULE hNtdll = CustomGetModuleHandle(L"ntdll.dll");
    if (!hNtdll) return FALSE;

    FARPROC pFunc = CustomGetProcProcess(hNtdll, funcName);
    if (!pFunc) return FALSE;

    BYTE* pByte = (BYTE*)pFunc;

    // Tìm mẫu stub: 4C 8B D1 B8 xx xx 00 00
    //             mov r10,rcx | mov eax, id
    if (pByte[0] == 0x4C && pByte[1] == 0x8B && pByte[2] == 0xD1 && pByte[3] == 0xB8) {
        // Lấy Syscall ID
        syscallId = *(DWORD*)(pByte + 4);

        // Tìm lệnh "syscall" (0F 05) trong 32 byte tiếp theo
        for (int i = 0; i < 32; ++i) {
            if (pByte[i] == 0x0F && pByte[i + 1] == 0x05) {
                syscallInstAddr = (PVOID)(pByte + i);
                return TRUE;
            }
        }
    }
    return FALSE;
}

BOOL InitializeSyscalls() {
    if (!FindSyscall("NtAllocateVirtualMemory", g_ssn_NtAllocateVirtualMemory, g_syscall_addr)) return FALSE;
    if (!FindSyscall("NtCreateThreadEx", g_ssn_NtCreateThreadEx, g_syscall_addr)) return FALSE;
    if (!FindSyscall("NtWaitForSingleObject", g_ssn_NtWaitForSingleObject, g_syscall_addr)) return FALSE;
    
    // Find Syscall for other APIs
    
    return TRUE;
}