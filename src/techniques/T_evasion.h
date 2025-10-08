#pragma once
#include "../core/win_internals.h"

// // EV1: Check BeingDebugged flag in PEB
// BOOL IsDebugged() {
//     PPEB pPeb = GetPeb();
//     if (pPeb->BeingDebugged) {
//         return TRUE;
//     }
//     return FALSE;
// }

// // EV3: Check for low RAM (common in sandboxes)
// BOOL IsSandboxed_LowRam() {
//     MEMORYSTATUSEX statex;
//     statex.dwLength = sizeof(statex);
//     GlobalMemoryStatusEx(&statex);
//     // Less than 4GB RAM is suspicious
//     if ((statex.ullTotalPhys / 1024 / 1024) < 4096) {
//         return TRUE;
//     }
//     return FALSE;
// }

// // EV4: Check for Sleep acceleration
// BOOL IsSandboxed_Sleep() {
//     DWORD startTime = GetTickCount();
//     Sleep(3000); // Request a 3-second sleep
//     DWORD endTime = GetTickCount();
//     // If the sleep duration was less than 2.5 seconds, it was likely accelerated.
//     if ((endTime - startTime) < 2500) {
//         return TRUE;
//     }
//     return FALSE;
// }

