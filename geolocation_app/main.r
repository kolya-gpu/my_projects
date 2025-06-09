#!/usr/bin/env Rscript
# Загрузка необходимых библиотекзх
install.packages("vroom")
library(dplyr)
library(ggplot2)
library(readr)

data <- read_csv("geodata.csv")
print("Первичные данные:")
print(head(data))

# Фильтрация данных (например, выбираем записи с latitude > 40)
filtered_data <- data %>% filter(latitude > 40)
print("Отфильтрованные данные:")
print(filtered_data, n = Inf)

# Построение графика геолокационных точек
plot <- ggplot(filtered_data, aes(x = longitude, y = latitude)) +
  geom_point(color = "#00ff48", size = 3, alpha = 0.8) +
  labs(title = "Геолокационные данные", x = "Долгота", y = "Широта") +
  theme_minimal() +  # Базовая тема
  theme(
    plot.title = element_text(size = 16, face = "bold", color = "#2c3e50", hjust = 0.5), # Заголовок # nolint
    axis.title.x = element_text(size = 14, face = "bold", color = "#34495e"),
    axis.title.y = element_text(size = 14, face = "bold", color = "#34495e"),
    axis.text = element_text(size = 12, color = "#7f8c8d"),
    panel.grid.major = element_line(color = "#dfe6e9"),   # Основная сетка
    #panel.grid.minor = element_blank(),                # Мелкая сетка отключена
    panel.background = element_rect(fill = "#f5f6fa"), # Фон панели
    plot.background = element_rect(fill = "#ecf0f1")   # Фон всей области графика # nolint
  ) +
  coord_fixed(ratio = 1) +  # Зафиксировать соотношение сторон (опционально)
  scale_x_continuous(limits=c(min(filtered_data$longitude), max(filtered_data$longitude))) + # nolint
  scale_y_continuous(limits=c(min(filtered_data$latitude), max(filtered_data$latitude))) # nolint

# Сохранение графика в файл
ggsave("geolocation_plot.png", plot = plot)
