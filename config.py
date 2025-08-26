import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки Telegram бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'demo_token_for_testing')

# Настройки PostgreSQL (alwaysdata)
POSTGRES_HOST = os.getenv('DB_HOST', 'localhost')
POSTGRES_PORT = os.getenv('DB_PORT', '5432')
POSTGRES_DB = os.getenv('DB_NAME', 'visitors')
POSTGRES_USER = os.getenv('DB_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('DB_PASSWORD', '')

# Проверка обязательных переменных
if not BOT_TOKEN or BOT_TOKEN == 'your_telegram_bot_token_here':
    print("⚠️  ВНИМАНИЕ: BOT_TOKEN не установлен или установлен по умолчанию")
    print("📝 Для работы бота создайте файл .env с вашим токеном:")
    print("   BOT_TOKEN=ваш_токен_от_botfather")
    print("🔄 Бот будет работать в демо-режиме")

if not POSTGRES_PASSWORD:
    print("⚠️  ВНИМАНИЕ: DB_PASSWORD не установлен")
    print("📝 Для работы с PostgreSQL добавьте в .env файл:")
    print("   DB_HOST=ваш_хост")
    print("   DB_PORT=5432")
    print("   DB_NAME=имя_базы")
    print("   DB_USER=пользователь")
    print("   DB_PASSWORD=пароль")
else:
    print(f"✅ Подключение к PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

print("✅ Конфигурация загружена успешно")

