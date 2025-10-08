#pragma once
#include <windows.h> 

// =================================================================
//                 WINDOWS INTERNAL STRUCTURES
// =================================================================

// Định nghĩa LIST_ENTRY nếu chưa có
#ifndef _LIST_ENTRY_DEFINED
#define _LIST_ENTRY_DEFINED
typedef struct _LIST_ENTRY {
    struct _LIST_ENTRY* Flink;
    struct _LIST_ENTRY* Blink;
} LIST_ENTRY, * PLIST_ENTRY;
#endif

typedef struct _UNICODE_STRING {
    USHORT Length;
    USHORT MaximumLength;
    PWSTR  Buffer;
} UNICODE_STRING, * PUNICODE_STRING;

struct PEB_LDR_DATA
{
    ULONG Length;
    BOOLEAN Initialized;
    HANDLE SsHandle;
    LIST_ENTRY InLoadOrderModuleList;
    LIST_ENTRY InMemoryOrderModuleList;
    LIST_ENTRY InInitializationOrderModuleList;
    PVOID EntryInProgress;
    BOOLEAN ShutdownInProgress;
    HANDLE ShutdownThreadId;
};
//https://processhacker.sourceforge.io/doc/ntpebteb_8h_source.html#l00008
struct PEB
{
    BOOLEAN InheritedAddressSpace;
    BOOLEAN ReadImageFileExecOptions;
    BOOLEAN BeingDebugged;
    union
    {
        BOOLEAN BitField;
        struct
        {
            BOOLEAN ImageUsesLargePages : 1;
            BOOLEAN IsProtectedProcess : 1;
            BOOLEAN IsImageDynamicallyRelocated : 1;
            BOOLEAN SkipPatchingUser32Forwarders : 1;
            BOOLEAN IsPackagedProcess : 1;
            BOOLEAN IsAppContainer : 1;
            BOOLEAN IsProtectedProcessLight : 1;
            BOOLEAN SpareBits : 1;
        };
    };
    HANDLE Mutant;
    PVOID ImageBaseAddress;
    PEB_LDR_DATA* Ldr;
    //...
};

struct LDR_DATA_TABLE_ENTRY
{
    LIST_ENTRY InLoadOrderLinks;
    LIST_ENTRY InMemoryOrderLinks;
    union
    {
        LIST_ENTRY InInitializationOrderLinks;
        LIST_ENTRY InProgressLinks;
    };
    PVOID DllBase;
    PVOID EntryPoint;
    ULONG SizeOfImage;
    UNICODE_STRING FullDllName;
    UNICODE_STRING BaseDllName;
    //...
};

typedef struct _RTL_USER_PROCESS_PARAMETERS {
    BYTE Reserved1[16];
    PVOID Reserved2[10];
    UNICODE_STRING ImagePathName;
    UNICODE_STRING CommandLine;
} RTL_USER_PROCESS_PARAMETERS, * PRTL_USER_PROCESS_PARAMETERS;

typedef VOID(NTAPI* PPS_POST_PROCESS_INIT_ROUTINE) (VOID);

// // Định nghĩa cho Thread Information Block (TIB) và Thread Environment Block (TEB)
// // TEB chứa một con trỏ đến PEB
// typedef struct _TEB {
//     PVOID Reserved1[12];
//     PPEB ProcessEnvironmentBlock;
//     PVOID Reserved2[399];
//     BYTE Reserved3[1952];
//     PVOID TlsSlots[64];
//     BYTE Reserved4[8];
//     PVOID Reserved5[26];
//     PVOID Reserved6;
//     PVOID Reserved7;
//     PVOID Reserved8;
//     ULONG LastErrorValue;
// } TEB, * PTEB;

