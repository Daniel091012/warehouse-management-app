from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime
import uuid

app = Flask(__name__, static_folder='static')
DB_PATH = 'warehouse.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT DEFAULT 'cái',
            quantity INTEGER DEFAULT 0,
            location TEXT,
            min_stock INTEGER DEFAULT 10,
            price REAL DEFAULT 0,
            description TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS movements (
            id TEXT PRIMARY KEY,
            product_id TEXT,
            type TEXT,  -- 'in', 'out', 'adjust'
            quantity INTEGER,
            note TEXT,
            created_at TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    # Sample data if empty
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        samples = [
            ('SP001', 'Laptop Dell XPS 13', 'Điện tử', 'cái', 25, 'Kệ A1', 5, 25000000, 'Laptop cao cấp'),
            ('SP002', 'Chuột Logitech MX Master', 'Phụ kiện', 'cái', 150, 'Kệ B2', 20, 1800000, 'Chuột không dây'),
            ('SP003', 'Bàn phím cơ Keychron K2', 'Phụ kiện', 'cái', 80, 'Kệ B1', 15, 2200000, 'Bàn phím cơ'),
            ('SP004', 'Màn hình LG 27 inch', 'Điện tử', 'cái', 40, 'Kệ A2', 8, 5500000, 'Màn hình IPS'),
            ('SP005', 'Tai nghe Sony WH-1000XM5', 'Âm thanh', 'cái', 60, 'Kệ C1', 10, 8500000, 'Tai nghe chống ồn'),
            ('SP006', 'Ổ cứng SSD Samsung 1TB', 'Lưu trữ', 'cái', 200, 'Kệ D1', 30, 1800000, 'SSD NVMe'),
            ('SP007', 'Giấy A4 Double A', 'Văn phòng phẩm', 'ream', 500, 'Kệ E1', 50, 85000, 'Giấy in'),
            ('SP008', 'Bút bi Thiên Long', 'Văn phòng phẩm', 'hộp', 300, 'Kệ E2', 40, 35000, 'Bút viết'),
            ('SP009', 'Ghế văn phòng ergonomic', 'Nội thất', 'cái', 15, 'Kệ F1', 3, 4500000, 'Ghế công thái học'),
            ('SP010', 'Máy in HP LaserJet', 'Điện tử', 'cái', 12, 'Kệ A3', 2, 3200000, 'Máy in laser'),
            ('SP011', 'Cáp USB-C 2m', 'Phụ kiện', 'cái', 400, 'Kệ B3', 50, 120000, 'Cáp sạc'),
            ('SP012', 'Webcam Logitech C920', 'Phụ kiện', 'cái', 35, 'Kệ C2', 5, 2100000, 'Webcam HD'),
            ('SP013', 'Router WiFi TP-Link', 'Mạng', 'cái', 45, 'Kệ D2', 8, 850000, 'Router dual band'),
            ('SP014', 'Pin AA Energizer', 'Pin', 'hộp', 250, 'Kệ E3', 30, 45000, 'Pin tiểu'),
            ('SP015', 'Nước rửa tay Lifebuoy', 'Vệ sinh', 'chai', 180, 'Kệ G1', 20, 35000, 'Nước rửa tay'),
        ]
        now = datetime.now().isoformat()
        for s in samples:
            pid = str(uuid.uuid4())
            c.execute('''
                INSERT INTO products (id, sku, name, category, unit, quantity, location, min_stock, price, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pid, *s, now))
            mid = str(uuid.uuid4())
            c.execute('''
                INSERT INTO movements (id, product_id, type, quantity, note, created_at)
                VALUES (?, ?, 'in', ?, 'Nhập kho ban đầu', ?)
            ''', (mid, pid, s[4], now))
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    conn = get_db()
    query = 'SELECT * FROM products WHERE 1=1'
    params = []
    if search:
        query += ' AND (LOWER(name) LIKE ? OR LOWER(sku) LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    if category:
        query += ' AND category = ?'
        params.append(category)
    query += ' ORDER BY name'
    products = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    pid = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO products (id, sku, name, category, unit, quantity, location, min_stock, price, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pid, data['sku'], data['name'], data.get('category', ''),
            data.get('unit', 'cái'), data.get('quantity', 0), data.get('location', ''),
            data.get('min_stock', 10), data.get('price', 0), data.get('description', ''), now
        ))
        if data.get('quantity', 0) > 0:
            mid = str(uuid.uuid4())
            conn.execute('''
                INSERT INTO movements (id, product_id, type, quantity, note, created_at)
                VALUES (?, ?, 'in', ?, 'Thêm sản phẩm mới', ?)
            ''', (mid, pid, data.get('quantity', 0), now))
        conn.commit()
        conn.close()
        return jsonify({'id': pid, 'success': True}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/products/<pid>', methods=['PUT'])
def update_product(pid):
    data = request.json
    conn = get_db()
    conn.execute('''
        UPDATE products SET name=?, category=?, unit=?, location=?, min_stock=?, price=?, description=?
        WHERE id=?
    ''', (
        data.get('name'), data.get('category'), data.get('unit'),
        data.get('location'), data.get('min_stock'), data.get('price'),
        data.get('description'), pid
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/products/<pid>', methods=['DELETE'])
def delete_product(pid):
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id=?', (pid,))
    conn.execute('DELETE FROM movements WHERE product_id=?', (pid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stock/in', methods=['POST'])
def stock_in():
    data = request.json
    pid = data['product_id']
    qty = int(data['quantity'])
    note = data.get('note', 'Nhập kho')
    now = datetime.now().isoformat()
    conn = get_db()
    conn.execute('UPDATE products SET quantity = quantity + ? WHERE id=?', (qty, pid))
    mid = str(uuid.uuid4())
    conn.execute('''
        INSERT INTO movements (id, product_id, type, quantity, note, created_at)
        VALUES (?, ?, 'in', ?, ?, ?)
    ''', (mid, pid, qty, note, now))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stock/out', methods=['POST'])
def stock_out():
    data = request.json
    pid = data['product_id']
    qty = int(data['quantity'])
    note = data.get('note', 'Xuất kho')
    now = datetime.now().isoformat()
    conn = get_db()
    row = conn.execute('SELECT quantity FROM products WHERE id=?', (pid,)).fetchone()
    if not row or row['quantity'] < qty:
        conn.close()
        return jsonify({'error': 'Không đủ tồn kho'}), 400
    conn.execute('UPDATE products SET quantity = quantity - ? WHERE id=?', (qty, pid))
    mid = str(uuid.uuid4())
    conn.execute('''
        INSERT INTO movements (id, product_id, type, quantity, note, created_at)
        VALUES (?, ?, 'out', ?, ?, ?)
    ''', (mid, pid, qty, note, now))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stock/adjust', methods=['POST'])
def stock_adjust():
    data = request.json
    pid = data['product_id']
    new_qty = int(data['quantity'])
    note = data.get('note', 'Điều chỉnh kiểm kê')
    now = datetime.now().isoformat()
    conn = get_db()
    row = conn.execute('SELECT quantity FROM products WHERE id=?', (pid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Sản phẩm không tồn tại'}), 404
    diff = new_qty - row['quantity']
    conn.execute('UPDATE products SET quantity = ? WHERE id=?', (new_qty, pid))
    mid = str(uuid.uuid4())
    conn.execute('''
        INSERT INTO movements (id, product_id, type, quantity, note, created_at)
        VALUES (?, ?, 'adjust', ?, ?, ?)
    ''', (mid, pid, diff, note, now))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/movements', methods=['GET'])
def get_movements():
    limit = request.args.get('limit', 50, type=int)
    conn = get_db()
    rows = conn.execute('''
        SELECT m.*, p.name as product_name, p.sku
        FROM movements m
        JOIN products p ON m.product_id = p.id
        ORDER BY m.created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_quantity = conn.execute('SELECT SUM(quantity) FROM products').fetchone()[0] or 0
    total_value = conn.execute('SELECT SUM(quantity * price) FROM products').fetchone()[0] or 0
    low_stock = conn.execute('SELECT COUNT(*) FROM products WHERE quantity <= min_stock').fetchone()[0]
    conn.close()
    return jsonify({
        'total_products': total_products,
        'total_quantity': total_quantity,
        'total_value': round(total_value, 0),
        'low_stock': low_stock
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    rows = conn.execute('SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != "" ORDER BY category').fetchall()
    conn.close()
    return jsonify([r['category'] for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
