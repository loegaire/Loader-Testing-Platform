# controller/modules/definitions.py

# Map các tùy chọn CLI sang cờ Preprocessor của C++
# Format: 'cli_option': '-DFLAG_NAME'

ENCRYPTION_FLAGS = {
    'xor': '-DENCRYPTION_XOR',
    'aes': '-DENCRYPTION_AES',
    'none': ''
}

INJECTION_FLAGS = {
    'classic': '-DINJECTION_CLASSIC',
    'hollowing': '-DINJECTION_HOLLOWING',
    'apc': '-DINJECTION_APC', # Ví dụ mở rộng
}

API_FLAGS = {
    'syscalls': '-DUSE_DIRECT_SYSCALLS',
    'winapi-indirect': '-DUSE_INDIRECT_WINAPI',
    'winapi': '' 
}

# Các cờ bật/tắt (Boolean)
FEATURE_FLAGS = {
    'anti_evasion': '-DEVASION_CHECKS_ENABLED',
    'debug': '-DDEBUG_MODE'
}

def get_defines(options):
    """Tổng hợp tất cả các cờ dựa trên options được truyền vào"""
    defines = []
    
    # 1. Encryption
    enc_method = options.get('encryption', 'none')
    if enc_method in ENCRYPTION_FLAGS:
        flag = ENCRYPTION_FLAGS[enc_method]
        if flag: defines.append(flag)
        
    # 2. Injection
    inj_method = options.get('injection', 'classic')
    if inj_method in INJECTION_FLAGS:
        flag = INJECTION_FLAGS[inj_method]
        if flag: defines.append(flag)
        
    # 3. API Method
    api_method = options.get('api_method', 'winapi')
    if api_method in API_FLAGS:
        flag = API_FLAGS[api_method]
        if flag: defines.append(flag)
        
    # 4. Features (Boolean flags)
    for key, flag in FEATURE_FLAGS.items():
        if options.get(key):
            defines.append(flag)
            
    return " ".join(defines)