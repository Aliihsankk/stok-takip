from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)
DATABASE = 'stok.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS malzemeler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL UNIQUE,
        stok_kodu TEXT NOT NULL UNIQUE,
        birim_fiyat REAL NOT NULL,
        min_stok INTEGER NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stok (
        malzeme_id INTEGER PRIMARY KEY,
        miktar INTEGER NOT NULL,
        FOREIGN KEY (malzeme_id) REFERENCES malzemeler(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS girisler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        malzeme_id INTEGER NOT NULL,
        miktar INTEGER NOT NULL,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (malzeme_id) REFERENCES malzemeler(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cikislar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        malzeme_id INTEGER NOT NULL,
        miktar INTEGER NOT NULL,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (malzeme_id) REFERENCES malzemeler(id)
    )''')

    conn.commit()
    conn.close()

# API Endpoint'leri
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/malzemeler', methods=['GET'])
def get_malzemeler():
    conn = get_db_connection()
    malzemeler = conn.execute('SELECT * FROM malzemeler').fetchall()
    conn.close()
    return jsonify([dict(row) for row in malzemeler])

@app.route('/malzeme_ekle', methods=['POST'])
def malzeme_ekle():
    data = request.json
    try:
        conn = get_db_connection()
        conn.execute('''
        INSERT INTO malzemeler (ad, stok_kodu, birim_fiyat, min_stok)
        VALUES (?, ?, ?, ?)
        ''', (data['ad'], data['stok_kodu'], data['birim_fiyat'], data['min_stok']))
        conn.commit()
        return jsonify({'status': 'success'})
    except sqlite3.IntegrityError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()

@app.route('/stok', methods=['GET'])
def get_stok():
    conn = get_db_connection()
    stok = conn.execute('''
    SELECT m.id, m.ad, m.stok_kodu, m.min_stok, COALESCE(s.miktar, 0) AS miktar
    FROM malzemeler m
    LEFT JOIN stok s ON m.id = s.malzeme_id
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in stok])

@app.route('/giris', methods=['POST'])
def giris():
    data = request.json
    try:
        conn = get_db_connection()
        conn.execute('''
        INSERT INTO girisler (malzeme_id, miktar) VALUES (?, ?)
        ''', (data['malzeme_id'], data['miktar']))
        conn.execute('''
        INSERT OR REPLACE INTO stok (malzeme_id, miktar)
        VALUES (?, COALESCE((SELECT miktar FROM stok WHERE malzeme_id = ?), 0) + ?)
        ''', (data['malzeme_id'], data['malzeme_id'], data['miktar']))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()

@app.route('/cikis', methods=['POST'])
def cikis():
    data = request.json
    try:
        conn = get_db_connection()
        current_stock = conn.execute('SELECT miktar FROM stok WHERE malzeme_id = ?', (data['malzeme_id'],)).fetchone()
        if not current_stock or current_stock['miktar'] < data['miktar']:
            return jsonify({'status': 'error', 'message': 'Yetersiz stok!'}), 400
        conn.execute('''
        INSERT INTO cikislar (malzeme_id, miktar) VALUES (?, ?)
        ''', (data['malzeme_id'], data['miktar']))
        conn.execute('''
        UPDATE stok SET miktar = miktar - ? WHERE malzeme_id = ?
        ''', (data['miktar'], data['malzeme_id']))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)