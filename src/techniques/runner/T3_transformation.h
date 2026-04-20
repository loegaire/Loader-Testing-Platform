#pragma once
#include "../context.h"

#ifdef T3_TRANSFORM_XOR
#include "../3_transformation/crypto_xor.h"
#endif

#ifdef T3_TRANSFORM_AES
#include "../3_transformation/crypto_aes.h"
#endif

#ifdef T3_TRANSFORM_RC4
#include "../3_transformation/crypto_rc4.h"
#endif

#ifdef T3_TRANSFORM_CHACHA20
#include "../3_transformation/crypto_chacha20.h"
#endif

#ifdef T3_TRANSFORM_BITWISE
#include "../3_transformation/crypto_bitwise.h"
#endif

inline BOOL Run_T3_Transform(TechniqueContext* ctx)
{

#ifdef T3_TRANSFORM_NONE
    return TRUE;
#endif

#ifdef T3_TRANSFORM_XOR
    return Stage3_Transform_XOR(ctx);
#endif

#ifdef T3_TRANSFORM_AES
    return Stage3_Transform_AES(ctx);
#endif

#ifdef T3_TRANSFORM_RC4
    return Stage3_Transform_RC4(ctx);
#endif

#ifdef T3_TRANSFORM_CHACHA20
    return Stage3_Transform_ChaCha20(ctx);
#endif

#ifdef T3_TRANSFORM_BITWISE
    return Stage3_Transform_Bitwise(ctx);
#endif

    return FALSE;
}