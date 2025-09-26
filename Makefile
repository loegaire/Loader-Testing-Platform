.PHONY: build clean

# Trình biên dịch C++ (cross-compiler cho Windows)
CC = x86_64-w64-mingw32-g++

# Các cờ biên dịch: -s (strip symbols), -O2 (tối ưu hóa), -Wall (hiển thị cảnh báo)
# -lws2_32: Link thư viện Windows Sockets
# -Wno-write-strings: Tắt cảnh báo khi gán chuỗi ký tự cho char* (hữu ích cho key)
CFLAGS = -s -O2 -Wall -Isrc -lws2_32 -Wno-write-strings

# Thư mục
SRC_DIR = build
OUT_DIR = output

# Target mặc định
all:
	@echo "Usage: make build SRC=<source_file> OUT=<output_file>"

# Target để build payload
build:
	$(CC) $(SRC_DIR)/$(SRC) -o $(OUT_DIR)/$(OUT) $(CFLAGS)
	@echo " [+] Payload built successfully: $(OUT_DIR)/$(OUT)"

# Target để dọn dẹp
clean:
	rm -f $(OUT_DIR)/* $(SRC_DIR)/*