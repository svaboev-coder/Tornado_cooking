@echo off
echo ========================================
echo    Tornado Cooking - Запуск приложения
echo ========================================
echo.

REM Проверяем, установлен ли Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен или не запущен!
    echo Пожалуйста, установите Docker Desktop и запустите его.
    pause
    exit /b 1
)

echo ✅ Docker найден
echo.

REM Проверяем, существует ли файл .env
if not exist ".env" (
    echo ❌ Файл .env не найден!
    echo Создайте файл .env с данными для подключения к базе данных.
    echo Пример содержимого .env:
    echo DB_HOST=postgresql-tornado.alwaysdata.net
    echo DB_PORT=5432
    echo DB_USER=ваш_пользователь
    echo DB_PASSWORD=ваш_пароль
    echo DB_NAME=tornado_dining
    pause
    exit /b 1
)

echo ✅ Файл .env найден
echo.

REM Останавливаем существующие контейнеры
echo 🔄 Останавливаем существующие контейнеры...
docker-compose down

REM Запускаем приложение
echo 🚀 Запускаем приложение...
docker-compose up -d

REM Проверяем статус
echo.
echo 📊 Проверяем статус контейнеров...
docker-compose ps

echo.
echo ========================================
echo    Приложение запущено!
echo ========================================
echo.
echo 🌐 Доступные интерфейсы:
echo    • Основное приложение: http://localhost:8080
echo    • Клиентское приложение: http://localhost:8081
echo    • Административное приложение: http://localhost:5000
echo.
echo 💡 Для просмотра логов используйте: docker-compose logs
echo 💡 Для остановки используйте: docker-compose down
echo.
pause
