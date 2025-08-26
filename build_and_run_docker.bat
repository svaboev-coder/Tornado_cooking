@echo off
echo ========================================
echo Сборка и запуск Docker контейнеров
echo ========================================

echo.
echo 1. Остановка существующих контейнеров...
docker-compose down

echo.
echo 2. Сборка образов...
docker-compose build --no-cache

echo.
echo 3. Запуск контейнеров...
docker-compose up -d

echo.
echo 4. Проверка статуса контейнеров...
docker-compose ps

echo.
echo ========================================
echo Контейнеры запущены!
echo ========================================
echo Основное приложение: http://localhost:8080
echo Админ панель: http://localhost:5000
echo Клиентское приложение: http://localhost:8081
echo ========================================

pause

