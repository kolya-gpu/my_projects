import pandas as pd
import sqlite3
import folium
import os
import argparse

# Модуль argparse в Python предназначен для обработки аргументов командной строки в скриптах Python. 
# Он позволяет создавать удобные и понятные интерфейсы командной строки, 
# #принимающие различные типы аргументов и генерирующие сообщения об использовании и справке. 

# Исходные данные (если файла нет, создаем его автоматически)

DEFAULT_CSV_FILE = "geodata.csv"
DEFAULT_DB_FILE = "geolocations.db"
OUTPUT_MAP = "map.html"

csv_content = """id,name,latitude,longitude,timestamp
1,Location1,55.424975, 37.578936,2025-04-22 12:00:00
2,Location2,55.817062, 37.383687,2025-04-28 22:00:00
3,Location3,55.457021, 37.598932,2025-04-28 22:00:00
4,Vologda,59.223058, 39.889616,2004-01-26 06:15:00
5,St. Petersburg,59.947343, 30.304550,2025-04-28 22:00:00
6,N. Novgorod,56.330062, 43.998288,2025-04-28 22:00:00
7,Kazan,55.800484, 49.105920,2025-04-28 22:00:00
8,Location4,55.826270, 37.637526,2025-04-28 22:00:00
9,Location5,55.715765, 37.553634,2025-04-28 22:00:00
10,Location6,55.791170, 37.559590,2025-04-28 22:00:00
11,Kaliningrad,54.712899, 20.496575,2025-04-28 22:00:00
12,Location7,55.775551, 37.658467,2025-04-28 22:00:00
13,Location8,55.761132, 37.606334,2025-04-28 22:00:00
14,Location9,55.457021, 37.598932,2022-11-22 10:00:00
15,Location10,55.397756, 37.564221,2025-04-25 16:00:00
16,Location11,55.421855, 37.569188,2025-03-03 17:00:00
17,Location12,55.446694, 37.545452,2024-12-22 16:00:00
18,Location13,55.329042, 37.483137,2024-12-22 16:00:00
19,Location14,55.346994, 37.395084,2013-10-10 20:00:00
20,Russia,54.712899, 20.496575,2025-04-28 22:00:00
21,IqnixTech,55.423306, 37.579285,2022-03-24 15:00:00
22,Podolsk Cadets Square,55.423252, 37.518292, 2022-03-24 15:00:00
23,Yaroslavl',57.626559, 39.893813, 2025-04-28 22:00:00
24,Kostroma,57.767918, 40.926894, 2025-04-28 22:00:00
25,Tver',56.858745, 35.917421, 2025-04-28 22:00:00
26,Smolensk,54.778263, 32.051054, 2025-04-28 22:00:00
27,Bryansk,53.243397, 34.360934, 2025-04-28 22:00:00
28,Vladimir,56.130789, 40.404232, 2025-04-28 22:00:00
29,Arkhangel'sk,64.546907, 40.497798, 2025-04-28 22:00:00
30,Volgograd,48.706584, 44.493640, 2025-04-28 22:00:00
31,Sochi,43.593763, 39.705235, 2025-04-28 22:00:00
32,Pyatigorsk,44.042100, 43.065374,2025-04-28 22:00:00
33,Taganrog,47.211333, 38.931935,2025-04-28 22:00:00
34,Serpukhov,54.914743, 37.412855,2025-06-26 09:00:00
35,Minsk,53.908358, 27.552593,2025-06-26 09:00:00
36,Petrozavodsk,61.793016, 34.333415,2025-06-26 09:00:00
37,Murmansk,68.977104, 33.056507,2025-06-26 09:00:00
38,Rogachevo Airport, 71.611780, 52.466269,2025-06-26 09:00:00
39,White lip,71.536107, 52.343941,2025-06-26 09:00:00
40,Vorkuta,67.503124, 64.043542,2025-06-26 09:00:00
41,Kostomuksha,64.589504, 30.579746,2025-06-26 09:00:00
42,Mount Elbrus,43.353264, 42.435176,2025-06-26 09:00:00
43,Mogilev,53.898607, 30.321062,2025-06-26 09:00:00
44,Brest,52.099228, 23.683341,2025-06-26 09:00:00
45,Vitebsk,55.184919, 30.199976,2025-06-26 09:00:00
46,Gomel',52.430170, 31.003547,2025-06-26 09:00:00
47,Lida,53.892105, 25.301492,2025-06-26 09:00:00
48,Grodno,53.678613, 23.829195,2025-06-26 09:00:00"""

def ensure_csv_exists(csv_path):
    if not os.path.exists(csv_path):
        with open(csv_path, "w") as f:
            f.write(csv_content)
        print(f"{csv_path} создан автоматически.")

def load_data(csv_path):
    return pd.read_csv(csv_path)

def save_to_db(df, db_path):
    conn = sqlite3.connect(db_path)
    df.to_sql('geolocations', conn, if_exists='replace', index=False)
    conn.close()

def query_db(db_path, query):
    conn = sqlite3.connect(db_path)
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result

def create_map(df, output_html=OUTPUT_MAP):
    if df.empty:
        print("Нет данных для отображения карты.")
        return
    
    avg_lat = df['latitude'].mean()
    avg_lon = df['longitude'].mean()
    
    geo_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)
    
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=row.get('name', 'Location')
        ).add_to(geo_map)
    
    geo_map.save(output_html)
    print(f"Карта сохранена в {output_html}")

def main():
    parser = argparse.ArgumentParser(description="Автоматизация работы с геоданными.")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV_FILE,
                        help="Путь к CSV файлу.")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_FILE,
                        help="Путь к базе данных SQLite.")
    parser.add_argument("--filter", type=str,
                        help="SQL условие для фильтрации данных (например 'latitude > 30').")
    parser.add_argument("--map", action='store_true',
                        help="Создать карту по выбранным данным.")
    
    args = parser.parse_args()

    # Проверка и создание CSV файла при необходимости
    ensure_csv_exists(args.csv)

    # Загрузка данных из CSV файла
    data = load_data(args.csv)

    # Создание или обновление базы данных
    save_to_db(data.copy(), args.db)

    # Формирование SQL-запрос для фильтрации или выбор всех данных по умолчанию
    if args.filter:
        query_str = f"SELECT * FROM geolocations WHERE {args.filter}"
        print(f"Выполняется фильтрация по условию:\n{query_str}")
        filtered_df = query_db(args.db, query_str)
    else:
        filtered_df = data

    print("Отфильтрованные данные:")
    print(filtered_df.head())

    # Создание карты при необходимости
    if args.map:
        create_map(filtered_df)

if __name__ == "__main__":
    main()

# После выполнения можно запускать так:
# python main_new.py --help   - для просмотра всех опций.
# Например:
# python main_new.py --filter "latitude >30 and longitude <50" --map

# Также можно запускать без аргументов для автоматической обработки.

#Что добавлено:
#Модуль argparse — для обработки командных аргументов.
#Параметры запуска:
#--csv — путь к CSV файлу.
#--db — путь к базе данных.
#--filter — SQL условие для фильтрации.
#--map — флаг для генерации карты.

#Примеры использования:
# Запустить с автоматической обработкой (создаст CSV если нет и т.п.)
#python main_new.py

# Фильтровать места с широтой >30 и создать карту:
#python main_new.py --filter "latitude >30" --map

# Использовать другой CSV файл и базу данных:
#python main_new.py --csv mydata.csv --db mydatabase.db --filter "name LIKE '%Location%'" --map