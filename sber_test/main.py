import sqlite3
from datetime import datetime, timedelta

# Подключение к базе данных
conn = sqlite3.connect('bank_system.db')
cursor = conn.cursor()

# Создание таблиц
def create_tables():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            birthdate TEXT,
            phone TEXT,
            email TEXT,
            registration_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            amount REAL,
            interest_rate REAL,
            term_months INTEGER,
            start_date TEXT,
            status TEXT, -- например: 'Открыт', 'Погашен', 'Отменен'
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            payment_number INTEGER,
            due_date TEXT,
            amount REAL,
            paid BOOLEAN DEFAULT 0,
            payment_date TEXT,
            FOREIGN KEY(loan_id) REFERENCES loans(id)
        )
    ''')
    conn.commit()

# Регистрация нового клиента
def register_client(name, birthdate, phone, email):
    reg_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO clients (name, birthdate, phone, email, registration_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, birthdate, phone, email, reg_date))
    conn.commit()
    print("Клиент зарегистрирован успешно.")

# Расчет аннуитетного платежа
def calculate_annuity_payment(amount, annual_rate_percent, term_months):
    monthly_rate = annual_rate_percent / 100 / 12
    if monthly_rate == 0:
        return round(amount / term_months, 2)
    payment = amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    return round(payment, 2)

# Генерация графика погашения
def generate_payment_schedule(loan_id):
    cursor.execute("SELECT amount, interest_rate, term_months, start_date FROM loans WHERE id=?", (loan_id,))
    row = cursor.fetchone()
    if not row:
        print("Кредит не найден.")
        return
    
    amount, interest_rate, term_months, start_date_str = row
    payment_amount = calculate_annuity_payment(amount, interest_rate*100, term_months)
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    
    # Удаляем предыдущий график для этого кредита (если есть)
    cursor.execute("DELETE FROM payments WHERE loan_id=?", (loan_id,))
    
    for n in range(1, term_months + 1):
        due_date = start_date + timedelta(days=30 * n)  # приблизительно месяц
        cursor.execute('''
            INSERT INTO payments (loan_id, payment_number, due_date, amount)
            VALUES (?, ?, ?, ?)
        ''', (loan_id, n, due_date.strftime("%Y-%m-%d"), payment_amount))
    
    conn.commit()
    print(f"График погашения для кредита {loan_id} создан.")

# Оформление кредита с автоматическим расчетом платежей и графиком
def create_loan(client_id, amount, interest_rate_percent, term_months):
    start_date = datetime.now().strftime("%Y-%m-%d")
    status = 'Открыт'
    cursor.execute('''
        INSERT INTO loans (client_id, amount, interest_rate, term_months, start_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (client_id, amount, interest_rate_percent/100.0 , term_months , start_date , status))
    
    loan_id = cursor.lastrowid
    
    generate_payment_schedule(loan_id)
    
    conn.commit()
    print("Кредит оформлен успешно и график погашения создан.")

# Просмотр всех клиентов
def list_clients():
    cursor.execute("SELECT * FROM clients")
    return cursor.fetchall()

# Просмотр всех кредитов
def list_loans():
    cursor.execute('''
        SELECT loans.id, clients.name, loans.amount, loans.interest_rate,
               loans.term_months, loans.start_date, loans.status
        FROM loans JOIN clients ON loans.client_id=clients.id
    ''')
    return cursor.fetchall()

# Просмотр графика платежей по кредиту
def view_payment_schedule(loan_id):
    cursor.execute('''
        SELECT payment_number, due_date, amount,payment_date,paid 
        FROM payments WHERE loan_id=?
        ORDER BY payment_number
    ''', (loan_id,))
    
    payments = cursor.fetchall()
    
    print(f"График платежей по кредиту {loan_id}:")
    for p in payments:
        paid_status = "Оплачен" if p[4] else "Не оплачен"
        print(f"Платеж {p[0]}: Дата: {p[1]}, Сумма: {p[2]}, Статус: {paid_status}")

# Обновление статуса платежа (оплата)
def pay_payment(payment_id):
    payment_date = datetime.now().strftime("%Y-%m-%d")
    
    # Обновляем запись о платеже как оплаченной
    cursor.execute('''
        UPDATE payments SET paid=1,payment_date=?
        WHERE id=?
    ''', (payment_date,payment_id))
    
    # Проверяем есть ли еще неоплаченные платежи по этому кредиту
    cursor.execute('''
        SELECT COUNT(*) FROM payments WHERE loan_id=(SELECT loan_id FROM payments WHERE id=?) AND paid=0
     ''', (payment_id,))
     
    remaining_unpaid = cursor.fetchone()[0]
     
    if remaining_unpaid == 0:
         # Все платежи оплачены — закрываем кредит
         cursor.execute("UPDATE loans SET status='Погашен' WHERE id=(SELECT loan_id FROM payments WHERE id=?)", (payment_id,))
         
    conn.commit()
    print(f"Платеж {payment_id} оплачен.")

# Основное меню взаимодействия с добавлением новых функций
def main():
    create_tables()
    
    while True:
        print("\n--- Удаленное обслуживание клиентов банка ---")
        print("1. Зарегистрировать клиента")
        print("2. Оформить кредит")
        print("3. Просмотреть список клиентов")
        print("4. Просмотреть список кредитов")
        print("5. Посмотреть график погашения кредита")
        print("6. Оплатить платеж")
        print("0. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            name = input("Имя клиента: ")
            birthdate = input("Дата рождения (ГГГГ-ММ-ДД): ")
            phone = input("Телефон: ")
            email = input("Email: ")
            register_client(name, birthdate, phone , email )
            
        elif choice == '2':
            try:
                client_id = int(input("ID клиента: "))
                amount = float(input("Сумма кредита: "))
                interest_rate_percent = float(input("Процентная ставка (%): "))
                term_months = int(input("Срок кредита (месяцев): "))
                create_loan(client_id , amount , interest_rate_percent , term_months )
            except ValueError:
                print("Некорректный ввод.")
                
        elif choice == '3':
            clients = list_clients()
            for c in clients:
                print(f"ID: {c[0]}, Имя: {c[1]}, ДР: {c[2]}, Телефон: {c[3]}, Email: {c[4]}, Зарегистрирован: {c[5]}")
                
        elif choice == '4':
            loans = list_loans()
            for l in loans:
                print(f"ID: {l[0]}, Клиент: {l[1]}, Сумма: {l[2]}, Процент: {l[3]*100}%, Срок: {l[4]} мес., Начало: {l[5]}, Статус: {l[6]}")
                
        elif choice == '5':
            try:
                loan_id = int(input("ID кредита для просмотра графика: "))
                view_payment_schedule(loan_id)
            except ValueError:
                print("Некорректный ввод.")
                
        elif choice == '6':
            try:
                payment_id = int(input("ID платежа для оплаты: "))
                pay_payment(payment_id)
            except ValueError:
                print("Некорректный ввод.")
                
        elif choice == '0':
            break

if __name__ == "__main__":
    main()