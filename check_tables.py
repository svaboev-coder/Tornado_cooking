#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from database import db_manager
from sqlite_backup import sqlite_backup_manager

def check_database():
    """Проверка и инициализация базы данных"""
    print("🔍 Проверка базы данных SQLite3...")
    
    try:
        # Проверяем подключение к базе данных
        if not db_manager.is_connected():
            print("❌ Не удалось подключиться к базе данных")
            return False
        
        print("✅ Подключение к базе данных установлено")
        
        # Получаем список таблиц
        tables = db_manager.get_tables()
        print(f"📋 Найдено таблиц: {len(tables)}")
        
        for table in tables:
            print(f"  - {table}")
        
        # Проверяем содержимое таблиц
        print("\n📊 Содержимое таблиц:")
        
        for table in tables:
            row_count = db_manager.get_table_row_count(table)
            print(f"  📋 {table}: {row_count} записей")
            
            if row_count > 0:
                # Показываем первые 3 записи
                sample_data = db_manager.get_table_data(table, 3)
                print(f"    Примеры записей:")
                for i, record in enumerate(sample_data, 1):
                    print(f"      {i}. {record}")
        
        # Проверяем резервные копии
        print("\n💾 Резервные копии:")
        backup_info = sqlite_backup_manager.get_backup_info()
        print(f"  📁 Директория: {backup_info['backup_dir']}")
        print(f"  📊 Количество копий: {backup_info['backup_count']}")
        print(f"  💾 Общий размер: {backup_info['total_size_mb']} МБ")
        
        if backup_info['latest_backup']:
            print(f"  🕒 Последняя копия: {backup_info['latest_backup']['created']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки базы данных: {e}")
        return False

def initialize_database():
    """Инициализация базы данных с тестовыми данными"""
    print("\n🚀 Инициализация базы данных...")
    
    try:
        # Добавляем тестовые номера в справочник
        test_rooms = ["к1/1", "к1/2", "к2/1", "Б1/1", "Б1/2", "Б2/1", "Б2/2"]
        
        for room in test_rooms:
            try:
                db_manager.insert_record("справочник_номеров", {"номер": room})
                print(f"  ✅ Добавлен номер: {room}")
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    print(f"  ⚠️ Номер уже существует: {room}")
                else:
                    print(f"  ❌ Ошибка добавления номера {room}: {e}")
        
        # Добавляем тестовые записи посетителей
        test_visitors = [
            {
                "номер": "к1/1",
                "дата": "2024-08-25",
                "ФИО": "Иванов Иван Иванович",
                "зд": 0, "зв": 2, "од": 0, "ов": 2, "уд": 0, "ув": 2
            },
            {
                "номер": "к1/2",
                "дата": "2024-08-26",
                "ФИО": "Петров Петр Петрович",
                "зд": 1, "зв": 1, "од": 1, "ов": 1, "уд": 1, "ув": 1
            }
        ]
        
        for visitor in test_visitors:
            try:
                db_manager.insert_record("посетители", visitor)
                print(f"  ✅ Добавлен посетитель: {visitor['ФИО']} - {visitor['номер']} - {visitor['дата']}")
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    print(f"  ⚠️ Запись уже существует: {visitor['ФИО']} - {visitor['номер']} - {visitor['дата']}")
                else:
                    print(f"  ❌ Ошибка добавления посетителя: {e}")
        
        print("✅ Инициализация завершена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

def create_backup():
    """Создание резервной копии"""
    print("\n💾 Создание резервной копии...")
    
    try:
        backup_path = sqlite_backup_manager.create_backup()
        if backup_path:
            print(f"✅ Резервная копия создана: {backup_path}")
            return True
        else:
            print("❌ Не удалось создать резервную копию")
            return False
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return False

def main():
    """Главная функция"""
    print("=" * 50)
    print("🔧 Проверка и инициализация базы данных SQLite3")
    print("=" * 50)
    
    # Проверяем базу данных
    if not check_database():
        print("❌ Проверка базы данных не прошла")
        return
    
    # Спрашиваем пользователя о необходимости инициализации
    print("\n" + "=" * 50)
    response = input("Хотите инициализировать базу данных тестовыми данными? (y/n): ").lower().strip()
    
    if response in ['y', 'yes', 'да', 'д']:
        if initialize_database():
            print("\n✅ База данных успешно инициализирована")
            
            # Создаем резервную копию после инициализации
            if create_backup():
                print("✅ Резервная копия создана")
            else:
                print("⚠️ Не удалось создать резервную копию")
        else:
            print("❌ Ошибка инициализации базы данных")
    else:
        print("⏭️ Инициализация пропущена")
    
    print("\n" + "=" * 50)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()
