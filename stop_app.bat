@echo off
echo ========================================
echo    Tornado Cooking - Остановка приложения
echo ========================================
echo.

echo 🔄 Останавливаем контейнеры...
docker-compose down

echo.
echo ✅ Приложение остановлено!
echo.
pause
