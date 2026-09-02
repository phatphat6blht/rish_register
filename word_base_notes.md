# HƯỚNG DẪN CHI TIẾT TỪNG BƯỚC THỰC HIỆN BÁO CÁO RISK REGISTER & DASHBOARD DOCKER
*(Sử dụng làm tài liệu căn bản để soạn thảo Báo cáo Word)*

---

## BƯỚC 1: TỔ CHỨC CẤU TRÚC THƯ MỤC VÀ CẤU HÌNH MÔI TRƯỜNG

### 1.1. Lý do thiết kế & Mục đích
- Đóng gói ứng dụng thành mô hình microservices giúp quản lý dễ dàng và đồng bộ môi trường.
- Phân tách cấu hình nhạy cảm (biến môi trường như mật khẩu, tên DB) ra khỏi mã nguồn để đảm bảo an toàn thông tin (tuân thủ tiêu chuẩn OWASP / 12-Factor App).
- File `.env.example` cung cấp mẫu cấu hình an toàn không chứa mật khẩu thật để commit lên Git repo.

### 1.2. Các tệp tin cấu hình đã tạo
- `.env`: Chứa biến môi trường chạy thật (đã add vào `.gitignore`).
- `.env.example`: Tệp tin mẫu môi trường.
- `.gitignore`: Loại bỏ các file nhạy cảm và dữ liệu tạm khỏi Git.

### 📸 Vị trí cần chụp ảnh cho báo cáo:
1. Ảnh cây thư mục dự án (`tree` hoặc giao diện VS Code/Explorer).
2. Ảnh nội dung file `.env.example` và `.gitignore`.

---

## BƯỚC 2: THIẾT KẾ MÔ HÌNH DỮ LIỆU BẢO MẬT & DATABASE INIT

### 2.1. Thiết kế 4 Bảng Register (SQLAlchemy Models)
1. **Asset Register (`assets`)**: Quản lý tài sản CNTT (Tên, Loại tài sản, Chủ sở hữu, Mức độ quan trọng 1-5).
2. **Threat Register (`threats`)**: Quản lý mối đe dọa (Tên, Nhóm đe dọa như Malware, Phishing, Insider...).
3. **Vulnerability Register (`vulnerabilities`)**: Quản lý điểm yếu / lỗ hổng (Tên, CVE ID, Mức độ nghiêm trọng).
4. **Risk Register (`risks`)**: Liên kết Asset + Threat + Vulnerability, chứa:
   - **Likelihood (Khả năng xảy ra)**: Thang 1 - 5.
   - **Impact (Mức độ ảnh hưởng)**: Thang 1 - 5.
   - **Risk Score = Likelihood × Impact**: Tự động tính toán khi lưu (Thang 1 - 25).
   - **Risk Level (Mức rủi ro)**: Tự động phân loại:
     - **Critical** (Nghiêm trọng): Score ≥ 20
     - **High** (Cao): Score 12 – 19
     - **Medium** (Trung bình): Score 5 – 11
     - **Low** (Thấp): Score 1 – 4
   - **Status**: Trạng thái xử lý (`Open`, `Mitigating`, `Accepted`, `Closed`).

### 2.2. Thiết lập Bảo mật Cơ sở dữ liệu (`db/init.sql`)
- Tạo Role `metabase_readonly` dành riêng cho dịch vụ Metabase Dashboard.
- Áp dụng **Nguyên tắc Phân quyền Tối thiểu (Principle of Least Privilege)**: Role này CHỈ được phép `SELECT` (đọc dữ liệu), KHÔNG thể `INSERT/UPDATE/DELETE`.

### 📸 Vị trí cần chụp ảnh cho báo cáo:
1. Sơ đồ liên kết ERD giữa 4 bảng.
2. Đoạn code tự động tính `Risk Score` & `Risk Level` trong `flask_app/models.py`.
3. Tệp tin `db/init.sql` thể hiện lệnh phân quyền `GRANT SELECT`.

---

## BƯỚC 3: XÂY DỰNG ỨNG DỤNG WEB NỘI BỘ (FLASK APP)

### 3.1. Chức năng chính của Flask App
- **Quản lý CRUD**: Thêm/Sửa/Xóa tài sản, mối đe dọa, lỗ hổng và rủi ro.
- **Tự động hóa**: Giao diện preview Risk Score ngay khi điều chỉnh thanh Likelihood / Impact.
- **Bộ lọc đa tiêu chí**: Lọc theo Mức rủi ro (Critical/High/Medium/Low), Chủ sở hữu (Owner) và Trạng thái xử lý (Status).
- **Xuất dữ liệu**: Xuất danh sách rủi ro đã lọc ra định dạng CSV và Excel (.xlsx).
- **Seed Data tự động**: Nạp sẵn 22+ rủi ro CNTT giả lập thực tế cho doanh nghiệp SME.

### 📸 Vị trí cần chụp ảnh cho báo cáo:
1. Giao diện bảng Risk Register chính (`http://localhost:5000/risks`).
2. Giao diện Form thêm rủi ro mới với thanh tính điểm preview.
3. Giao diện bộ lọc rủi ro hoạt động (VD: Lọc danh sách rủi ro Critical).
4. Kết quả xuất file CSV và Excel mở trên Microsoft Excel/Calc.

---

## BƯỚC 4: DOCKERIZATION & ISOLATION HỆ THỐNG

### 4.1. Kiến trúc Docker Network & Isolation
- Tất cả 3 container (`postgres`, `flask_app`, `metabase`) chạy chung trong bridge network `risk_network`.
- **An toàn thông tin (Network Boundary Isolation)**:
  - Database PostgreSQL **KHÔNG** expose cổng `5432` ra bên ngoài máy Host.
  - Chỉ có `flask_app` và `metabase` nằm trong mạng nội bộ Docker mới truy cập được PostgreSQL.
  - Người dùng bên ngoài máy host chỉ giao tiếp với ứng dụng Web (`port 5000`) và Dashboard (`port 3000`).

### 4.2. File `compose.yaml` & `Dockerfile`
- Sử dụng Image có phiên bản cố định (`postgres:16-alpine`, `python:3.12-slim`).
- Cấu hình Healthcheck cho PostgreSQL đảm bảo DB sẵn sàng trước khi khởi chạy Flask App và Metabase.

### 📸 Vị trí cần chụp ảnh cho báo cáo:
1. File `flask_app/Dockerfile` và `compose.yaml`.
2. Lệnh khởi chạy: `docker compose up -d --build`.
3. Trạng thái các container: `docker compose ps`.
4. Danh sách các Docker Networks: `docker network ls` và `docker network inspect risk_network`.

---

## BƯỚC 5: THIẾT LẬP METABASE DASHBOARD

### 5.1. Các bước kết nối Metabase với PostgreSQL
1. Truy cập `http://localhost:3000` và hoàn tất các bước setup ban đầu.
2. Chọn loại Database: **PostgreSQL**.
3. Khai báo thông tin kết nối an toàn:
   - Host: `postgres` (Tên container trong Docker network)
   - Port: `5432`
   - Database name: `risk_db`
   - Username: `metabase_readonly`
   - Password: `metabase_ro_pass`

### 5.2. Các Biểu đồ Dashboard cần tạo trên Metabase:
1. **Biểu đồ hình quạt/tròn (Pie Chart)**: Phân bố rủi ro theo Mức độ (Critical, High, Medium, Low).
2. **Biểu đồ cột (Bar Chart)**: Phân bố rủi ro theo Trạng thái xử lý (Open, Mitigating, Accepted, Closed).
3. **Danh sách Top 5 Rủi ro ưu tiên cao nhất**: Bảng sắp xếp theo `risk_score` giảm dần.
4. **Biểu đồ rủi ro theo Chủ sở hữu (Risk by Owner)**.

### 📸 Vị trí cần chụp ảnh cho báo cáo:
1. Màn hình cấu hình kết nối Database trong Metabase (dùng user `metabase_readonly`).
2. Màn hình Dashboard tổng thể hiển thị đầy đủ các biểu đồ.
3. Ảnh chi tiết Top 5 rủi ro ưu tiên nhất.

---

## BƯỚC 6: KIỂM THỬ BẢO MẬT & CHỨC NĂNG (TEST CASES)

| STT | Tên Test Case | Mục đích / Kiểm tra | Thao tác thực hiện | Kết quả mong đợi | Loại Kiểm thử |
|---|---|---|---|---|---|
| **TC1** | Kiểm tra tính toán Risk Score tự động | Đảm bảo công thức `Risk Score = Likelihood × Impact` chính xác | Nhập Likelihood = 4, Impact = 5 | Risk Score = 20, Risk Level tự chọn = Critical | Chức năng (Allowed) |
| **TC2** | Lọc rủi ro theo Mức độ | Đảm bảo bộ lọc dữ liệu chính xác | Trên giao diện Web, chọn Filter `Level = Critical` | Chỉ hiển thị các rủi ro mức Critical | Chức năng (Allowed) |
| **TC3** | Xuất dữ liệu ra Excel/CSV | Đảm bảo tính năng báo cáo dữ liệu hoạt động | Click nút "Export Excel" và "Export CSV" | Tải về thành công file `.xlsx` và `.csv` đầy đủ dữ liệu | Chức năng (Allowed) |
| **TC4** | Kiểm tra Network Isolation (Chặn kết nối trực tiếp DB) | Chứng minh DB không lộ cổng ra ngoài máy Host | Từ máy Host chạy lệnh: `psql -h localhost -p 5432 -U risk_user -d risk_db` | **Thất bại** (Connection Refused) do port 5432 không expose | Bảo mật (Denied) |
| **TC5** | Kiểm tra Phân quyền Tối thiểu (Least Privilege trên Metabase) | Chứng minh tài khoản Metabase không thể ghi/sửa/xóa DB | Dùng tài khoản `metabase_readonly` thực hiện lệnh `INSERT` hoặc `DELETE` | **Thất bại** (Permission Denied for table) | Bảo mật (Denied) |

### 📸 Vị trí cần chụp ảnh cho báo cáo:
- Chụp ảnh màn hình terminal / giao diện kết quả của cả 5 Test Cases trên.

---

## BƯỚC 7: SO SÁNH QUẢN LÝ RỦI RO: DOCKER HỆ THỐNG VS EXCEL THUẦN TÚY

| Tiêu chí so sánh | Quản lý thuần túy bằng Excel | Hệ thống tự động trên Docker |
|---|---|---|
| **Tính tự động & Chính xác** | Phụ thuộc vào công thức thủ công, dễ bị sửa nhầm ô/hàm. | Tự động tính điểm và phân loại cấp độ bằng code chuẩn hóa. |
| **Bảo mật & Phân quyền** | File Excel dễ bị copy, gửi nhầm email, không phân quyền theo vai trò. | Phân vùng mạng Docker, tách biệt user đọc/ghi, áp dụng Least Privilege. |
| **Truy cập đồng thời** | Xung đột file khi nhiều người cùng mở/sửa (File Lock). | Hỗ trợ nhiều người dùng truy cập web đồng thời qua kiến trúc CSDL CSDL tập trung. |
| **Trực quan hóa (Dashboard)** | Phải vẽ biểu đồ thủ công, không tự cập nhật realtime khi có dữ liệu mới. | Metabase Dashboard tự động vẽ biểu đồ và cập nhật realtime từ CSDL. |
| **Lịch sử thay đổi & Toàn vẹn** | Khó theo dõi ai đã sửa dòng nào, dễ bị xóa nhầm dữ liệu. | Có trường `created_at`, `updated_at`, ràng buộc khóa ngoại (Foreign Key Integrity). |
| **Khả năng triển khai (Portability)** | Phụ thuộc vào phiên bản Excel của từng máy. | Triển khai nhất quán trên mọi môi trường với duy nhất 1 lệnh `docker compose up`. |
