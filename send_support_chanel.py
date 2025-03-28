import requests

from config import TELEGRAM_TOKEN, TARGET_CHAT_ID
from database import get_user_by_chat_id
from logging_config import logging


def send_data_to_support_channel(data: dict):
    """
    Отправляет данные пользователя в канал технической поддержки.

    :param data: Словарь с данными пользователя. Обязательные ключи: chat_id, problem_type.
                 Дополнительные ключи: name, phone, anydesk_number, sub_problem_type, text_description.
    :raises: Логирует ошибку, если отправка данных не удалась.
    """
    user_id = data['chat_id']
    name = data.get('name')

    if not name:
        user = get_user_by_chat_id(user_id)
        name = user[2] if user else 'Не указано'  # Извлекаем имя из базы данных, если оно отсутствует в data

    phone = data.get('phone')  # Используем номер из переданных данных
    anydesk_number = data.get('anydesk_number', 'Не указан')  # Получаем номер AnyDesk, если он есть
    text_description = data.get('text_description', 'Не указано')

    message = (
        f"Новая заявка в техническую поддержку:\n"
        f"Сотрудник: {name}\n"
        f"Телефон: {phone}\n"
        f"Номер AnyDesk: {anydesk_number}\n"
        f"Категория проблемы: {data['problem_type']}\n"
        f"Подкатегория: {data.get('sub_problem_type', 'Не указана')}\n"
        f"Описание проблемы: {text_description}"
    )

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

