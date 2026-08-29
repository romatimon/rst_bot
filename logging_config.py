import logging
import sys
import os
from config import LOG_DIR

# Создаем папку для логов если её нет
os.makedirs(LOG_DIR, exist_ok=True)

# Настройка логирования и в файл, и в консоль
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),  # В консоль
        logging.FileHandler(os.path.join(LOG_DIR, 'bot.log'), encoding='utf-8')  # В файл
    ]
)