"""
Расширенный калькулятор статистики
Выполняет комплексный анализ числовых данных
"""

import statistics
import math
from typing import List, Tuple, Optional
from collections import Counter
import sys


class DataAnalyzer:
    """Класс для комплексного анализа числовых данных"""
    
    def __init__(self, data: List[float]):
        self.data = sorted(data)
        self.n = len(data)
        
    def basic_stats(self) -> dict:
        """Вычисляет базовую статистику"""
        if self.n == 0:
            return {}
            
        return {
            'count': self.n,
            'sum': sum(self.data),
            'mean': statistics.mean(self.data),
            'median': statistics.median(self.data),
            'mode': statistics.mode(self.data) if self.n > 0 else None,
            'min': min(self.data),
            'max': max(self.data),
            'range': max(self.data) - min(self.data)
        }
    
    def variance_stats(self) -> dict:
        """Вычисляет статистику дисперсии"""
        if self.n < 2:
            return {}
            
        return {
            'variance': statistics.variance(self.data),
            'population_variance': statistics.pvariance(self.data),
            'std_dev': statistics.stdev(self.data),
            'population_std_dev': statistics.pstdev(self.data),
            'coefficient_of_variation': statistics.stdev(self.data) / statistics.mean(self.data) if statistics.mean(self.data) != 0 else None
        }
    
    def percentile_stats(self) -> dict:
        """Вычисляет перцентили и квартили"""
        if self.n == 0:
            return {}
            
        return {
            'q1': statistics.quantiles(self.data, n=4)[0],
            'q2': statistics.quantiles(self.data, n=4)[1],
            'q3': statistics.quantiles(self.data, n=4)[2],
            'iqr': statistics.quantiles(self.data, n=4)[2] - statistics.quantiles(self.data, n=4)[0],
            'p10': statistics.quantiles(self.data, n=10)[0],
            'p90': statistics.quantiles(self.data, n=10)[8]
        }
    
    def skewness_kurtosis(self) -> dict:
        """Вычисляет асимметрию и эксцесс"""
        if self.n < 3:
            return {}
            
        mean = statistics.mean(self.data)
        std = statistics.stdev(self.data)
        
        # Асимметрия
        skewness = sum(((x - mean) / std) ** 3 for x in self.data) / self.n
        
        # Эксцесс
        kurtosis = sum(((x - mean) / std) ** 4 for x in self.data) / self.n - 3
        
        return {
            'skewness': skewness,
            'kurtosis': kurtosis
        }
    
    def outliers(self, method: str = 'iqr') -> List[float]:
        """Находит выбросы в данных"""
        if self.n < 4:
            return []
            
        if method == 'iqr':
            q1, q3 = statistics.quantiles(self.data, n=4)[0], statistics.quantiles(self.data, n=4)[2]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            return [x for x in self.data if x < lower_bound or x > upper_bound]
        
        elif method == 'zscore':
            mean = statistics.mean(self.data)
            std = statistics.stdev(self.data)
            return [x for x in self.data if abs((x - mean) / std) > 2]
        
        return []
    
    def frequency_distribution(self, bins: int = 10) -> dict:
        """Создает частотное распределение"""
        if self.n == 0:
            return {}
            
        min_val, max_val = min(self.data), max(self.data)
        bin_width = (max_val - min_val) / bins
        
        distribution = {}
        for i in range(bins):
            lower = min_val + i * bin_width
            upper = min_val + (i + 1) * bin_width
            count = sum(1 for x in self.data if lower <= x < upper)
            if count > 0:
                distribution[f"{lower:.2f}-{upper:.2f}"] = count
        
        return distribution


def validate_input(data_str: str) -> Tuple[bool, str, Optional[List[float]]]:
    """Валидирует введенные данные"""
    if not data_str.strip():
        return False, "Введена пустая строка", None
    
    try:
        numbers = [float(x.strip()) for x in data_str.split()]
        if not numbers:
            return False, "Не найдено ни одного числа", None
        
        # Проверка на бесконечность и NaN
        for num in numbers:
            if math.isinf(num) or math.isnan(num):
                return False, f"Обнаружено некорректное значение: {num}", None
        
        return True, "Данные корректны", numbers
        
    except ValueError as e:
        return False, f"Ошибка преобразования: {e}", None


def print_statistics(analyzer: DataAnalyzer) -> None:
    """Выводит все статистики в красивом формате"""
    print("\n" + "="*60)
    print("📊 КОМПЛЕКСНЫЙ СТАТИСТИЧЕСКИЙ АНАЛИЗ")
    print("="*60)
    
    # Базовая статистика
    basic = analyzer.basic_stats()
    if basic:
        print("\n🔢 БАЗОВАЯ СТАТИСТИКА:")
        print(f"   Количество элементов: {basic['count']}")
        print(f"   Сумма: {basic['sum']:.4f}")
        print(f"   Среднее арифметическое: {basic['mean']:.4f}")
        print(f"   Медиана: {basic['median']:.4f}")
        print(f"   Мода: {basic['mode']:.4f}" if basic['mode'] is not None else "   Мода: не определена")
        print(f"   Минимум: {basic['min']:.4f}")
        print(f"   Максимум: {basic['max']:.4f}")
        print(f"   Размах: {basic['range']:.4f}")
    
    # Статистика дисперсии
    variance = analyzer.variance_stats()
    if variance:
        print("\n📈 СТАТИСТИКА ДИСПЕРСИИ:")
        print(f"   Дисперсия выборки: {variance['variance']:.4f}")
        print(f"   Дисперсия генеральной совокупности: {variance['population_variance']:.4f}")
        print(f"   Стандартное отклонение выборки: {variance['std_dev']:.4f}")
        print(f"   Стандартное отклонение генеральной совокупности: {variance['population_std_dev']:.4f}")
        if variance['coefficient_of_variation']:
            print(f"   Коэффициент вариации: {variance['coefficient_of_variation']:.4f}")
    
    # Перцентили
    percentiles = analyzer.percentile_stats()
    if percentiles:
        print("\n📊 ПЕРЦЕНТИЛИ И КВАРТИЛИ:")
        print(f"   Q1 (25%): {percentiles['q1']:.4f}")
        print(f"   Q2 (50%): {percentiles['q2']:.4f}")
        print(f"   Q3 (75%): {percentiles['q3']:.4f}")
        print(f"   Межквартильный размах: {percentiles['iqr']:.4f}")
        print(f"   P10 (10%): {percentiles['p10']:.4f}")
        print(f"   P90 (90%): {percentiles['p90']:.4f}")
    
    # Асимметрия и эксцесс
    skew_kurt = analyzer.skewness_kurtosis()
    if skew_kurt:
        print("\n📐 ФОРМА РАСПРЕДЕЛЕНИЯ:")
        print(f"   Асимметрия: {skew_kurt['skewness']:.4f}")
        print(f"   Эксцесс: {skew_kurt['kurtosis']:.4f}")
        
        # Интерпретация асимметрии
        if abs(skew_kurt['skewness']) < 0.5:
            skew_interpretation = "симметричное"
        elif skew_kurt['skewness'] > 0:
            skew_interpretation = "правостороннее (положительная асимметрия)"
        else:
            skew_interpretation = "левостороннее (отрицательная асимметрия)"
        print(f"   Интерпретация асимметрии: {skew_interpretation}")
    
    # Выбросы
    outliers_iqr = analyzer.outliers('iqr')
    outliers_zscore = analyzer.outliers('zscore')
    if outliers_iqr or outliers_zscore:
        print("\n⚠️  ВЫБРОСЫ:")
        if outliers_iqr:
            print(f"   По методу IQR: {outliers_iqr}")
        if outliers_zscore:
            print(f"   По методу Z-score: {outliers_zscore}")
    
    # Частотное распределение
    distribution = analyzer.frequency_distribution()
    if distribution:
        print("\n📊 ЧАСТОТНОЕ РАСПРЕДЕЛЕНИЕ:")
        for interval, count in distribution.items():
            percentage = (count / analyzer.n) * 100
            bar = "█" * int(percentage / 5)  # Визуализация
            print(f"   {interval}: {count} ({percentage:.1f}%) {bar}")


def interactive_mode() -> None:
    """Интерактивный режим работы"""
    print("🎯 ИНТЕРАКТИВНЫЙ РЕЖИМ СТАТИСТИЧЕСКОГО АНАЛИЗА")
    print("="*60)
    
    while True:
        try:
            print("\nВыберите действие:")
            print("1. Ввести новые данные")
            print("2. Загрузить данные из файла")
            print("3. Показать справку")
            print("4. Выход")
            
            choice = input("\nВаш выбор (1-4): ").strip()
            
            if choice == '1':
                data_input = input("\nВведите числа через пробел: ")
                is_valid, message, numbers = validate_input(data_input)
                
                if is_valid:
                    analyzer = DataAnalyzer(numbers)
                    print_statistics(analyzer)
                else:
                    print(f"❌ Ошибка: {message}")
            
            elif choice == '2':
                filename = input("Введите имя файла: ").strip()
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                    is_valid, message, numbers = validate_input(content)
                    
                    if is_valid:
                        analyzer = DataAnalyzer(numbers)
                        print_statistics(analyzer)
                    else:
                        print(f"❌ Ошибка в файле: {message}")
                except FileNotFoundError:
                    print(f"❌ Файл '{filename}' не найден")
                except Exception as e:
                    print(f"❌ Ошибка чтения файла: {e}")
            
            elif choice == '3':
                print_help()
            
            elif choice == '4':
                print("👋 До свидания!")
                break
            
            else:
                print("❌ Неверный выбор. Попробуйте снова.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Программа прервана пользователем")
            break
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")


def print_help() -> None:
    """Выводит справку по программе"""
    print("\n📚 СПРАВКА ПО ПРОГРАММЕ")
    print("="*60)
    print("Эта программа выполняет комплексный статистический анализ числовых данных.")
    print("\n📊 ВЫЧИСЛЯЕМЫЕ ПОКАЗАТЕЛИ:")
    print("• Базовая статистика (среднее, медиана, мода, минимум, максимум)")
    print("• Статистика дисперсии (дисперсия, стандартное отклонение)")
    print("• Перцентили и квартили")
    print("• Асимметрия и эксцесс")
    print("• Выбросы (методы IQR и Z-score)")
    print("• Частотное распределение")
    print("\n💡 СОВЕТЫ:")
    print("• Вводите числа через пробел (например: 1 2 3 4 5)")
    print("• Поддерживаются десятичные числа")
    print("• Программа автоматически сортирует данные")
    print("• Для выхода используйте Ctrl+C или выберите пункт 4")


def main():
    """Главная функция программы"""
    print("🚀 ЗАПУСК РАСШИРЕННОГО СТАТИСТИЧЕСКОГО АНАЛИЗАТОРА")
    
    try:
        interactive_mode()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()