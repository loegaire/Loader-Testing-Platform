# controller/modules/definitions.py

# Map trực tiếp từ -tN value sang C++ preprocessor flag
STAGE_FLAGS = {
    # -t0
    't0': {
        'none':     '',
        'antidebug': '-DEVASION_CHECKS_ENABLED',
    },
    # -t1: chưa có flag (storage mặc định là rdata)
    't1': {
        'rdata': '-DT1_STORAGE_RDATA',
    },
    # -t2
    't2': {
        'local': '-DT2_ALLOC_LOCAL',
    },
    # -t3
    't3': {
        'none': '-DT3_TRANSFORM_NONE',
        'xor':  '-DT3_TRANSFORM_XOR',
        'aes':  '-DT3_TRANSFORM_AES',
    },
    # -t4
    't4': {
        'local': '-DT4_WRITE_LOCAL',
    },
    # -t5
    't5': {
        'local': '-DT5_EXEC_LOCAL',
        'monitors': '-DT5_EXEC_DISPLAY_MONITORS',
    },
}

API_FLAGS = {
    'winapi':   '',
    'indirect': '-DUSE_INDIRECT_WINAPI',
    'syscalls': '-DUSE_DIRECT_SYSCALLS',
}

def get_defines(options):
    defines = []

    # Stage flags
    for stage, mapping in STAGE_FLAGS.items():
        val = options.get(stage, '')
        flag = mapping.get(val, '')
        if flag:
            defines.append(flag)

    # API layer
    api = options.get('api_method', 'winapi')
    flag = API_FLAGS.get(api, '')
    if flag:
        defines.append(flag)

    # Debug
    if options.get('debug'):
        defines.append('-DDEBUG_MODE')

    return " ".join(defines)