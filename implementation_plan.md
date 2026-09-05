# Xây dựng Risk Register tự động và Dashboard bằng Docker

## Tổng quan đề bài

Đề bài yêu cầu xây dựng hệ thống **Risk Register (Sổ đăng ký rủi ro)** tự động cho môn An toàn thông tin, bao gồm:
- Ứng dụng web quản lý rủi ro (Flask/Python)
- Database PostgreSQL
- Dashboard trực quan bằng Metabase
- Tất cả triển khai bằng Docker Compose

**Ngữ cảnh dữ liệu**: Công ty phần mềm vừa và nhỏ (SME) với 20+ rủi ro CNTT giả lập.

---

## Phân tích kiến trúc tổng thể

### Sơ đồ kiến trúc

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                   (risk_network)                         │
│                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ PostgreSQL│◄───│  Flask App   │    │   Metabase   │   │
│  │  :5432    │    │   :5000      │    │    :3000     │   │
│  │ (backend) │    │  (backend)   │    │  (backend)   │   │
│  └──────────┘    └──────────────┘    └──────────────┘   │
│       ▲                │ :5000              │ :3000      │
│       │                ▼                    ▼            │
│       │          ┌──────────┐        ┌──────────┐       │
│       └──────────│  Volume  │        │  Volume  │       │
│                  │ pg_data  │        │ mb_data  │       │
│                  └──────────┘        └──────────┘       │
└─────────────────────────────────────────────────────────┘
         │ :5000              │ :3000
         ▼                    ▼
    ┌─────────────────────────────────┐
    │        Trình duyệt (Host)       │
    │  localhost:5000  localhost:3000  │
    └─────────────────────────────────┘
```

### Các container và vai trò

| Container | Image | Cổng | Vai trò | Giao tiếp |
|-----------|-------|------|---------|------------|
| **postgres** | `postgres:16-alpine` | 5432 (internal) | Database lưu trữ tất cả dữ liệu | Chỉ nhận kết nối từ flask_app và metabase |
| **flask_app** | Build từ Dockerfile | 5000→5000 | Ứng dụng CRUD quản lý rủi ro, tính toán risk score | Kết nối tới postgres, expose ra host |
| **metabase** | `metabase/metabase:v0.50.21` | 3000→3000 | Dashboard trực quan, biểu đồ | Kết nối tới postgres (read-only), expose ra host |

### Trust Boundary & Network Security

```
┌─ TRUST BOUNDARY ──────────────────────────────────────┐
│                                                        │
│  Docker Internal Network (risk_network)                │
│  ┌────────────┐                                        │
│  │  postgres   │ ← Không expose ra host                │
│  │  Port 5432  │ ← Chỉ flask_app & metabase truy cập  │
│  └────────────┘                                        │
│        ▲    ▲                                          │
│        │    │                                          │
│  ┌─────┘    └─────┐                                    │
│  │                │                                    │
│  ▼                ▼                                    │
│  ┌──────────┐  ┌──────────┐                            │
│  │ flask_app│  │ metabase │                            │
│  │ :5000    │  │ :3000    │                            │
│  └──────────┘  └──────────┘                            │
│       │              │                                 │
└───────│──────────────│─────────────────────────────────┘
        │              │
        ▼              ▼
   Host :5000     Host :3000     ← Expose cho user
```

**Giải thích giao tiếp**:
- **postgres** KHÔNG expose port ra host → bảo vệ database khỏi truy cập trực tiếp từ bên ngoài
- **flask_app** → postgres: Cần thiết để CRUD dữ liệu rủi ro
- **metabase** → postgres: Cần thiết để đọc dữ liệu tạo dashboard (nên dùng user read-only)
- **flask_app** ↔ **metabase**: KHÔNG giao tiếp trực tiếp → nguyên tắc least privilege

---

## Mô hình dữ liệu (Data Model)

### Thiết kế 4 Register theo yêu cầu đề bài

```
┌──────────────┐     ┌──────────────────┐
│ Asset Register│     │ Threat Register   │
│──────────────│     │──────────────────│
│ id (PK)      │     │ id (PK)          │
│ name         │◄─┐  │ name             │
│ type         │  │  │ category         │──┐
│ owner        │  │  │ description      │  │
│ criticality  │  │  └──────────────────┘  │
│ description  │  │                        │
└──────────────┘  │  ┌───────────────────┐ │
                  │  │Vulnerability Reg.  │ │
                  │  │───────────────────│ │
                  │  │ id (PK)           │ │
                  │  │ name              │─┤
                  │  │ cve_id            │ │
                  │  │ severity          │ │
                  │  │ description       │ │
                  │  └───────────────────┘ │
                  │                        │
                  │  ┌───────────────────┐ │
                  └──│  Risk Register    │◄┘
                     │───────────────────│
                     │ id (PK)           │
                     │ asset_id (FK)     │→ Asset
                     │ threat_id (FK)    │→ Threat
                     │ vuln_id (FK)      │→ Vulnerability
                     │ likelihood (1-5)  │
                     │ impact (1-5)      │
                     │ risk_score        │← = likelihood × impact
                     │ risk_level        │← Tự động: Low/Med/High/Critical
                     │ owner             │
                     │ status            │← Open/Mitigating/Accepted/Closed
                     │ mitigation        │
                     │ created_at        │
                     │ updated_at        │
                     └───────────────────┘
```

### Công thức tính điểm rủi ro

$$\text{Risk Score} = \text{Likelihood} \times \text{Impact}$$

Trong đó:
- **Likelihood** (Khả năng xảy ra): Thang 1–5
- **Impact** (Mức độ ảnh hưởng): Thang 1–5
- **Risk Score**: Giá trị từ 1–25

### Ma trận phân loại mức rủi ro (Risk Level)

|                  | Impact 1 | Impact 2 | Impact 3 | Impact 4 | Impact 5 |
|------------------|----------|----------|----------|----------|----------|
| **Likelihood 5** | 5 Med    | 10 High  | 15 High  | 20 Crit  | 25 Crit  |
| **Likelihood 4** | 4 Med    | 8 Med    | 12 High  | 16 High  | 20 Crit  |
| **Likelihood 3** | 3 Low    | 6 Med    | 9 Med    | 12 High  | 15 High  |
| **Likelihood 2** | 2 Low    | 4 Med    | 6 Med    | 8 Med    | 10 High  |
| **Likelihood 1** | 1 Low    | 2 Low    | 3 Low    | 4 Med    | 5 Med    |

**Quy tắc phân loại**:
- **Critical** (Nghiêm trọng): Score ≥ 20
- **High** (Cao): Score 12–19
- **Medium** (Trung bình): Score 5–11
- **Low** (Thấp): Score 1–4

### Trạng thái xử lý rủi ro

| Trạng thái     | Ý nghĩa                             |
|----------------|-------------------------------------|
| **Open**       | Mới phát hiện, chưa có hành động    |
| **Mitigating** | Đang thực hiện biện pháp giảm thiểu |
| **Accepted**   | Chấp nhận rủi ro (cost > benefit)   |
| **Closed**     | Đã xử lý xong                       |

---

## Proposed Changes (Cấu trúc dự án)

### Cấu trúc thư mục sau khi hoàn thành

```
risk_register/
├── compose.yaml                 # Docker Compose file
├── .env.example                 # Biến môi trường mẫu (không chứa secret thật)
├── .env                         # Biến môi trường thật (trong .gitignore)
├── README.md                    # Hướng dẫn cài đặt & sử dụng
├── flask_app/
│   ├── Dockerfile               # Build image cho Flask app
│   ├── requirements.txt         # Python dependencies
│   ├── app.py                   # Ứng dụng Flask chính
│   ├── models.py                # SQLAlchemy models (4 Register)
│   ├── seed_data.py             # Script tạo 20+ rủi ro mẫu
│   ├── templates/
│   │   ├── base.html            # Template gốc
│   │   ├── index.html           # Trang chủ - Risk Register
│   │   ├── assets.html          # Quản lý Asset Register
│   │   ├── threats.html         # Quản lý Threat Register
│   │   ├── vulnerabilities.html # Quản lý Vulnerability Register
│   │   └── risk_form.html       # Form thêm/sửa rủi ro
│   └── static/
│       └── style.css            # CSS styling
├── db/
│   └── init.sql                 # SQL khởi tạo schema + user read-only cho Metabase
├── data/
│   └── sample_risks.csv         # Dữ liệu mẫu xuất ra CSV
├── docs/
│   └── screenshots/             # Ảnh chụp màn hình cho báo cáo
└── general_requirements_for_the_report.md
```

---

### Component 1: Database (PostgreSQL)

#### [NEW] [init.sql](file:///c:/Users/ADMIN/Downloads/risk_register/db/init.sql)
- Tạo schema cho 4 bảng: `assets`, `threats`, `vulnerabilities`, `risks`
- Tạo user `metabase_readonly` chỉ có quyền SELECT (read-only) cho Metabase
- Tạo các constraint, index cần thiết

---

### Component 2: Flask Application

#### [NEW] [Dockerfile](file:///c:/Users/ADMIN/Downloads/risk_register/flask_app/Dockerfile)
- Base image: `python:3.12-slim`
- Cài đặt dependencies từ requirements.txt
- Copy source code và chạy ứng dụng

#### [NEW] [requirements.txt](file:///c:/Users/ADMIN/Downloads/risk_register/flask_app/requirements.txt)
- Flask, SQLAlchemy, psycopg2-binary, Flask-SQLAlchemy, python-dotenv, openpyxl (xuất Excel)

#### [NEW] [models.py](file:///c:/Users/ADMIN/Downloads/risk_register/flask_app/models.py)
- 4 SQLAlchemy models: Asset, Threat, Vulnerability, Risk
- Computed property `risk_score` = likelihood × impact
- Method phân loại `risk_level` tự động

#### [NEW] [app.py](file:///c:/Users/ADMIN/Downloads/risk_register/flask_app/app.py)
- Routes CRUD cho cả 4 register
- Endpoint lọc theo mức độ, chủ sở hữu, trạng thái
- Endpoint xuất CSV/Excel
- API endpoint cho dữ liệu (Metabase có thể dùng)

#### [NEW] [seed_data.py](file:///c:/Users/ADMIN/Downloads/risk_register/flask_app/seed_data.py)
- Script nhập 20+ rủi ro mẫu cho công ty phần mềm SME
- Chạy tự động khi khởi tạo lần đầu

#### [NEW] Templates & Static files
- Giao diện web quản lý đơn giản, rõ ràng
- Bảng hiển thị Risk Register với màu sắc theo risk level
- Form thêm/sửa rủi ro
- Bộ lọc theo mức độ, chủ sở hữu, trạng thái

---

### Component 3: Docker Compose

#### [NEW] [compose.yaml](file:///c:/Users/ADMIN/Downloads/risk_register/compose.yaml)
- 3 services: postgres, flask_app, metabase
- 1 network: risk_network (bridge)
- 2 volumes: pg_data, mb_data
- Image ghim phiên bản cụ thể (không dùng `latest`)
- Health checks cho postgres

#### [NEW] [.env.example](file:///c:/Users/ADMIN/Downloads/risk_register/.env.example)
- Template biến môi trường không chứa mật khẩu thật

---

### Component 4: Documentation

#### [MODIFY] [README.md](file:///c:/Users/ADMIN/Downloads/risk_register/README.md)
- Hướng dẫn cài đặt, khởi chạy, kiểm tra, dọn dẹp
- Mô tả kiến trúc và mô hình dữ liệu

---

## Kế hoạch thực hiện từng bước (Step-by-Step)

Mỗi bước dưới đây sẽ được ghi chi tiết vào file Word ghi chú, kèm:
- ✍️ Giải thích lý do thiết kế
- 💻 Lệnh/code cần chạy
- 📸 Vị trí cần chụp ảnh cho báo cáo
- ✅ Kết quả mong đợi

### Bước 1: Chuẩn bị dự án
- Tạo cấu trúc thư mục
- Tạo `.env.example` và `.env`
- Cập nhật `.gitignore`

### Bước 2: Thiết kế Database
- Viết `db/init.sql` với schema đầy đủ
- Tạo user read-only cho Metabase
- 📸 Chụp: ERD diagram, file SQL

### Bước 3: Xây dựng Flask App
- Viết models.py (4 register)
- Viết app.py (routes CRUD + lọc + xuất CSV/Excel)
- Viết templates HTML
- Viết Dockerfile
- 📸 Chụp: Code, giao diện web

### Bước 4: Tạo dữ liệu mẫu
- Viết seed_data.py với 20+ rủi ro cho SME
- 📸 Chụp: Bảng Risk Register đầy đủ

### Bước 5: Docker Compose
- Viết compose.yaml
- Cấu hình network, volumes, health checks
- 📸 Chụp: `docker compose up`, `docker ps`, `docker network ls`

### Bước 6: Khởi chạy & kiểm tra
- `docker compose up -d`
- Truy cập Flask app tại `localhost:5000`
- Truy cập Metabase tại `localhost:3000`
- 📸 Chụp: Trạng thái container, ứng dụng chạy

### Bước 7: Cấu hình Metabase Dashboard
- Kết nối Metabase tới PostgreSQL
- Tạo các biểu đồ: phân bố rủi ro, top 5 rủi ro cao nhất
- 📸 Chụp: Dashboard, biểu đồ, bộ lọc

### Bước 8: Kiểm thử (5 test cases)
1. **TC1**: Thêm rủi ro mới → verify risk_score tính đúng ✅
2. **TC2**: Lọc theo mức độ "Critical" → chỉ hiện rủi ro Critical ✅
3. **TC3**: Xuất CSV/Excel → file có đủ dữ liệu ✅
4. **TC4**: Truy cập postgres từ host → bị từ chối ❌ (security)
5. **TC5**: Metabase chỉ SELECT → không thể INSERT/DELETE ❌ (read-only)
- 📸 Chụp: Kết quả từng test case

### Bước 9: Xuất dữ liệu & Dọn dẹp
- Xuất Risk Register sang CSV/Excel
- `docker compose down -v` (dọn dẹp)
- 📸 Chụp: File CSV/Excel, lệnh dọn dẹp

---

## Verification Plan

### Automated Tests
```bash
# Kiểm tra tất cả container đang chạy
docker compose ps

# Kiểm tra network
docker network ls
docker network inspect risk_register_risk_network

# Kiểm tra postgres không expose port ra host
# (Lệnh này phải thất bại vì port 5432 không expose)
psql -h localhost -p 5432 -U risk_user -d risk_db

# Kiểm tra Flask app
curl http://localhost:5000

# Kiểm tra Metabase
curl http://localhost:3000/api/health
```

### Manual Verification
- Truy cập `localhost:5000` → thấy Risk Register
- Thêm/sửa/xóa rủi ro → dữ liệu cập nhật đúng
- Lọc theo mức độ/chủ sở hữu/trạng thái → kết quả chính xác
- Xuất CSV/Excel → file đầy đủ
- Metabase dashboard → biểu đồ hiển thị đúng
- Top 5 rủi ro cao nhất → đúng thứ tự

---

## So sánh với quản lý thuần túy bằng Excel (cho báo cáo)

| Tiêu chí | Excel thuần túy | Risk Register + Docker |
|---|---|---|
| **Tính tự động** | Tính score thủ công hoặc bằng formula | Tự động tính score, phân loại risk level |
| **Đa người dùng** | Conflict khi nhiều người cùng sửa | Hỗ trợ truy cập đồng thời qua web |
| **Dashboard** | Tạo chart thủ công, khó cập nhật | Metabase tự động cập nhật realtime |
| **Bảo mật** | File có thể copy, gửi email tùy ý | Kiểm soát truy cập, network isolation |
| **Audit trail** | Không có lịch sử thay đổi | Có `created_at`, `updated_at` |
| **Tính toàn vẹn** | Dễ bị xóa nhầm formula | Constraint ở database level |
| **Khả năng mở rộng** | Chậm khi >1000 dòng | PostgreSQL xử lý hàng triệu bản ghi |
| **Triển khai** | Gửi file qua email | `docker compose up` trên bất kỳ máy nào |
| **Backup** | Thủ công | Docker volume + pg_dump tự động |

---

> [!IMPORTANT]
> **Về dữ liệu mẫu**: Tôi sẽ tạo sẵn 20+ rủi ro giả lập cho công ty phần mềm SME trực tiếp trong code `seed_data.py`. Dữ liệu sẽ bao gồm các rủi ro CNTT phổ biến như: ransomware, phishing, SQL injection, data breach, insider threat, DDoS, v.v. Bạn không cần tạo prompt riêng - dữ liệu sẽ được seed tự động khi chạy `docker compose up`.

> [!NOTE]
> **Phần lý thuyết** (CIA, quản trị rủi ro, Defense-in-Depth, RBAC/ABAC...) sẽ do bạn tự xử lý sau như đã nói. Kế hoạch này chỉ tập trung vào phần **thiết kế + triển khai + kiểm thử**.
