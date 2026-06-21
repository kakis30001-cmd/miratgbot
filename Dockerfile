FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы
COPY . .

# Открываем порт
EXPOSE 8080

# Запускаем приложение
CMD ["python", "main.py"]
