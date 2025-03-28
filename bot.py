from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, Filters, MessageHandler

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
    updater = Updater(TELEGRAM_TOKEN)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, handle_user_name_input)],
            CODE: [MessageHandler(Filters.text & ~Filters.command, code_verification)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
            CONFIRM_PHONE: [CallbackQueryHandler(handle_confirmation_callback)],
            PROBLEM_TYPE: [CallbackQueryHandler(get_problem_type)],
            SUB_PROBLEM_TYPE: [
                CallbackQueryHandler(get_sub_problem_type, pattern='^(?!back_to_menu).*'),
                CallbackQueryHandler(handle_back, pattern='^back_to_menu$')
            ],
            ANYDESK: [MessageHandler(Filters.text & ~Filters.command, get_anydesk_number)],
            TEXT_DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, handle_text_description)],
        },
        fallbacks=[CommandHandler('end', end)],
    )

    updater.dispatcher.add_handler(conv_handler)

    # Запуск бота
    try:
        logging.info("Запуск бота...")
        updater.start_polling()
        logging.info("Бот работает.")
        updater.idle()
    except Exception as e:
        logging.error("Ошибка при запуске бота: %s", e)
    finally:
        logging.info("Бот завершил работу.")


if __name__ == '__main__':
    main()





