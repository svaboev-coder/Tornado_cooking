import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
from config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для работы с PostgreSQL базой данных"""
    
    def __init__(self):
        self.connection = None
        self.demo_mode = False
        try:
            self.connect()
            self.create_tables()
        except Exception as e:
            logger.warning(f"Не удалось подключиться к PostgreSQL БД: {e}")
            logger.info("Переключение в демо-режим")
            self.demo_mode = True
    
    def connect(self) -> None:
        """Установка соединения с PostgreSQL базой данных"""
        try:
            self.connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            logger.info(f"Успешное подключение к PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise
    
    def disconnect(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("Соединение с PostgreSQL закрыто")
    
    def is_connected(self) -> bool:
        """Проверка состояния соединения с базой данных"""
        try:
            if self.connection:
                # Проверяем соединение простым запросом
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                return True
            return False
        except Exception:
            return False
    
    def create_tables(self) -> None:
        """Создание таблиц в PostgreSQL базе данных"""
        try:
            cursor = self.connection.cursor()
            
            # Создание таблицы справочника номеров
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "справочник номеров" (
                    номер VARCHAR(50) PRIMARY KEY
                )
            """)
            
            # Создание таблицы посетителей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS посетители (
                    id SERIAL PRIMARY KEY,
                    номер VARCHAR(50) NOT NULL,
                    дата VARCHAR(20) NOT NULL,
                    ФИО VARCHAR(200) NOT NULL,
                    зд INTEGER DEFAULT 0,
                    зв INTEGER DEFAULT 0,
                    од INTEGER DEFAULT 0,
                    ов INTEGER DEFAULT 0,
                    уд INTEGER DEFAULT 0,
                    ув INTEGER DEFAULT 0,
                    UNIQUE(номер, дата, ФИО)
                )
            """)
            
            # Добавляем базовые номера в справочник, если таблица пуста
            cursor.execute('SELECT COUNT(*) FROM "справочник номеров"')
            if cursor.fetchone()[0] == 0:
                base_rooms = ["к1/1", "к1/2", "к2/1", "Б1/1", "Б1/2"]
                for room in base_rooms:
                    cursor.execute('INSERT INTO "справочник номеров" (номер) VALUES (%s)', (room,))
                logger.info("Добавлены базовые номера в справочник")
            
            self.connection.commit()
            logger.info("Таблицы PostgreSQL созданы/проверены успешно")
            
        except Exception as e:
            logger.error(f"Ошибка создания таблиц PostgreSQL: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Выполнение SQL запроса с возвратом результатов"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса PostgreSQL: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Выполнение SQL запроса для обновления данных"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            rows_affected = cursor.rowcount
            return rows_affected
        except Exception as e:
            logger.error(f"Ошибка выполнения обновления PostgreSQL: {e}")
            raise
    
    def get_tables(self) -> List[str]:
        """Получение списка всех таблиц в базе данных"""
        if self.demo_mode:
            return ["демо_таблица_1", "демо_таблица_2", "справочник номеров"]
        
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        result = self.execute_query(query)
        return [table['table_name'] for table in result]
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """Получение структуры таблицы"""
        query = """
            SELECT 
                column_name as name,
                data_type as type,
                is_nullable as nullable,
                CASE WHEN column_default IS NOT NULL THEN 'DEFAULT' ELSE '' END as default_value
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        result = self.execute_query(query, (table_name,))
        
        structure = []
        for column in result:
            structure.append({
                'Field': column['name'],
                'Type': column['type'],
                'Null': 'YES' if column['nullable'] == 'YES' else 'NO',
                'Key': 'PRI' if column['name'] == 'id' else ''
            })
        return structure
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Получение списка колонок таблицы"""
        structure = self.get_table_structure(table_name)
        return [column['Field'] for column in structure]
    
    def get_table_data(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение данных из таблицы с ограничением"""
        if self.demo_mode:
            demo_data = {
                "демо_таблица_1": [
                    {'id': 1, 'имя': 'Иванов И.И.', 'дата': '2024-01-15'},
                    {'id': 2, 'имя': 'Петров П.П.', 'дата': '2024-01-16'},
                    {'id': 3, 'имя': 'Сидоров С.С.', 'дата': '2024-01-17'}
                ],
                "справочник номеров": [
                    {'номер': 'к1/1'}, {'номер': 'к1/2'}, {'номер': 'к2/1'},
                    {'номер': 'Б1/1'}, {'номер': 'Б1/2'}
                ]
            }
            return demo_data.get(table_name, demo_data["демо_таблица_1"])[:limit]
        
        # Обрабатываем имена таблиц с пробелами
        if ' ' in table_name:
            if limit:
                query = f'SELECT * FROM "{table_name}" LIMIT %s'
                return self.execute_query(query, (limit,))
            else:
                query = f'SELECT * FROM "{table_name}"'
                return self.execute_query(query)
        else:
            if limit:
                query = f"SELECT * FROM {table_name} LIMIT %s"
                return self.execute_query(query, (limit,))
            else:
                query = f"SELECT * FROM {table_name}"
                return self.execute_query(query)
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Получение полной информации о таблице"""
        if self.demo_mode:
            # Демо-данные для тестирования
            demo_data = {
                "демо_таблица_1": {
                    'name': 'демо_таблица_1',
                    'structure': [
                        {'Field': 'id', 'Type': 'SERIAL', 'Null': 'NO', 'Key': 'PRI'},
                        {'Field': 'имя', 'Type': 'VARCHAR', 'Null': 'NO', 'Key': ''},
                        {'Field': 'дата', 'Type': 'VARCHAR', 'Null': 'YES', 'Key': ''}
                    ],
                    'columns': ['id', 'имя', 'дата'],
                    'sample_data': [{'id': 1, 'имя': 'Иванов И.И.', 'дата': '2024-01-15'}],
                    'row_count': 5
                },
                "справочник номеров": {
                    'name': 'справочник номеров',
                    'structure': [
                        {'Field': 'номер', 'Type': 'VARCHAR', 'Null': 'NO', 'Key': 'PRI'}
                    ],
                    'columns': ['номер'],
                    'sample_data': [{'номер': 'к1/1'}, {'номер': 'к1/2'}, {'номер': 'к2/1'}],
                    'row_count': 6
                }
            }
            return demo_data.get(table_name, demo_data["демо_таблица_1"])
        
        try:
            structure = self.get_table_structure(table_name)
            sample_data = self.get_table_data(table_name, 1)
            
            return {
                'name': table_name,
                'structure': structure,
                'columns': [col['Field'] for col in structure],
                'sample_data': sample_data,
                'row_count': self.get_table_row_count(table_name)
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о таблице {table_name}: {e}")
            raise
    
    def get_table_row_count(self, table_name: str) -> int:
        """Получение количества строк в таблице"""
        # Обрабатываем имена таблиц с пробелами
        if ' ' in table_name:
            query = f'SELECT COUNT(*) as count FROM "{table_name}"'
        else:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def search_in_table(self, table_name: str, search_column: str, search_value: str) -> List[Dict[str, Any]]:
        """Поиск данных в таблице"""
        # Обрабатываем имена таблиц с пробелами
        if ' ' in table_name:
            query = f'SELECT * FROM "{table_name}" WHERE {search_column} ILIKE %s'
        else:
            query = f"SELECT * FROM {table_name} WHERE {search_column} ILIKE %s"
        return self.execute_query(query, (f"%{search_value}%",))
    
    def insert_record(self, table_name: str, data: Dict[str, Any]) -> int:
        """Вставка новой записи в таблицу"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s' for _ in data])
        # Обрабатываем имена таблиц с пробелами
        if ' ' in table_name:
            query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
        else:
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        return self.execute_update(query, tuple(data.values()))
    
    def update_record(self, table_name: str, data: Dict[str, Any], condition: Dict[str, Any]) -> int:
        """Обновление записи в таблице"""
        set_clause = ', '.join([f"{col} = %s" for col in data.keys()])
        where_clause = ' AND '.join([f"{col} = %s" for col in condition.keys()])
        # Обрабатываем имена таблиц с пробелами
        if ' ' in table_name:
            query = f'UPDATE "{table_name}" SET {set_clause} WHERE {where_clause}'
        else:
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(data.values()) + tuple(condition.values())
        return self.execute_update(query, params)

    def check_date_conflicts(self, room: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Проверка пересечения дат с существующими записями"""
        try:
            if self.demo_mode:
                # В демо-режиме возвращаем пустой список конфликтов
                return []
            
            query = """
                SELECT номер, дата, ФИО
                FROM посетители
                WHERE номер = %s 
                AND дата BETWEEN %s AND %s
                ORDER BY дата
            """
            
            result = self.execute_query(query, (room, start_date, end_date))
            return result
        except Exception as e:
            logger.error(f"Ошибка проверки конфликтов дат: {e}")
            return []


# Создание глобального экземпляра менеджера базы данных
db_manager = DatabaseManager()

