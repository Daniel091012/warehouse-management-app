from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

app = Flask(__name__, static_folder='static')

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL not set")
    result = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port,
        sslmode='require'
    )
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
            type TEXT,
            quantity INTEGER,
            note TEXT,
            created_at TEXT
        )
    ''')
    # Sample data
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (pid, *s, now))
            mid = str(uuid.uuid4())
            c.execute('''
                INSERT INTO movements (id, product_id, type, quantity, note, created_at)
                VALUES (%s, %s, 'in', %s, 'Nhập kho ban đầu', %s)
            ''', (mid, pid, s[4], now))
    conn.commit()
    conn.close()

# Initialize on startup
try:
    init_db()
except Exception as e:
    print("DB init error (will retry later):", e)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    query = 'SELECT * FROM products WHERE 1=1'
    params = []
    if search:
        query += ' AND (LOWER(name) LIKE %s OR LOWER(sku) LIKE %s)'
        params.extend([f'%{search}%', f'%{search}%'])
    if category:
        query += ' AND category = %s'
        params.append(category)
    query += ' ORDER BY name'
    c.execute(query, params)
    products = c.fetchall()
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    pid = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO products (id, sku, name, category, unit, quantity, location, min_stock, price, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            pid, data['sku'], data['name'], data.get('category', ''),
            data.get('unit', 'cái'), data.get('quantity', 0), data.get('location', ''),
            data.get('min_stock', 10), data.get('price', 0), data.get('description', ''), now
        ))
        if data.get('quantity', 0) > 0:
            mid = str(uuid.uuid4())
            c.execute('''
                INSERT INTO movements (id, product_id, type, quantity, note, created_at)
                VALUES (%s, %s, 'in', %s, 'Thêm sản phẩm mới', %s)
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
    c = conn.cursor()
    c.execute('''
        UPDATE products SET name=%s, category=%s, unit=%s, location=%s, min_stock=%s, price=%s, description=%s
        WHERE id=%s
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
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=%s', (pid,))
    c.execute('DELETE FROM movements WHERE product_id=%s', (pid,))
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
    c = conn.cursor()
    c.execute('UPDATE products SET quantity = quantity + %s WHERE id=%s', (qty, pid))
    mid = str(uuid.uuid4())
    c.execute('''
        INSERT INTO movements (id, product_id, type, quantity, note, created_at)
        VALUES (%s, %s, 'in', %s, %s, %s)
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
    c = conn.cursor()
    c.execute('SELECT quantity FROM products WHERE id=%s', (pid,))
    row = c.fetchone()
    if not row or row[0] < qty:
        conn.close()
        return jsonify({'error': 'Không đủ tồn kho'}), 400
    c.execute('UPDATE products SET quantity = quantity - %s WHERE id=%s', (qty, pid))
    mid = str(uuid.uuid4())
    c.execute('''
        INSERT INTO movements (id, product_id, type, quantity, note, created_at)
        VALUES (%s, %s, 'out', %s, %s, %s)
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
    c = conn.cursor()
    c.execute('SELECT quantity FROM products WHERE id=%s', (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Sản phẩm không tồn tại'}), 404
    diff = new_qty - row[0]
    c.execute('UPDATE products SET quantity = %s WHERE id=%s', (new_qty, pid))
    mid = str(uuid.uuid4())
    c.execute('''
        INSERT INTO movements (id, product_id, type, quantity, note, created_at)
        VALUES (%s, %s, 'adjust', %s, %s, %s)
    ''', (mid, pid, diff, note, now))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/movements', methods=['GET'])
def get_movements():
    limit = request.args.get('limit', 50, type=int)
    conn = get_db()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('''
        SELECT m.*, p.name as product_name, p.sku
        FROM movements m
        JOIN products p ON m.product_id = p.id
        ORDER BY m.created_at DESC
        LIMIT %s
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM products')
    total_products = c.fetchone()[0]
    c.execute('SELECT COALESCE(SUM(quantity), 0) FROM products')
    total_quantity = c.fetchone()[0]
    c.execute('SELECT COALESCE(SUM(quantity * price), 0) FROM products')
    total_value = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM products WHERE quantity <= min_stock')
    low_stock = c.fetchone()[0]
    conn.close()
    return jsonify({
        'total_products': total_products,
        'total_quantity': total_quantity,
        'total_value': round(float(total_value), 0),
        'low_stock': low_stock
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category")
    rows = c.fetchall()
    conn.close()
    return jsonify([r[0] for r in rows])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
