import sqlite3

# Путь к базе данных в томе
USERS_DB = '/data/users.db'
EMPLOYEES_DB = '/data/employees.db'


def create_user_db():
    """Создает базу данных пользователей."""
    conn = sqlite3.connect(USERS_DB)
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
    """Возвращает пользователя по chat_id."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def save_user_to_db(chat_id, name, phone):
    """Сохраняет или обновляет пользователя."""
    conn = sqlite3.connect(USERS_DB)
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
    Возвращает сотрудника по полному имени.
    Регистронезависимый поиск + поиск по частям (без отчества).
    """
    conn = sqlite3.connect(EMPLOYEES_DB)
    cursor = conn.cursor()
    
    # Приводим к верхнему регистру
    name_upper = name.upper().strip()
    
    # 1. Пробуем точное совпадение
    cursor.execute("SELECT * FROM employees WHERE full_name = ?", (name_upper,))
    result = cursor.fetchone()
    
    # 2. Если не найдено - пробуем по частям (фамилия + имя)
    if not result:
        parts = name_upper.split()
        if len(parts) >= 2:
            # Ищем по фамилии (первое слово) и имени (второе слово)
            # Это позволяет найти "ТИМОНИН РОМАН" в "ТИМОНИН РОМАН ЮРЬЕВИЧ"
            cursor.execute("""
                SELECT * FROM employees 
                WHERE full_name LIKE ? 
                AND full_name LIKE ?
            """, (f'%{parts[0]}%', f'%{parts[1]}%'))
            result = cursor.fetchone()
    
    # 3. Если всё ещё не найдено - пробуем по любому слову
    if not result:
        parts = name_upper.split()
        if len(parts) >= 1:
            for part in parts:
                cursor.execute("SELECT * FROM employees WHERE full_name LIKE ?", (f'%{part}%',))
                result = cursor.fetchone()
                if result:
                    break
    
    conn.close()
    return result


# Создаем БД при импорте
create_user_db()