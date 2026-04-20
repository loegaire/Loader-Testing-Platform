# controller/modules/crypto_utils.py
import os
import tinyaes


def _rotl8(value, shift):
    shift &= 7
    return ((value << shift) | (value >> (8 - shift))) & 0xFF


def _rotl32(value, shift):
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF


def xor_encrypt(data):
    key = os.urandom(16)
    ciphertext = bytearray(b ^ key[i % len(key)] for i, b in enumerate(data))
    return ciphertext, key


def aes_encrypt(data):
    key = os.urandom(16)
    nonce = os.urandom(8)

    # tinyaes needs a 16-byte IV for CTR mode: [8-byte nonce][8-byte counter]
    iv = nonce + b"\x00" * 8
    cipher = tinyaes.AES(key, iv)
    ciphertext = cipher.CTR_xcrypt_buffer(bytes(data))

    return ciphertext, key, nonce


def rc4_encrypt(data):
    key = os.urandom(16)
    sbox = list(range(256))

    # KSA
    j = 0
    for i in range(256):
        j = (j + sbox[i] + key[i % len(key)]) & 0xFF
        sbox[i], sbox[j] = sbox[j], sbox[i]

    # PRGA
    i = 0
    j = 0
    out = bytearray(len(data))
    for idx, b in enumerate(data):
        i = (i + 1) & 0xFF
        j = (j + sbox[i]) & 0xFF
        sbox[i], sbox[j] = sbox[j], sbox[i]
        k = sbox[(sbox[i] + sbox[j]) & 0xFF]
        out[idx] = b ^ k

    return out, key


def _chacha20_quarter_round(state, a, b, c, d):
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 16)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 12)

    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 8)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 7)


def _chacha20_block(key, counter, nonce):
    constants = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]
    key_words = [
        int.from_bytes(key[i:i + 4], "little")
        for i in range(0, 32, 4)
    ]
    nonce_words = [
        int.from_bytes(nonce[i:i + 4], "little")
        for i in range(0, 12, 4)
    ]

    state = constants + key_words + [counter] + nonce_words
    working = state.copy()

    for _ in range(10):
        # column rounds
        _chacha20_quarter_round(working, 0, 4, 8, 12)
        _chacha20_quarter_round(working, 1, 5, 9, 13)
        _chacha20_quarter_round(working, 2, 6, 10, 14)
        _chacha20_quarter_round(working, 3, 7, 11, 15)
        # diagonal rounds
        _chacha20_quarter_round(working, 0, 5, 10, 15)
        _chacha20_quarter_round(working, 1, 6, 11, 12)
        _chacha20_quarter_round(working, 2, 7, 8, 13)
        _chacha20_quarter_round(working, 3, 4, 9, 14)

    for i in range(16):
        working[i] = (working[i] + state[i]) & 0xFFFFFFFF

    return b"".join(word.to_bytes(4, "little") for word in working)


def chacha20_encrypt(data):
    key = os.urandom(32)
    nonce = os.urandom(12)
    counter = 1
    out = bytearray(len(data))

    offset = 0
    while offset < len(data):
        block = _chacha20_block(key, counter, nonce)
        chunk = data[offset:offset + 64]
        for i, b in enumerate(chunk):
            out[offset + i] = b ^ block[i]
        offset += len(chunk)
        counter = (counter + 1) & 0xFFFFFFFF

    return out, key, nonce


def bitwise_encrypt(data):
    # Runtime decrypt is: ROR(byte, 3) then XOR 0x06.
    # Build-time encrypt applies the inverse operation.
    ciphertext = bytearray(_rotl8((b ^ 0x06), 3) for b in data)
    return ciphertext


def apply_encryption(data, method):
    if method == "xor":
        encrypted_data, key = xor_encrypt(data)
        return {
            "method": "xor",
            "ciphertext": encrypted_data,
            "key": key,
        }

    if method == "aes":
        encrypted_data, key, nonce = aes_encrypt(data)
        return {
            "method": "aes-ctr",
            "ciphertext": encrypted_data,
            "key": key,
            "nonce": nonce,
        }

    if method == "rc4":
        encrypted_data, key = rc4_encrypt(data)
        return {
            "method": "rc4",
            "ciphertext": encrypted_data,
            "key": key,
        }

    if method == "chacha20":
        encrypted_data, key, nonce = chacha20_encrypt(data)
        return {
            "method": "chacha20",
            "ciphertext": encrypted_data,
            "key": key,
            "nonce": nonce,
        }

    if method == "bitwise":
        encrypted_data = bitwise_encrypt(data)
        return {
            "method": "bitwise-ror3-xor06",
            "ciphertext": encrypted_data,
            "key": b"",
            "nonce": b"",
        }

    return {
        "method": "none",
        "ciphertext": data,
        "key": b"",
        "nonce": b"",
    }