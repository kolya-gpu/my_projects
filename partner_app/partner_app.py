import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
import json
import os
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from dataclasses import dataclass, asdict
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import webbrowser
import requests
import csv
from pathlib import Path

@dataclass
class Partner:
    """Расширенный класс для представления партнера."""
    id: int
    name: str
    email: str
    phone: str
    company: str
    total_sales: float
    commission_rate: float
    join_date: str
    status: str
    notes: str
    category: str
    region: str
    last_contact: str
    priority: str = "medium"
    tags: str = ""
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Task:
    """Класс для представления задач."""
    id: int
    partner_id: int
    title: str
    description: str
    due_date: str
    priority: str
    status: str
    assigned_to: str
    created_date: str

@dataclass
class Notification:
    """Класс для представления уведомлений."""
    id: int
    partner_id: int
    type: str
    message: str
    date: str
    read: bool

class DatabaseManager:
    """Менеджер базы данных для хранения информации о партнерах."""
    
    def __init__(self, db_path: str = "partners.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                company TEXT,
                total_sales REAL DEFAULT 0,
                commission_rate REAL DEFAULT 0.1,
                join_date TEXT,
                status TEXT DEFAULT 'active',
                notes TEXT,
                category TEXT DEFAULT 'general',
                region TEXT,
                last_contact TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                amount REAL,
                date TEXT,
                description TEXT,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                contact_type TEXT,
                date TEXT,
                notes TEXT,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_partner(self, partner: Partner) -> int:
        """Добавление партнера в базу данных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO partners (name, email, phone, company, total_sales, commission_rate, 
                                join_date, status, notes, category, region, last_contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (partner.name, partner.email, partner.phone, partner.company, partner.total_sales,
              partner.commission_rate, partner.join_date, partner.status, partner.notes,
              partner.category, partner.region, partner.last_contact))
        
        partner_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return partner_id
    
    def get_all_partners(self) -> List[Partner]:
        """Получение всех партнеров из базы данных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM partners')
        rows = cursor.fetchall()
        conn.close()
        
        partners = []
        for row in rows:
            partner = Partner(
                id=row[0], name=row[1], email=row[2], phone=row[3], company=row[4],
                total_sales=row[5], commission_rate=row[6], join_date=row[7], status=row[8],
                notes=row[9], category=row[10], region=row[11], last_contact=row[12]
            )
            partners.append(partner)
        
        return partners
    
    def update_partner(self, partner: Partner):
        """Обновление партнера в базе данных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE partners SET name=?, email=?, phone=?, company=?, total_sales=?, 
                              commission_rate=?, join_date=?, status=?, notes=?, 
                              category=?, region=?, last_contact=?
            WHERE id=?
        ''', (partner.name, partner.email, partner.phone, partner.company, partner.total_sales,
              partner.commission_rate, partner.join_date, partner.status, partner.notes,
              partner.category, partner.region, partner.last_contact, partner.id))
        
        conn.commit()
        conn.close()
    
    def delete_partner(self, partner_id: int):
        """Удаление партнера из базы данных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM partners WHERE id=?', (partner_id,))
        cursor.execute('DELETE FROM sales_history WHERE partner_id=?', (partner_id,))
        cursor.execute('DELETE FROM contacts WHERE partner_id=?', (partner_id,))
        
        conn.commit()
        conn.close()
    
    def search_partners(self, query: str) -> List[Partner]:
        """Поиск партнеров по различным критериям."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM partners WHERE 
                name LIKE ? OR email LIKE ? OR company LIKE ? OR 
                category LIKE ? OR region LIKE ? OR status LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        partners = []
        for row in rows:
            partner = Partner(
                id=row[0], name=row[1], email=row[2], phone=row[3], company=row[4],
                total_sales=row[5], commission_rate=row[6], join_date=row[7], status=row[8],
                notes=row[9], category=row[10], region=row[11], last_contact=row[12]
            )
            partners.append(partner)
        
        return partners

class AnalyticsManager:
    """Менеджер аналитики для работы с данными партнеров."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_sales_summary(self) -> Dict:
        """Получение сводки по продажам."""
        partners = self.db_manager.get_all_partners()
        
        total_sales = sum(p.total_sales for p in partners)
        total_commission = sum(p.total_sales * p.commission_rate for p in partners)
        active_partners = len([p for p in partners if p.status == 'active'])
        
        return {
            'total_sales': total_sales,
            'total_commission': total_commission,
            'active_partners': active_partners,
            'total_partners': len(partners)
        }
    
    def get_top_performers(self, limit: int = 5) -> List[Partner]:
        """Получение топ-партнеров по продажам."""
        partners = self.db_manager.get_all_partners()
        return sorted(partners, key=lambda x: x.total_sales, reverse=True)[:limit]
    
    def get_category_distribution(self) -> Dict[str, int]:
        """Получение распределения партнеров по категориям."""
        partners = self.db_manager.get_all_partners()
        distribution = {}
        
        for partner in partners:
            category = partner.category or 'general'
            distribution[category] = distribution.get(category, 0) + 1
        
        return distribution
    
    def get_region_performance(self) -> Dict[str, float]:
        """Получение производительности по регионам."""
        partners = self.db_manager.get_all_partners()
        region_sales = {}
        
        for partner in partners:
            region = partner.region or 'Unknown'
            region_sales[region] = region_sales.get(region, 0) + partner.total_sales
        
        return region_sales

class EmailManager:
    """Менеджер для отправки email уведомлений."""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = ""
        self.sender_password = ""
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Отправка email."""
        try:
            if not self.sender_email or not self.sender_password:
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return False
    
    def send_partner_welcome(self, partner: Partner):
        """Отправка приветственного email новому партнеру."""
        subject = "Добро пожаловать в нашу партнерскую программу!"
        body = f"""
        Здравствуйте, {partner.name}!
        
        Мы рады приветствовать вас в нашей партнерской программе.
        Ваша компания: {partner.company}
        Регион: {partner.region}
        
        Если у вас есть вопросы, не стесняйтесь обращаться к нам.
        
        С уважением,
        Команда поддержки
        """
        
        return self.send_email(partner.email, subject, body)

class TaskManager:
    """Менеджер для управления задачами."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.init_tasks_table()
    
    def init_tasks_table(self):
        """Инициализация таблицы задач."""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                assigned_to TEXT,
                created_date TEXT,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_task(self, task: Task) -> int:
        """Добавление новой задачи."""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (partner_id, title, description, due_date, priority, status, assigned_to, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task.partner_id, task.title, task.description, task.due_date, 
              task.priority, task.status, task.assigned_to, task.created_date))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def get_tasks_for_partner(self, partner_id: int) -> List[Task]:
        """Получение задач для конкретного партнера."""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE partner_id = ? ORDER BY due_date', (partner_id,))
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            task = Task(
                id=row[0], partner_id=row[1], title=row[2], description=row[3],
                due_date=row[4], priority=row[5], status=row[6], assigned_to=row[7], created_date=row[8]
            )
            tasks.append(task)
        
        return tasks
    
    def update_task_status(self, task_id: int, status: str):
        """Обновление статуса задачи."""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        conn.commit()
        conn.close()

class NotificationManager:
    """Менеджер для управления уведомлениями."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.init_notifications_table()
    
    def init_notifications_table(self):
        """Инициализация таблицы уведомлений."""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                type TEXT,
                message TEXT,
                date TEXT,
                read BOOLEAN DEFAULT 0,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_notification(self, notification: Notification):
        """Добавление нового уведомления."""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (partner_id, type, message, date, read)
            VALUES (?, ?, ?, ?, ?)
        ''', (notification.partner_id, notification.type, notification.message, 
              notification.date, notification.read))
        
        conn.commit()
        conn.close()
    
    def get_unread_notifications(self) -> List[Notification]:
        """Получение непрочитанных уведомлений."""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM notifications WHERE read = 0 ORDER BY date DESC')
        rows = cursor.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notification = Notification(
                id=row[0], partner_id=row[1], type=row[2], message=row[3],
                date=row[4], read=bool(row[5])
            )
            notifications.append(notification)
        
        return notifications

class AdvancedDatabaseManager(DatabaseManager):
    """Расширенный менеджер базы данных."""
    
    def __init__(self, db_path: str = "partners.db"):
        super().__init__(db_path)
        self.init_advanced_tables()
    
    def init_advanced_tables(self):
        """Инициализация дополнительных таблиц."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для тегов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                tag TEXT,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Таблица для истории изменений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS change_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                change_date TEXT,
                user TEXT,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Таблица для файлов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                filename TEXT,
                file_path TEXT,
                upload_date TEXT,
                file_type TEXT,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_partner_with_history(self, partner: Partner, user: str = "system"):
        """Добавление партнера с записью в историю."""
        partner_id = self.add_partner(partner)
        
        # Запись в историю изменений
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO change_history (partner_id, field_name, old_value, new_value, change_date, user)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (partner_id, "creation", "", "created", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user))
        
        conn.commit()
        conn.close()
        
        return partner_id
    
    def update_partner_with_history(self, partner: Partner, old_partner: Partner, user: str = "system"):
        """Обновление партнера с записью изменений в историю."""
        # Запись изменений в историю
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        changes = [
            ("name", old_partner.name, partner.name),
            ("email", old_partner.email, partner.email),
            ("phone", old_partner.phone, partner.phone),
            ("company", old_partner.company, partner.company),
            ("total_sales", str(old_partner.total_sales), str(partner.total_sales)),
            ("status", old_partner.status, partner.status),
            ("category", old_partner.category, partner.category)
        ]
        
        for field, old_val, new_val in changes:
            if old_val != new_val:
                cursor.execute('''
                    INSERT INTO change_history (partner_id, field_name, old_value, new_value, change_date, user)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (partner.id, field, str(old_val), str(new_val), 
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user))
        
        conn.commit()
        conn.close()
        
        # Обновление партнера
        self.update_partner(partner)
    
    def get_partner_history(self, partner_id: int) -> List[Dict]:
        """Получение истории изменений партнера."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT field_name, old_value, new_value, change_date, user 
            FROM change_history 
            WHERE partner_id = ? 
            ORDER BY change_date DESC
        ''', (partner_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'field': row[0],
                'old_value': row[1],
                'new_value': row[2],
                'date': row[3],
                'user': row[4]
            })
        
        return history
    
    def search_partners_advanced(self, query: str, filters: Dict = None) -> List[Partner]:
        """Расширенный поиск партнеров."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = '''
            SELECT DISTINCT p.* FROM partners p
            LEFT JOIN partner_tags pt ON p.id = pt.partner_id
            WHERE (p.name LIKE ? OR p.email LIKE ? OR p.company LIKE ? 
                   OR p.category LIKE ? OR p.region LIKE ? OR p.status LIKE ?
                   OR pt.tag LIKE ?)
        '''
        
        params = [f'%{query}%'] * 6 + [f'%{query}%']
        
        if filters:
            if filters.get('category') and filters['category'] != 'all':
                sql += ' AND p.category = ?'
                params.append(filters['category'])
            
            if filters.get('status') and filters['status'] != 'all':
                sql += ' AND p.status = ?'
                params.append(filters['status'])
            
            if filters.get('region') and filters['region'] != 'all':
                sql += ' AND p.region = ?'
                params.append(filters['region'])
        
        sql += ' ORDER BY p.total_sales DESC'
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        partners = []
        for row in rows:
            partner = Partner(
                id=row[0], name=row[1], email=row[2], phone=row[3], company=row[4],
                total_sales=row[5], commission_rate=row[6], join_date=row[7], status=row[8],
                notes=row[9], category=row[10], region=row[11], last_contact=row[12]
            )
            partners.append(partner)
        
        return partners

class AdvancedAnalyticsManager(AnalyticsManager):
    """Расширенный менеджер аналитики."""
    
    def __init__(self, db_manager: AdvancedDatabaseManager):
        super().__init__(db_manager)
        self.db_manager = db_manager
    
    def get_performance_trends(self, days: int = 30) -> Dict:
        """Получение трендов производительности."""
        # Здесь можно добавить логику для анализа трендов
        # Пока возвращаем заглушку
        return {
            'sales_growth': 0.15,
            'new_partners': 5,
            'active_partners_change': 0.08
        }
    
    def get_partner_engagement_score(self, partner_id: int) -> float:
        """Расчет показателя вовлеченности партнера."""
        # Простая формула для демонстрации
        partner = next((p for p in self.db_manager.get_all_partners() if p.id == partner_id), None)
        if not partner:
            return 0.0
        
        # Базовый балл на основе продаж
        base_score = min(partner.total_sales / 10000, 1.0) * 50
        
        # Бонус за активность
        if partner.status == 'active':
            base_score += 20
        
        # Бонус за категорию
        if partner.category == 'vip':
            base_score += 15
        elif partner.category == 'premium':
            base_score += 10
        
        return min(base_score, 100.0)
    
    def generate_performance_report(self) -> str:
        """Генерация отчета о производительности."""
        summary = self.get_sales_summary()
        top_performers = self.get_top_performers(10)
        trends = self.get_performance_trends()
        
        report = f"""
        ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ ПАРТНЕРОВ
        ======================================
        
        ОБЩАЯ СТАТИСТИКА:
        - Всего партнеров: {summary['total_partners']}
        - Активных партнеров: {summary['active_partners']}
        - Общий объем продаж: ${summary['total_sales']:,.2f}
        - Общая комиссия: ${summary['total_commission']:,.2f}
        
        ТРЕНДЫ:
        - Рост продаж: {trends['sales_growth']*100:.1f}%
        - Новых партнеров: {trends['new_partners']}
        - Изменение активных партнеров: {trends['active_partners_change']*100:.1f}%
        
        ТОП-10 ПАРТНЕРОВ:
        """
        
        for i, partner in enumerate(top_performers, 1):
            engagement = self.get_partner_engagement_score(partner.id)
            report += f"\n{i}. {partner.name} - ${partner.total_sales:,.2f} (Вовлеченность: {engagement:.1f}%)"
        
        return report

class AdvancedPartnerApp:
    """Расширенное приложение для управления партнерами."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Partner Management System")
        self.root.geometry("1200x800")
        
        # Инициализация менеджеров
        self.db_manager = AdvancedDatabaseManager()
        self.analytics_manager = AdvancedAnalyticsManager(self.db_manager)
        self.email_manager = EmailManager()
        self.task_manager = TaskManager(self.db_manager)
        self.notification_manager = NotificationManager(self.db_manager)
        
        # Переменные состояния
        self.current_view = "main"
        self.search_query = tk.StringVar()
        self.filter_category = tk.StringVar(value="all")
        self.filter_status = tk.StringVar(value="all")
        
        # Создание интерфейса
        self.create_menu()
        self.create_main_interface()
        self.load_partners()
        
        # Загрузка настроек
        self.load_settings()
        
        # Запуск автообновления
        self.start_auto_refresh()
    
    def create_menu(self):
        """Создание главного меню."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт в CSV", command=self.export_to_csv)
        file_menu.add_command(label="Импорт из CSV", command=self.import_from_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню партнеры
        partner_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Партнеры", menu=partner_menu)
        partner_menu.add_command(label="Добавить партнера", command=self.show_add_partner_dialog)
        partner_menu.add_command(label="Массовое редактирование", command=self.show_bulk_edit_dialog)
        partner_menu.add_command(label="Управление категориями", command=self.show_category_manager)
        
        # Меню аналитика
        analytics_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Аналитика", menu=analytics_menu)
        analytics_menu.add_command(label="Дашборд", command=self.show_dashboard)
        analytics_menu.add_command(label="Отчеты", command=self.show_reports)
        analytics_menu.add_command(label="Графики", command=self.show_charts)
        
        # Меню настройки
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Настройки приложения", command=self.show_settings)
        settings_menu.add_command(label="Резервное копирование", command=self.backup_database)
    
    def create_main_interface(self):
        """Создание основного интерфейса."""
        # Главный фрейм
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель с поиском и фильтрами
        top_panel = ttk.Frame(main_frame)
        top_panel.pack(fill=tk.X, pady=(0, 10))
        
        # Поиск
        ttk.Label(top_panel, text="Поиск:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(top_panel, textvariable=self.search_query, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Расширенный поиск
        ttk.Button(top_panel, text="🔍", command=self.show_advanced_search, width=3).pack(side=tk.LEFT, padx=(0, 10))
        
        # Фильтры
        ttk.Label(top_panel, text="Категория:").pack(side=tk.LEFT)
        category_combo = ttk.Combobox(top_panel, textvariable=self.filter_category, 
                                    values=["all", "general", "premium", "vip", "new"], width=10)
        category_combo.pack(side=tk.LEFT, padx=(5, 10))
        category_combo.bind('<<ComboboxSelected>>', self.apply_filters)
        
        ttk.Label(top_panel, text="Статус:").pack(side=tk.LEFT)
        status_combo = ttk.Combobox(top_panel, textvariable=self.filter_status,
                                  values=["all", "active", "inactive", "pending"], width=10)
        status_combo.pack(side=tk.LEFT, padx=(5, 10))
        status_combo.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # Кнопки действий
        ttk.Button(top_panel, text="Обновить", command=self.load_partners).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(top_panel, text="Добавить", command=self.show_add_partner_dialog).pack(side=tk.RIGHT)
        
        # Создание Treeview для партнеров
        columns = ('ID', 'Имя', 'Компания', 'Email', 'Продажи', 'Комиссия', 'Категория', 'Статус', 'Регион')
        self.partner_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        # Настройка колонок
        for col in columns:
            self.partner_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.partner_tree.column(col, width=100, minwidth=80)
        
        # Скроллбары
        tree_scroll_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.partner_tree.yview)
        tree_scroll_x = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.partner_tree.xview)
        self.partner_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Размещение элементов
        self.partner_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Привязка событий
        self.partner_tree.bind('<Double-1>', self.on_partner_double_click)
        self.partner_tree.bind('<Button-3>', self.show_context_menu)
        
        # Нижняя панель с информацией
        bottom_panel = ttk.Frame(main_frame)
        bottom_panel.pack(fill=tk.X, pady=(10, 0))
        
        # Статистика
        self.stats_label = ttk.Label(bottom_panel, text="")
        self.stats_label.pack(side=tk.LEFT)
        
        # Кнопки быстрых действий
        ttk.Button(bottom_panel, text="Редактировать", command=self.edit_selected_partner).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_panel, text="Удалить", command=self.delete_selected_partner).pack(side=tk.RIGHT)
        ttk.Button(bottom_panel, text="Задачи", command=self.show_tasks_manager).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_panel, text="Уведомления", command=self.show_notifications).pack(side=tk.RIGHT, padx=(5, 0))
    
    def load_partners(self):
        """Загрузка партнеров в Treeview."""
        # Очистка существующих данных
        for item in self.partner_tree.get_children():
            self.partner_tree.delete(item)
        
        # Получение партнеров
        partners = self.db_manager.get_all_partners()
        
        # Применение фильтров
        filtered_partners = self.filter_partners(partners)
        
        # Добавление в Treeview
        for partner in filtered_partners:
            commission = partner.total_sales * partner.commission_rate
            self.partner_tree.insert('', 'end', values=(
                partner.id, partner.name, partner.company, partner.email,
                f"${partner.total_sales:,.2f}", f"${commission:,.2f}",
                partner.category, partner.status, partner.region
            ))
        
        # Обновление статистики
        self.update_statistics()
    
    def filter_partners(self, partners: List[Partner]) -> List[Partner]:
        """Фильтрация партнеров по заданным критериям."""
        filtered = partners
        
        # Фильтр по категории
        if self.filter_category.get() != "all":
            filtered = [p for p in filtered if p.category == self.filter_category.get()]
        
        # Фильтр по статусу
        if self.filter_status.get() != "all":
            filtered = [p for p in filtered if p.status == self.filter_status.get()]
        
        # Фильтр по поиску
        query = self.search_query.get().lower()
        if query:
            filtered = [p for p in filtered if 
                       query in p.name.lower() or 
                       query in p.company.lower() or 
                       query in p.email.lower()]
        
        return filtered
    
    def on_search(self, event=None):
        """Обработчик поиска."""
        self.load_partners()
    
    def apply_filters(self, event=None):
        """Применение фильтров."""
        self.load_partners()
    
    def update_statistics(self):
        """Обновление статистики."""
        summary = self.analytics_manager.get_sales_summary()
        stats_text = f"Всего партнеров: {summary['total_partners']} | " \
                    f"Активных: {summary['active_partners']} | " \
                    f"Общие продажи: ${summary['total_sales']:,.2f} | " \
                    f"Общая комиссия: ${summary['total_commission']:,.2f}"
        self.stats_label.config(text=stats_text)
    
    def show_add_partner_dialog(self):
        """Показать диалог добавления партнера."""
        dialog = PartnerDialog(self.root, self.db_manager, self)
        self.root.wait_window(dialog.dialog)
    
    def edit_selected_partner(self):
        """Редактирование выбранного партнера."""
        selection = self.partner_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите партнера для редактирования.")
            return
        
        partner_id = self.partner_tree.item(selection[0])['values'][0]
        partners = self.db_manager.get_all_partners()
        partner = next((p for p in partners if p.id == partner_id), None)
        
        if partner:
            dialog = PartnerDialog(self.root, self.db_manager, self, partner)
            self.root.wait_window(dialog.dialog)
    
    def delete_selected_partner(self):
        """Удаление выбранного партнера."""
        selection = self.partner_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите партнера для удаления.")
            return
        
        partner_id = self.partner_tree.item(selection[0])['values'][0]
        partner_name = self.partner_tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить партнера '{partner_name}'?"):
            self.db_manager.delete_partner(partner_id)
            self.load_partners()
            messagebox.showinfo("Успех", "Партнер удален.")
    
    def on_partner_double_click(self, event):
        """Обработчик двойного клика по партнеру."""
        self.edit_selected_partner()
    
    def show_context_menu(self, event):
        """Показать контекстное меню."""
        selection = self.partner_tree.selection()
        if not selection:
            return
        
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Редактировать", command=self.edit_selected_partner)
        context_menu.add_command(label="Удалить", command=self.delete_selected_partner)
        context_menu.add_separator()
        context_menu.add_command(label="Просмотр деталей", command=self.show_partner_details)
        context_menu.add_command(label="История изменений", command=self.show_partner_history)
        context_menu.add_command(label="История контактов", command=self.show_contact_history)
        
        context_menu.tk_popup(event.x_root, event.y_root)
    
    def show_partner_details(self):
        """Показать детальную информацию о партнере."""
        selection = self.partner_tree.selection()
        if not selection:
            return
        
        partner_id = self.partner_tree.item(selection[0])['values'][0]
        partners = self.db_manager.get_all_partners()
        partner = next((p for p in partners if p.id == partner_id), None)
        
        if partner:
            self.show_partner_details_window(partner)
    
    def show_partner_details_window(self, partner: Partner):
        """Окно с детальной информацией о партнере."""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали партнера: {partner.name}")
        details_window.geometry("600x500")
        
        # Создание интерфейса
        notebook = ttk.Notebook(details_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка основной информации
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Основная информация")
        
        # Поля информации
        fields = [
            ("ID:", partner.id),
            ("Имя:", partner.name),
            ("Email:", partner.email),
            ("Телефон:", partner.phone),
            ("Компания:", partner.company),
            ("Продажи:", f"${partner.total_sales:,.2f}"),
            ("Комиссия:", f"{partner.commission_rate*100:.1f}%"),
            ("Дата присоединения:", partner.join_date),
            ("Статус:", partner.status),
            ("Категория:", partner.category),
            ("Регион:", partner.region),
            ("Последний контакт:", partner.last_contact)
        ]
        
        for i, (label, value) in enumerate(fields):
            ttk.Label(info_frame, text=label, font=("Arial", 10, "bold")).grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            ttk.Label(info_frame, text=str(value)).grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Вкладка заметок
        notes_frame = ttk.Frame(notebook)
        notebook.add(notes_frame, text="Заметки")
        
        notes_text = scrolledtext.ScrolledText(notes_frame, wrap=tk.WORD, height=15)
        notes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        notes_text.insert(tk.END, partner.notes or "")
        
        # Кнопка сохранения
        def save_notes():
            partner.notes = notes_text.get("1.0", tk.END).strip()
            self.db_manager.update_partner(partner)
            messagebox.showinfo("Успех", "Заметки сохранены.")
        
        ttk.Button(notes_frame, text="Сохранить заметки", command=save_notes).pack(pady=10)
    
    def show_partner_history(self):
        """Показать историю изменений партнера."""
        selection = self.partner_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите партнера для просмотра истории.")
            return
        
        partner_id = self.partner_tree.item(selection[0])['values'][0]
        partners = self.db_manager.get_all_partners()
        partner = next((p for p in partners if p.id == partner_id), None)
        
        if partner:
            self.show_partner_history_window(partner)
    
    def show_partner_history_window(self, partner: Partner):
        """Окно с историей изменений партнера."""
        history_window = tk.Toplevel(self.root)
        history_window.title(f"История изменений: {partner.name}")
        history_window.geometry("700x500")
        
        # Создание интерфейса
        ttk.Label(history_window, text=f"История изменений партнера: {partner.name}", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Список изменений
        history_frame = ttk.Frame(history_window)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создание Treeview для истории
        columns = ('Поле', 'Старое значение', 'Новое значение', 'Дата', 'Пользователь')
        history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            history_tree.heading(col, text=col)
            history_tree.column(col, width=120, minwidth=100)
        
        # Скроллбары
        history_scroll_y = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscrollcommand=history_scroll_y.set)
        
        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Загрузка истории
        try:
            if hasattr(self.db_manager, 'get_partner_history'):
                history = self.db_manager.get_partner_history(partner.id)
                
                for change in history:
                    history_tree.insert('', 'end', values=(
                        change['field'],
                        change['old_value'][:50] + "..." if len(str(change['old_value'])) > 50 else str(change['old_value']),
                        change['new_value'][:50] + "..." if len(str(change['new_value'])) > 50 else str(change['new_value']),
                        change['date'],
                        change['user']
                    ))
            else:
                ttk.Label(history_frame, text="История изменений недоступна для базовой версии").pack(pady=20)
        except Exception as e:
            ttk.Label(history_frame, text=f"Ошибка загрузки истории: {str(e)}").pack(pady=20)
    
    def show_contact_history(self):
        """Показать историю контактов с партнером."""
        # Заглушка для демонстрации
        messagebox.showinfo("Информация", "Функция истории контактов будет реализована в следующей версии.")
    
    def show_dashboard(self):
        """Показать дашборд с аналитикой."""
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("Аналитический дашборд")
        dashboard_window.geometry("1000x700")
        
        # Создание вкладок
        notebook = ttk.Notebook(dashboard_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка обзора
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="Обзор")
        
        # Сводная статистика
        summary = self.analytics_manager.get_sales_summary()
        
        stats_frame = ttk.LabelFrame(overview_frame, text="Сводная статистика")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        stats_text = f"""
        Всего партнеров: {summary['total_partners']}
        Активных партнеров: {summary['active_partners']}
        Общий объем продаж: ${summary['total_sales']:,.2f}
        Общая комиссия: ${summary['total_commission']:,.2f}
        """
        
        ttk.Label(stats_frame, text=stats_text, font=("Arial", 12)).pack(padx=20, pady=20)
        
        # Топ-партнеры
        top_partners = self.analytics_manager.get_top_performers(5)
        
        top_frame = ttk.LabelFrame(overview_frame, text="Топ-5 партнеров")
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for i, partner in enumerate(top_partners, 1):
            partner_text = f"{i}. {partner.name} - ${partner.total_sales:,.2f}"
            ttk.Label(top_frame, text=partner_text).pack(anchor=tk.W, padx=20, pady=5)
        
        # Вкладка графиков
        charts_frame = ttk.Frame(notebook)
        notebook.add(charts_frame, text="Графики")
        
        # Создание графиков
        self.create_charts(charts_frame)
    
    def create_charts(self, parent):
        """Создание графиков для дашборда."""
        # Распределение по категориям
        category_data = self.analytics_manager.get_category_distribution()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Круговая диаграмма категорий
        if category_data:
            categories = list(category_data.keys())
            values = list(category_data.values())
            ax1.pie(values, labels=categories, autopct='%1.1f%%')
            ax1.set_title('Распределение по категориям')
        
        # Столбчатая диаграмма регионов
        region_data = self.analytics_manager.get_region_performance()
        if region_data:
            regions = list(region_data.keys())
            sales = list(region_data.values())
            
            ax2.bar(regions, sales)
            ax2.set_title('Продажи по регионам')
            ax2.set_xlabel('Регион')
            ax2.set_ylabel('Продажи ($)')
            ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Встраивание в tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def show_reports(self):
        """Показать окно отчетов."""
        report_window = tk.Toplevel(self.root)
        report_window.title("Генерация отчетов")
        report_window.geometry("800x600")
        
        # Создание интерфейса для отчетов
        notebook = ttk.Notebook(report_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка производительности
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="Производительность")
        
        # Кнопка генерации отчета
        ttk.Button(perf_frame, text="Сгенерировать отчет о производительности", 
                  command=self.generate_performance_report).pack(pady=20)
        
        # Область для отображения отчета
        report_text = scrolledtext.ScrolledText(perf_frame, wrap=tk.WORD, height=25)
        report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка экспорта
        export_frame = ttk.Frame(notebook)
        notebook.add(export_frame, text="Экспорт данных")
        
        ttk.Button(export_frame, text="Экспорт в PDF", 
                  command=self.export_to_pdf).pack(pady=10)
        ttk.Button(export_frame, text="Экспорт в Excel", 
                  command=self.export_to_excel).pack(pady=10)
        ttk.Button(export_frame, text="Экспорт в JSON", 
                  command=self.export_to_json).pack(pady=10)
    
    def generate_performance_report(self):
        """Генерация отчета о производительности."""
        try:
            report = self.analytics_manager.generate_performance_report()
            
            # Сохранение отчета в файл
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                messagebox.showinfo("Успех", f"Отчет сохранен в {file_path}")
                
                # Отображение отчета в окне
                for widget in self.root.winfo_children():
                    if isinstance(widget, tk.Toplevel) and widget.title() == "Генерация отчетов":
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Notebook):
                                for tab in child.winfo_children():
                                    if isinstance(tab, ttk.Frame):
                                        for widget in tab.winfo_children():
                                            if isinstance(widget, scrolledtext.ScrolledText):
                                                widget.delete("1.0", tk.END)
                                                widget.insert("1.0", report)
                                                break
                                        break
                                break
                        break
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при генерации отчета: {str(e)}")
    
    def export_to_pdf(self):
        """Экспорт данных в PDF."""
        messagebox.showinfo("Информация", "Функция экспорта в PDF будет реализована в следующей версии.")
    
    def export_to_excel(self):
        """Экспорт данных в Excel."""
        messagebox.showinfo("Информация", "Функция экспорта в Excel будет реализована в следующей версии.")
    
    def export_to_json(self):
        """Экспорт данных в JSON."""
        try:
            partners = self.db_manager.get_all_partners()
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                data = []
                for partner in partners:
                    data.append(partner.to_dict())
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Успех", f"Данные экспортированы в JSON: {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте в JSON: {str(e)}")
    
    def show_charts(self):
        """Показать окно графиков."""
        self.show_dashboard()
    
    def show_settings(self):
        """Показать настройки приложения."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки приложения")
        settings_window.geometry("600x500")
        
        # Создание интерфейса настроек
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка общих настроек
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Общие")
        
        # Настройки автообновления
        ttk.Label(general_frame, text="Интервал автообновления (секунды):").pack(anchor=tk.W, padx=10, pady=5)
        refresh_var = tk.StringVar(value="30")
        refresh_entry = ttk.Entry(general_frame, textvariable=refresh_var, width=10)
        refresh_entry.pack(anchor=tk.W, padx=10, pady=5)
        
        # Настройки email
        email_frame = ttk.Frame(notebook)
        notebook.add(email_frame, text="Email")
        
        ttk.Label(email_frame, text="SMTP сервер:").pack(anchor=tk.W, padx=10, pady=5)
        smtp_var = tk.StringVar(value="smtp.gmail.com")
        smtp_entry = ttk.Entry(email_frame, textvariable=smtp_var, width=30)
        smtp_entry.pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Label(email_frame, text="Email:").pack(anchor=tk.W, padx=10, pady=5)
        email_var = tk.StringVar()
        email_entry = ttk.Entry(email_frame, textvariable=email_var, width=30)
        email_entry.pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Label(email_frame, text="Пароль:").pack(anchor=tk.W, padx=10, pady=5)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(email_frame, textvariable=password_var, show="*", width=30)
        password_entry.pack(anchor=tk.W, padx=10, pady=5)
        
        # Кнопка сохранения
        def save_settings():
            # Сохранение настроек
            settings = {
                'refresh_interval': int(refresh_var.get()),
                'smtp_server': smtp_var.get(),
                'email': email_var.get(),
                'password': password_var.get()
            }
            
            try:
                with open('settings.json', 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
                
                # Обновление менеджеров
                self.email_manager.smtp_server = smtp_var.get()
                self.email_manager.sender_email = email_var.get()
                self.email_manager.sender_password = password_var.get()
                
                messagebox.showinfo("Успех", "Настройки сохранены")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении настроек: {str(e)}")
        
        ttk.Button(email_frame, text="Сохранить настройки", command=save_settings).pack(pady=20)
    
    def load_settings(self):
        """Загрузка настроек приложения."""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Применение настроек
                if 'email' in settings:
                    self.email_manager.sender_email = settings['email']
                if 'password' in settings:
                    self.email_manager.sender_password = settings['password']
                if 'smtp_server' in settings:
                    self.email_manager.smtp_server = settings['smtp_server']
                
                # Здесь можно добавить другие настройки
                
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    
    def backup_database(self):
        """Создание резервной копии базы данных."""
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if backup_path:
            try:
                import shutil
                shutil.copy2(self.db_manager.db_path, backup_path)
                messagebox.showinfo("Успех", f"Резервная копия создана: {backup_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при создании резервной копии: {str(e)}")
    
    def export_to_csv(self):
        """Экспорт данных в CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                partners = self.db_manager.get_all_partners()
                
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    import csv
                    writer = csv.writer(csvfile)
                    
                    # Заголовки
                    writer.writerow(['ID', 'Имя', 'Email', 'Телефон', 'Компания', 'Продажи', 
                                   'Комиссия', 'Дата присоединения', 'Статус', 'Категория', 'Регион'])
                    
                    # Данные
                    for partner in partners:
                        writer.writerow([
                            partner.id, partner.name, partner.email, partner.phone, partner.company,
                            partner.total_sales, partner.commission_rate, partner.join_date,
                            partner.status, partner.category, partner.region
                        ])
                
                messagebox.showinfo("Успех", f"Данные экспортированы в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при экспорте: {str(e)}")
    
    def import_from_csv(self):
        """Импорт данных из CSV."""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for row in reader:
                        # Создание партнера из строки CSV
                        partner = Partner(
                            id=0,  # Будет назначен базой данных
                            name=row.get('Имя', ''),
                            email=row.get('Email', ''),
                            phone=row.get('Телефон', ''),
                            company=row.get('Компания', ''),
                            total_sales=float(row.get('Продажи', 0)),
                            commission_rate=float(row.get('Комиссия', 0.1)),
                            join_date=row.get('Дата присоединения', datetime.now().strftime('%Y-%m-%d')),
                            status=row.get('Статус', 'active'),
                            notes='',
                            category=row.get('Категория', 'general'),
                            region=row.get('Регион', ''),
                            last_contact=datetime.now().strftime('%Y-%m-%d')
                        )
                        
                        self.db_manager.add_partner(partner)
                
                self.load_partners()
                messagebox.showinfo("Успех", "Данные импортированы")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при импорте: {str(e)}")
    
    def show_bulk_edit_dialog(self):
        """Показать диалог массового редактирования."""
        messagebox.showinfo("Информация", "Функция массового редактирования будет реализована в следующей версии.")
    
    def show_advanced_search(self):
        """Показать окно расширенного поиска."""
        search_window = tk.Toplevel(self.root)
        search_window.title("Расширенный поиск")
        search_window.geometry("600x500")
        
        # Создание интерфейса
        main_frame = ttk.Frame(search_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="Расширенный поиск партнеров", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Поля поиска
        search_fields = [
            ("Имя:", "name"),
            ("Email:", "email"),
            ("Компания:", "company"),
            ("Категория:", "category"),
            ("Регион:", "region"),
            ("Статус:", "status")
        ]
        
        self.search_entries = {}
        for i, (label, field) in enumerate(search_fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if field == "category":
                combo = ttk.Combobox(main_frame, values=["", "general", "premium", "vip", "new"], width=30)
                combo.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=5)
                self.search_entries[field] = combo
            elif field == "status":
                combo = ttk.Combobox(main_frame, values=["", "active", "inactive", "pending"], width=30)
                combo.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=5)
                self.search_entries[field] = combo
            else:
                entry = ttk.Entry(main_frame, width=30)
                entry.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=5)
                self.search_entries[field] = entry
        
        # Диапазон продаж
        ttk.Label(main_frame, text="Продажи от:").grid(row=len(search_fields), column=0, sticky=tk.W, pady=5)
        sales_from = ttk.Entry(main_frame, width=15)
        sales_from.grid(row=len(search_fields), column=1, sticky=tk.W, padx=(10, 5), pady=5)
        
        ttk.Label(main_frame, text="до:").grid(row=len(search_fields), column=1, sticky=tk.W, padx=(0, 0), pady=5)
        sales_to = ttk.Entry(main_frame, width=15)
        sales_to.grid(row=len(search_fields), column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        self.search_entries["sales_from"] = sales_from
        self.search_entries["sales_to"] = sales_to
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(search_fields)+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Поиск", command=self.perform_advanced_search).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Очистить", command=self.clear_advanced_search).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Закрыть", command=search_window.destroy).pack(side=tk.LEFT)
        
        # Результаты поиска
        results_frame = ttk.LabelFrame(main_frame, text="Результаты поиска")
        results_frame.grid(row=len(search_fields)+2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Treeview для результатов
        columns = ('ID', 'Имя', 'Компания', 'Email', 'Продажи', 'Категория', 'Статус')
        self.search_results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.search_results_tree.heading(col, text=col)
            self.search_results_tree.column(col, width=80, minwidth=70)
        
        # Скроллбары
        search_scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.search_results_tree.yview)
        self.search_results_tree.configure(yscrollcommand=search_scroll_y.set)
        
        self.search_results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        search_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Настройка расширения колонок
        main_frame.columnconfigure(1, weight=1)
    
    def perform_advanced_search(self):
        """Выполнение расширенного поиска."""
        try:
            # Сбор критериев поиска
            search_criteria = {}
            for field, widget in self.search_entries.items():
                if isinstance(widget, ttk.Combobox):
                    value = widget.get()
                else:
                    value = widget.get()
                
                if value and value.strip():
                    search_criteria[field] = value.strip()
            
            # Поиск партнеров
            if hasattr(self.db_manager, 'search_partners_advanced'):
                partners = self.db_manager.search_partners_advanced("", search_criteria)
            else:
                # Fallback к базовому поиску
                partners = self.db_manager.search_partners(self.search_query.get())
            
            # Фильтрация по диапазону продаж
            if search_criteria.get("sales_from") or search_criteria.get("sales_to"):
                filtered_partners = []
                for partner in partners:
                    include = True
                    
                    if search_criteria.get("sales_from"):
                        try:
                            if partner.total_sales < float(search_criteria["sales_from"]):
                                include = False
                        except ValueError:
                            pass
                    
                    if search_criteria.get("sales_to"):
                        try:
                            if partner.total_sales > float(search_criteria["sales_to"]):
                                include = False
                        except ValueError:
                            pass
                    
                    if include:
                        filtered_partners.append(partner)
                
                partners = filtered_partners
            
            # Отображение результатов
            self.display_search_results(partners)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при поиске: {str(e)}")
    
    def display_search_results(self, partners: List[Partner]):
        """Отображение результатов поиска."""
        # Очистка существующих данных
        for item in self.search_results_tree.get_children():
            self.search_results_tree.delete(item)
        
        # Добавление результатов
        for partner in partners:
            self.search_results_tree.insert('', 'end', values=(
                partner.id, partner.name, partner.company, partner.email,
                f"${partner.total_sales:,.2f}", partner.category, partner.status
            ))
        
        # Показ количества результатов
        messagebox.showinfo("Результаты поиска", f"Найдено партнеров: {len(partners)}")
    
    def clear_advanced_search(self):
        """Очистка полей расширенного поиска."""
        for field, widget in self.search_entries.items():
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)
    
    def show_category_manager(self):
        """Показать менеджер категорий."""
        messagebox.showinfo("Информация", "Функция управления категориями будет реализована в следующей версии.")
    
    def show_tasks_manager(self):
        """Показать менеджер задач."""
        tasks_window = tk.Toplevel(self.root)
        tasks_window.title("Управление задачами")
        tasks_window.geometry("800x600")
        
        # Создание интерфейса для задач
        notebook = ttk.Notebook(tasks_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка списка задач
        tasks_frame = ttk.Frame(notebook)
        notebook.add(tasks_frame, text="Список задач")
        
        # Создание Treeview для задач
        columns = ('ID', 'Партнер', 'Заголовок', 'Описание', 'Срок', 'Приоритет', 'Статус', 'Исполнитель')
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tasks_tree.heading(col, text=col)
            self.tasks_tree.column(col, width=100, minwidth=80)
        
        # Скроллбары
        tasks_scroll_y = ttk.Scrollbar(tasks_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=tasks_scroll_y.set)
        
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tasks_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки управления задачами
        button_frame = ttk.Frame(tasks_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Добавить задачу", command=self.add_task).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Редактировать задачу", command=self.edit_task).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Удалить задачу", command=self.delete_task).pack(side=tk.LEFT)
        
        # Загрузка задач
        self.load_tasks()
        
        # Вкладка создания задач
        create_frame = ttk.Frame(notebook)
        notebook.add(create_frame, text="Создать задачу")
        
        # Форма создания задачи
        ttk.Label(create_frame, text="Партнер:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        partner_combo = ttk.Combobox(create_frame, values=[p.name for p in self.db_manager.get_all_partners()], width=30)
        partner_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(create_frame, text="Заголовок:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        title_entry = ttk.Entry(create_frame, width=30)
        title_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(create_frame, text="Описание:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        desc_text = scrolledtext.ScrolledText(create_frame, height=5, width=30)
        desc_text.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(create_frame, text="Срок:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        due_entry = ttk.Entry(create_frame, width=30)
        due_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(create_frame, text="Приоритет:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        priority_combo = ttk.Combobox(create_frame, values=["low", "medium", "high"], width=30)
        priority_combo.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(create_frame, text="Исполнитель:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        assignee_entry = ttk.Entry(create_frame, width=30)
        assignee_entry.grid(row=5, column=1, sticky=tk.W, padx=10, pady=5)
        
        def create_task():
            try:
                # Получение ID партнера по имени
                partner_name = partner_combo.get()
                partners = self.db_manager.get_all_partners()
                partner = next((p for p in partners if p.name == partner_name), None)
                
                if not partner:
                    messagebox.showerror("Ошибка", "Выберите партнера")
                    return
                
                task = Task(
                    id=0,
                    partner_id=partner.id,
                    title=title_entry.get(),
                    description=desc_text.get("1.0", tk.END).strip(),
                    due_date=due_entry.get(),
                    priority=priority_combo.get(),
                    status="pending",
                    assigned_to=assignee_entry.get(),
                    created_date=datetime.now().strftime('%Y-%m-%d')
                )
                
                self.task_manager.add_task(task)
                self.load_tasks()
                messagebox.showinfo("Успех", "Задача создана")
                
                # Очистка полей
                title_entry.delete(0, tk.END)
                desc_text.delete("1.0", tk.END)
                due_entry.delete(0, tk.END)
                priority_combo.set("")
                assignee_entry.delete(0, tk.END)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при создании задачи: {str(e)}")
        
        ttk.Button(create_frame, text="Создать задачу", command=create_task).grid(row=6, column=0, columnspan=2, pady=20)
    
    def load_tasks(self):
        """Загрузка задач в Treeview."""
        # Очистка существующих данных
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Получение всех задач
        partners = self.db_manager.get_all_partners()
        all_tasks = []
        
        for partner in partners:
            tasks = self.task_manager.get_tasks_for_partner(partner.id)
            all_tasks.extend(tasks)
        
        # Добавление в Treeview
        for task in all_tasks:
            partner = next((p for p in partners if p.id == task.partner_id), None)
            partner_name = partner.name if partner else "Неизвестно"
            
            self.tasks_tree.insert('', 'end', values=(
                task.id, partner_name, task.title, task.description[:50] + "..." if len(task.description) > 50 else task.description,
                task.due_date, task.priority, task.status, task.assigned_to
            ))
    
    def add_task(self):
        """Добавление новой задачи."""
        # Переключение на вкладку создания задач
        pass
    
    def edit_task(self):
        """Редактирование выбранной задачи."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу для редактирования.")
            return
        
        # Здесь можно добавить логику редактирования задачи
        messagebox.showinfo("Информация", "Функция редактирования задач будет реализована в следующей версии.")
    
    def delete_task(self):
        """Удаление выбранной задачи."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу для удаления.")
            return
        
        task_id = self.tasks_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Подтверждение", "Удалить эту задачу?"):
            # Здесь можно добавить логику удаления задачи
            messagebox.showinfo("Информация", "Функция удаления задач будет реализована в следующей версии.")
    
    def show_notifications(self):
        """Показать уведомления."""
        notifications_window = tk.Toplevel(self.root)
        notifications_window.title("Уведомления")
        notifications_window.geometry("600x400")
        
        # Создание интерфейса для уведомлений
        ttk.Label(notifications_window, text="Непрочитанные уведомления", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Список уведомлений
        notifications_frame = ttk.Frame(notifications_window)
        notifications_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создание Treeview для уведомлений
        columns = ('Тип', 'Сообщение', 'Дата', 'Партнер')
        self.notifications_tree = ttk.Treeview(notifications_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.notifications_tree.heading(col, text=col)
            self.notifications_tree.column(col, width=120, minwidth=100)
        
        # Скроллбары
        notif_scroll_y = ttk.Scrollbar(notifications_frame, orient=tk.VERTICAL, command=self.notifications_tree.yview)
        self.notifications_tree.configure(yscrollcommand=notif_scroll_y.set)
        
        self.notifications_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notif_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Загрузка уведомлений
        self.load_notifications()
        
        # Кнопки
        button_frame = ttk.Frame(notifications_window)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Отметить как прочитанные", command=self.mark_notifications_read).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Очистить все", command=self.clear_notifications).pack(side=tk.LEFT)
    
    def load_notifications(self):
        """Загрузка уведомлений в Treeview."""
        # Очистка существующих данных
        for item in self.notifications_tree.get_children():
            self.notifications_tree.delete(item)
        
        # Получение непрочитанных уведомлений
        notifications = self.notification_manager.get_unread_notifications()
        partners = self.db_manager.get_all_partners()
        
        # Добавление в Treeview
        for notification in notifications:
            partner = next((p for p in partners if p.id == notification.partner_id), None)
            partner_name = partner.name if partner else "Неизвестно"
            
            self.notifications_tree.insert('', 'end', values=(
                notification.type, notification.message[:50] + "..." if len(notification.message) > 50 else notification.message,
                notification.date, partner_name
            ))
    
    def mark_notifications_read(self):
        """Отметить уведомления как прочитанные."""
        # Здесь можно добавить логику отметки уведомлений как прочитанных
        messagebox.showinfo("Информация", "Функция отметки уведомлений будет реализована в следующей версии.")
    
    def clear_notifications(self):
        """Очистить все уведомления."""
        if messagebox.askyesno("Подтверждение", "Очистить все уведомления?"):
            # Здесь можно добавить логику очистки уведомлений
            messagebox.showinfo("Информация", "Функция очистки уведомлений будет реализована в следующей версии.")
    
    def sort_treeview(self, col):
        """Сортировка Treeview по колонке."""
        # Заглушка для демонстрации
        pass
    
    def start_auto_refresh(self):
        """Запуск автоматического обновления данных."""
        def auto_refresh():
            while True:
                time.sleep(30)  # Обновление каждые 30 секунд
                try:
                    self.root.after(0, self.load_partners)
                except:
                    break
        
        refresh_thread = threading.Thread(target=auto_refresh, daemon=True)
        refresh_thread.start()

class PartnerDialog:
    """Диалог для добавления/редактирования партнера."""
    
    def __init__(self, parent, db_manager, app, partner=None):
        self.parent = parent
        self.db_manager = db_manager
        self.app = app
        self.partner = partner
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить партнера" if not partner else "Редактировать партнера")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        if partner:
            self.load_partner_data()
    
    def create_widgets(self):
        """Создание виджетов диалога."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Поля ввода
        fields = [
            ("Имя:", "name"),
            ("Email:", "email"),
            ("Телефон:", "phone"),
            ("Компания:", "company"),
            ("Продажи:", "total_sales"),
            ("Комиссия (%):", "commission_rate"),
            ("Дата присоединения:", "join_date"),
            ("Статус:", "status"),
            ("Категория:", "category"),
            ("Регион:", "region"),
            ("Последний контакт:", "last_contact")
        ]
        
        self.entries = {}
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if field == "status":
                combo = ttk.Combobox(main_frame, values=["active", "inactive", "pending"])
                combo.grid(row=i, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
                self.entries[field] = combo
            elif field == "category":
                combo = ttk.Combobox(main_frame, values=["general", "premium", "vip", "new"])
                combo.grid(row=i, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
                self.entries[field] = combo
            elif field in ["total_sales", "commission_rate"]:
                entry = ttk.Entry(main_frame)
                entry.grid(row=i, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
                self.entries[field] = entry
            else:
                entry = ttk.Entry(main_frame)
                entry.grid(row=i, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
                self.entries[field] = entry
        
        # Поле заметок
        ttk.Label(main_frame, text="Заметки:").grid(row=len(fields), column=0, sticky=tk.W, pady=5)
        notes_text = scrolledtext.ScrolledText(main_frame, height=5, width=40)
        notes_text.grid(row=len(fields), column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        self.entries["notes"] = notes_text
        
        # Дополнительные поля
        ttk.Label(main_frame, text="Приоритет:").grid(row=len(fields)+1, column=0, sticky=tk.W, pady=5)
        priority_combo = ttk.Combobox(main_frame, values=["low", "medium", "high"], width=20)
        priority_combo.grid(row=len(fields)+1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.entries["priority"] = priority_combo
        
        ttk.Label(main_frame, text="Теги:").grid(row=len(fields)+2, column=0, sticky=tk.W, pady=5)
        tags_entry = ttk.Entry(main_frame, width=40)
        tags_entry.grid(row=len(fields)+2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.entries["tags"] = tags_entry
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields)+3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save_partner).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # Настройка расширения колонок
        main_frame.columnconfigure(1, weight=1)
    
    def load_partner_data(self):
        """Загрузка данных партнера в поля."""
        if not self.partner:
            return
        
        self.entries["name"].insert(0, self.partner.name)
        self.entries["email"].insert(0, self.partner.email or "")
        self.entries["phone"].insert(0, self.partner.phone or "")
        self.entries["company"].insert(0, self.partner.company or "")
        self.entries["total_sales"].insert(0, str(self.partner.total_sales))
        self.entries["commission_rate"].insert(0, str(self.partner.commission_rate * 100))
        self.entries["join_date"].insert(0, self.partner.join_date or "")
        self.entries["status"].set(self.partner.status)
        self.entries["category"].set(self.partner.category)
        self.entries["region"].insert(0, self.partner.region or "")
        self.entries["last_contact"].insert(0, self.partner.last_contact or "")
        self.entries["notes"].insert("1.0", self.partner.notes or "")
        self.entries["priority"].set(self.partner.priority)
        self.entries["tags"].insert(0, self.partner.tags or "")
    
    def save_partner(self):
        """Сохранение партнера."""
        try:
            # Получение данных из полей
            data = {}
            for field, widget in self.entries.items():
                if isinstance(widget, scrolledtext.ScrolledText):
                    data[field] = widget.get("1.0", tk.END).strip()
                elif isinstance(widget, ttk.Combobox):
                    data[field] = widget.get()
                else:
                    data[field] = widget.get()
            
            # Валидация
            if not data["name"]:
                messagebox.showerror("Ошибка", "Имя партнера обязательно")
                return
            
            try:
                data["total_sales"] = float(data["total_sales"])
                data["commission_rate"] = float(data["commission_rate"]) / 100
            except ValueError:
                messagebox.showerror("Ошибка", "Продажи и комиссия должны быть числами")
                return
            
            # Создание или обновление партнера
            if self.partner:
                # Обновление существующего
                self.partner.name = data["name"]
                self.partner.email = data["email"]
                self.partner.phone = data["phone"]
                self.partner.company = data["company"]
                self.partner.total_sales = data["total_sales"]
                self.partner.commission_rate = data["commission_rate"]
                self.partner.join_date = data["join_date"]
                self.partner.status = data["status"]
                self.partner.notes = data["notes"]
                self.partner.category = data["category"]
                self.partner.region = data["region"]
                self.partner.last_contact = data["last_contact"]
                self.partner.priority = data.get("priority", "medium")
                self.partner.tags = data.get("tags", "")
                
                self.db_manager.update_partner(self.partner)
                messagebox.showinfo("Успех", "Партнер обновлен")
            else:
                # Создание нового
                new_partner = Partner(
                    id=0,
                    name=data["name"],
                    email=data["email"],
                    phone=data["phone"],
                    company=data["company"],
                    total_sales=data["total_sales"],
                    commission_rate=data["commission_rate"],
                    join_date=data["join_date"] or datetime.now().strftime('%Y-%m-%d'),
                    status=data["status"] or "active",
                    notes=data["notes"],
                    category=data["category"] or "general",
                    region=data["region"],
                    last_contact=data["last_contact"] or datetime.now().strftime('%Y-%m-%d'),
                    priority=data.get("priority", "medium"),
                    tags=data.get("tags", "")
                )
                
                partner_id = self.db_manager.add_partner(new_partner)
                new_partner.id = partner_id
                
                # Отправка приветственного email
                if new_partner.email:
                    try:
                        if self.email_manager.send_partner_welcome(new_partner):
                            messagebox.showinfo("Успех", "Партнер добавлен и приветственное письмо отправлено")
                        else:
                            messagebox.showinfo("Успех", "Партнер добавлен, но не удалось отправить email")
                    except Exception as e:
                        messagebox.showinfo("Успех", f"Партнер добавлен, ошибка отправки email: {str(e)}")
                else:
                    messagebox.showinfo("Успех", "Партнер добавлен")
            
            # Обновление основного списка
            self.app.load_partners()
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")

def main():
    """Главная функция приложения."""
    try:
        root = tk.Tk()
        app = AdvancedPartnerApp(root)
        
        # Центрирование окна
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        root.mainloop()
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")

if __name__ == "__main__":
    main()