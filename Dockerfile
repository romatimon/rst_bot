FROM python:3.9

WORKDIR /app

# Копируем requirements.txt первым (для кэширования)
COPY requirements.txt .

# Устанавливаем зависимости с официального PyPI
# Увеличиваем таймауты и добавляем повторы для обхода блокировок
RUN pip install --no-cache-dir \
    --default-timeout=100 \
    --retries=5 \
    -r requirements.txt

# Копируем остальной код
COPY . .

CMD ["python", "bot.py"]