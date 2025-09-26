#pragma once
#include <windows.h>
#include <string.h>

void Decrypt_XOR(unsigned char* data, int data_len, const char* key) {
    int key_len = strlen(key);
    for (int i = 0; i < data_len; i++) {
        data[i] = data[i] ^ key[i % key_len];
    }
}

