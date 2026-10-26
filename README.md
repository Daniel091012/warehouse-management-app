# Ứng dụng Quản lý Kho hàng (Warehouse Management System)

Ứng dụng full-stack quản lý kho hàng với Backend Flask + SQLite và Frontend hiện đại.

## Tính năng

- **Tổng quan Dashboard**: Thống kê sản phẩm, tồn kho, giá trị, cảnh báo tồn thấp
- **Quản lý Sản phẩm**: Thêm, sửa, xóa, tìm kiếm, lọc theo danh mục
- **Nhập kho**: Tăng tồn kho với ghi chú
- **Xuất kho**: Giảm tồn kho (kiểm tra đủ hàng)
- **Kiểm kê / Điều chỉnh**: Cập nhật số lượng thực tế
- **Lịch sử giao dịch**: Theo dõi tất cả biến động tồn kho
- Dữ liệu mẫu đầy đủ (15 sản phẩm)

## Công nghệ

- **Backend**: Python Flask + SQLite (built-in)
- **Frontend**: HTML + Tailwind CSS + Vanilla JS (SPA mượt mà)
- **API**: RESTful đầy đủ

## Cách chạy

```bash
pip install -r requirements.txt
python server.py
```

Mở trình duyệt: http://localhost:5000

Database `warehouse.db` sẽ được tạo tự động khi chạy lần đầu, kèm dữ liệu mẫu.

## Chạy trên GitHub Codespaces

1. Mở repo này trên GitHub
2. Bấm Code → Codespaces → Create codespace
3. Trong terminal Codespaces chạy:
```bash
pip install -r requirements.txt
python server.py
```
4. GitHub sẽ tự động forward port 5000 để bạn truy cập.
