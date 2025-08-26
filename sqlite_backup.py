#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SQLiteBackupManager:
    """Менеджер для резервного копирования данных SQLite3"""
    
    def __init__(self, db_path: str = "visitors.db", backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # Создаем директорию для резервных копий, если её нет
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"Создана директория для резервных копий: {self.backup_dir}")
    
    def create_backup(self) -> str:
        """Создание резервной копии базы данных"""
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"Файл базы данных не найден: {self.db_path}")
                return None
            
            # Создаем имя файла резервной копии с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"visitors_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Копируем файл базы данных
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Создана резервная копия: {backup_path}")
            
            # Очищаем старые резервные копии, оставляя только 3 последние
            self.cleanup_old_backups(keep_count=3)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Восстановление базы данных из резервной копии"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Файл резервной копии не найден: {backup_path}")
                return False
            
            # Создаем резервную копию текущей БД перед восстановлением
            current_backup = self.create_backup()
            if current_backup:
                logger.info(f"Создана резервная копия текущей БД: {current_backup}")
            
            # Восстанавливаем из резервной копии
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"База данных восстановлена из: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка восстановления из резервной копии: {e}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Получение списка доступных резервных копий"""
        try:
            backups = []
            
            if not os.path.exists(self.backup_dir):
                return backups
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("visitors_backup_") and filename.endswith(".db"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    backups.append({
                        'filename': filename,
                        'path': file_path,
                        'size': file_stat.st_size,
                        'created': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'size_mb': round(file_stat.st_size / (1024 * 1024), 2)
                    })
            
            # Сортируем по дате создания (новые сначала)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Ошибка получения списка резервных копий: {e}")
            return []
    
    def delete_backup(self, backup_path: str) -> bool:
        """Удаление резервной копии"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Файл резервной копии не найден: {backup_path}")
                return False
            
            os.remove(backup_path)
            logger.info(f"Удалена резервная копия: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления резервной копии: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 3) -> int:
        """Очистка старых резервных копий, оставляя только последние N"""
        try:
            backups = self.get_backup_list()
            
            if len(backups) <= keep_count:
                logger.info(f"Количество резервных копий ({len(backups)}) не превышает лимит ({keep_count})")
                return 0
            
            deleted_count = 0
            for backup in backups[keep_count:]:
                if self.delete_backup(backup['path']):
                    deleted_count += 1
            
            logger.info(f"Удалено {deleted_count} старых резервных копий")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки старых резервных копий: {e}")
            return 0
    
    def get_backup_info(self) -> Dict[str, Any]:
        """Получение информации о резервных копиях"""
        try:
            backups = self.get_backup_list()
            
            total_size = sum(backup['size'] for backup in backups)
            total_size_mb = round(total_size / (1024 * 1024), 2)
            
            return {
                'backup_count': len(backups),
                'total_size_mb': total_size_mb,
                'backup_dir': self.backup_dir,
                'latest_backup': backups[0] if backups else None,
                'backups': backups[:5]  # Последние 5 копий
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о резервных копиях: {e}")
            return {
                'backup_count': 0,
                'total_size_mb': 0,
                'backup_dir': self.backup_dir,
                'error': str(e)
            }
    
    def export_to_csv(self, table_name: str, csv_path: str = None) -> str:
        """Экспорт таблицы в CSV файл"""
        try:
            if not csv_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_path = os.path.join(self.backup_dir, f"{table_name}_export_{timestamp}.csv")
            
            # Подключаемся к базе данных
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем данные из таблицы
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning(f"Таблица {table_name} пуста")
                conn.close()
                return None
            
            # Получаем названия колонок
            columns = [description[0] for description in cursor.description]
            
            # Записываем в CSV
            with open(csv_path, 'w', encoding='utf-8') as f:
                # Записываем заголовки
                f.write(','.join(columns) + '\n')
                
                # Записываем данные
                for row in rows:
                    f.write(','.join(str(value) for value in row) + '\n')
            
            conn.close()
            logger.info(f"Таблица {table_name} экспортирована в {csv_path}")
            return csv_path
            
        except Exception as e:
            logger.error(f"Ошибка экспорта таблицы {table_name}: {e}")
            return None


# Создание глобального экземпляра менеджера резервного копирования
sqlite_backup_manager = SQLiteBackupManager()
