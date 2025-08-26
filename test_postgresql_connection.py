#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для тестирования подключения к PostgreSQL базе данных
Использование: python test_postgresql_connection.py
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_postgresql_connection():
    """Тестирование подключения к PostgreSQL"""
    print("🔍 Тестирование подключения к PostgreSQL...")
    
    try:
        from database import DatabaseManager
        
        # Создаем экземпляр менеджера
        db = DatabaseManager()
        
        if db.demo_mode:
            print("⚠️  Подключение не удалось, работает в демо-режиме")
            return False
        
        # Проверяем подключение
        if db.is_connected():
            print("✅ Подключение к PostgreSQL успешно!")
            
            # Получаем список таблиц
            tables = db.get_tables()
            print(f"📋 Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"  - {table}")
            
            # Проверяем структуру таблиц
            for table in tables:
                try:
                    structure = db.get_table_structure(table)
                    row_count = db.get_table_row_count(table)
                    print(f"  📊 {table}: {len(structure)} колонок, {row_count} записей")
                except Exception as e:
                    print(f"  ❌ Ошибка получения информации о таблице {table}: {e}")
            
            return True
        else:
            print("❌ Подключение к PostgreSQL не удалось")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📝 Убедитесь, что установлен psycopg2-binary: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def check_environment():
    """Проверка настроек окружения"""
    print("🔧 Проверка настроек окружения...")
    
    required_vars = [
        'DB_HOST',
        'DB_PORT', 
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Скрываем пароль в выводе
            if var == 'DB_PASSWORD':
                print(f"  ✅ {var}: {'*' * len(value)}")
            else:
                print(f"  ✅ {var}: {value}")
    
    if missing_vars:
        print(f"  ❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return False
    
    return True

def test_database_manager():
    """Тестирование менеджера базы данных"""
    print("\n🔄 Тестирование менеджера базы данных...")
    
    try:
        from database import db_manager
        
        if db_manager.demo_mode:
            print("  ⚠️  Работает в демо-режиме")
        else:
            print("  ✅ Подключение активно")
            
        # Получаем информацию о подключении
        from config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
        print(f"  🔗 Подключение: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка менеджера базы данных: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тестирование подключения к PostgreSQL")
    print("=" * 50)
    
    # Проверяем настройки
    if not check_environment():
        print("\n❌ Настройки окружения неполные")
        print("📝 Убедитесь, что в файле .env указаны все необходимые параметры:")
        print("   DB_HOST=ваш_хост")
        print("   DB_PORT=5432")
        print("   DB_NAME=имя_базы")
        print("   DB_USER=пользователь")
        print("   DB_PASSWORD=пароль")
        sys.exit(1)
    
    # Тестируем подключение
    if test_postgresql_connection():
        print("\n✅ PostgreSQL подключение работает корректно!")
    else:
        print("\n❌ Проблемы с подключением к PostgreSQL")
    
    # Тестируем менеджер базы данных
    test_database_manager()
    
    print("\n🏁 Тестирование завершено")
