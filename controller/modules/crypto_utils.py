# controller/modules/crypto_utils.py
import random
import string
import logging
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

logger = logging.getLogger("CryptoUtils")

def xor_encrypt(data):
    key = get_random_bytes(16)
    ciphertext = bytearray(b ^ key[i % len(key)] for i, b in enumerate(data))
    return ciphertext, key

def aes_encrypt(data):
    key = get_random_bytes(32)  # AES-256
    cipher = AES.new(key, AES.MODE_CTR)
    
    ciphertext = cipher.encrypt(data)
    
    return ciphertext, key, cipher.nonce

# Dispatcher: Hàm điều phối chính
def apply_encryption(data, method):
    
    if method == 'xor':
        encrypted_data, key = xor_encrypt(data)
        return {
            "method": "xor",
            "ciphertext": encrypted_data,
            "key": key
        }

    elif method == 'aes':
        encrypted_data, key, nonce = aes_encrypt(data)
        return {
            "method": "aes-ctr",
            "ciphertext": encrypted_data,
            "key": key,
            "nonce": nonce
        }

    else:
        return {
            "method": "none",
            "ciphertext": data,
            "key": ""
        }