import logging
import sys
import os

# Создаем папку для логов если её нет
log_dir = '/data'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# Настройка логирования И в файл, И в консоль
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),  # В консоль
        logging.FileHandler('/data/log.log', encoding='utf-8')  # В файл
    ]
)