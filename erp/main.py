import sqlite3

# Создаем или подключаемся к базе данных
conn = sqlite3.connect('erp_system.db')
cursor = conn.cursor()

# Создаем таблицы
def create_tables():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            date TEXT,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    conn.commit()

# Функции для работы с данными
def add_product(name, price, stock):
    cursor.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
    conn.commit()

def list_products():
    cursor.execute("SELECT * FROM products")
    return cursor.fetchall()

def add_client(name, email):
    cursor.execute("INSERT INTO clients (name, email) VALUES (?, ?)", (name, email))
    conn.commit()

def list_clients():
    cursor.execute("SELECT * FROM clients")
    return cursor.fetchall()

def create_order(client_id):
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO orders (client_id, date) VALUES (?, ?)", (client_id, date_str))
    conn.commit()
    return cursor.lastrowid

def add_order_item(order_id, product_id, quantity):
    # Проверка наличия товара на складе
    cursor.execute("SELECT stock FROM products WHERE id=?", (product_id,))
    stock = cursor.fetchone()
    if stock and stock[0] >= quantity:
        # Обновляем склад
        new_stock = stock[0] - quantity
        cursor.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))
        # Добавляем товар в заказ
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)", (order_id, product_id, quantity))
        conn.commit()
        print("Товар добавлен в заказ.")
    else:
        print("Недостаточно товара на складе.")

def list_orders():
    cursor.execute('''
        SELECT o.id, c.name, o.date FROM orders o JOIN clients c ON o.client_id=c.id
    ''')
    return cursor.fetchall()

def get_order_details(order_id):
    cursor.execute('''
        SELECT p.name, oi.quantity FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?
    ''', (order_id,))
    return cursor.fetchall()

# Простое меню для взаимодействия
def main():
    create_tables()
    
    while True:
        print("\n--- ERP-система ---")
        print("1. Добавить товар")
        print("2. Список товаров")
        print("3. Добавить клиента")
        print("4. Список клиентов")
        print("5. Создать заказ")
        print("6. Просмотр заказов")
        print("7. Детали заказа")
        print("0. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            name = input("Название товара: ")
            price = float(input("Цена: "))
            stock = int(input("Количество на складе: "))
            add_product(name, price, stock)
            
        elif choice == '2':
            products = list_products()
            for p in products:
                print(f"ID: {p[0]}, Название: {p[1]}, Цена: {p[2]}, Остаток: {p[3]}")
                
        elif choice == '3':
            name = input("Имя клиента: ")
            email = input("Email: ")
            add_client(name, email)
            
        elif choice == '4':
            clients = list_clients()
            for c in clients:
                print(f"ID: {c[0]}, Имя: {c[1]}, Email: {c[2]}")
                
        elif choice == '5':
            client_id = int(input("ID клиента: "))
            order_id = create_order(client_id)
            while True:
                product_id = int(input("ID товара для добавления в заказ (-1 для завершения): "))
                if product_id == -1:
                    break
                quantity = int(input("Количество: "))
                add_order_item(order_id, product_id, quantity)
                
        elif choice == '6':
            orders = list_orders()
            for o in orders:
                print(f"Заказ ID: {o[0]}, Клиент: {o[1]}, Дата: {o[2]}")
                
        elif choice == '7':
            order_id = int(input("Введите ID заказа: "))
            details = get_order_details(order_id)
            print(f"Детали заказа {order_id}:")
            for item in details:
                print(f"Товар: {item[0]}, Количество: {item[1]}")
                
        elif choice == '0':
            break
            
if __name__ == "__main__":
    main()