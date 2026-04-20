#pragma once
#include "../context.h"
#include "../../core/utils.h"
#include "../../api/api_wrappers.h"

static __forceinline unsigned int ChachaRotl32(unsigned int v, int shift)
{
    return (v << shift) | (v >> (32 - shift));
}

static __forceinline unsigned int ChachaLoad32LE(const unsigned char* p)
{
    return (unsigned int)p[0] |
           ((unsigned int)p[1] << 8) |
           ((unsigned int)p[2] << 16) |
           ((unsigned int)p[3] << 24);
}

static __forceinline void ChachaStore32LE(unsigned char* p, unsigned int v)
{
    p[0] = (unsigned char)(v & 0xFF);
    p[1] = (unsigned char)((v >> 8) & 0xFF);
    p[2] = (unsigned char)((v >> 16) & 0xFF);
    p[3] = (unsigned char)((v >> 24) & 0xFF);
}

static __forceinline void ChachaQuarterRound(
    unsigned int& a,
    unsigned int& b,
    unsigned int& c,
    unsigned int& d)
{
    a += b; d ^= a; d = ChachaRotl32(d, 16);
    c += d; b ^= c; b = ChachaRotl32(b, 12);
    a += b; d ^= a; d = ChachaRotl32(d, 8);
    c += d; b ^= c; b = ChachaRotl32(b, 7);
}

static void Chacha20Block(
    const unsigned int key[8],
    unsigned int counter,
    const unsigned int nonce[3],
    unsigned char out[64])
{
    const unsigned int constants[4] = {
        0x61707865u, 0x3320646eu, 0x79622d32u, 0x6b206574u
    };

    unsigned int state[16] = {
        constants[0], constants[1], constants[2], constants[3],
        key[0], key[1], key[2], key[3],
        key[4], key[5], key[6], key[7],
        counter,
        nonce[0], nonce[1], nonce[2]
    };

    unsigned int x[16];
    for (int i = 0; i < 16; ++i) x[i] = state[i];

    for (int i = 0; i < 10; ++i) {
        // Column rounds
        ChachaQuarterRound(x[0], x[4], x[8], x[12]);
        ChachaQuarterRound(x[1], x[5], x[9], x[13]);
        ChachaQuarterRound(x[2], x[6], x[10], x[14]);
        ChachaQuarterRound(x[3], x[7], x[11], x[15]);

        // Diagonal rounds
        ChachaQuarterRound(x[0], x[5], x[10], x[15]);
        ChachaQuarterRound(x[1], x[6], x[11], x[12]);
        ChachaQuarterRound(x[2], x[7], x[8], x[13]);
        ChachaQuarterRound(x[3], x[4], x[9], x[14]);
    }

    for (int i = 0; i < 16; ++i) {
        x[i] += state[i];
        ChachaStore32LE(out + (i * 4), x[i]);
    }
}

inline BOOL Stage3_Transform_ChaCha20(TechniqueContext* ctx)
{
    if (!ctx) return FALSE;
    if (!ctx->data) return FALSE;
    if (!ctx->key || ctx->key_len != 32) return FALSE;
    if (!ctx->nonce || ctx->nonce_len != 12) return FALSE;

    unsigned int key_words[8];
    unsigned int nonce_words[3];

    for (int i = 0; i < 8; ++i) {
        key_words[i] = ChachaLoad32LE(ctx->key + (i * 4));
    }
    for (int i = 0; i < 3; ++i) {
        nonce_words[i] = ChachaLoad32LE(ctx->nonce + (i * 4));
    }

    unsigned int counter = 1;
    SIZE_T offset = 0;
    while (offset < ctx->length) {
        unsigned char block[64] = {0};
        Chacha20Block(key_words, counter, nonce_words, block);

        SIZE_T remain = ctx->length - offset;
        SIZE_T chunk = (remain < sizeof(block)) ? remain : sizeof(block);
        for (SIZE_T i = 0; i < chunk; ++i) {
            ctx->data[offset + i] ^= block[i];
        }

        SecureZeroMemory(block, sizeof(block));
        counter++;
        offset += chunk;
    }

    SecureZeroMemory(key_words, sizeof(key_words));

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 3", "ChaCha20 Decryption Complete (%llu bytes)", ctx->length);
#endif

    return TRUE;
}
