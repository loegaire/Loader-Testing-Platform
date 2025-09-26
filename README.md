# Nền tảng Tự động hóa Kiểm thử Payload FUD
*(Automated Payload FUD Testing Platform – Research Only)*

## 🎯 Mục tiêu Đồ án
Đây là một dự án **nghiên cứu – giáo dục** nhằm xây dựng một **nền tảng tự động hóa** để kiểm thử và đánh giá hiệu quả của các **kỹ thuật lẩn tránh (evasion techniques)** được sử dụng trong **shellcode loader**.

Mục tiêu chính:
1.  **Đánh giá khả năng phát hiện** của các giải pháp **Antivirus (AV)** và **Endpoint Detection & Response (EDR)** đối với nhiều kỹ thuật mã hóa (encryption) và nạp mã (injection).
2.  Cung cấp **bảng điều khiển (dashboard)** giúp **Red Team** nhanh chóng thử nghiệm kỹ thuật lẩn tránh và giúp **Blue Team** thu thập log, phân tích hành vi.

> ⚠️ **Cảnh báo:** Công cụ chỉ phục vụ **mục đích nghiên cứu và đào tạo** trong **môi trường lab cô lập**.
> Không sử dụng cho bất kỳ hoạt động tấn công trái phép nào.

---

## 💡 Lợi ích cho Red Team và Blue Team
-   **Đối với Red Team**
    -   Cho phép thử nghiệm nhanh nhiều kỹ thuật **obfuscation, injection** trên cùng một shellcode.
    -   Đo lường mức độ thành công của từng kỹ thuật để tối ưu chiến thuật **bypass AV/EDR**.
-   **Đối với Blue Team**
    -   Tự động thu thập log cảnh báo và phân tích hành vi thực tế của các loader.
    -   Cải thiện khả năng phát hiện, điều chỉnh chính sách giám sát và signature.

---

## 🏗️ Kiến trúc Hệ thống
Hệ thống được thiết kế theo mô hình **Dashboard nội bộ**, gồm 4 thành phần chính:

```
[Web Dashboard] → [Core Engine] → [Loader Builder] → [VMware VMs]
```

| Thành phần | Vai trò |
| :--- | :--- |
| **Giao diện Web (Frontend)** | Giao diện Flask, chạy local, cho phép tải shellcode, chọn kỹ thuật, chọn VM. |
| **Core Engine** | Module Python (`core_engine.py`) điều phối toàn bộ: build, deploy, thực thi, thu log. |
| **Loader Builder** | Mã nguồn C++/MinGW-64, đóng gói shellcode + kỹ thuật thành file `.exe`. |
| **VMware Hypervisor** | Chạy các máy ảo Windows với AV/EDR, cung cấp snapshot để reset trạng thái sạch. |

---

## ⚡ Quy trình Làm việc (Workflow)
1.  **Cấu hình & Tải lên** – Người dùng tải lên file shellcode (`.bin`) và chọn các tùy chọn trên Dashboard.
2.  **Build Payload** – Core Engine gọi `builder` biên dịch loader C++ thành file thực thi độc nhất.
3.  **Triển khai & Thực thi** – Payload được tự động đưa vào từng máy ảo và khởi chạy.
4.  **Thu thập & Báo cáo** – Hệ thống thu thập log phát hiện và trạng thái chạy, sau đó xuất báo cáo trên Dashboard.

---

## 📂 Cấu trúc Thư mục

```
FUD_Testing_Platform/
├── app.py              # Backend Flask cho giao diện web
├── core_engine.py      # Logic chính: build, deploy, log
├── requirements.txt    # Thư viện Python cần thiết
├── Makefile            # Cấu hình biên dịch C++
├── .gitignore          # Bỏ qua các file không cần thiết
├── src/                # Mã nguồn C++ của loader
├── templates/          # Giao diện HTML cho Flask
├── shellcodes/         # Lưu shellcode mẫu
├── uploads/            # Shellcode do người dùng upload
├── output/             # Payload .exe sau khi build
└── test_logs/          # Log kết quả từ các máy ảo
```

---

## 🔧 Công nghệ Sử dụng
-   **Python 3.8+** – Flask web dashboard, Core Engine automation.
-   **C++ (MinGW-w64)** – Viết loader, tận dụng Windows API.
-   **HTML/Jinja2** – Xây dựng giao diện người dùng đơn giản.
-   **VMware Workstation/Player** – Quản lý các máy ảo Windows đích.
-   **vmrun CLI** – Điều khiển snapshot, upload file và chạy lệnh trong VM.

---

## ⚙️ Yêu cầu Cài đặt
1.  **Python 3.8+** và `pip`.
2.  **VMware Workstation/Player** và công cụ dòng lệnh `vmrun` (đi kèm với cài đặt VMware trên máy Host).
3.  **MinGW-w64** để biên dịch loader C++.
4.  **Máy ảo (VMs)**:
    -   Hệ điều hành Windows (10/11) đã cài **VMware Tools**.
    -   Cài đặt các **AV/EDR** cần kiểm thử (Defender, SentinelOne, CrowdStrike, OpenEDR…).
    -   Mỗi VM cần một snapshot tên **`clean_snapshot`** để reset sau mỗi bài test.
5.  **Dung lượng**: Đề xuất tối thiểu **100 GB** để lưu nhiều VM và snapshot.

---

## 🚀 Hướng dẫn Cài đặt
1.  **Clone dự án**
    ```bash
    git clone <your-repo-url>
    cd FUD_Testing_Platform
    ```
2.  **Tạo môi trường ảo và cài thư viện**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # Trên Windows
    pip install -r requirements.txt
    ```
3.  **Cấu hình máy ảo**
    -   Chuẩn bị các máy ảo Windows và snapshot như mô tả ở trên.
    -   Cập nhật đường dẫn `.vmx` và thông tin đăng nhập trong `core_engine.py` hoặc file config riêng.
    -   Vô hiệu hóa tính năng **Sample Submission** trong AV để tránh gửi payload ra ngoài.

---

## 💻 Cách Sử dụng
1.  **Khởi động Dashboard**
    ```bash
    python app.py
    ```
    Mở trình duyệt và truy cập: [http://127.0.0.1:5000](http://127.0.0.1:5000)
2.  **Trên giao diện:**
    -   Upload file shellcode `.bin`.
    -   Chọn kỹ thuật mã hóa & injection mong muốn.
    -   Chọn danh sách máy ảo để kiểm thử.
    -   Nhấn **Run Test**.
3.  **Xem kết quả:**
    -   Dashboard sẽ hiển thị trạng thái (SUCCESS/FAILED) và log chi tiết của từng môi trường.
    -   Log cũng được lưu vào thư mục `test_logs/` để phân tích sau.

---

## 📅 Lộ trình Phát triển (Roadmap)

Dự án được chia thành các giai đoạn chính, tập trung vào việc xây dựng nền tảng, nghiên cứu kỹ thuật, và mở rộng khả năng phân tích.

---

### ✅ **Giai đoạn 1: Xây dựng Nền tảng Tự động hóa (Đã hoàn thành)**

Giai đoạn này tập trung vào việc xây dựng bộ khung và quy trình tự động hóa cốt lõi. Các công việc đã hoàn thành bao gồm:

*   **Phát triển Engine Điều khiển (`core_engine.py`):**
    -   Xây dựng logic điều khiển `vmrun` để quản lý máy ảo (revert, start, stop).
    -   Tích hợp chức năng build payload tự động.
    -   Xây dựng C2 Listener đơn giản để xác nhận kết quả.

*   **Xây dựng Giao diện Dòng lệnh (`cli.py`):**
    -   Tạo giao diện CLI cho phép người dùng cấu hình và chạy các bài test một cách linh hoạt.

*   **Phát triển Loader Cơ bản (C++):**
    -   Cài đặt kỹ thuật mã hóa cơ bản: **XOR Encryption**.
    -   Cài đặt kỹ thuật nạp mã cơ bản: **Classic Injection (`CreateThread`)**.

*   **Xây dựng Môi trường Lab Ban đầu:**
    -   Thiết lập máy ảo **Windows Defender** với cấu hình chuẩn.
    -   Cài đặt và cấu hình **Sysmon** để ghi log hành vi chi tiết.
    -   Phát triển script thu thập log tự động cho môi trường Defender & Sysmon.

*   **Hoàn thiện Quy trình Tự động (Pipeline):**
    -   Tự động hóa thành công toàn bộ chuỗi: **Build → Revert VM → Start VM → Deploy → Execute → Collect Logs → Report**.

---

### 🚀 **Giai đoạn 2: Nghiên cứu Kỹ thuật & Mở rộng Lab (Các bước tiếp theo)**

Giai đoạn này tập trung vào mục tiêu nghiên cứu chính của đồ án: phát triển và đánh giá các kỹ thuật lẩn tránh mới.

*   **🔬 Nghiên cứu & Phát triển Kỹ thuật Lẩn tránh:**
    -   **Mã hóa (Encryption):**
        -   Tích hợp mã hóa **AES-256** (sử dụng thư viện C++ hoặc tự triển khai).
    -   **Nạp mã (Injection):**
        -   Triển khai kỹ thuật **Process Hollowing**.
        -   Triển khai kỹ thuật **APC Injection**.
    -   **Lẩn tránh Phân tích (Evasion & Anti-Analysis):**
        -   Cài đặt các kỹ thuật **Anti-Sandbox** (kiểm tra RAM, CPU, thời gian `Sleep`).
        -   Tích hợp **API Hashing** để che giấu các lệnh gọi Windows API nhạy cảm.

*   **🧪 Mở rộng Môi trường Lab:**
    -   Xây dựng và cấu hình máy ảo cho ít nhất **một giải pháp EDR của bên thứ ba** (ví dụ: SentinelOne, Bitdefender...).
    -   Nghiên cứu và phát triển **script thu thập log tùy chỉnh** cho môi trường EDR mới.

*   **🖥️ Phát triển Nền tảng & Giao diện (UI/UX):**
    -   Xây dựng **giao diện web (Dashboard)** cơ bản bằng Flask cho phép cấu hình và chạy test.
    -   Thiết kế trang hiển thị kết quả một cách trực quan (bảng, log có thể thu gọn).

---

### 🌟 **Giai đoạn 3: Phân tích Nâng cao & Hoàn thiện (Tầm nhìn dài hạn)**

Giai đoạn cuối cùng tập trung vào việc biến dữ liệu thu thập được thành các thông tin hữu ích và hoàn thiện công cụ.

*   **📊 Phân tích & Báo cáo Dữ liệu:**
    -   Nâng cấp module thu thập log để lấy được các sự kiện chi tiết hơn (ví dụ: từ các kênh Event Log khác).
    -   Xây dựng một **engine phân tích log dựa trên quy tắc (rule-based)** để tự động nhận diện các mẫu hành vi và cảnh báo tương ứng.
    -   Trực quan hóa dữ liệu (ví dụ: biểu đồ so sánh hiệu quả của các kỹ thuật trên từng AV).

*   **🖥️ Nâng cấp Nền tảng & Giao diện:**
    -   Cải thiện Dashboard với khả năng **hiển thị tiến trình test theo thời gian thực** (sử dụng AJAX/JavaScript).
    -   Thêm chức năng quản lý, xem lại và so sánh kết quả của các lần test cũ.
    
---

## 🔒 Phạm vi & Giới hạn
-   Toàn bộ thử nghiệm **chỉ được thực hiện trên môi trường nội bộ**.
-   Payload được sinh ra **không được phát tán ra Internet**.
-   Đây **không phải công cụ tấn công**, chỉ phục vụ nghiên cứu cho mục đích phòng thủ (Blue Team) và kiểm thử (Red Team).