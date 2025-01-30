import logging
import os
import requests
from dotenv import load_dotenv

from db import get_user_by_chat_id

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

def send_data_to_support_channel(data: dict):
    """Отправляет данные пользователя в канал поддержки."""
    user_id = data['chat_id']
    name = data.get('name')

    if not name:
        user = get_user_by_chat_id(user_id)
        name = user[2] if user else 'Не указано'  # Извлекаем имя из базы данных, если оно отсутствует в data

    phone = data.get('phone')  # Используем номер из переданных данных
    anydesk_number = data.get('anydesk_number', 'Не указан')  # Получаем номер AnyDesk, если он есть

    message = f"""
    Новая заявка в техническую поддержку:
    Сотрудник: {name}
    Телефон: {phone}
    Номер AnyDesk: {anydesk_number}
    Категория проблемы: {data['problem_type']}
    Подкатегория: {data.get('sub_problem_type', 'Не указана')}
    """

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": TARGET_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, params=params)
        logging.info("Данные успешно отправлены в канал поддержки.")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")
