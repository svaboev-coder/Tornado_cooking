#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

try:
    conn = sqlite3.connect('visitors.db')
    cursor = conn.cursor()
    
    # Проверяем таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Таблицы в базе данных:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Проверяем справочник номеров
    print("\nСодержимое справочника номеров:")
    cursor.execute('SELECT * FROM "справочник номеров" LIMIT 10')
    rooms = cursor.fetchall()
    if rooms:
        for room in rooms:
            print(f"  - {room[0]}")
    else:
        print("  - Таблица пуста!")
    
    # Проверяем посетителей
    print("\nКоличество записей в таблице посетителей:")
    cursor.execute("SELECT COUNT(*) FROM посетители")
    count = cursor.fetchone()[0]
    print(f"  - {count} записей")
    
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")



