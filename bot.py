import telebot
from telebot import types
import logging
import os
from config import BOT_TOKEN
from database import db_manager
from registration import registration_manager
from sqlite_backup import sqlite_backup_manager
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения состояния пользователей
user_states = {}


class UserState:
    """Класс для управления состоянием пользователя"""
    def __init__(self):
        self.current_state = None
        self.registration_data = {}
        self.current_table = None
        self.current_step = None


def get_user_state(user_id: int) -> UserState:
    """Получение состояния пользователя"""
    if user_id not in user_states:
        user_states[user_id] = UserState()
        logger.info(f"Создано новое состояние для пользователя {user_id}")
    else:
        logger.info(f"Получено существующее состояние для пользователя {user_id}: current_state={user_states[user_id].current_state}, current_step={user_states[user_id].current_step}")
    return user_states[user_id]


@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    user_state.current_state = None
    user_state.registration_data.clear()
    
    welcome_text = (
        "👋 Добро пожаловать в бот регистрации на питание!\n\n"
        "Я помогу вам зарегистрироваться для постановки на питание в столовой.\n\n"
        "Доступные команды:\n"
        "/start - Главное меню\n"
        "/register - Регистрация на питание\n"
        "/tables - Просмотр таблиц базы данных\n"
        "/help - Справка\n"
    )
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Регистрация"))
    markup.add(types.KeyboardButton("📊 Таблицы БД"))
    markup.add(types.KeyboardButton("❓ Справка"))
    
    bot.reply_to(message, welcome_text, reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработчик команды /help"""
    help_text = (
        "📋 Справка по использованию бота:\n\n"
        "🔹 <b>Регистрация на питание</b>\n"
        "Используйте кнопку '📝 Регистрация' или команду /register\n\n"
        "🔹 <b>Просмотр таблиц</b>\n"
        "Используйте кнопку '📊 Таблицы БД' или команду /tables\n\n"
        "🔹 <b>Отмена операции</b>\n"
        "Используйте команду /cancel для отмены текущей операции\n\n"
        "🔹 <b>Главное меню</b>\n"
        "Используйте команду /start для возврата в главное меню"
    )
    
    bot.reply_to(message, help_text, parse_mode='HTML')





@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    """Обработчик команды /cancel"""
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    user_state.current_state = None
    user_state.registration_data.clear()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Регистрация"))
    markup.add(types.KeyboardButton("📊 Таблицы БД"))
    markup.add(types.KeyboardButton("❓ Справка"))
    
    bot.reply_to(message, "❌ Операция отменена. Выберите действие:", reply_markup=markup)


@bot.message_handler(commands=['register'])
def register_command(message):
    """Обработчик команды /register"""
    start_registration(message)


@bot.message_handler(commands=['tables'])
def tables_command(message):
    """Обработчик команды /tables"""
    show_tables(message)


def start_registration(message):
    """Начало процесса регистрации"""
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    user_state.current_state = "registration"
    user_state.current_step = "start"
    
    # Запускаем процесс регистрации
    step_result, text, markup = registration_manager.step_start(message, user_state)
    
    if step_result == 'error':
        bot.reply_to(message, text, parse_mode='HTML')
        return
    
    bot.reply_to(message, text, parse_mode='HTML', reply_markup=markup)


def show_tables(message):
    """Показать список таблиц базы данных"""
    try:
        tables = db_manager.get_tables()
        
        if not tables:
            bot.reply_to(message, "📭 В базе данных нет таблиц.")
            return
        
        markup = types.InlineKeyboardMarkup()
        for table in tables:
            markup.add(types.InlineKeyboardButton(
                f"📋 {table}",
                callback_data=f"table_{table}"
            ))
        
        mode_text = "🔄 Демо-режим" if db_manager.demo_mode else "✅ Режим БД"
        bot.reply_to(
            message,
            f"📊 <b>Таблицы в базе данных:</b>\n\n"
            f"Режим работы: {mode_text}\n"
            f"Найдено таблиц: {len(tables)}\n"
            f"Выберите таблицу для просмотра:",
            parse_mode='HTML',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении таблиц: {e}")
        bot.reply_to(message, "❌ Ошибка при подключении к базе данных.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('table_'))
def handle_table_selection(call):
    """Обработчик выбора таблицы"""
    table_name = call.data.replace('table_', '')
    
    try:
        table_info = db_manager.get_table_info(table_name)
        
        # Формируем информацию о структуре таблицы
        structure_text = "📋 <b>Структура таблицы:</b>\n"
        for column in table_info['structure']:
            structure_text += f"• <b>{column['Field']}</b> - {column['Type']}"
            if column['Null'] == 'NO':
                structure_text += " (NOT NULL)"
            if column['Key'] == 'PRI':
                structure_text += " (PRIMARY KEY)"
            structure_text += "\n"
        
        # Формируем информацию о данных
        data_text = ""
        if table_info['sample_data']:
            data_text = "\n📄 <b>Пример данных:</b>\n"
            for row in table_info['sample_data'][:3]:  # Показываем только первые 3 записи
                data_text += f"• {', '.join([f'{k}: {v}' for k, v in row.items()])}\n"
        
        full_text = (
            f"📊 <b>Таблица: {table_name}</b>\n\n"
            f"Количество записей: {table_info['row_count']}\n\n"
            f"{structure_text}"
            f"{data_text}"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Показать данные", callback_data=f"data_{table_name}"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад к таблицам", callback_data="back_to_tables"))
        
        bot.edit_message_text(
            full_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации о таблице {table_name}: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при получении информации о таблице")


@bot.callback_query_handler(func=lambda call: call.data.startswith('data_'))
def handle_data_view(call):
    """Обработчик просмотра данных таблицы"""
    table_name = call.data.replace('data_', '')
    
    try:
        data = db_manager.get_table_data(table_name, 10)
        
        if not data:
            bot.answer_callback_query(call.id, "📭 Таблица пуста")
            return
        
        data_text = f"📄 <b>Данные таблицы {table_name}:</b>\n\n"
        for i, row in enumerate(data, 1):
            data_text += f"<b>{i}.</b> "
            data_text += ", ".join([f"{k}: {v}" for k, v in row.items()])
            data_text += "\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад к структуре", callback_data=f"table_{table_name}"))
        markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        
        bot.edit_message_text(
            data_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных таблицы {table_name}: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при получении данных")


@bot.callback_query_handler(func=lambda call: call.data == "back_to_tables")
def handle_back_to_tables(call):
    """Обработчик возврата к списку таблиц"""
    show_tables(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def handle_main_menu(call):
    """Обработчик возврата в главное меню"""
    start_command(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "registration_coming_soon")
def handle_registration_coming_soon(call):
    """Обработчик заглушки регистрации"""
    bot.answer_callback_query(call.id, "🔜 Функция будет доступна в ближайшее время!")


@bot.message_handler(func=lambda message: message.text == "📝 Регистрация")
def handle_registration_button(message):
    """Обработчик кнопки регистрации"""
    start_registration(message)


@bot.message_handler(func=lambda message: message.text == "📊 Таблицы БД")
def handle_tables_button(message):
    """Обработчик кнопки таблиц"""
    show_tables(message)


@bot.message_handler(func=lambda message: message.text == "❓ Справка")
def handle_help_button(message):
    """Обработчик кнопки справки"""
    help_command(message)


@bot.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    """Обработчик неизвестных сообщений"""
    try:
        logger.info(f"Получено сообщение: '{message.text}' от пользователя {message.from_user.id}")
        user_state = get_user_state(message.from_user.id)
        
        logger.info(f"Состояние пользователя: current_state={user_state.current_state}, current_step={user_state.current_step}")
        
        if user_state.current_state == "registration":
            # Обработка шагов регистрации
            logger.info(f"Обрабатываем шаг регистрации: {user_state.current_step}")
            step_result, text, markup = registration_manager.process_step(message, user_state)
            logger.info(f"Результат обработки шага: {step_result}")
            
            if step_result == 'cancel':
                # Отмена регистрации - возврат в главное меню
                user_state.current_state = None
                user_state.current_step = None
                user_state.registration_data.clear()
                
                main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                main_markup.add(types.KeyboardButton("📝 Регистрация"))
                main_markup.add(types.KeyboardButton("📊 Таблицы БД"))
                main_markup.add(types.KeyboardButton("❓ Справка"))
                
                bot.reply_to(message, text, reply_markup=main_markup)
                
            elif step_result == 'success':
                # Успешное завершение регистрации
                user_state.current_state = None
                user_state.current_step = None
                user_state.registration_data.clear()
                
                bot.reply_to(message, text, parse_mode='HTML', reply_markup=markup)
                
            elif step_result == 'error':
                # Ошибка в процессе регистрации
                bot.reply_to(message, text, parse_mode='HTML')
                
            else:
                # Продолжение регистрации
                logger.info(f"Продолжение регистрации, отправляем ответ пользователю")
                bot.reply_to(message, text, parse_mode='HTML', reply_markup=markup)
                
        else:
            bot.reply_to(
                message,
                "❓ Неизвестная команда. Используйте /start для получения списка доступных команд."
            )
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        try:
            bot.reply_to(message, "❌ Произошла ошибка при обработке сообщения. Попробуйте еще раз.")
        except:
            logger.error("Не удалось отправить сообщение об ошибке пользователю")


def main():
    """Главная функция запуска бота"""
    try:
        logger.info("Запуск телеграм-бота...")
        
        # Проверка подключения к базе данных
        try:
            tables = db_manager.get_tables()
            if db_manager.demo_mode:
                logger.info(f"Демо-режим активен. Доступно таблиц: {len(tables)}")
                print("🔄 Бот запущен в демо-режиме (без подключения к БД)")
            else:
                logger.info(f"Подключение к БД успешно. Найдено таблиц: {len(tables)}")
                print("✅ Подключение к базе данных установлено")
                
                # Создание резервной копии при запуске
                logger.info("Создание резервной копии при запуске...")
                backup_path = sqlite_backup_manager.create_backup()
                if backup_path:
                    logger.info(f"Резервная копия создана: {backup_path}")
                else:
                    logger.warning("Не удалось создать резервную копию")
                    
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            print("❌ Не удалось подключиться к базе данных. Проверьте настройки в .env файле.")
            print("🔄 Бот будет работать в демо-режиме")
        
        # Запуск бота с улучшенной обработкой ошибок
        logger.info("Бот запущен и готов к работе!")
        
        # Настройка повторных попыток
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Попытка подключения к Telegram API (попытка {retry_count + 1}/{max_retries})")
                bot.polling(none_stop=True, interval=1, timeout=60)
                break  # Если успешно, выходим из цикла
            except Exception as e:
                retry_count += 1
                logger.error(f"Ошибка подключения к Telegram API (попытка {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"Повторная попытка через 10 секунд...")
                    import time
                    time.sleep(10)
                else:
                    logger.error("Превышено максимальное количество попыток подключения")
                    raise e
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки. Завершение работы...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        db_manager.disconnect()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    main()

