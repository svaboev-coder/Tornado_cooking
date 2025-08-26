# Docker Setup для Tornado Cooking

Этот проект теперь использует PostgreSQL вместо SQLite. Все Docker образы обновлены для работы с сетевой базой данных.

## Структура проекта

- `Dockerfile` - Основное приложение (порт 8080)
- `Dockerfile.admin` - Административная панель (порт 5000)
- `Dockerfile.client` - Клиентское приложение (порт 8081)
- `docker-compose.yml` - Оркестрация всех сервисов

## Требования

1. Docker и Docker Compose установлены
2. Файл `.env` с настройками PostgreSQL (см. `env_docker_example.txt`)

## Настройка

1. Создайте файл `.env` на основе `env_docker_example.txt`:
```bash
cp env_docker_example.txt .env
```

2. Отредактируйте `.env` файл, указав ваши данные PostgreSQL:
```env
DB_HOST=postgresql-tornado.alwaysdata.net
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=tornado_dining
```

## Запуск

### Автоматический запуск
```bash
build_and_run_docker.bat
```

### Ручной запуск
```bash
# Сборка образов
docker-compose build --no-cache

# Запуск контейнеров
docker-compose up -d

# Проверка статуса
docker-compose ps
```

## Остановка

### Автоматическая остановка
```bash
stop_docker.bat
```

### Ручная остановка
```bash
# Остановка контейнеров
docker-compose down

# Остановка и удаление образов
docker-compose down --rmi all
```

## Доступные сервисы

После запуска будут доступны:

- **Основное приложение**: http://localhost:8080
- **Админ панель**: http://localhost:5000
- **Клиентское приложение**: http://localhost:8081

## Логи

Просмотр логов:
```bash
# Все сервисы
docker-compose logs

# Конкретный сервис
docker-compose logs app
docker-compose logs admin
docker-compose logs client

# Логи в реальном времени
docker-compose logs -f
```

## Обновление

Для обновления приложения:

1. Остановите контейнеры: `stop_docker.bat`
2. Обновите код
3. Запустите заново: `build_and_run_docker.bat`

## Устранение неполадок

### Проблемы с подключением к БД
1. Проверьте настройки в `.env` файле
2. Убедитесь, что PostgreSQL сервер доступен
3. Проверьте логи: `docker-compose logs`

### Проблемы с портами
Если порты заняты, измените маппинг в `docker-compose.yml`:
```yaml
ports:
  - "8082:5000"  # Измените 8082 на свободный порт
```

### Пересборка образов
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Резервные копии

Резервные копии создаются автоматически в папке `backups/` и монтируются в контейнеры.

## Переменные окружения

Все необходимые переменные окружения передаются из `.env` файла в контейнеры через `docker-compose.yml`.


