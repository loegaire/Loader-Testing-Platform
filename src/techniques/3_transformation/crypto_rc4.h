#pragma once
#include "../context.h"
#include "../../core/utils.h"
#include "../../api/api_wrappers.h"

inline BOOL Stage3_Transform_RC4(TechniqueContext* ctx)
{
    if (!ctx) return FALSE;
    if (!ctx->data) return FALSE;
    if (!ctx->key || ctx->key_len == 0) return FALSE;

    unsigned char sbox[256] = {0};
    for (unsigned int i = 0; i < 256; ++i) {
        sbox[i] = (unsigned char)i;
    }

    // KSA
    unsigned int j = 0;
    for (unsigned int i = 0; i < 256; ++i) {
        j = (j + sbox[i] + ctx->key[i % ctx->key_len]) & 0xFF;
        unsigned char tmp = sbox[i];
        sbox[i] = sbox[j];
        sbox[j] = tmp;
    }

    // PRGA
    unsigned int i_idx = 0;
    unsigned int j_idx = 0;
    for (SIZE_T n = 0; n < ctx->length; ++n) {
        i_idx = (i_idx + 1) & 0xFF;
        j_idx = (j_idx + sbox[i_idx]) & 0xFF;

        unsigned char tmp = sbox[i_idx];
        sbox[i_idx] = sbox[j_idx];
        sbox[j_idx] = tmp;

        unsigned char k = sbox[(sbox[i_idx] + sbox[j_idx]) & 0xFF];
        ctx->data[n] ^= k;
    }

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 3", "RC4 Decryption Complete (%llu bytes)", ctx->length);
#endif

    return TRUE;
}
