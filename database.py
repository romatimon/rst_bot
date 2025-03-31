import sqlite3


def create_user_db():
    """
    Создает базу данных пользователей, если она не существует.
    Создает таблицу `users` с полями: id, chat_id, name, phone.
    """
    conn = sqlite3.connect('/data/users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id BIGINT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_user_by_chat_id(chat_id):
    """
    Возвращает информацию о пользователе по его chat_id из базы данных.

    :param chat_id: Уникальный идентификатор чата пользователя.
    :return: Кортеж с данными пользователя (id, chat_id, name, phone) или None, если пользователь не найден.
    """
    conn = sqlite3.connect('/data/users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result # (1, 1996846711, 'Роман Тимонин', '+79250411559')

def save_user_to_db(chat_id, name, phone):
    """
    Сохраняет данные пользователя в базу данных.

    Если пользователь с таким chat_id уже существует, обновляет его данные.

    :param chat_id: Уникальный идентификатор чата пользователя.
    :param name: Имя пользователя.
    :param phone: Номер телефона пользователя.
    """
    conn = sqlite3.connect('/data/users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (chat_id, name, phone) 
        VALUES (?, ?, ?) 
        ON CONFLICT(chat_id) 
        DO UPDATE SET name = excluded.name, phone = excluded.phone
    """, (chat_id, name, phone))
    conn.commit()
    conn.close()

def get_employees_db(name):
    """
    Получает информацию о сотрудниках из базы данных по полному имени.

    :param full_name: Полное имя сотрудника.
    :return: Кортеж с данными сотрудника или None, если не найден.
    """
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    
    # Выполнение запроса с использованием параметризованного SQL
    cursor.execute("SELECT * FROM employees WHERE full_name = ?", (name,))
    
    # Получение одного результата
    result = cursor.fetchone()
    conn.close()
    return result