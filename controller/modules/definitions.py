# controller/modules/definitions.py

# Map trực tiếp từ -tN value sang C++ preprocessor flag
STAGE_FLAGS = {
    # -t0
    't0': {
        'none':       '-DT0_ANTIANALYSIS_NONE',
        'antidebug':  '-DT0_ANTIANALYSIS_DEBUG',
        'sleep_skew': '-DT0_ANTIANALYSIS_SLEEP_SKEW',
    },
    # -t1
    't1': {
        'rdata': '-DT1_STORAGE_RDATA',
        'data':  '-DT1_STORAGE_DATA',
    },
    # -t2
    't2': {
        'local':    '-DT2_ALLOC_LOCAL',
        'local_rw': '-DT2_ALLOC_LOCAL_RW',
        'remote':   '-DT2_ALLOC_REMOTE',
        'spawn':    '-DT2_ALLOC_SPAWN',
    },
    # -t3
    't3': {
        'none':     '-DT3_TRANSFORM_NONE',
        'xor':      '-DT3_TRANSFORM_XOR',
        'aes':      '-DT3_TRANSFORM_AES',
        'rc4':      '-DT3_TRANSFORM_RC4',
        'chacha20': '-DT3_TRANSFORM_CHACHA20',
        'bitwise':  '-DT3_TRANSFORM_BITWISE',
    },
    # -t4
    't4': {
        'local':    '-DT4_WRITE_LOCAL',
        'local_rx': '-DT4_WRITE_LOCAL_RX',
        'remote':   '-DT4_WRITE_REMOTE',
    },
    # -t5
    't5': {
        'local':         '-DT5_EXEC_LOCAL',
        'monitors':      '-DT5_EXEC_DISPLAY_MONITORS',
        'fiber':         '-DT5_EXEC_FIBER',
        'remote_thread': '-DT5_EXEC_REMOTE_THREAD',
    },
}

API_FLAGS = {
    'winapi':   '',
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
