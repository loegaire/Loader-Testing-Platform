#pragma once
#include <windows.h>

typedef struct {

    unsigned char* data;
    SIZE_T length;

    unsigned char* key;
    SIZE_T key_len;

    unsigned char* nonce;
    SIZE_T nonce_len;

    unsigned char* transformed;   // decrypted buffer

    unsigned char* allocated_mem;
    HANDLE target_process;          // Set by remote-allocation techniques (T2.3)
    HANDLE target_thread;           // Suspended main thread of target process

} TechniqueContext;