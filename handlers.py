import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackContext

from config import NAME, CODE, PHONE, CONFIRM_PHONE, PROBLEM_TYPE, SUB_PROBLEM_TYPE, ANYDESK, TEXT_DESCRIPTION
from database import create_user_db, get_user_by_chat_id, save_user_to_db, get_employees_db
from email_service import send_code_to_email
from send_support_chanel import send_data_to_support_channel
from logging_config import logging


create_user_db() # Создаем базу данных при импорте модуля

user_data = {}  # Словарь для хранения временных данных пользователя


def get_first_name_from_full(full_name):
    """
    Из полного ФИО возвращает только имя.
    Пример: "ТИМОНИН РОМАН ЮРЬЕВИЧ" → "Роман"
    """
    if not full_name:
        return None
    
    parts = full_name.strip().split()
    
    if len(parts) >= 3:
        return parts[1].title()  # Фамилия Имя Отчество → Имя
    elif len(parts) == 2:
        return parts[1].title()  # Фамилия Имя → Имя
    else:
        return full_name.title()


async def start(update: Update, context: CallbackContext) -> int:
    """
    Начинает разговор с пользователем и проверяет, существует ли он в базе данных.

    Если пользователь существует, предлагает подтвердить номер телефона.
    Если пользователь новый, запрашивает имя.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние CONFIRM_PHONE, если пользователь существует, иначе NAME.
    """
    user_id = update.message.chat.id
    logging.info(f"Пользователь {user_id} начал разговор.")

    user = get_user_by_chat_id(user_id)

    if user:
        # Если пользователь существует, предлагаем подтвердить номер телефона
        existing_phone = user[3]  # +79250411559
        user_name = user[2]  # Роман Тимонин

        logging.info(f"Пользователь {user_id} существует. Существующий телефон: {existing_phone}")
        
        # Создаем кнопки для подтверждения
        keyboard = [
            [InlineKeyboardButton("Да, все верно", callback_data='confirm_yes')],
            [InlineKeyboardButton("Нет, не верно", callback_data='confirm_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f'Здравствуйте, {user_name}. Вы обратились в службу технической поддержки АО «РОСТЕСТ». '
            f'Ваш номер телефона: {existing_phone}. Верно?',
            reply_markup=reply_markup
        )

        user_data[user_id] = {'phone': existing_phone}  # Сохраняем в словарь номер телефона из бд
        return CONFIRM_PHONE
    
    else:
        # Новый пользователь, запрашиваем имя
        await update.message.reply_text('Добрый день! Вы обратились в службу технической поддержки АО «РОСТЕСТ». '
                                  'Пожалуйста, напишите ваше полное имя и фамилию:')
        # Сохраняем задание для возможности его отмены
        job = context.job_queue.run_once(send_notification, 300, context=user_id, name=str(user_id))
        user_data[user_id] = {'job': job}  # Сохраняем ссылку на задание
        return NAME
    

def send_notification(context: CallbackContext) -> None:
    """
    Отправляет уведомление пользователю с предложением завершить разговор.

    :param context: Объект CallbackContext из python-telegram-bot.
    """
    user_id = context.job.context
    context.application.bot.send_message(chat_id=user_id, text='Если Вы не хотите продолжать, введите /end для завершения разговора.')


async def end(update: Update, context: CallbackContext) -> int:
    """
    Завершает общение с ботом и очищает временные данные пользователя.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние ConversationHandler.END.
    """
    user_id = update.message.chat.id
    logging.info(f"Пользователь {user_id} завершил разговор.")

    if user_id in user_data:
        del user_data[user_id]

    await update.message.reply_text('Спасибо за обращение! Если у Вас возникнут дополнительные вопросы или потребуется помощь, пожалуйста, '
                              'запустите бот заново из меню или введите /start.')
    return ConversationHandler.END


async def handle_user_name_input(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает введенное имя пользователя.

    Проверяет, является ли пользователь сотрудником, и отправляет код подтверждения на email.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние CODE, если имя корректно, иначе NAME или ConversationHandler.END.
    """
    user_id = update.message.chat.id
    name = update.message.text
    logging.info(f"Пользователь {user_id} ввел имя: {name}")

    # Проверка на команду "end"
    if name.lower() == 'end':
        return await end(update, context)

    # Отменяем задачу отправки уведомления, если пользователь ввел имя
    if user_id in user_data and 'job' in user_data[user_id]:
        # Отменяем явно сохраненное задание
        user_data[user_id]['job'].schedule_removal()

    name_parts = name.split()

    if len(name_parts) < 2:
        await update.message.reply_text('Пожалуйста, напишите полное имя, а затем фамилию:')
        return NAME

    name_upper = name.upper()

   # Получаем список сотрудников из базы данных
    employees = get_employees_db(name_upper)

    if not employees:
        await update.message.reply_text('Пожалуйста, проверьте и введите свои данные правильно. Всего доброго.')
        logging.warning(f"Пользователь {user_id} не найден в списке сотрудников.")
        return ConversationHandler.END
    
    email = employees[2]
    
    logging.info(f"Пользователь {user_id} найден в списке сотрудников.")

    # Генерация кода подтверждения
    code = random.randint(1000, 9999)

    # Получаем полное имя из БД сотрудников
    full_name_from_db = employees[1]  # "ТИМОНИН РОМАН ЮРЬЕВИЧ"
    first_name = get_first_name_from_full(full_name_from_db)  # "Роман"

    user_data[user_id] = {'name': first_name, 'chat_id': user_id, 'code': code}

    # Отправка кода на электронную почту
    send_code_to_email(email, code)

    await update.message.reply_text('На Вашу электронную почту был направлен 4-значный код. Пожалуйста, введите его:')
    return CODE

 
def is_valid_code(code: str) -> bool:
    """
    Проверяет корректность введенного кода подтверждения.

    :param code: Введенный пользователем код.
    :return: True, если код корректен (4 цифры), иначе False.
    """
    return code.isdigit() and len(code) == 4   


async def code_verification(update: Update, context: CallbackContext) -> int:
    """
    Проверяет введенный код подтверждения.

    Если код верный, запрашивает номер телефона.
    Если код неверный, просит ввести его снова.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние PHONE, если код верный, иначе CODE.
    """
    user_id = update.message.chat.id
    from_user_code = update.message.text
    logging.info(f"Пользователь {user_id} ввел код: {from_user_code}")
    
    if not is_valid_code(from_user_code):
        await update.message.reply_text('Пожалуйста, введите корректный код (4 цифры):')
        return CODE
    
    user_code = int(from_user_code)

    if user_data[user_id]['code'] != user_code:
        await update.message.reply_text('К сожалению, введенный вами код неверный. Пожалуйста, проверьте его и введите снова.')
        logging.warning(f"Пользователь {user_id} ввел неверный код.")
        return CODE
    
    await update.message.reply_text('Для продолжения введите номер телефона в формате +7 XXXXXXXXXX (12 цифр):')
    return PHONE


def is_valid_phone(phone: str) -> bool:
    """
    Проверяет корректность введенного номера телефона.

    :param phone: Введенный номер телефона.
    :return: True, если номер корректен (формат +7XXXXXXXXXX), иначе False.
    """
    return phone.startswith('+7') and phone[2:].isdigit() and len(phone) == 12


async def get_phone(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает введенный номер телефона.

    Сохраняет номер телефона в базе данных и переходит к выбору типа проблемы.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние PROBLEM_TYPE.
    """
    user_id = update.message.chat.id
    phone = update.message.text
    logging.info(f"Пользователь {user_id} ввел номер телефона: {phone}")

    # Проверяем корректность номера телефона
    if not is_valid_phone(phone):
        await update.message.reply_text('Похоже, что номер телефона введен неправильно. Он должен быть в формате +7 XXXXXXXXXX (12 цифр). Попробуйте еще раз.')
        logging.warning(f"Пользователь {user_id} ввел некорректный номер телефона.")
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

    await update.message.reply_text('Благодарю Вас за информацию!')
    logging.info(f"Пользователь {user_id} успешно сохранил номер телефона.")

    # Переход к выбору типа проблемы
    await show_problem_type_menu(update)
    return PROBLEM_TYPE  # Возвращаем состояние выбора типа проблемы


async def handle_confirmation_callback(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает подтверждение номера телефона пользователем.

    Если номер подтвержден, переходит к выбору типа проблемы.
    Если номер не подтвержден, запрашивает новый номер.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние PROBLEM_TYPE, если номер подтвержден, иначе PHONE.
    """
    query = update.callback_query # объект содержит информацию о нажатой кнопке
    await query.answer() # метод отправляет ответ Telegram, подтверждая, что бот обработал нажатие кнопки. Это также закрывает всплывающее окно, если оно было открыто
    user_id = query.message.chat.id
    existing_phone = user_data[user_id]['phone']

    if query.data == 'confirm_yes':
        logging.info(f"Пользователь {user_id} подтвердил телефон: {existing_phone}.")
        # Если подтвержден номер, продолжаем к выбору типа проблемы
        await show_problem_type_menu(update)
        return PROBLEM_TYPE
    
    elif query.data == 'confirm_no':
        logging.info(f"Пользователь {user_id} отклонил подтверждение телефона.")
        await query.edit_message_text(text='Пожалуйста, введите номер телефона для связи, в формате +7 XXXXXXXXXX (12 цифр).')
        return PHONE
    

async def show_problem_type_menu(update: Update, text: str = 'Выберите категорию вашей проблемы:'):
    """
    Отображает меню выбора типа проблемы.

    :param update: Объект Update из python-telegram-bot.
    :param text: Текст сообщения с меню.
    """
    keyboard = [
        [InlineKeyboardButton("Эл. почта 📧", callback_data='email')],
        [InlineKeyboardButton("ПО 'Синтез' 💙", callback_data='sintez')],
        [InlineKeyboardButton("Проблема с ПК 🖥️", callback_data='pc')],
        [InlineKeyboardButton("Телефон ☎️", callback_data='phone')],
        [InlineKeyboardButton("Принтеры, МФУ 🖨️", callback_data='printer')],
        [InlineKeyboardButton("Удаленный доступ 🌐", callback_data='remote')],
        [InlineKeyboardButton("Другое ❓", callback_data='other')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если объект update содержит сообщение (то есть это обычное сообщение от пользователя), то бот отправляет текст с клавиатурой в ответ на это сообщение
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)

    # Если объект update содержит обратный вызов (то есть пользователь нажал на кнопку), бот редактирует предыдущее сообщение, изменяя его текст и добавляя клавиатуру.
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def show_sub_problem_type_menu(update: Update, context: CallbackContext) -> int:
    """
    Отображает меню выбора подкатегории проблемы.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние SUB_PROBLEM_TYPE.
    """
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
        'pc': [
            "Не включается",
            "Медленная работа ПК",
            "Не работает интернет",
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
            "Замена картриджа",
            "Другое"
        ],
        'remote': [
            "Настройка удаленного доступа",
            "Не работает удаленный доступ",
            "Другое"
        ],
        'other': [
            "Выдача доступа"
        ]
    }

    keyboard = [[InlineKeyboardButton(sub, callback_data=sub)] for sub in sub_categories.get(problem_type, [])]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text('Выберите подкатегорию проблемы:', reply_markup=reply_markup)

    # Сохраняем задание для возможности его отмены
    job = context.job_queue.run_once(send_notification, 300, context=user_id, name=str(user_id))
    user_data[user_id]['job'] = job  # Обновляем сохраненное задание
    return SUB_PROBLEM_TYPE


async def handle_back(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает нажатие кнопки "Назад" в меню выбора проблемы.

    Возвращает пользователя к выбору типа проблемы.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние PROBLEM_TYPE.
    """
    query = update.callback_query
    user_id = query.message.chat.id

    # Удаляем данные по текущему выбору
    user_data[user_id].pop('problem_type', None)
    user_data[user_id].pop('sub_problem_type', None)

    # Возврат к выбору
    await show_problem_type_menu(update)
    return PROBLEM_TYPE


async def get_problem_type(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает выбор типа проблемы пользователем.

    Переходит к выбору подкатегории проблемы.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние SUB_PROBLEM_TYPE.
    """
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id
    problem_type = query.data
    user_data[user_id]['problem_type'] = problem_type

    logging.info(f"Пользователь {user_id} выбрал тип проблемы: {problem_type}")

    await show_sub_problem_type_menu(update, context)
    return SUB_PROBLEM_TYPE


async def get_sub_problem_type(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает выбор подкатегории проблемы пользователем.

    Если выбрана подкатегория, связанная с удаленным доступом, запрашивает номер AnyDesk.
    Если выбрана подкатегория "Другое", запрашивает текстовое описание проблемы.
    Иначе отправляет данные в техподдержку.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние ANYDESK, TEXT_DESCRIPTION или ConversationHandler.END.
    """
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id
    sub_problem_type = query.data
    user_data[user_id]['sub_problem_type'] = sub_problem_type

    logging.info(f"Пользователь {user_id} выбрал подкатегорию проблемы: {sub_problem_type}")

    if sub_problem_type in ["Настройка удаленного доступа", "Не работает удаленный доступ"]:
        await query.edit_message_text(text='Пожалуйста, введите Ваш код AnyDesk (9 или 10 символов после фразы «Это рабочее место»):')
        return ANYDESK
    
    elif sub_problem_type in ['Другое', 'Выдача доступа']:
        await query.edit_message_text(text='Пожалуйста, опишите проблему в свободной форме:')
        return TEXT_DESCRIPTION

    # Добавляем chat_id в данные, которые будут отправлены
    user_data[user_id]['chat_id'] = user_id  # Убедитесь, что chat_id сохранен

    send_data_to_support_channel(user_data[user_id])

    del user_data[user_id]

    await query.edit_message_text(text='Данные успешно отправлены в техническую поддержку. '
                            'В ближайшее время коллеги свяжутся с Вами для решения проблемы.')
    return ConversationHandler.END


async def get_anydesk_number(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает введенный номер AnyDesk.

    Сохраняет номер AnyDesk и отправляет данные в техподдержку.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние ConversationHandler.END.
    """
    user_id = update.message.chat.id
    anydesk_number = update.message.text
    logging.info(f"Пользователь {user_id} ввел номер AnyDesk: {anydesk_number}")

    user_data[user_id]['anydesk_number'] = anydesk_number
    user_data[user_id]['chat_id'] = user_id

    send_data_to_support_channel(user_data[user_id])

    del user_data[user_id]

    await update.message.reply_text('Данные успешно отправлены в техническую поддержку. '
                              'В ближайшее время коллеги свяжутся с Вами для решения проблемы.')
    return ConversationHandler.END


async def handle_text_description(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает введенное текстовое описание проблемы.

    Сохраняет описание и отправляет данные в техподдержку.

    :param update: Объект Update из python-telegram-bot.
    :param context: Объект CallbackContext из python-telegram-bot.
    :return: Состояние ConversationHandler.END.
    """
    user_id = update.message.chat.id
    text_description = update.message.text
    logging.info(f"Пользователь {user_id} ввел описание проблемы: {text_description}")

    user_data[user_id]['text_description'] = text_description
    user_data[user_id]['chat_id'] = user_id

    send_data_to_support_channel(user_data[user_id])

    del user_data[user_id]
    
    await update.message.reply_text('Данные успешно отправлены в техническую поддержку. '
                              'В ближайшее время коллеги свяжутся с Вами для решения проблемы.')
    return ConversationHandler.END
    