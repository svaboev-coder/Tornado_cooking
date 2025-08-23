import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки Telegram бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'demo_token_for_testing')

# Настройки базы данных SQLite3
DB_PATH = os.getenv('DB_PATH', 'visitors.db')

# Проверка обязательных переменных
if not BOT_TOKEN or BOT_TOKEN == 'your_telegram_bot_token_here':
    print("⚠️  ВНИМАНИЕ: BOT_TOKEN не установлен или установлен по умолчанию")
    print("📝 Для работы бота создайте файл .env с вашим токеном:")
    print("   BOT_TOKEN=ваш_токен_от_botfather")
    print("🔄 Бот будет работать в демо-режиме")

print("✅ Конфигурация загружена успешно")
print(f"📁 Путь к базе данных SQLite3: {DB_PATH}")

