.PHONY: up down restart logs clean clean-all help

# Mặc định khi gọi 'make' sẽ hiển thị help
default: help

up:
	@echo "Đang khởi động toàn bộ hệ thống (chạy ngầm)..."
	docker compose up -d

down:
	@echo "Đang tắt hệ thống (giữ lại dữ liệu)..."
	docker compose down

restart:
	@echo "Đang khởi động lại hệ thống..."
	docker compose down
	docker compose up -d

logs:
	@echo "Đang xem log hệ thống..."
	docker compose logs -f

clean:
	@echo "Đang xóa hệ thống VÀ xóa SẠCH CẢ DỮ LIỆU CŨ (Metabase, Postgres)..."
	docker compose down -v

clean-all:
	@echo "Đang xóa sạch hệ thống, dữ liệu cũ và cả các image không dùng..."
	docker compose down -v --rmi all --remove-orphans

help:
	@echo "Các lệnh có sẵn:"
	@echo "  make up        : Khởi động hệ thống (Postgres, Flask, Metabase)"
	@echo "  make down      : Tắt hệ thống nhưng VẪN GIỮ LẠI dữ liệu"
	@echo "  make restart   : Khởi động lại toàn bộ"
	@echo "  make logs      : Xem logs của các container"
	@echo "  make clean     : Tắt và XÓA SẠCH MỌI DỮ LIỆU (Database, Metabase cũ)"
	@echo "  make clean-all : Xóa sạch dữ liệu và cả Docker images"
