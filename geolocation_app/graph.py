# Импорт необходимых библиотек
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Загрузка данных
data = pd.read_csv("geodata.csv")
print("Первичные данные:")
print(data.head())

# Фильтрация данных (например, выбираем записи с latitude > 30)
filtered_data = data[data['latitude'] > 30]
print("Отфильтрованные данные:")
print(filtered_data)

# Настройка стилей для графика
sns.set_theme(style="whitegrid")

# Построение графика геолокационных точек
plt.figure(figsize=(12, 12))
ax = sns.scatterplot(
    data=filtered_data,
    x='longitude',
    y='latitude',
    color='#00ff48',
    s=100,  # Размер точек (аналог size=3 в ggplot2, масштабируем)
    alpha=0.8
)

# Настройка заголовка и подписей осей
ax.set_title("Геолокационные данные", fontsize=16, fontweight='bold', color="#3F3D70", loc='center')
ax.set_xlabel("Долгота", fontsize=14, fontweight='bold', color="#3F3D70")
ax.set_ylabel("Широта", fontsize=14, fontweight='bold', color="#3F3D70")

# Настройка текста осей
ax.tick_params(axis='both', which='major', labelsize=12, colors="#7f8c8d")

# Установка границ по данным
ax.set_xlim(filtered_data['longitude'].min(), filtered_data['longitude'].max())
ax.set_ylim(filtered_data['latitude'].min(), filtered_data['latitude'].max())

# Настройка фона и сетки
ax.set_facecolor("#3F3D70")
plt.gcf().set_facecolor("#FFFFFF")
sns.despine()

# Зафиксировать соотношение сторон (опционально)
ax.set_aspect('equal', adjustable='box')

# Сохранение графика в файл
plt.tight_layout()
plt.savefig("geolocation_plot(1).png")
plt.show()