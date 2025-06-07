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
print(filtered_data)

# Построение графика геолокационных точек
plot <- ggplot(filtered_data, aes(x = longitude, y = latitude)) +
  geom_point(color = "blue") +
  labs(title = "Геолокационные данные", x = "Долгота", y = "Широта") +
  theme_minimal()

# Сохранение графика в файл
ggsave("geolocation_plot.png", plot = plot)
