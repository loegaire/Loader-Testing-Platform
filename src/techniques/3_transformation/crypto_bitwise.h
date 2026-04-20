#pragma once
#include "../context.h"
#include "../../core/utils.h"

static __forceinline unsigned char Ror8(unsigned char value, unsigned int shift)
{
    shift &= 7;
    if (shift == 0) return value;
    return (unsigned char)((value >> shift) | (value << (8 - shift)));
}

inline BOOL Stage3_Transform_Bitwise(TechniqueContext* ctx)
{
    if (!ctx) return FALSE;
    if (!ctx->data) return FALSE;

    for (SIZE_T i = 0; i < ctx->length; ++i) {
        ctx->data[i] = (unsigned char)(Ror8(ctx->data[i], 3) ^ 0x06);
    }

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage 3", "Bitwise Deobfuscation Complete (%llu bytes)", ctx->length);
#endif

    return TRUE;
}
