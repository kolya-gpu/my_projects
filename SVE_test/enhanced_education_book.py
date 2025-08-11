import json
import os
import hashlib
import datetime
import random
import sqlite3
from typing import Dict, List, Optional, Tuple
import time

class User:
    def __init__(self, username: str, password_hash: str, user_id: int = None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.created_at = datetime.datetime.now()
        self.last_login = None
        self.is_admin = False

class ProgressTracker:
    def __init__(self, db_path: str = "education_progress.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                section TEXT NOT NULL,
                topic TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                completion_date TIMESTAMP,
                time_spent INTEGER DEFAULT 0,
                test_score INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                section TEXT NOT NULL,
                topic TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Bookmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                section TEXT NOT NULL,
                topic TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> bool:
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                (username, password_hash, is_admin)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, password_hash, is_admin FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user = User(result[1], result[2], result[0])
            user.is_admin = result[3]
            return user
        return None
    
    def update_last_login(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
    
    def mark_topic_completed(self, user_id: int, section: str, topic: str, time_spent: int = 0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if progress exists
        cursor.execute(
            'SELECT id FROM progress WHERE user_id = ? AND section = ? AND topic = ?',
            (user_id, section, topic)
        )
        
        if cursor.fetchone():
            cursor.execute('''
                UPDATE progress 
                SET completed = TRUE, completion_date = CURRENT_TIMESTAMP, time_spent = time_spent
                WHERE user_id = ? AND section = ? AND topic = ?
            ''', (user_id, section, topic))
        else:
            cursor.execute('''
                INSERT INTO progress (user_id, section, topic, completed, completion_date, time_spent)
                VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP, ?)
            ''', (user_id, section, topic, time_spent))
        
        conn.commit()
        conn.close()
    
    def save_test_result(self, user_id: int, section: str, topic: str, score: int, total_questions: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO test_results (user_id, section, topic, score, total_questions)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, section, topic, score, total_questions))
        conn.commit()
        conn.close()
    
    def get_user_progress(self, user_id: int) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT section, topic, completed, completion_date, time_spent, test_score
            FROM progress WHERE user_id = ?
        ''', (user_id,))
        results = cursor.fetchall()
        conn.close()
        
        progress = {}
        for row in results:
            section, topic, completed, completion_date, time_spent, test_score = row
            if section not in progress:
                progress[section] = {}
            progress[section][topic] = {
                'completed': completed,
                'completion_date': completion_date,
                'time_spent': time_spent,
                'test_score': test_score
            }
        return progress
    
    def add_bookmark(self, user_id: int, section: str, topic: str, note: str = ""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookmarks (user_id, section, topic, note)
            VALUES (?, ?, ?, ?)
        ''', (user_id, section, topic, note))
        conn.commit()
        conn.close()
    
    def get_bookmarks(self, user_id: int) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT section, topic, note, created_at FROM bookmarks WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        results = cursor.fetchall()
        conn.close()
        return results

class AdvancedTestSystem:
    def __init__(self, content_data: Dict):
        self.content_data = content_data
        self.question_templates = {
            'definition': 'Что такое {term}?',
            'example': 'Приведите пример {concept}',
            'comparison': 'В чем разница между {term1} и {term2}?',
            'application': 'Где применяется {concept}?',
            'true_false': 'Верно ли утверждение: {statement}'
        }
    
    def generate_questions(self, section: str, topic: str, num_questions: int = 5) -> List[Dict]:
        """Generate dynamic questions based on content"""
        content = self.content_data[section][topic]
        questions = []
        
        # Extract key terms and concepts from content
        terms = self.extract_key_terms(content)
        
        for i in range(min(num_questions, len(terms))):
            if i < len(terms):
                term = terms[i]
                question_type = random.choice(list(self.question_templates.keys()))
                
                if question_type == 'definition':
                    question = self.question_templates[question_type].format(term=term)
                    options = self.generate_definition_options(term, content)
                elif question_type == 'true_false':
                    question = self.question_templates[question_type].format(statement=f"{term} является важным понятием")
                    options = ['Верно', 'Неверно']
                else:
                    question = self.question_templates[question_type].format(concept=term)
                    options = self.generate_general_options(term, content)
                
                questions.append({
                    'question': question,
                    'options': options,
                    'correct_answer': 1,  # Simplified for now
                    'explanation': f"Правильный ответ связан с понятием '{term}'"
                })
        
        return questions
    
    def extract_key_terms(self, content: str) -> List[str]:
        """Extract key terms from content (simplified)"""
        # This is a simplified version - in a real app you'd use NLP
        words = content.split()
        # Filter for potential key terms (words starting with capital letters, longer words)
        terms = [word for word in words if len(word) > 4 and word[0].isupper()]
        return terms[:10]  # Return up to 10 terms
    
    def generate_definition_options(self, term: str, content: str) -> List[str]:
        """Generate multiple choice options for definition questions"""
        options = [
            f"Понятие, связанное с {term.lower()}",
            f"Определение {term.lower()}",
            f"Пример {term.lower()}",
            f"Применение {term.lower()}"
        ]
        random.shuffle(options)
        return options
    
    def generate_general_options(self, term: str, content: str) -> List[str]:
        """Generate general multiple choice options"""
        options = [
            f"Вариант A для {term}",
            f"Вариант B для {term}",
            f"Вариант C для {term}",
            f"Вариант D для {term}"
        ]
        random.shuffle(options)
        return options

class ContentManager:
    def __init__(self, content_data: Dict):
        self.content_data = content_data
        self.backup_file = "content_backup.json"
    
    def backup_content(self):
        """Create a backup of current content"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.backup_file.replace('.json', '')}_{timestamp}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(self.content_data, f, ensure_ascii=False, indent=2)
        
        return backup_filename
    
    def add_section(self, section_name: str, description: str = ""):
        """Add a new section"""
        if section_name not in self.content_data:
            self.content_data[section_name] = {
                "Описание": description,
                "Введение": "Содержимое введения..."
            }
            return True
        return False
    
    def add_topic(self, section_name: str, topic_name: str, content: str):
        """Add a new topic to a section"""
        if section_name in self.content_data:
            self.content_data[section_name][topic_name] = content
            return True
        return False
    
    def edit_topic(self, section_name: str, topic_name: str, new_content: str):
        """Edit existing topic content"""
        if section_name in self.content_data and topic_name in self.content_data[section_name]:
            self.content_data[section_name][topic_name] = new_content
            return True
        return False
    
    def delete_topic(self, section_name: str, topic_name: str):
        """Delete a topic"""
        if section_name in self.content_data and topic_name in self.content_data[section_name]:
            del self.content_data[section_name][topic_name]
            return True
        return False
    
    def save_content(self, filename: str = "content.json"):
        """Save content to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.content_data, f, ensure_ascii=False, indent=2)

class EnhancedEducationalBook:
    def __init__(self, content_file: str = "content.json"):
        self.content_file = content_file
        self.load_content()
        self.progress_tracker = ProgressTracker()
        self.test_system = AdvancedTestSystem(self.content_data)
        self.content_manager = ContentManager(self.content_data)
        self.current_user = None
        self.session_start_time = None
        
    def load_content(self):
        """Load content from file"""
        try:
            with open(self.content_file, 'r', encoding='utf-8') as f:
                self.content_data = json.load(f)
        except FileNotFoundError:
            print(f"Файл {self.content_file} не найден. Создаю базовое содержимое.")
            self.content_data = {
                "Программирование": {
                    "Введение в программирование": "Программирование - это процесс создания компьютерных программ...",
                    "Переменные и типы данных": "Переменные - это контейнеры для хранения данных...",
                    "Условия и циклы": "Условия позволяют программе принимать решения..."
                },
                "Математика": {
                    "Алгебра": "Алгебра - раздел математики, изучающий алгебраические структуры...",
                    "Геометрия": "Геометрия - раздел математики, изучающий пространственные отношения..."
                }
            }
            self.save_content()
    
    def save_content(self):
        """Save content to file"""
        self.content_manager.save_content(self.content_file)
    
    def login_menu(self):
        """Main login and registration menu"""
        while True:
            print("\n" + "="*50)
            print("🎓 ЭЛЕКТРОННЫЙ УЧЕБНИК - СИСТЕМА ВХОДА")
            print("="*50)
            print("1. Войти в систему")
            print("2. Зарегистрироваться")
            print("3. Войти как гость")
            print("0. Выход")
            
            choice = input("\nВыберите действие: ")
            
            if choice == '1':
                if self.login():
                    self.main_menu()
            elif choice == '2':
                self.register()
            elif choice == '3':
                self.current_user = User("Гость", "", 0)
                self.main_menu()
            elif choice == '0':
                print("До свидания!")
                break
            else:
                print("Некорректный выбор. Попробуйте снова.")
    
    def login(self) -> bool:
        """User login process"""
        print("\n--- ВХОД В СИСТЕМУ ---")
        username = input("Имя пользователя: ")
        password = input("Пароль: ")
        
        user = self.progress_tracker.authenticate_user(username, password)
        if user:
            self.current_user = user
            self.progress_tracker.update_last_login(user.user_id)
            self.session_start_time = time.time()
            print(f"Добро пожаловать, {username}!")
            return True
        else:
            print("Неверное имя пользователя или пароль.")
            return False
    
    def register(self):
        """User registration process"""
        print("\n--- РЕГИСТРАЦИЯ ---")
        username = input("Имя пользователя: ")
        password = input("Пароль: ")
        confirm_password = input("Подтвердите пароль: ")
        
        if password != confirm_password:
            print("Пароли не совпадают.")
            return
        
        if len(password) < 6:
            print("Пароль должен содержать минимум 6 символов.")
            return
        
        if self.progress_tracker.create_user(username, password):
            print("Регистрация успешна! Теперь вы можете войти в систему.")
        else:
            print("Пользователь с таким именем уже существует.")
    
    def main_menu(self):
        """Enhanced main menu with user-specific features"""
        while True:
            print("\n" + "="*50)
            print(f"🎓 ЭЛЕКТРОННЫЙ УЧЕБНИК - {self.current_user.username.upper()}")
            print("="*50)
            
            # Show user progress summary
            if self.current_user.user_id != 0:
                self.show_progress_summary()
            
            print("\nДоступные разделы:")
            for idx, section in enumerate(self.content_data.keys(), 1):
                print(f"{idx}. {section}")
            
            print("\nДополнительные функции:")
            print("s. Поиск по содержимому")
            print("p. Мой прогресс")
            print("b. Закладки")
            print("t. Тесты")
            
            if self.current_user.is_admin:
                print("a. Администрирование")
            
            print("0. Выход")
            
            choice = input("\nВыберите действие: ")
            
            if choice == '0':
                if self.current_user.user_id != 0:
                    self.logout()
                break
            elif choice == 's':
                self.search_content()
            elif choice == 'p':
                self.show_detailed_progress()
            elif choice == 'b':
                self.bookmarks_menu()
            elif choice == 't':
                self.tests_menu()
            elif choice == 'a' and self.current_user.is_admin:
                self.admin_menu()
            elif choice.isdigit() and 1 <= int(choice) <= len(self.content_data):
                section_name = list(self.content_data.keys())[int(choice)-1]
                self.show_section(section_name)
            else:
                print("Некорректный ввод. Попробуйте снова.")
    
    def show_progress_summary(self):
        """Show brief progress summary"""
        progress = self.progress_tracker.get_user_progress(self.current_user.user_id)
        total_topics = sum(len(section) for section in self.content_data.values())
        completed_topics = sum(1 for section in progress.values() for topic in section.values() if topic['completed'])
        
        completion_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        print(f"📊 Прогресс: {completed_topics}/{total_topics} тем ({completion_percentage:.1f}%)")
    
    def show_detailed_progress(self):
        """Show detailed user progress"""
        if self.current_user.user_id == 0:
            print("Гости не могут отслеживать прогресс.")
            return
        
        progress = self.progress_tracker.get_user_progress(self.current_user.user_id)
        
        print("\n" + "="*50)
        print("📊 ДЕТАЛЬНЫЙ ПРОГРЕСС")
        print("="*50)
        
        for section_name, section_data in self.content_data.items():
            print(f"\n📚 {section_name}:")
            section_progress = progress.get(section_name, {})
            
            for topic_name in section_data.keys():
                topic_progress = section_progress.get(topic_name, {})
                if topic_progress.get('completed'):
                    print(f"  ✅ {topic_name} - Завершено")
                    if topic_progress.get('test_score'):
                        print(f"      Тест: {topic_progress['test_score']}%")
                else:
                    print(f"  ⏳ {topic_name} - Не завершено")
        
        input("\nНажмите Enter для возврата...")
    
    def bookmarks_menu(self):
        """Bookmarks management menu"""
        if self.current_user.user_id == 0:
            print("Гости не могут использовать закладки.")
            return
        
        while True:
            print("\n" + "="*40)
            print("🔖 ЗАКЛАДКИ")
            print("="*40)
            print("1. Просмотреть закладки")
            print("2. Добавить закладку")
            print("3. Удалить закладку")
            print("0. Назад")
            
            choice = input("\nВыберите действие: ")
            
            if choice == '1':
                self.show_bookmarks()
            elif choice == '2':
                self.add_bookmark()
            elif choice == '3':
                self.delete_bookmark()
            elif choice == '0':
                break
            else:
                print("Некорректный выбор.")
    
    def show_bookmarks(self):
        """Display user bookmarks"""
        bookmarks = self.progress_tracker.get_bookmarks(self.current_user.user_id)
        
        if not bookmarks:
            print("У вас пока нет закладок.")
            return
        
        print("\nВаши закладки:")
        for idx, (section, topic, note, created_at) in enumerate(bookmarks, 1):
            print(f"{idx}. {section} → {topic}")
            if note:
                print(f"   Заметка: {note}")
            print(f"   Создано: {created_at}")
        
        input("\nНажмите Enter для возврата...")
    
    def add_bookmark(self):
        """Add a new bookmark"""
        print("\nДобавление закладки:")
        print("Доступные разделы:")
        
        sections = list(self.content_data.keys())
        for idx, section in enumerate(sections, 1):
            print(f"{idx}. {section}")
        
        try:
            section_idx = int(input("Выберите раздел: ")) - 1
            if 0 <= section_idx < len(sections):
                section_name = sections[section_idx]
                
                topics = list(self.content_data[section_name].keys())
                print(f"\nТемы в разделе '{section_name}':")
                for idx, topic in enumerate(topics, 1):
                    print(f"{idx}. {topic}")
                
                topic_idx = int(input("Выберите тему: ")) - 1
                if 0 <= topic_idx < len(topics):
                    topic_name = topics[topic_idx]
                    note = input("Добавить заметку (необязательно): ")
                    
                    self.progress_tracker.add_bookmark(
                        self.current_user.user_id, section_name, topic_name, note
                    )
                    print("Закладка добавлена!")
                else:
                    print("Некорректный номер темы.")
            else:
                print("Некорректный номер раздела.")
        except ValueError:
            print("Введите корректный номер.")
        
        input("\nНажмите Enter для продолжения...")
    
    def delete_bookmark(self):
        """Delete a bookmark"""
        bookmarks = self.progress_tracker.get_bookmarks(self.current_user.user_id)
        
        if not bookmarks:
            print("У вас нет закладок для удаления.")
            return
        
        print("\nВыберите закладку для удаления:")
        for idx, (section, topic, note, created_at) in enumerate(bookmarks, 1):
            print(f"{idx}. {section} → {topic}")
        
        try:
            choice = int(input("Введите номер закладки: ")) - 1
            if 0 <= choice < len(bookmarks):
                # Note: This would require adding a delete method to ProgressTracker
                print("Функция удаления закладок будет добавлена в следующей версии.")
            else:
                print("Некорректный номер.")
        except ValueError:
            print("Введите корректный номер.")
        
        input("\nНажмите Enter для продолжения...")
    
    def tests_menu(self):
        """Tests management menu"""
        while True:
            print("\n" + "="*40)
            print("📝 ТЕСТЫ")
            print("="*40)
            print("1. Пройти тест по разделу")
            print("2. Пройти тест по теме")
            print("3. Мои результаты тестов")
            print("0. Назад")
            
            choice = input("\nВыберите действие: ")
            
            if choice == '1':
                self.take_section_test()
            elif choice == '2':
                self.take_topic_test()
            elif choice == '3':
                self.show_test_results()
            elif choice == '0':
                break
            else:
                print("Некорректный выбор.")
    
    def take_section_test(self):
        """Take a test covering an entire section"""
        print("\nВыберите раздел для тестирования:")
        sections = list(self.content_data.keys())
        for idx, section in enumerate(sections, 1):
            print(f"{idx}. {section}")
        
        try:
            choice = int(input("Введите номер раздела: ")) - 1
            if 0 <= choice < len(sections):
                section_name = sections[choice]
                self.run_section_test(section_name)
            else:
                print("Некорректный номер раздела.")
        except ValueError:
            print("Введите корректный номер.")
    
    def take_topic_test(self):
        """Take a test on a specific topic"""
        print("\nВыберите раздел:")
        sections = list(self.content_data.keys())
        for idx, section in enumerate(sections, 1):
            print(f"{idx}. {section}")
        
        try:
            section_idx = int(input("Введите номер раздела: ")) - 1
            if 0 <= section_idx < len(sections):
                section_name = sections[section_idx]
                
                topics = list(self.content_data[section_name].keys())
                print(f"\nТемы в разделе '{section_name}':")
                for idx, topic in enumerate(topics, 1):
                    print(f"{idx}. {topic}")
                
                topic_idx = int(input("Введите номер темы: ")) - 1
                if 0 <= topic_idx < len(topics):
                    topic_name = topics[topic_idx]
                    self.run_topic_test(section_name, topic_name)
                else:
                    print("Некорректный номер темы.")
            else:
                print("Некорректный номер раздела.")
        except ValueError:
            print("Введите корректный номер.")
    
    def run_section_test(self, section_name: str):
        """Run a test for an entire section"""
        print(f"\n📝 ТЕСТ ПО РАЗДЕЛУ: {section_name}")
        print("="*50)
        
        all_questions = []
        for topic_name in self.content_data[section_name].keys():
            topic_questions = self.test_system.generate_questions(section_name, topic_name, 3)
            all_questions.extend(topic_questions)
        
        if not all_questions:
            print("Не удалось сгенерировать вопросы для теста.")
            return
        
        self.run_test(all_questions, section_name, "Общий раздел")
    
    def run_topic_test(self, section_name: str, topic_name: str):
        """Run a test for a specific topic"""
        print(f"\n📝 ТЕСТ ПО ТЕМЕ: {topic_name}")
        print("="*50)
        
        questions = self.test_system.generate_questions(section_name, topic_name, 5)
        
        if not questions:
            print("Не удалось сгенерировать вопросы для теста.")
            return
        
        self.run_test(questions, section_name, topic_name)
    
    def run_test(self, questions: List[Dict], section_name: str, topic_name: str):
        """Execute a test with given questions"""
        score = 0
        total_questions = len(questions)
        
        print(f"Тест содержит {total_questions} вопросов.")
        print("Нажмите Enter для начала теста...")
        input()
        
        for i, question in enumerate(questions, 1):
            print(f"\n--- Вопрос {i}/{total_questions} ---")
            print(question['question'])
            
            for idx, option in enumerate(question['options'], 1):
                print(f"{idx}. {option}")
            
            while True:
                try:
                    answer = int(input("Ваш ответ (номер): "))
                    if 1 <= answer <= len(question['options']):
                        break
                    else:
                        print(f"Введите число от 1 до {len(question['options'])}")
                except ValueError:
                    print("Введите корректный номер.")
            
            if answer == question['correct_answer']:
                print("✅ Правильно!")
                score += 1
            else:
                print(f"❌ Неправильно!")
                print(f"Объяснение: {question['explanation']}")
            
            if i < total_questions:
                print("Нажмите Enter для следующего вопроса...")
                input()
        
        percentage = (score / total_questions) * 100
        print(f"\n🎯 РЕЗУЛЬТАТ ТЕСТА")
        print(f"Правильных ответов: {score}/{total_questions}")
        print(f"Процент: {percentage:.1f}%")
        
        if percentage >= 80:
            print("🎉 Отличный результат!")
        elif percentage >= 60:
            print("👍 Хороший результат!")
        else:
            print("📚 Есть над чем поработать!")
        
        # Save test result if user is logged in
        if self.current_user.user_id != 0:
            self.progress_tracker.save_test_result(
                self.current_user.user_id, section_name, topic_name, int(percentage), total_questions
            )
        
        input("\nНажмите Enter для продолжения...")
    
    def show_test_results(self):
        """Display user's test results"""
        if self.current_user.user_id == 0:
            print("Гости не могут просматривать результаты тестов.")
            return
        
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТОВ")
        print("="*50)
        
        # This would require adding a method to get test results from ProgressTracker
        print("Функция просмотра результатов тестов будет добавлена в следующей версии.")
        
        input("\nНажмите Enter для возврата...")
    
    def admin_menu(self):
        """Administrative functions menu"""
        while True:
            print("\n" + "="*40)
            print("⚙️ АДМИНИСТРИРОВАНИЕ")
            print("="*40)
            print("1. Добавить раздел")
            print("2. Добавить тему")
            print("3. Редактировать тему")
            print("4. Удалить тему")
            print("5. Создать резервную копию")
            print("6. Статистика пользователей")
            print("0. Назад")
            
            choice = input("\nВыберите действие: ")
            
            if choice == '1':
                self.admin_add_section()
            elif choice == '2':
                self.admin_add_topic()
            elif choice == '3':
                self.admin_edit_topic()
            elif choice == '4':
                self.admin_delete_topic()
            elif choice == '5':
                self.admin_backup_content()
            elif choice == '6':
                self.admin_user_stats()
            elif choice == '0':
                break
            else:
                print("Некорректный выбор.")
    
    def admin_add_section(self):
        """Add a new section (admin only)"""
        print("\n--- ДОБАВЛЕНИЕ РАЗДЕЛА ---")
        section_name = input("Название раздела: ")
        description = input("Описание раздела: ")
        
        if self.content_manager.add_section(section_name, description):
            self.save_content()
            print(f"Раздел '{section_name}' успешно добавлен!")
        else:
            print(f"Раздел '{section_name}' уже существует.")
        
        input("\nНажмите Enter для продолжения...")
    
    def admin_add_topic(self):
        """Add a new topic (admin only)"""
        print("\n--- ДОБАВЛЕНИЕ ТЕМЫ ---")
        
        print("Доступные разделы:")
        sections = list(self.content_data.keys())
        for idx, section in enumerate(sections, 1):
            print(f"{idx}. {section}")
        
        try:
            section_idx = int(input("Выберите раздел: ")) - 1
            if 0 <= section_idx < len(sections):
                section_name = sections[section_idx]
                topic_name = input("Название темы: ")
                content = input("Содержимое темы: ")
                
                if self.content_manager.add_topic(section_name, topic_name, content):
                    self.save_content()
                    print(f"Тема '{topic_name}' успешно добавлена!")
                else:
                    print("Ошибка при добавлении темы.")
            else:
                print("Некорректный номер раздела.")
        except ValueError:
            print("Введите корректный номер.")
        
        input("\nНажмите Enter для продолжения...")
    
    def admin_edit_topic(self):
        """Edit existing topic (admin only)"""
        print("\n--- РЕДАКТИРОВАНИЕ ТЕМЫ ---")
        
        print("Доступные разделы:")
        sections = list(self.content_data.keys())
        for idx, section in enumerate(sections, 1):
            print(f"{idx}. {section}")
        
        try:
            section_idx = int(input("Выберите раздел: ")) - 1
            if 0 <= section_idx < len(sections):
                section_name = sections[section_idx]
                
                topics = list(self.content_data[section_name].keys())
                print(f"\nТемы в разделе '{section_name}':")
                for idx, topic in enumerate(topics, 1):
                    print(f"{idx}. {topic}")
                
                topic_idx = int(input("Выберите тему для редактирования: ")) - 1
                if 0 <= topic_idx < len(topics):
                    topic_name = topics[topic_idx]
                    print(f"\nТекущее содержимое темы '{topic_name}':")
                    print(self.content_data[section_name][topic_name])
                    
                    new_content = input("\nВведите новое содержимое: ")
                    if self.content_manager.edit_topic(section_name, topic_name, new_content):
                        self.save_content()
                        print("Тема успешно отредактирована!")
                    else:
                        print("Ошибка при редактировании темы.")
                else:
                    print("Некорректный номер темы.")
            else:
                print("Некорректный номер раздела.")
        except ValueError:
            print("Введите корректный номер.")
        
        input("\nНажмите Enter для продолжения...")
    
    def admin_delete_topic(self):
        """Delete a topic (admin only)"""
        print("\n--- УДАЛЕНИЕ ТЕМЫ ---")
        
        print("Доступные разделы:")
        sections = list(self.content_data.keys())
        for idx, section in enumerate(sections, 1):
            print(f"{idx}. {section}")
        
        try:
            section_idx = int(input("Выберите раздел: ")) - 1
            if 0 <= section_idx < len(sections):
                section_name = sections[section_idx]
                
                topics = list(self.content_data[section_name].keys())
                print(f"\nТемы в разделе '{section_name}':")
                for idx, topic in enumerate(topics, 1):
                    print(f"{idx}. {topic}")
                
                topic_idx = int(input("Выберите тему для удаления: ")) - 1
                if 0 <= topic_idx < len(topics):
                    topic_name = topics[topic_idx]
                    confirm = input(f"Вы уверены, что хотите удалить тему '{topic_name}'? (y/n): ")
                    
                    if confirm.lower() == 'y':
                        if self.content_manager.delete_topic(section_name, topic_name):
                            self.save_content()
                            print("Тема успешно удалена!")
                        else:
                            print("Ошибка при удалении темы.")
                else:
                    print("Некорректный номер темы.")
            else:
                print("Некорректный номер раздела.")
        except ValueError:
            print("Введите корректный номер.")
        
        input("\nНажмите Enter для продолжения...")
    
    def admin_backup_content(self):
        """Create a backup of content (admin only)"""
        print("\n--- СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ ---")
        
        backup_file = self.content_manager.backup_content()
        print(f"Резервная копия создана: {backup_file}")
        
        input("\nНажмите Enter для продолжения...")
    
    def admin_user_stats(self):
        """Show user statistics (admin only)"""
        print("\n--- СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ ---")
        print("Функция статистики будет добавлена в следующей версии.")
        
        input("\nНажмите Enter для возврата...")
    
    def logout(self):
        """Logout current user"""
        if self.current_user and self.current_user.user_id != 0:
            session_time = time.time() - self.session_start_time if self.session_start_time else 0
            print(f"Время сессии: {session_time:.0f} секунд")
            print(f"До свидания, {self.current_user.username}!")
            self.current_user = None
            self.session_start_time = None
    
    def show_section(self, section_name: str):
        """Show section content with enhanced features"""
        section = self.content_data[section_name]
        while True:
            print(f"\n=== {section_name} ===")
            topics = list(section.keys())
            
            # Show completion status for logged-in users
            if self.current_user.user_id != 0:
                progress = self.progress_tracker.get_user_progress(self.current_user.user_id)
                section_progress = progress.get(section_name, {})
                
                for idx, topic in enumerate(topics, 1):
                    topic_progress = section_progress.get(topic, {})
                    status = "✅" if topic_progress.get('completed') else "⏳"
                    print(f"{idx}. {status} {topic}")
            else:
                for idx, topic in enumerate(topics, 1):
                    print(f"{idx}. {topic}")
            
            print("s. Поиск по содержимому")
            print("t. Пройти тест по разделу")
            print("0. Назад")
            
            choice = input("Выберите тему по номеру или команду: ")
            
            if choice == '0':
                return
            elif choice.lower() == 's':
                self.search_content()
            elif choice.lower() == 't':
                self.run_section_test(section_name)
            elif choice.isdigit() and 1 <= int(choice) <= len(topics):
                topic_name = topics[int(choice)-1]
                self.show_topic(section_name, topic_name)
            else:
                print("Некорректный ввод. Попробуйте снова.")
    
    def show_topic(self, section_name: str, topic_name: str):
        """Show topic content with enhanced features"""
        content = self.content_data[section_name][topic_name]
        start_time = time.time()
        
        print(f"\n--- {topic_name} ---")
        print("="*50)
        print(content)
        print("="*50)
        
        # Mark as completed for logged-in users
        if self.current_user.user_id != 0:
            time_spent = int(time.time() - start_time)
            self.progress_tracker.mark_topic_completed(
                self.current_user.user_id, section_name, topic_name, time_spent
            )
        
        self.post_topic_menu(section_name, topic_name)
    
    def post_topic_menu(self, section_name: str, topic_name: str):
        """Enhanced post-topic menu"""
        while True:
            print(f"\nДополнительные действия для '{topic_name}':")
            print("1. Пройти тест по теме")
            print("2. Добавить в закладки")
            print("3. Поделиться темой")
            print("0. Вернуться к списку тем")
            
            choice = input("Выберите действие: ")
            
            if choice == '1':
                self.run_topic_test(section_name, topic_name)
            elif choice == '2':
                if self.current_user.user_id != 0:
                    note = input("Добавить заметку к закладке: ")
                    self.progress_tracker.add_bookmark(
                        self.current_user.user_id, section_name, topic_name, note
                    )
                    print("Тема добавлена в закладки!")
                else:
                    print("Гости не могут использовать закладки.")
            elif choice == '3':
                print(f"Ссылка на тему: {section_name} → {topic_name}")
                print("Функция шаринга будет добавлена в следующей версии.")
            elif choice == '0':
                return
            else:
                print("Некорректный ввод.")
    
    def search_content(self):
        """Enhanced search functionality"""
        query = input("\nВведите слово или фразу для поиска: ").lower()
        results = []
        
        for section, topics in self.content_data.items():
            for topic_title, text in topics.items():
                if query in text.lower():
                    results.append((section, topic_title, text))
        
        if results:
            print(f"\nРезультаты поиска по '{query}':")
            print(f"Найдено: {len(results)} результатов")
            
            for idx, (sec, top, text) in enumerate(results, 1):
                # Show context around the search term
                context_start = max(0, text.lower().find(query) - 50)
                context_end = min(len(text), text.lower().find(query) + len(query) + 50)
                context = text[context_start:context_end]
                
                print(f"\n{idx}. Раздел: {sec} | Тема: {top}")
                print(f"   Контекст: ...{context}...")
            
            choice = input("\nВведите номер результата для просмотра или Enter для возврата: ")
            if choice.isdigit() and 1 <= int(choice) <= len(results):
                sec_idx = int(choice)-1
                section_name, topic_name, _ = results[sec_idx]
                self.show_topic(section_name, topic_name)
        else:
            print("Ничего не найдено.")
            print("Попробуйте:")
            print("- Использовать другие ключевые слова")
            print("- Проверить правильность написания")
            print("- Использовать более общие термины")
        
        input("\nНажмите Enter для возврата...")

if __name__ == "__main__":
    # Create default admin user if database is empty
    book = EnhancedEducationalBook()
    
    # Check if admin user exists, if not create one
    if not os.path.exists("education_progress.db"):
        book.progress_tracker.create_user("admin", "admin123", True)
        print("Создан пользователь по умолчанию:")
        print("Логин: admin")
        print("Пароль: admin123")
        print("(Рекомендуется сменить пароль после первого входа)")
    
    book.login_menu()
