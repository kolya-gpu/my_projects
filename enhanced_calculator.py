import math
import json
import datetime
import os
from typing import Dict, List, Tuple, Optional, Union
import statistics
import random

class AdvancedCalculator:
    """Advanced calculator with scientific functions, history, and unit conversions"""
    
    def __init__(self):
        self.history = []
        self.memory = 0
        self.angle_mode = "degrees"  # degrees or radians
        self.history_file = "calculator_history.json"
        self.load_history()
        
    def load_history(self):
        """Load calculation history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except:
            self.history = []
    
    def save_history(self):
        """Save calculation history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_to_history(self, expression: str, result: str, operation_type: str = "basic"):
        """Add calculation to history"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "expression": expression,
            "result": result,
            "type": operation_type
        }
        self.history.append(entry)
        if len(self.history) > 100:  # Keep only last 100 entries
            self.history = self.history[-100:]
        self.save_history()
    
    def clear_history(self):
        """Clear calculation history"""
        self.history = []
        self.save_history()
        print("История вычислений очищена.")
    
    def show_history(self, limit: int = 10):
        """Show recent calculation history"""
        if not self.history:
            print("История вычислений пуста.")
            return
        
        print(f"\nПоследние {min(limit, len(self.history))} вычислений:")
        print("-" * 60)
        
        for entry in self.history[-limit:]:
            print(f"[{entry['timestamp']}] {entry['expression']} = {entry['result']} ({entry['type']})")
    
    def basic_operations(self, x: float, y: float, operation: str) -> Tuple[float, str]:
        """Perform basic arithmetic operations"""
        if operation == "add":
            result = x + y
            expression = f"{x} + {y}"
        elif operation == "subtract":
            result = x - y
            expression = f"{x} - {y}"
        elif operation == "multiply":
            result = x * y
            expression = f"{x} × {y}"
        elif operation == "divide":
            if y == 0:
                return None, "Ошибка: деление на ноль!"
            result = x / y
            expression = f"{x} ÷ {y}"
        elif operation == "power":
            result = x ** y
            expression = f"{x} ^ {y}"
        elif operation == "modulo":
            if y == 0:
                return None, "Ошибка: деление на ноль!"
            result = x % y
            expression = f"{x} mod {y}"
        else:
            return None, "Неизвестная операция"
        
        return result, expression
    
    def scientific_operations(self, x: float, operation: str) -> Tuple[float, str]:
        """Perform scientific mathematical operations"""
        try:
            if operation == "sqrt":
                if x < 0:
                    return None, "Ошибка: корень из отрицательного числа"
                result = math.sqrt(x)
                expression = f"√({x})"
            elif operation == "cbrt":
                result = x ** (1/3)
                expression = f"∛({x})"
            elif operation == "square":
                result = x ** 2
                expression = f"({x})²"
            elif operation == "cube":
                result = x ** 3
                expression = f"({x})³"
            elif operation == "factorial":
                if x < 0 or x != int(x):
                    return None, "Ошибка: факториал определен только для неотрицательных целых чисел"
                result = math.factorial(int(x))
                expression = f"({x})!"
            elif operation == "log":
                if x <= 0:
                    return None, "Ошибка: логарифм определен только для положительных чисел"
                result = math.log10(x)
                expression = f"log₁₀({x})"
            elif operation == "ln":
                if x <= 0:
                    return None, "Ошибка: натуральный логарифм определен только для положительных чисел"
                result = math.log(x)
                expression = f"ln({x})"
            elif operation == "sin":
                if self.angle_mode == "degrees":
                    x_rad = math.radians(x)
                else:
                    x_rad = x
                result = math.sin(x_rad)
                expression = f"sin({x}°)"
            elif operation == "cos":
                if self.angle_mode == "degrees":
                    x_rad = math.radians(x)
                else:
                    x_rad = x
                result = math.cos(x_rad)
                expression = f"cos({x}°)"
            elif operation == "tan":
                if self.angle_mode == "degrees":
                    x_rad = math.radians(x)
                else:
                    x_rad = x
                if abs(math.cos(x_rad)) < 1e-10:
                    return None, "Ошибка: тангенс не определен для этого угла"
                result = math.tan(x_rad)
                expression = f"tan({x}°)"
            elif operation == "asin":
                result = math.degrees(math.asin(x)) if self.angle_mode == "degrees" else math.asin(x)
                expression = f"arcsin({x})"
            elif operation == "acos":
                result = math.degrees(math.acos(x)) if self.angle_mode == "degrees" else math.acos(x)
                expression = f"arccos({x})"
            elif operation == "atan":
                result = math.degrees(math.atan(x)) if self.angle_mode == "degrees" else math.atan(x)
                expression = f"arctan({x})"
            elif operation == "abs":
                result = abs(x)
                expression = f"|{x}|"
            elif operation == "floor":
                result = math.floor(x)
                expression = f"⌊{x}⌋"
            elif operation == "ceil":
                result = math.ceil(x)
                expression = f"⌈{x}⌉"
            elif operation == "round":
                result = round(x)
                expression = f"round({x})"
            else:
                return None, "Неизвестная научная операция"
            
            return result, expression
        except Exception as e:
            return None, f"Ошибка вычисления: {str(e)}"
    
    def unit_conversion(self, value: float, from_unit: str, to_unit: str) -> Tuple[float, str]:
        """Convert between different units"""
        conversions = {
            "length": {
                "m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001,
                "mi": 1609.34, "yd": 0.9144, "ft": 0.3048, "in": 0.0254
            },
            "weight": {
                "kg": 1.0, "g": 0.001, "mg": 0.000001,
                "lb": 0.453592, "oz": 0.0283495
            },
            "temperature": {
                "celsius": "c", "fahrenheit": "f", "kelvin": "k"
            },
            "area": {
                "m2": 1.0, "km2": 1000000.0, "cm2": 0.0001,
                "ha": 10000.0, "acres": 4046.86
            },
            "volume": {
                "m3": 1.0, "l": 0.001, "ml": 0.000001,
                "gal": 0.00378541, "qt": 0.000946353
            }
        }
        
        # Temperature conversion (special case)
        if from_unit in conversions["temperature"] and to_unit in conversions["temperature"]:
            return self._convert_temperature(value, from_unit, to_unit)
        
        # Find the category
        category = None
        for cat, units in conversions.items():
            if from_unit in units and to_unit in units:
                category = cat
                break
        
        if category is None:
            return None, f"Неподдерживаемое преобразование: {from_unit} → {to_unit}"
        
        # Convert to base unit, then to target unit
        base_value = value * conversions[category][from_unit]
        result = base_value / conversions[category][to_unit]
        
        expression = f"{value} {from_unit} = {result:.6f} {to_unit}"
        return result, expression
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> Tuple[float, str]:
        """Convert temperature between different scales"""
        # Convert to Celsius first
        if from_unit == "fahrenheit":
            celsius = (value - 32) * 5/9
        elif from_unit == "kelvin":
            celsius = value - 273.15
        else:  # celsius
            celsius = value
        
        # Convert from Celsius to target unit
        if to_unit == "fahrenheit":
            result = celsius * 9/5 + 32
        elif to_unit == "kelvin":
            result = celsius + 273.15
        else:  # celsius
            result = celsius
        
        expression = f"{value}°{from_unit[0].upper()} = {result:.2f}°{to_unit[0].upper()}"
        return result, expression
    
    def statistics_operations(self, numbers: List[float], operation: str) -> Tuple[float, str]:
        """Perform statistical operations"""
        if not numbers:
            return None, "Список чисел пуст"
        
        try:
            if operation == "mean":
                result = statistics.mean(numbers)
                expression = f"Среднее({', '.join(map(str, numbers))})"
            elif operation == "median":
                result = statistics.median(numbers)
                expression = f"Медиана({', '.join(map(str, numbers))})"
            elif operation == "mode":
                result = statistics.mode(numbers)
                expression = f"Мода({', '.join(map(str, numbers))})"
            elif operation == "std":
                result = statistics.stdev(numbers)
                expression = f"Стандартное отклонение({', '.join(map(str, numbers))})"
            elif operation == "variance":
                result = statistics.variance(numbers)
                expression = f"Дисперсия({', '.join(map(str, numbers))})"
            elif operation == "min":
                result = min(numbers)
                expression = f"Минимум({', '.join(map(str, numbers))})"
            elif operation == "max":
                result = max(numbers)
                expression = f"Максимум({', '.join(map(str, numbers))})"
            elif operation == "sum":
                result = sum(numbers)
                expression = f"Сумма({', '.join(map(str, numbers))})"
            else:
                return None, "Неизвестная статистическая операция"
            
            return result, expression
        except Exception as e:
            return None, f"Ошибка статистических вычислений: {str(e)}"
    
    def solve_equation(self, a: float, b: float, c: float = 0) -> Tuple[List[float], str]:
        """Solve quadratic equation ax² + bx + c = 0"""
        if a == 0:
            if b == 0:
                if c == 0:
                    return [float('inf')], "Бесконечное количество решений"
                else:
                    return [], "Нет решений"
            else:
                x = -c / b
                return [x], f"Линейное уравнение: x = {x}"
        
        discriminant = b**2 - 4*a*c
        expression = f"{a}x² + {b}x + {c} = 0"
        
        if discriminant > 0:
            x1 = (-b + math.sqrt(discriminant)) / (2*a)
            x2 = (-b - math.sqrt(discriminant)) / (2*a)
            return [x1, x2], expression
        elif discriminant == 0:
            x = -b / (2*a)
            return [x], expression
        else:
            real_part = -b / (2*a)
            imag_part = math.sqrt(abs(discriminant)) / (2*a)
            return [complex(real_part, imag_part), complex(real_part, -imag_part)], expression
    
    def memory_operations(self, operation: str, value: float = 0) -> Tuple[float, str]:
        """Perform memory operations"""
        if operation == "store":
            self.memory = value
            return self.memory, f"M = {value}"
        elif operation == "recall":
            return self.memory, f"M = {self.memory}"
        elif operation == "add":
            self.memory += value
            return self.memory, f"M += {value} = {self.memory}"
        elif operation == "subtract":
            self.memory -= value
            return self.memory, f"M -= {value} = {self.memory}"
        elif operation == "clear":
            self.memory = 0
            return self.memory, "M = 0"
        else:
            return None, "Неизвестная операция с памятью"
    
    def generate_random_number(self, min_val: float, max_val: float, count: int = 1) -> Tuple[List[float], str]:
        """Generate random numbers in specified range"""
        if count < 1:
            return None, "Количество должно быть положительным"
        
        numbers = [random.uniform(min_val, max_val) for _ in range(count)]
        if count == 1:
            expression = f"Случайное число в диапазоне [{min_val}, {max_val}]"
        else:
            expression = f"{count} случайных чисел в диапазоне [{min_val}, {max_val}]"
        
        return numbers, expression
    
    def calculate_percentage(self, value: float, percentage: float, operation: str) -> Tuple[float, str]:
        """Calculate percentage operations"""
        if operation == "of":
            result = value * percentage / 100
            expression = f"{percentage}% от {value} = {result}"
        elif operation == "increase":
            result = value * (1 + percentage / 100)
            expression = f"{value} + {percentage}% = {result}"
        elif operation == "decrease":
            result = value * (1 - percentage / 100)
            expression = f"{value} - {percentage}% = {result}"
        elif operation == "change":
            if value != 0:
                result = ((percentage - value) / value) * 100
                expression = f"Изменение от {value} до {percentage} = {result:.2f}%"
            else:
                return None, "Ошибка: деление на ноль"
        else:
            return None, "Неизвестная процентная операция"
        
        return result, expression

class CalculatorInterface:
    """User interface for the advanced calculator"""
    
    def __init__(self):
        self.calc = AdvancedCalculator()
    
    def display_main_menu(self):
        """Display the main calculator menu"""
        print("\n" + "="*60)
        print("🧮 РАСШИРЕННЫЙ КАЛЬКУЛЯТОР")
        print("="*60)
        print("1.  Базовые операции")
        print("2.  Научные функции")
        print("3.  Преобразование единиц")
        print("4.  Статистика")
        print("5.  Решение уравнений")
        print("6.  Операции с памятью")
        print("7.  Случайные числа")
        print("8.  Процентные вычисления")
        print("9.  История вычислений")
        print("10. Настройки")
        print("0.  Выход")
        print("="*60)
    
    def basic_operations_menu(self):
        """Handle basic arithmetic operations"""
        print("\n📊 БАЗОВЫЕ ОПЕРАЦИИ")
        print("1. Сложение (+)")
        print("2. Вычитание (-)")
        print("3. Умножение (×)")
        print("4. Деление (÷)")
        print("5. Возведение в степень (^)")
        print("6. Остаток от деления (mod)")
        print("0. Назад")
        
        choice = input("\nВыберите операцию: ")
        
        if choice == "0":
            return
        
        operations = {
            "1": "add", "2": "subtract", "3": "multiply",
            "4": "divide", "5": "power", "6": "modulo"
        }
        
        if choice not in operations:
            print("Неверный выбор!")
            return
        
        try:
            num1 = float(input("Введите первое число: "))
            num2 = float(input("Введите второе число: "))
            
            result, expression = self.calc.basic_operations(num1, num2, operations[choice])
            
            if result is not None:
                print(f"\nРезультат: {expression} = {result}")
                self.calc.add_to_history(expression, str(result), "basic")
            else:
                print(f"Ошибка: {expression}")
                
        except ValueError:
            print("Ошибка: введите корректное число!")
    
    def scientific_functions_menu(self):
        """Handle scientific mathematical functions"""
        print("\n🔬 НАУЧНЫЕ ФУНКЦИИ")
        print("1.  Квадратный корень (√)")
        print("2.  Кубический корень (∛)")
        print("3.  Квадрат (x²)")
        print("4.  Куб (x³)")
        print("5.  Факториал (x!)")
        print("6.  Десятичный логарифм (log₁₀)")
        print("7.  Натуральный логарифм (ln)")
        print("8.  Синус (sin)")
        print("9.  Косинус (cos)")
        print("10. Тангенс (tan)")
        print("11. Арксинус (arcsin)")
        print("12. Арккосинус (arccos)")
        print("13. Арктангенс (arctan)")
        print("14. Модуль (|x|)")
        print("15. Округление вниз (⌊x⌋)")
        print("16. Округление вверх (⌈x⌉)")
        print("17. Округление (round)")
        print("0.  Назад")
        
        choice = input("\nВыберите функцию: ")
        
        if choice == "0":
            return
        
        operations = {
            "1": "sqrt", "2": "cbrt", "3": "square", "4": "cube",
            "5": "factorial", "6": "log", "7": "ln", "8": "sin",
            "9": "cos", "10": "tan", "11": "asin", "12": "acos",
            "13": "atan", "14": "abs", "15": "floor", "16": "ceil", "17": "round"
        }
        
        if choice not in operations:
            print("Неверный выбор!")
            return
        
        try:
            num = float(input("Введите число: "))
            
            result, expression = self.calc.scientific_operations(num, operations[choice])
            
            if result is not None:
                print(f"\nРезультат: {expression} = {result}")
                self.calc.add_to_history(expression, str(result), "scientific")
            else:
                print(f"Ошибка: {expression}")
                
        except ValueError:
            print("Ошибка: введите корректное число!")
    
    def unit_conversion_menu(self):
        """Handle unit conversions"""
        print("\n📏 ПРЕОБРАЗОВАНИЕ ЕДИНИЦ")
        print("1. Длина")
        print("2. Вес")
        print("3. Температура")
        print("4. Площадь")
        print("5. Объем")
        print("0. Назад")
        
        choice = input("\nВыберите тип единиц: ")
        
        if choice == "0":
            return
        
        categories = {
            "1": ("length", ["м", "км", "см", "мм", "мили", "ярды", "футы", "дюймы"]),
            "2": ("weight", ["кг", "г", "мг", "фунты", "унции"]),
            "3": ("temperature", ["Цельсий", "Фаренгейт", "Кельвин"]),
            "4": ("area", ["м²", "км²", "см²", "га", "акры"]),
            "5": ("volume", ["м³", "л", "мл", "галлоны", "кварты"])
        }
        
        if choice not in categories:
            print("Неверный выбор!")
            return
        
        category, units = categories[choice]
        
        print(f"\nДоступные единицы: {', '.join(units)}")
        
        try:
            value = float(input("Введите значение: "))
            from_unit = input(f"Из единицы ({units[0]}): ").strip()
            to_unit = input(f"В единицу ({units[1]}): ").strip()
            
            result, expression = self.calc.unit_conversion(value, from_unit, to_unit)
            
            if result is not None:
                print(f"\nРезультат: {expression}")
                self.calc.add_to_history(expression, str(result), "conversion")
            else:
                print(f"Ошибка: {expression}")
                
        except ValueError:
            print("Ошибка: введите корректное число!")
    
    def statistics_menu(self):
        """Handle statistical operations"""
        print("\n📈 СТАТИСТИКА")
        print("1. Среднее значение")
        print("2. Медиана")
        print("3. Мода")
        print("4. Стандартное отклонение")
        print("5. Дисперсия")
        print("6. Минимум")
        print("7. Максимум")
        print("8. Сумма")
        print("0. Назад")
        
        choice = input("\nВыберите операцию: ")
        
        if choice == "0":
            return
        
        operations = {
            "1": "mean", "2": "median", "3": "mode", "4": "std",
            "5": "variance", "6": "min", "7": "max", "8": "sum"
        }
        
        if choice not in operations:
            print("Неверный выбор!")
            return
        
        try:
            numbers_input = input("Введите числа через запятую: ")
            numbers = [float(x.strip()) for x in numbers_input.split(",")]
            
            result, expression = self.calc.statistics_operations(numbers, operations[choice])
            
            if result is not None:
                print(f"\nРезультат: {expression} = {result}")
                self.calc.add_to_history(expression, str(result), "statistics")
            else:
                print(f"Ошибка: {expression}")
                
        except ValueError:
            print("Ошибка: введите корректные числа!")
    
    def equation_solver_menu(self):
        """Handle equation solving"""
        print("\n📝 РЕШЕНИЕ УРАВНЕНИЙ")
        print("Решаем квадратное уравнение ax² + bx + c = 0")
        
        try:
            a = float(input("Введите коэффициент a: "))
            b = float(input("Введите коэффициент b: "))
            c = float(input("Введите коэффициент c: "))
            
            solutions, expression = self.calc.solve_equation(a, b, c)
            
            if solutions:
                if len(solutions) == 1:
                    print(f"\nУравнение: {expression}")
                    print(f"Решение: x = {solutions[0]}")
                else:
                    print(f"\nУравнение: {expression}")
                    print(f"Решения: x₁ = {solutions[0]}, x₂ = {solutions[1]}")
                
                self.calc.add_to_history(expression, str(solutions), "equation")
            else:
                print(f"Уравнение: {expression}")
                print("Решений нет")
                
        except ValueError:
            print("Ошибка: введите корректные коэффициенты!")
    
    def memory_menu(self):
        """Handle memory operations"""
        print("\n💾 ОПЕРАЦИИ С ПАМЯТЬЮ")
        print(f"Текущее значение памяти: M = {self.calc.memory}")
        print("1. Сохранить значение")
        print("2. Вызвать значение")
        print("3. Добавить к памяти")
        print("4. Вычесть из памяти")
        print("5. Очистить память")
        print("0. Назад")
        
        choice = input("\nВыберите операцию: ")
        
        if choice == "0":
            return
        
        operations = {
            "1": "store", "2": "recall", "3": "add",
            "4": "subtract", "5": "clear"
        }
        
        if choice not in operations:
            print("Неверный выбор!")
            return
        
        if choice in ["1", "3", "4"]:
            try:
                value = float(input("Введите значение: "))
                result, expression = self.calc.memory_operations(operations[choice], value)
            except ValueError:
                print("Ошибка: введите корректное число!")
                return
        else:
            result, expression = self.calc.memory_operations(operations[choice])
        
        if result is not None:
            print(f"Результат: {expression}")
            self.calc.add_to_history(expression, str(result), "memory")
        else:
            print(f"Ошибка: {expression}")
    
    def random_numbers_menu(self):
        """Handle random number generation"""
        print("\n🎲 СЛУЧАЙНЫЕ ЧИСЛА")
        
        try:
            min_val = float(input("Введите минимальное значение: "))
            max_val = float(input("Введите максимальное значение: "))
            count = int(input("Введите количество чисел: "))
            
            if count < 1:
                print("Количество должно быть положительным!")
                return
            
            numbers, expression = self.calc.generate_random_number(min_val, max_val, count)
            
            if numbers:
                if count == 1:
                    print(f"\nРезультат: {expression} = {numbers[0]}")
                else:
                    print(f"\nРезультат: {expression}")
                    print(f"Числа: {', '.join(map(str, numbers))}")
                
                self.calc.add_to_history(expression, str(numbers), "random")
            else:
                print(f"Ошибка: {expression}")
                
        except ValueError:
            print("Ошибка: введите корректные значения!")
    
    def percentage_menu(self):
        """Handle percentage calculations"""
        print("\n💯 ПРОЦЕНТНЫЕ ВЫЧИСЛЕНИЯ")
        print("1. X% от числа")
        print("2. Увеличить число на X%")
        print("3. Уменьшить число на X%")
        print("4. Процентное изменение")
        print("0. Назад")
        
        choice = input("\nВыберите операцию: ")
        
        if choice == "0":
            return
        
        operations = {
            "1": "of", "2": "increase", "3": "decrease", "4": "change"
        }
        
        if choice not in operations:
            print("Неверный выбор!")
            return
        
        try:
            if choice == "4":
                value1 = float(input("Введите первое число: "))
                value2 = float(input("Введите второе число: "))
                result, expression = self.calc.calculate_percentage(value1, value2, operations[choice])
            else:
                value = float(input("Введите число: "))
                percentage = float(input("Введите процент: "))
                result, expression = self.calc.calculate_percentage(value, percentage, operations[choice])
            
            if result is not None:
                print(f"\nРезультат: {expression}")
                self.calc.add_to_history(expression, str(result), "percentage")
            else:
                print(f"Ошибка: {expression}")
                
        except ValueError:
            print("Ошибка: введите корректные значения!")
    
    def settings_menu(self):
        """Handle calculator settings"""
        print("\n⚙️ НАСТРОЙКИ")
        print(f"1. Режим углов: {self.calc.angle_mode}")
        print("2. Изменить режим углов")
        print("3. Очистить историю")
        print("0. Назад")
        
        choice = input("\nВыберите опцию: ")
        
        if choice == "1":
            print(f"Текущий режим углов: {self.calc.angle_mode}")
        elif choice == "2":
            print("Выберите режим углов:")
            print("1. Градусы")
            print("2. Радианы")
            mode_choice = input("Ваш выбор: ")
            if mode_choice == "1":
                self.calc.angle_mode = "degrees"
                print("Режим углов изменен на градусы")
            elif mode_choice == "2":
                self.calc.angle_mode = "radians"
                print("Режим углов изменен на радианы")
            else:
                print("Неверный выбор!")
        elif choice == "3":
            self.calc.clear_history()
        elif choice == "0":
            return
        else:
            print("Неверный выбор!")
    
    def run(self):
        """Main calculator loop"""
        while True:
            self.display_main_menu()
            choice = input("\nВыберите опцию (0-10): ")
            
            if choice == "0":
                print("\nСпасибо за использование расширенного калькулятора! 👋")
                break
            elif choice == "1":
                self.basic_operations_menu()
            elif choice == "2":
                self.scientific_functions_menu()
            elif choice == "3":
                self.unit_conversion_menu()
            elif choice == "4":
                self.statistics_menu()
            elif choice == "5":
                self.equation_solver_menu()
            elif choice == "6":
                self.memory_menu()
            elif choice == "7":
                self.random_numbers_menu()
            elif choice == "8":
                self.percentage_menu()
            elif choice == "9":
                self.calc.show_history()
            elif choice == "10":
                self.settings_menu()
            else:
                print("Неверный выбор! Попробуйте снова.")
            
            input("\nНажмите Enter для продолжения...")

def main():
    """Main function to run the enhanced calculator"""
    print("🚀 Запуск расширенного калькулятора...")
    calculator = CalculatorInterface()
    calculator.run()

if __name__ == "__main__":
    main()
