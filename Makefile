.PHONY: build clean

# --- Trình biên dịch & Assembler ---
# CC: Trình biên dịch C++ (MinGW)
# AS: Assembler (NASM)
CC = x86_64-w64-mingw32-g++
AS = nasm

# --- Thư mục ---
SRC_DIR = src
BUILD_DIR = build/src
OBJ_DIR = build/obj
OUT_DIR = build/bin

# --- Cờ biên dịch & Lắp ráp ---
CFLAGS = -s -O2 -Wall -I$(SRC_DIR) -I$(BUILD_DIR) -DAES_CTR=1 -lws2_32 \
         -Wno-write-strings -ffunction-sections -fdata-sections $(DEFINES) \
         -static-libgcc -static-libstdc++
ASFLAGS = -f win64
LDFLAGS = -Wl,--gc-sections

# --- Định nghĩa các file Object ---
CPP_OBJ = $(OBJ_DIR)/$(patsubst %.cpp,%.obj,$(SRC))
ASM_OBJ = $(OBJ_DIR)/syscall.obj
AES_OBJ = $(OBJ_DIR)/aes.obj
OBJS = $(CPP_OBJ) $(ASM_OBJ) $(AES_OBJ)

ifeq ($(OS),Windows_NT)
    RM = rmdir /s /q
else
    RM = rm -rf
endif

# --- Các quy tắc (Rules) ---

# Target chính: build một file exe cụ thể
# Ví dụ: make build SRC=generated_loader.cpp OUT=payload.exe
build: $(OUT_DIR)/$(OUT)

# Quy tắc để liên kết các file object thành file exe cuối cùng
$(OUT_DIR)/$(OUT): $(OBJS)
	@echo " [LD] Linking object files into $(@)..."
	$(CC) -o $@ $^ $(LDFLAGS)

# Quy tắc để biên dịch file .cpp được tạo ra thành .obj
$(OBJ_DIR)/%.obj: $(BUILD_DIR)/%.cpp
	@echo " [CXX] Compiling $(<) to $(@)..."
	$(CC) -c -o $@ $< $(CFLAGS)

# Quy tắc để lắp ráp file .asm thành .obj
$(OBJ_DIR)/syscall.obj: $(SRC_DIR)/api/syscall.asm
	@echo " [ASM] Assembling $(<) to $(@)..."
	$(AS) $(ASFLAGS) $< -o $@

$(OBJ_DIR)/aes.obj: $(SRC_DIR)/techniques/3_transformation/aes.c
	@echo " [CC] Compiling $(<) to $(@)..."
	$(CC) -c -o $@ $< $(CFLAGS)

# Clean target
clean:
	@echo " [CLEAN] Removing build artifacts..."
	$(RM) $(OUT_DIR)/* $(BUILD_DIR)/* $(OBJ_DIR)/*