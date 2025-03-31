import os
from dotenv import load_dotenv


# Загрузка переменных окружения
load_dotenv()

# Константы для состояний
NAME, CODE, PHONE, CONFIRM_PHONE, PROBLEM_TYPE, SUB_PROBLEM_TYPE, ANYDESK, TEXT_DESCRIPTION = range(8)

# Токен бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

# Настройки SMTP для отправки email
SMTP_SERVER = 'smtp.yandex.ru'
SMTP_PORT = 587
FROM_EMAIL = os.getenv("FROM_EMAIL")
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')