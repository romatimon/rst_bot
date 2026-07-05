import os
from dotenv import load_dotenv


# Загрузка переменных окружения
load_dotenv()

# Константы для состояний
NAME, CODE, PHONE, CONFIRM_PHONE, PROBLEM_TYPE, SUB_PROBLEM_TYPE, ANYDESK, TEXT_DESCRIPTION = range(8)

# Токен бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("Ошибка: переменная окружения 'TELEGRAM_TOKEN' не установлена")

TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')
if not TARGET_CHAT_ID:
    raise ValueError("Ошибка: переменная окружения 'TARGET_CHAT_ID' не установлена")

# Настройки SMTP для отправки email
SMTP_SERVER = 'smtp.yandex.ru'
SMTP_PORT = 587
FROM_EMAIL = os.getenv("FROM_EMAIL")
if not FROM_EMAIL:
    raise ValueError("Ошибка: переменная окружения 'FROM_EMAIL' не установлена")

EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
if not EMAIL_PASSWORD:
    raise ValueError("Ошибка: переменная окружения 'EMAIL_PASSWORD' не установлена")

# Пути к базам данных (поддержка локальной разработки и Docker)
if os.path.exists('/data'):
    # В контейнере Docker используется /data
    USERS_DB_PATH = '/data/users.db'
    EMPLOYEES_DB_PATH = '/data/employees.db'
    LOG_DIR = '/data'
else:
    # Для локальной разработки используется .data в корне проекта
    USERS_DB_PATH = os.path.join(os.path.dirname(__file__), '.data', 'users.db')
    EMPLOYEES_DB_PATH = os.path.join(os.path.dirname(__file__), '.data', 'employees.db')
    LOG_DIR = os.path.join(os.path.dirname(__file__), '.data')