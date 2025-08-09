from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Замените на надежный ключ

# Инициализация базы данных
def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        # Таблица продуктов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        # Таблица пользователей (для авторизации)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        # Создаем администратора по умолчанию (если еще не создан)
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            password_hash = generate_password_hash('admin123')  # Задайте свой пароль
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', password_hash))
        conn.commit()

# Проверка авторизации
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect(url_for('admin_panel'))
            else:
                flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()
    return render_template('admin.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                (name, description, float(price))
            )
            conn.commit()
        return redirect(url_for('admin_panel'))
    return render_template('edit_product.html', product=None)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            cursor.execute(
                'UPDATE products SET name=?, description=?, price=? WHERE id=?',
                (name, description, float(price), product_id)
            )
            conn.commit()
            return redirect(url_for('admin_panel'))
        else:
            cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
            product = cursor.fetchone()
            if not product:
                return "Продукт не найден", 404
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)