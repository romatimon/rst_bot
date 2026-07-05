import os

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from handlers import (
    handle_back,
    start,
    end,
    handle_user_name_input,
    code_verification,
    get_phone,
    handle_confirmation_callback,
    get_problem_type,
    get_sub_problem_type,
    get_anydesk_number,
    handle_text_description,
)

from config import TELEGRAM_TOKEN, NAME, CODE, PHONE, CONFIRM_PHONE, PROBLEM_TYPE, SUB_PROBLEM_TYPE, ANYDESK, TEXT_DESCRIPTION
from logging_config import logging


def main():
    """
    Запускает Telegram-бота с использованием ConversationHandler.
    Бот обрабатывает команду /start и управляет диалогом с пользователем через состояния.
    """
    # Создаем приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_name_input)],
            CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, code_verification)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CONFIRM_PHONE: [CallbackQueryHandler(handle_confirmation_callback)],
            PROBLEM_TYPE: [CallbackQueryHandler(get_problem_type)],
            SUB_PROBLEM_TYPE: [
                CallbackQueryHandler(get_sub_problem_type, pattern='^(?!back_to_menu).*'),
                CallbackQueryHandler(handle_back, pattern='^back_to_menu$')
            ],
            ANYDESK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_anydesk_number)],
            TEXT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_description)],
        },
        fallbacks=[CommandHandler('end', end)],
    )

    app.add_handler(conv_handler)

    # Запуск бота
    try:
        logging.info("Запуск бота...")
        app.run_polling()
    except Exception as e:
        logging.error("Ошибка при запуске бота: %s", e)
    finally:
        logging.info("Бот завершил работу.")


if __name__ == '__main__':
    main()