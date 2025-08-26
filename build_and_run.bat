@echo off
echo ========================================
echo Сборка и запуск Tornado Cooking Docker
echo ========================================

echo.
echo 1. Остановка существующих контейнеров...
docker-compose down

echo.
echo 2. Сборка образов...
docker-compose build

echo.
echo 3. Запуск контейнеров...
docker-compose up -d

echo.
echo 4. Проверка статуса контейнеров...
docker-compose ps

echo.
echo ========================================
echo Приложения запущены:
echo - Админ панель: http://localhost:5000
echo - Клиентское приложение: http://localhost:8080
echo ========================================

echo.
echo Для просмотра логов используйте:
echo docker-compose logs -f
echo.
echo Для остановки используйте:
echo docker-compose down


