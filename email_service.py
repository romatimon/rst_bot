import smtplib
from email.mime.text import MIMEText

from config import SMTP_SERVER, SMTP_PORT, FROM_EMAIL, EMAIL_PASSWORD
from logging_config import logging

def send_code_to_email(to_email, code):
    """
    Отправляет код подтверждения на указанный email.

    :param to_email: Адрес электронной почты получателя.
    :param code: Код подтверждения для отправки.
    :raises: Логирует ошибку, если отправка не удалась.
    """
    server = None  # Инициализация переменной

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(FROM_EMAIL, EMAIL_PASSWORD)

        subject = "@rostest_support_bot"
        message = f'Код подтверждения: {str(code)}'

        msg = MIMEText(message, _charset='utf-8')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email

        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        logging.info(f'Сообщение с кодом {code} отправлено на {to_email}.')

    except Exception as e:
        logging.error(f"Неожиданная ошибка при отправке сообщения: {e}")

    finally:
        if server:  # Проверяем, что server был инициализирован
            server.quit()