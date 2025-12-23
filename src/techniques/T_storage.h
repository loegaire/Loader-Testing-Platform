#pragma once
#include <windows.h>

extern unsigned char shellcode[];
extern unsigned int shellcode_len;
extern char* key;

struct PayloadInfo {
    unsigned char* data;
    int length;
    char* key;
};

// S1: Access .rdata Storage
PayloadInfo Stage1_Access_DataSection() {
    
    PayloadInfo info;
    info.data = shellcode;
    info.length = shellcode_len;
    info.key = key;
    
    return info;
}