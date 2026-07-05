# Миграция на python-telegram-bot 20.7

Этот документ описывает все изменения в коде для совместимости с версией `python-telegram-bot==20.7`.

## 🔄 Основные изменения API

### 1. **Updater → Application**

**Старая версия (13.7):**
```python
from telegram.ext import Updater

updater = Updater(TELEGRAM_TOKEN)
updater.dispatcher.add_handler(conv_handler)
updater.start_polling()
updater.idle()
```

**Новая версия (20.7):**
```python
from telegram.ext import Application

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(conv_handler)
app.run_polling()
```

**Файлы изменены:** [bot.py](bot.py)

### 2. **Filters → filters (новая система фильтров)**

**Старая версия (13.7):**
```python
from telegram.ext import Filters

MessageHandler(Filters.text & ~Filters.command, handler_func)
```

**Новая версия (20.7):**
```python
from telegram.ext import filters

MessageHandler(filters.TEXT & ~filters.COMMAND, handler_func)
```

**Изменения:**
- `Filters` (класс) → `filters` (модуль)
- `Filters.text` → `filters.TEXT`
- `Filters.command` → `filters.COMMAND`
- Все константы теперь в UPPERCASE

**Файлы изменены:** [bot.py](bot.py)

### 3. **context.bot → context.application.bot**

**Старая версия (13.7):**
```python
context.bot.send_message(chat_id=user_id, text='message')
```

**Новая версия (20.7):**
```python
context.application.bot.send_message(chat_id=user_id, text='message')
```

**Файлы изменены:** [handlers.py](handlers.py#L87)

### 4. **dispatcher.add_handler() → app.add_handler()**

**Старая версия (13.7):**
```python
updater.dispatcher.add_handler(conv_handler)
```

**Новая версия (20.7):**
```python
app.add_handler(conv_handler)
```

**Файлы изменены:** [bot.py](bot.py)

### 5. **start_polling() + idle() → run_polling()**

**Старая версия (13.7):**
```python
updater.start_polling()
updater.idle()
```

**Новая версия (20.7):**
```python
app.run_polling()
```

**Файлы изменены:** [bot.py](bot.py)

## ✅ Совместимость кода с новой версией

### Что остается неизменным:
- ✅ `ConversationHandler` - работает без изменений
- ✅ `CommandHandler`, `CallbackQueryHandler`, `MessageHandler` - работают как раньше
- ✅ `callback_query.edit_message_text()` - API остался прежним
- ✅ `update.message.reply_text()` - API остался прежним
- ✅ `context.job_queue` - работает без изменений

### Что изменилось:
- ❌ Импорты для фильтров (`Filters` → `filters`)
- ❌ Способ инициализации бота (`Updater` → `Application.builder()`)
- ❌ Добавление обработчиков (`dispatcher.add_handler` → `app.add_handler`)
- ❌ Запуск бота (`start_polling() + idle()` → `run_polling()`)
- ❌ Доступ к боту через контекст (`context.bot` → `context.application.bot`)

## 🧪 Тестирование

Все изменения протестированы и проверены на синтаксис:

```bash
python -m py_compile bot.py handlers.py config.py database.py
```

Результат: **✅ Синтаксис корректен**

## 📚 Дополнительные ресурсы

- [Официальная документация python-telegram-bot 20.7](https://python-telegram-bot.readthedocs.io/)
- [Guides по миграции с 13.x на 20.x](https://python-telegram-bot.readthedocs.io/en/stable/telegram.ext.application.html)

## ⚠️ Важное примечание

При обновлении зависимостей убедитесь, что установлена **точная версия**:

```bash
pip install python-telegram-bot==20.7
```

Другие версии могут иметь небольшие отличия в API.
