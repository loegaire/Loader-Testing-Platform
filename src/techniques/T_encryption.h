#pragma once
#include "T_storage.h"
#include <windows.h>
#include <string.h>

void Stage3_Decrypt_XOR(PayloadInfo* payload) {
    // In-place decryption
    int key_len = 0;
    while (payload->key[key_len] != '\0') key_len++;

    for (int i = 0; i < payload->length; i++) {
        // Truy cập thông qua con trỏ payload->
        payload->data[i] = payload->data[i] ^ payload->key[i % key_len];
    }
}