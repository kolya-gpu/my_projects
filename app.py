#!/usr/bin/env python
import pandas as pd
import sqlite3
import folium

def load_data(csv_file):
    """Загружает данные из CSV-файла"""
    return pd.read_csv(csv_file)

def save_to_db(df, db_file):
    """Сохраняет данные в SQLite-базу"""
    conn = sqlite3.connect(db_file)
    df.to_sql('geolocations', conn, if_exists='replace', index=False)
    conn.close()

def query_db(db_file, query):
    """Выполняет SQL-запрос и возвращает результат в виде DataFrame"""
    conn = sqlite3.connect(db_file)
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result

def create_map(df, output_html='map.html'):
    """Создаёт HTML-карту с маркерами для каждой локации"""
    if df.empty:
        print("Нет данных для отображения карты.")
        return
    avg_lat = df['latitude'].mean()
    avg_lon = df['longitude'].mean()
    geo_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=5)
    for idx, row in df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=row.get('name', 'Location')
        ).add_to(geo_map)
    geo_map.save(output_html)
    print("Карта сохранена в", output_html)

def main():
    csv_file = "geodata.csv"          # CSV-файл с данными (ожидается наличие столбцов: id, name, latitude, longitude, timestamp)
    db_file = "geolocations.db"       # Файл SQLite базы данных
    # Загрузка данных
    data = load_data(csv_file)
    print("Первичные данные:")
    print(data.head())

    # Сохранение данных в БД
    save_to_db(data, db_file)

    # Пример SQL-запроса: выбор локаций с широтой больше 40
    query = "SELECT * FROM geolocations WHERE latitude > 40"
    filtered = query_db(db_file, query)
    print("\nОтфильтрованные данные:")
    print(filtered)

    # Создание карты по отфильтрованным данным
    create_map(filtered)

if __name__ == '__main__':
    main()
