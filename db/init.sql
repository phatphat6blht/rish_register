-- ============================================================
-- Risk Register - Database Initialization Script
-- Mục đích: Tạo user read-only cho Metabase (nguyên tắc Least Privilege)
-- Lưu ý: Các bảng sẽ được Flask-SQLAlchemy tự tạo khi app khởi động
-- ============================================================

-- Tạo user read-only cho Metabase
-- User này CHỈ có quyền SELECT, không thể INSERT/UPDATE/DELETE
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'metabase_readonly') THEN
        CREATE ROLE metabase_readonly WITH LOGIN PASSWORD 'metabase_ro_pass';
    END IF;
END
$$;

-- Cấp quyền kết nối vào database
GRANT CONNECT ON DATABASE risk_db TO metabase_readonly;

-- Cấp quyền sử dụng schema public
GRANT USAGE ON SCHEMA public TO metabase_readonly;

-- Cấp quyền SELECT trên TẤT CẢ bảng hiện tại trong schema public
GRANT SELECT ON ALL TABLES IN SCHEMA public TO metabase_readonly;

-- Tự động cấp quyền SELECT cho các bảng được tạo trong tương lai
-- (Quan trọng vì Flask-SQLAlchemy tạo bảng sau khi init.sql chạy)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO metabase_readonly;
