#pragma once
#include "../1_storage/storage_data.h"
#include "../../core/utils.h"

// T1: XOR Decryption Primitive
void Stage3_Transform_XOR(PayloadContext* ctx) {
    if (ctx->key_len == 0) return; 

    for (int i = 0; i < ctx->length; i++) {
        // ctx->key là mảng byte, ctx->data là mảng byte -> XOR bình thường
        ctx->data[i] ^= ctx->key[i % ctx->key_len];
    }
    
    #ifdef DEBUG_MODE
        DEBUG_MSG("Stage 3", "XOR Decryption Complete");
    #endif
}