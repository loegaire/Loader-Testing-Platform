# Hướng dẫn Cài đặt Môi trường Lab Ảo hóa

Tài liệu này mô tả quy trình chuẩn để tạo các máy ảo (VM) phục vụ cho việc kiểm thử payload tự động. Quy trình gồm 2 giai đoạn chính:
1.  **Tạo "Golden Image"**: Một máy ảo Windows gốc, sạch, đã được cấu hình sẵn các công cụ cần thiết.
2.  **Tạo VM Kiểm thử**: Nhân bản từ "Golden Image" và cài đặt các sản phẩm bảo mật cụ thể.

---

## Giai đoạn 1: Tạo "Golden Image" VM (Làm 1 lần duy nhất)

Mục tiêu của giai đoạn này là tạo ra một snapshot gốc tên là **`clean_install`**. Đây là "khuôn" để đúc ra tất cả các máy ảo kiểm thử sau này.

**Checklist các bước cần làm TRƯỚC KHI tạo snapshot `clean_install`:**

1.  **Cài đặt Windows:**
    -   Tạo một máy ảo mới và cài đặt Windows 10 hoặc Windows 11.
    -   Hoàn thành quá trình OOBE (Out-of-Box Experience).

2.  **Cập nhật Hệ điều hành:**
    -   Chạy Windows Update cho đến khi không còn bản cập nhật quan trọng nào. Việc này đảm bảo môi trường ổn định và thực tế.

3.  **Cài đặt VMware Tools:**
    -   Từ menu VMware, chọn `VM > Install VMware Tools...`.
    -   **Lý do:** Đây là bước **bắt buộc** để `vmrun` có thể giao tiếp với máy ảo (copy file, chạy lệnh).

4.  **Tạo User cho việc Test:**
    -   Tạo một tài khoản Local User (không dùng tài khoản Microsoft).
    -   Đặt tên và mật khẩu đơn giản (ví dụ: `user: test`, `pass: test`).
    -   Đăng nhập bằng tài khoản này.
    -   **Lý do:** Cung cấp thông tin xác thực cho `vmrun` để chạy lệnh trong Guest OS.

5.  **Cấu hình Hệ thống:**
    -   Tắt User Account Control (UAC) về mức thấp nhất.
    -   Tắt các thông báo không cần thiết.
    -   **Tắt Windows Firewall (Tạm thời):** Sẽ được bật lại trên từng VM cụ thể sau.
    -   **Tắt Windows Defender Real-time Protection (Tạm thời):** Để tránh việc nó cản trở quá trình cài đặt các công cụ sau.

6.  **Cài đặt các Công cụ Nền tảng:**
    -   **Cài đặt Sysmon:**
        -   Tải Sysmon từ Microsoft và file cấu hình (ví dụ: của SwiftOnSecurity).
        -   Cài đặt qua PowerShell (Admin): `.\sysmon.exe -accepteula -i sysmonconfig.xml`.
    -   **Tạo Script Thu thập Log:**
        -   Tạo file `collect_logs.ps1` trên Desktop của user `test`.
        -   Dán nội dung script PowerShell (phiên bản có cả Defender và Sysmon) vào file này.

7.  **Dọn dẹp và Hoàn tất:**
    -   Xóa các file cài đặt, dọn dẹp Recycle Bin.
    -   Khởi động lại máy ảo một lần cuối để đảm bảo mọi thứ ổn định.
    -   Shutdown máy ảo.

8.  **Tạo Snapshot Gốc:**
    -   Trong VMware, tạo một snapshot và đặt tên chính xác là: **`clean_install`**.

---

## Giai đoạn 2: Tạo VM Kiểm thử Cụ thể (Lặp lại cho mỗi AV)

Mục tiêu của giai đoạn này là tạo ra các máy ảo sẵn sàng cho việc test, mỗi máy có một snapshot tên là **`clean_snapshot`**.

**Checklist các bước cần làm TRƯỚC KHI tạo snapshot `clean_snapshot`:**

1.  **Nhân bản từ "Golden Image":**
    -   Tạo một **Full Clone** từ máy ảo "Golden Image".
    -   **Quan trọng:** Chọn clone từ trạng thái snapshot `clean_install`.
    -   Đặt tên cho máy ảo mới thật rõ ràng (ví dụ: `Win11_Defender`, `Win11_SentinelOne`).

2.  **Cài đặt Sản phẩm Bảo mật:**
    -   Khởi động máy ảo mới.
    -   **Nếu là VM Defender:**
        -   Bật lại Windows Defender Real-time Protection.
        -   Bật lại Windows Firewall.
        -   Chạy Windows Update để cập nhật signature cho Defender.
    -   **Nếu là VM cho AV/EDR khác:**
        -   Cài đặt phần mềm AV/EDR tương ứng (Bitdefender, Kaspersky, SentinelOne...).
        -   Làm theo hướng dẫn cài đặt của hãng.

3.  **Cấu hình Sản phẩm Bảo mật:**
    -   **Quan trọng nhất:** Mở giao diện của AV/EDR, tìm và **VÔ HIỆU HÓA** tất cả các tính năng liên quan đến:
        -   **Automatic Sample Submission** (Tự động gửi mẫu)
        -   **Cloud Protection** (Bảo vệ từ đám mây)
        -   **Data Sharing / Telemetry** (Chia sẻ dữ liệu)
    -   Cập nhật cơ sở dữ liệu virus (virus definitions) lên phiên bản mới nhất.

4.  **Kiểm tra và Hoàn tất:**
    -   Đảm bảo `collect_logs.ps1` vẫn còn trên Desktop.
    -   Đảm bảo Sysmon vẫn đang chạy.
    -   Khởi động lại máy ảo để chắc chắn rằng dịch vụ của AV/EDR khởi động cùng hệ thống và hoạt động bình thường.
    -   Shutdown máy ảo.

5.  **Tạo Snapshot Kiểm thử:**
    -   Trong VMware, tạo một snapshot và đặt tên chính xác là: **`clean_snapshot`**.

Bây giờ máy ảo này đã sẵn sàng để được `core_engine.py` điều khiển. Lặp lại Giai đoạn 2 cho mỗi sản phẩm bảo mật bạn muốn đưa vào hệ thống kiểm thử của mình.