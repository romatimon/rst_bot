import os
import logging
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Updater, Filters, MessageHandler, ConversationHandler, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv

from db import create_user_db, get_user_by_chat_id, save_user_to_db
from send_support import send_data_to_support_channel


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filemode='a',
    filename='log.log',
    encoding='utf-8'
)

# Константы для состояний
NAME, PHONE, CONFIRM_PHONE, PROBLEM_TYPE, SUB_PROBLEM_TYPE, ANYDESK = range(6)

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = Bot(TELEGRAM_TOKEN)
updater = Updater(TELEGRAM_TOKEN)


user_data = {}  # Словарь для хранения данных пользователей


def start(update: Update, context: CallbackContext) -> int:
    """Начинает разговор и проверяет, существует ли пользователь в базе данных."""
    logging.info(f"Пользователь {update.message.chat.id} начал разговор.")

    user_id = update.message.chat.id # получаем id чата пользователя
    user = get_user_by_chat_id(user_id) # проверяем, есть ли пользователь в бд, (1, 1996846711, 'Роман Тимонин', '+79250411559')

    if user:
        # Если пользователь существует, предлагаем подтвердить номер телефона
        existing_phone = user[3]  # +79250411559
        user_name = user[2]  # Роман Тимонин
        logging.info(f"Пользователь {user_id} существует. Существующий телефон: {existing_phone}")
        # Создаем кнопки для подтверждения
        keyboard = [
            [InlineKeyboardButton("Да, все верно", callback_data='confirm_yes')],
            [InlineKeyboardButton("Нет, это не тот", callback_data='confirm_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f'Здравствуйте, {user_name}! Рад Вас снова видеть! 😊 Ваш номер телефона: {existing_phone}. Верно?',
            reply_markup=reply_markup
        )

        user_data[user_id] = {'phone': existing_phone}  # Сохраняем в словарь номер телефона из бд
        return CONFIRM_PHONE
    else:
        # Новый пользователь, запрашиваем имя
        update.message.reply_text('Здравствуйте! 👋 Спасибо, что включили меня! Как Вас зовут? Напишите свое имя и фамилию:')
        return NAME
    
def end(update: Update, context: CallbackContext) -> int:
    """Завершает общение с ботом."""
    user_id = update.message.chat.id
    logging.info(f"Пользователь {user_id} завершил разговор.")
    update.message.reply_text('Благодарю Вас за общение! Если у Вас возникнут дополнительные вопросы или потребуется помощь, пожалуйста, не стесняйтесь обращаться. Мы всегда рады помочь! 😊')
    return ConversationHandler.END

def get_name(update: Update, context: CallbackContext) -> int:
    """Обрабатывает введенное имя пользователя."""
    user_id = update.message.chat.id
    name = update.message.text
    logging.info(f"Пользователь {user_id} ввел имя: {name}")

    # Сохраняем имя и chat_id в user_data
    user_data[user_id] = {'name': name, 'chat_id': user_id}  # Записываем данные в словарь

    # Запрашиваем номер телефона
    update.message.reply_text('Отлично! Теперь, пожалуйста, введите свой номер телефона в формате +7 XXXXXXXXXX (12 цифр).')
    return PHONE

def is_valid_phone(phone: str) -> bool:
    """Проверяет корректность введенного номера телефона."""
    return phone.startswith('+7') and phone[2:].isdigit() and len(phone) == 12

def get_phone(update: Update, context: CallbackContext) -> int:
    """Обрабатывает введенный номер телефона."""
    user_id = update.message.chat.id
    phone = update.message.text
    logging.info(f"Пользователь {user_id} ввел номер телефона: {phone}")

    # Проверяем корректность номера телефона
    if not is_valid_phone(phone):
        update.message.reply_text('Похоже, что номер телефона введен неправильно. Он должен быть в формате +7 XXXXXXXXXX (12 цифр). Попробуйте еще раз!')
        return PHONE  # Возвращаемся к вводу номера телефона

    # Проверяем, есть ли имя в user_data
    if user_id in user_data and 'name' in user_data[user_id]:
        name = user_data[user_id]['name']
    else:
        # Если имя отсутствует, можно запросить его или извлечь из базы данных
        user = get_user_by_chat_id(user_id)
        name = user[2] if user else 'Не указано'  # Извлекаем имя из базы данных

    # Сохраняем пользователя в базе данных
    save_user_to_db(user_id, name, phone)

    # Обновляем данные в user_data
    user_data[user_id]['phone'] = phone  # Обновляем номер в user_data

    update.message.reply_text('Благодарю Вас за информацию!')

    # Переход к выбору типа проблемы
    show_problem_type_menu(update)
    return PROBLEM_TYPE  # Возвращаем состояние выбора типа проблемы

def handle_confirmation_callback(update: Update, context: CallbackContext) -> int:
    """Обрабатывает подтверждение номера телефона пользователем."""
    query = update.callback_query # объект содержит информацию о нажатой кнопке
    query.answer() # метод отправляет ответ Telegram, подтверждая, что бот обработал нажатие кнопки. Это также закрывает всплывающее окно, если оно было открыто
    user_id = query.message.chat.id
    existing_phone = user_data[user_id]['phone']

    if query.data == 'confirm_yes':
        logging.info(f"Пользователь {user_id} подтвердил телефон: {existing_phone}.")
        # Если подтвержден номер, продолжаем к выбору типа проблемы
        show_problem_type_menu(update)
        return PROBLEM_TYPE
    elif query.data == 'confirm_no':
        logging.info(f"Пользователь {user_id} отклонил подтверждение телефона.")
        query.edit_message_text(text='Пожалуйста, введите новый номер телефона, чтобы мы могли продолжить!')
        return PHONE
    
def show_problem_type_menu(update: Update, text: str = 'В чем у Вас возникла проблема? Выберите, пожалуйста, категорию:'):
    """Отображает меню выбора типа проблемы."""
    keyboard = [
        [InlineKeyboardButton("Эл. почта 📧", callback_data='email')],
        [InlineKeyboardButton("ПО 'Синтез' 💙", callback_data='sintez')],
        [InlineKeyboardButton("Проблема с ПК 🖥️", callback_data='pc_issues')],
        [InlineKeyboardButton("Телефон ☎️", callback_data='phone')],
        [InlineKeyboardButton("Принтеры, МФУ 🖨️", callback_data='printer')],
        [InlineKeyboardButton("Удаленный доступ 🌐", callback_data='remote')],
        [InlineKeyboardButton("Другое ❓", callback_data='other')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если объект update содержит сообщение (то есть это обычное сообщение от пользователя), то бот отправляет текст с клавиатурой в ответ на это сообщение
    if hasattr(update, 'message') and update.message:
        update.message.reply_text(text, reply_markup=reply_markup)

    # Если объект update содержит обратный вызов (то есть пользователь нажал на кнопку), бот редактирует предыдущее сообщение, изменяя его текст и добавляя клавиатуру.
    elif hasattr(update, 'callback_query') and update.callback_query:
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

def show_sub_problem_type_menu(update: Update, context: CallbackContext) -> int:
    """Отображает меню выбора подкатегории проблемы."""
    user_id = update.callback_query.message.chat.id
    problem_type = user_data[user_id]['problem_type']

    sub_categories = {
        'email': [
            "Отправка/получение писем",
            "Почтовый ящик переполнен",
            "Настройка архивации",
            "Переадресация",
            "Другое"
        ],
        'sintez': [
            "Установка и настройка",
            "Ошибка при запуске",
            "Другое"
        ],
        'pc_issues': [
            "Не включается",
            "Медленная работа ПК",
            "Не работает интернет",
            "Замена периферии",
            "Другое"
        ],
        'phone': [
            "Не работает телефон",
            "Входящие/исходящие звонки",
            "Переадресация звонков",
            "Другое"
        ],
        'printer': [
            "Не печатает/ошибка при печати",
            "Проблема с подключением",
            "Замена картриджа",
            "Другое"
        ],
        'remote': [
            "Настройка удаленного доступа",
            "Не работает удаленный доступ",
            "Другое"
        ],
        'other': [
            "Выдача доступа",
            "Общие вопросы",
            "Запросы на информацию"
        ]
    }

    keyboard = [[InlineKeyboardButton(sub, callback_data=sub)] for sub in sub_categories.get(problem_type, [])]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text('Пожалуйста, выберите подкатегорию проблемы:', reply_markup=reply_markup)
    return SUB_PROBLEM_TYPE

def handle_back(update: Update, context: CallbackContext) -> int:
    """Обрабатывает нажатие кнопки 'Назад' в меню выбора проблемы."""
    query = update.callback_query
    user_id = query.message.chat.id

    # Удаляем данные по текущему выбору
    user_data[user_id].pop('problem_type', None)
    user_data[user_id].pop('sub_problem_type', None)

    # Возврат к выбору
    show_problem_type_menu(update)
    return PROBLEM_TYPE

def get_problem_type(update: Update, context: CallbackContext) -> int:
    """Обрабатывает выбор типа проблемы пользователем."""
    query = update.callback_query
    query.answer()
    user_id = query.message.chat.id
    problem_type = query.data
    user_data[user_id]['problem_type'] = problem_type

    show_sub_problem_type_menu(update, context)
    return SUB_PROBLEM_TYPE

def get_sub_problem_type(update: Update, context: CallbackContext) -> int:
    """Обрабатывает выбор подкатегории проблемы пользователем и отправляет данные в техподдержку."""
    query = update.callback_query
    query.answer()
    user_id = query.message.chat.id
    sub_problem_type = query.data
    user_data[user_id]['sub_problem_type'] = sub_problem_type

    if sub_problem_type in ["Настройка удаленного доступа", "Не работает удаленный доступ"]:
        query.edit_message_text(text='Пожалуйста, введите ваш 9-значный код AnyDesk:')
        return ANYDESK

    # Добавляем chat_id в данные, которые будут отправлены
    user_data[user_id]['chat_id'] = user_id  # Убедитесь, что chat_id сохранен

    send_data_to_support_channel(user_data[user_id])
    query.edit_message_text(text='Спасибо! 🙏 Ваши данные успешно отправлены в техподдержку. Мои коллеги скоро свяжутся с Вами для решения проблемы. 😊')
    return ConversationHandler.END

# Создание базы данных пользователей
create_user_db()

def get_anydesk_number(update: Update, context: CallbackContext) -> int:
    """Обрабатывает введенный номер AnyDesk."""
    user_id = update.message.chat.id
    anydesk_number = update.message.text
    logging.info(f"Пользователь {user_id} ввел номер AnyDesk: {anydesk_number}")

    user_data[user_id]['anydesk_number'] = anydesk_number
    user_data[user_id]['chat_id'] = user_id

    send_data_to_support_channel(user_data[user_id])
    update.message.reply_text('Спасибо! 🙏 Ваши данные успешно отправлены в техподдержку. Мои коллеги скоро свяжутся с Вами для решения проблемы. 😊')
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
        PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
        CONFIRM_PHONE: [CallbackQueryHandler(handle_confirmation_callback)],
        PROBLEM_TYPE: [CallbackQueryHandler(get_problem_type)],
        SUB_PROBLEM_TYPE: [
            CallbackQueryHandler(get_sub_problem_type, pattern='^(?!back_to_menu).*'),
            CallbackQueryHandler(handle_back, pattern='^back_to_menu$')
        ],
        ANYDESK: [MessageHandler(Filters.text & ~Filters.command, get_anydesk_number)],  # Новое состояние
    },
    fallbacks=[CommandHandler('end', end)],
)

# Добавляем обработчик для команд и состояний
updater.dispatcher.add_handler(conv_handler)

# Запуск бота
if __name__ == '__main__':
    logging.info("Бот запущен.")
    updater.start_polling()
    updater.idle()