import datetime
from typing import Dict, List, Any, Optional
from telebot import types
from database import db_manager
from sqlite_backup import sqlite_backup_manager
import logging

logger = logging.getLogger(__name__)


class RegistrationManager:
    """Менеджер для управления процессом регистрации"""
    
    def __init__(self):
        self.registration_steps = {
            'start': self.step_start,
            'select_building': self.step_select_building,
            'select_room': self.step_select_room,
            'enter_name': self.step_enter_name,
            'enter_dates': self.step_enter_dates,
            'enter_end_date': self.step_enter_end_date,
            'confirm_dates': self.step_confirm_dates,
            'date_conflict': self.step_date_conflict,
            'enter_meals_for_day': self.step_enter_meals_for_day,
            'confirm_registration': self.step_confirm_registration,
            'complete': self.step_complete
        }
    
    def get_available_rooms(self) -> List[str]:
        """Получение списка доступных номеров"""
        try:
            if db_manager.demo_mode:
                return ["к1/1", "к1/2", "к2/1", "Б1/1", "Б1/2"]
            
            # Проверяем соединение и переподключаемся при необходимости
            if not db_manager.is_connected():
                logger.info("Соединение с БД потеряно, переподключаемся...")
                db_manager.connect()
            
            # Получаем номера из справочника
            rooms_data = db_manager.get_table_data("справочник_номеров", 100)
            return [room['номер'] for room in rooms_data]
        except Exception as e:
            logger.error(f"Ошибка получения номеров: {e}")
            return []
    
    def get_available_buildings(self) -> List[str]:
        """Получение списка доступных корпусов"""
        try:
            rooms = self.get_available_rooms()
            buildings = set()
            
            for room in rooms:
                # Извлекаем корпус из номера (часть до "/")
                if '/' in room:
                    building = room.split('/')[0]
                    buildings.add(building)
            
            return sorted(list(buildings))
        except Exception as e:
            logger.error(f"Ошибка получения корпусов: {e}")
            return []
    
    def get_rooms_in_building(self, building: str) -> List[str]:
        """Получение списка номеров в конкретном корпусе"""
        try:
            rooms = self.get_available_rooms()
            building_rooms = []
            
            for room in rooms:
                if room.startswith(building + '/'):
                    building_rooms.append(room)
            
            return sorted(building_rooms)
        except Exception as e:
            logger.error(f"Ошибка получения номеров в корпусе {building}: {e}")
            return []
    
    def step_start(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Начальный шаг регистрации"""
        user_state.current_step = 'select_building'
        user_state.registration_data.clear()
        
        buildings = self.get_available_buildings()
        if not buildings:
            return 'error', '❌ Не удалось получить список корпусов. Попробуйте позже.', None
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for building in buildings:
            markup.add(types.KeyboardButton(building))
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        text = (
            "🏨 <b>Регистрация на питание</b>\n\n"
            "Шаг 1 из 6: Выбор корпуса\n\n"
            "Выберите корпус:"
        )
        
        return 'select_building', text, markup
    
    def step_select_building(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг выбора корпуса"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        building = message.text.strip()
        buildings = self.get_available_buildings()
        
        if building not in buildings:
            return 'select_building', "❌ Выберите корпус из списка:", None
        
        user_state.registration_data['building'] = building
        user_state.current_step = 'select_room'
        
        # Получаем номера в выбранном корпусе
        rooms = self.get_rooms_in_building(building)
        if not rooms:
            return 'error', f"❌ Не удалось получить номера в корпусе {building}. Попробуйте позже.", None
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for room in rooms:
            markup.add(types.KeyboardButton(room))
        markup.add(types.KeyboardButton("🔙 Назад к корпусам"))
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        text = (
            f"✅ Выбран корпус: <b>{building}</b>\n\n"
            "Шаг 1 из 6: Выбор номера\n\n"
            f"Выберите номер в корпусе {building}:"
        )
        
        return 'select_room', text, markup
    
    def step_select_room(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг выбора номера"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        if message.text == "🔙 Назад к корпусам":
            # Возвращаемся к выбору корпуса
            return self.step_start(message, user_state)
        
        room = message.text.strip()
        building = user_state.registration_data.get('building', '')
        rooms = self.get_rooms_in_building(building)
        
        if room not in rooms:
            return 'select_room', f"❌ Выберите номер из списка корпуса {building}:", None
        
        user_state.registration_data['room'] = room
        # Очищаем флаг конфликта при выборе нового номера
        user_state.registration_data.pop('date_conflict', None)
        user_state.current_step = 'enter_name'
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        text = (
            f"✅ Выбран номер: <b>{room}</b>\n\n"
            "Шаг 2 из 6: Ввод имени\n\n"
            "Введите ваше полное имя (ФИО):"
        )
        
        return 'enter_name', text, markup
    
    def step_enter_name(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг ввода имени"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        name = message.text.strip()
        if len(name) < 2:
            return 'enter_name', "❌ Имя должно содержать минимум 2 символа. Попробуйте снова:", None
        
        user_state.registration_data['name'] = name
        user_state.current_step = 'enter_dates'
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        text = (
            f"✅ Имя: <b>{name}</b>\n\n"
            "Шаг 3 из 6: Даты размещения\n\n"
            "Введите дату начала размещения в формате ДД.ММ.ГГГГ\n"
            "Например: 25.08.2024"
        )
        
        return 'enter_dates', text, markup
    
    def step_enter_dates(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг ввода дат"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        # Очищаем флаг конфликта при новом вводе дат
        user_state.registration_data.pop('date_conflict', None)
        
        try:
            start_date = datetime.datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
            today = datetime.date.today()
            
            if start_date < today:
                return 'enter_dates', "❌ Дата начала не может быть в прошлом. Введите корректную дату:", None
            
            user_state.registration_data['start_date'] = start_date
            user_state.current_step = 'enter_end_date'
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("❌ Отмена"))
            
            text = (
                f"✅ Дата начала: <b>{start_date.strftime('%d.%m.%Y')}</b>\n\n"
                "Теперь введите дату окончания размещения в формате ДД.ММ.ГГГГ\n"
                "Например: 30.08.2024"
            )
            
            return 'enter_end_date', text, markup
            
        except ValueError:
            return 'enter_dates', "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ:", None
    
    def step_enter_end_date(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг ввода даты окончания"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        try:
            end_date = datetime.datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
            start_date = user_state.registration_data['start_date']
            
            if end_date <= start_date:
                return 'enter_end_date', "❌ Дата окончания должна быть позже даты начала. Попробуйте снова:", None
            
            user_state.registration_data['end_date'] = end_date
            user_state.current_step = 'confirm_dates'
            
            # Генерируем список дат
            date_range = []
            current_date = start_date
            while current_date <= end_date:
                date_range.append(current_date)
                current_date += datetime.timedelta(days=1)
            
            user_state.registration_data['date_range'] = date_range
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("✅ Подтвердить"))
            markup.add(types.KeyboardButton("❌ Отмена"))
            
            text = (
                f"✅ Дата окончания: <b>{end_date.strftime('%d.%m.%Y')}</b>\n\n"
                f"📅 <b>Период размещения:</b>\n"
                f"С {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}\n"
                f"Всего дней: {len(date_range)}\n\n"
                "Подтвердите даты или начните заново:"
            )
            
            return 'confirm_dates', text, markup
            
        except ValueError:
            return 'enter_end_date', "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ:", None
    
    def step_confirm_dates(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг подтверждения дат"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        if message.text != "✅ Подтвердить":
            return 'confirm_dates', "❌ Выберите '✅ Подтвердить' или '❌ Отмена':", None
        
        # Проверяем конфликты дат перед продолжением
        room = user_state.registration_data.get('room', '')
        start_date = user_state.registration_data.get('start_date')
        end_date = user_state.registration_data.get('end_date')
        
        if room and start_date and end_date:
            # Проверяем конфликты в базе данных
            conflicts = db_manager.check_date_conflicts(
                room, 
                start_date.strftime('%Y-%m-%d'), 
                end_date.strftime('%Y-%m-%d')
            )
            
            if conflicts:
                # Есть конфликты - показываем их и предлагаем изменить даты
                conflict_text = "⚠️ <b>Обнаружены конфликты с существующими записями:</b>\n\n"
                conflict_text += f"🏨 Номер: <b>{room}</b>\n"
                conflict_text += f"📅 Период: <b>{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}</b>\n\n"
                conflict_text += "📋 <b>Существующие записи в этом периоде:</b>\n"
                
                for conflict in conflicts:
                    # Проверяем, является ли дата строкой или объектом datetime
                    if isinstance(conflict['дата'], str):
                        conflict_date = datetime.datetime.strptime(conflict['дата'], '%Y-%m-%d').strftime('%d.%m.%Y')
                    else:
                        conflict_date = conflict['дата'].strftime('%d.%m.%Y')
                    conflict_text += f"• {conflict_date} - {conflict['ФИО']}\n"
                
                conflict_text += "\n❌ <b>Регистрация невозможна из-за пересечения дат.</b>\n"
                conflict_text += "Пожалуйста, выберите другой период или номер."
                
                # Сохраняем состояние для возврата к вводу дат
                user_state.registration_data['date_conflict'] = True
                user_state.current_step = 'enter_dates'
                
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(types.KeyboardButton("📅 Изменить даты"))
                markup.add(types.KeyboardButton("🏨 Изменить номер"))
                markup.add(types.KeyboardButton("❌ Отмена"))
                
                return 'date_conflict', conflict_text, markup
        
        # Нет конфликтов - продолжаем регистрацию
        # Инициализируем данные для каждого дня
        user_state.registration_data['daily_meals'] = {}
        user_state.registration_data['current_day_index'] = 0
        user_state.current_step = 'enter_meals_for_day'
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("0 0 0 0 0 0"))
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        # Получаем первую дату
        date_range = user_state.registration_data['date_range']
        current_date = date_range[0]
        
        text = (
            f"✅ <b>Даты подтверждены без конфликтов!</b>\n\n"
            f"Шаг 4 из 6: Информация о питании\n\n"
            f"📅 <b>День {user_state.registration_data['current_day_index'] + 1} из {len(date_range)}</b>\n"
            f"Дата: <b>{current_date.strftime('%d.%m.%Y')}</b>\n\n"
            "Введите количество людей на каждый прием пищи для этого дня.\n\n"
            "<b>Формат ввода:</b> 6 чисел через пробел\n"
            "<b>Порядок:</b> взрослые завтрак, дети завтрак, взрослые обед, дети обед, взрослые ужин, дети ужин\n\n"
            "<b>Пример:</b> 2 1 2 1 2 0\n"
            "(2 взрослых и 1 ребенок на завтрак, 2 взрослых и 1 ребенок на обед, 2 взрослых и 0 детей на ужин)\n\n"
            "Введите данные:"
        )
        
        return 'enter_meals_for_day', text, markup

    def step_date_conflict(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Обработка конфликта дат"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        if message.text == "📅 Изменить даты":
            # Возвращаемся к вводу дат
            user_state.current_step = 'enter_dates'
            user_state.registration_data.pop('date_conflict', None)  # Убираем флаг конфликта
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("❌ Отмена"))
            
            text = (
                "📅 <b>Ввод дат размещения</b>\n\n"
                "Введите дату начала размещения в формате ДД.ММ.ГГГГ\n"
                "Например: 25.08.2024\n\n"
                "⚠️ <b>Убедитесь, что выбранные даты не пересекаются с существующими записями.</b>"
            )
            
            return 'enter_dates', text, markup
        
        elif message.text == "🏨 Изменить номер":
            # Возвращаемся к выбору номера
            user_state.current_step = 'select_room'
            user_state.registration_data.pop('date_conflict', None)  # Убираем флаг конфликта
            user_state.registration_data.pop('room', None)  # Убираем выбранный номер
            user_state.registration_data.pop('start_date', None)  # Убираем даты
            user_state.registration_data.pop('end_date', None)
            user_state.registration_data.pop('date_range', None)
            
            building = user_state.registration_data.get('building', '')
            if building:
                # Получаем номера в выбранном корпусе
                rooms = self.get_rooms_in_building(building)
                if rooms:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    for room in rooms:
                        markup.add(types.KeyboardButton(room))
                    markup.add(types.KeyboardButton("🔙 Назад к корпусам"))
                    markup.add(types.KeyboardButton("❌ Отмена"))
                    
                    text = (
                        f"✅ Выбран корпус: <b>{building}</b>\n\n"
                        "Шаг 1 из 6: Выбор номера\n\n"
                        f"Выберите номер в корпусе {building}:"
                    )
                    
                    return 'select_room', text, markup
            
            # Если что-то пошло не так, возвращаемся к началу
            return self.step_start(message, user_state)
        
        else:
            return 'date_conflict', "❌ Выберите '📅 Изменить даты', '🏨 Изменить номер' или '❌ Отмена':", None
    
    def step_enter_meals_for_day(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг ввода информации о питании для конкретного дня"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        # Получаем данные текущего дня
        current_day_index = user_state.registration_data['current_day_index']
        date_range = user_state.registration_data['date_range']
        current_date = date_range[current_day_index]
        date_key = current_date.strftime('%Y-%m-%d')
        
        # Инициализируем данные о питании для текущего дня, если их еще нет
        if date_key not in user_state.registration_data['daily_meals']:
            user_state.registration_data['daily_meals'][date_key] = {}
        
        # Обрабатываем ввод всех данных сразу
        input_text = message.text.strip()
        
        # Если пустой ввод или кнопка "0 0 0 0 0 0", устанавливаем все значения в 0
        if input_text == "" or input_text == "0 0 0 0 0 0":
            user_state.registration_data['daily_meals'][date_key] = {
                'зв': 0, 'зд': 0, 'ов': 0, 'од': 0, 'ув': 0, 'уд': 0
            }
        else:
            try:
                # Разбираем введенные числа
                numbers = input_text.split()
                
                # Проверяем количество чисел
                if len(numbers) != 6:
                    return 'enter_meals_for_day', (
                        "❌ Неверный формат ввода!\n\n"
                        "Введите ровно 6 чисел через пробел:\n"
                        "взрослые завтрак, дети завтрак, взрослые обед, дети обед, взрослые ужин, дети ужин\n\n"
                        "<b>Пример:</b> 2 1 2 1 2 0"
                    ), None
                
                # Преобразуем в числа и проверяем
                meal_counts = []
                for num_str in numbers:
                    count = int(num_str)
                    if count < 0:
                        return 'enter_meals_for_day', "❌ Количество не может быть отрицательным. Введите корректные числа:", None
                    meal_counts.append(count)
                
                # Сохраняем данные
                user_state.registration_data['daily_meals'][date_key] = {
                    'зв': meal_counts[0],  # взрослые завтрак
                    'зд': meal_counts[1],  # дети завтрак
                    'ов': meal_counts[2],  # взрослые обед
                    'од': meal_counts[3],  # дети обед
                    'ув': meal_counts[4],  # взрослые ужин
                    'уд': meal_counts[5]   # дети ужин
                }
                
            except ValueError:
                return 'enter_meals_for_day', (
                    "❌ Неверный формат ввода!\n\n"
                    "Введите только числа через пробел.\n"
                    "<b>Пример:</b> 2 1 2 1 2 0"
                ), None
        
        # Переходим к следующему дню или подтверждению
        return self.step_next_day_or_confirm(message, user_state)
    
    def step_next_day_or_confirm(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Переход к следующему дню или подтверждение регистрации"""
        current_day_index = user_state.registration_data['current_day_index']
        date_range = user_state.registration_data['date_range']
        
        # Проверяем, есть ли еще дни
        if current_day_index + 1 < len(date_range):
            # Переходим к следующему дню
            user_state.registration_data['current_day_index'] += 1
            user_state.registration_data['current_meal_step'] = 0  # Сбрасываем шаг для нового дня
            
            next_date = date_range[current_day_index + 1]
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("0 0 0 0 0 0"))
            markup.add(types.KeyboardButton("❌ Отмена"))
            
            # Показываем введенные данные для текущего дня
            current_date = date_range[current_day_index]
            date_key = current_date.strftime('%Y-%m-%d')
            current_day_meals = user_state.registration_data['daily_meals'][date_key]
            current_summary = (
                f"✅ <b>Данные для {date_range[current_day_index].strftime('%d.%m.%Y')} сохранены:</b>\n"
                f"• Завтрак: {current_day_meals.get('зв', 0)} взрослых, {current_day_meals.get('зд', 0)} детей\n"
                f"• Обед: {current_day_meals.get('ов', 0)} взрослых, {current_day_meals.get('од', 0)} детей\n"
                f"• Ужин: {current_day_meals.get('ув', 0)} взрослых, {current_day_meals.get('уд', 0)} детей\n\n"
            )
            
            text = (
                f"{current_summary}"
                f"📅 <b>День {current_day_index + 2} из {len(date_range)}</b>\n"
                f"Дата: <b>{next_date.strftime('%d.%m.%Y')}</b>\n\n"
                "Введите количество людей на каждый прием пищи для этого дня.\n\n"
                "<b>Формат ввода:</b> 6 чисел через пробел\n"
                "<b>Порядок:</b> взрослые завтрак, дети завтрак, взрослые обед, дети обед, взрослые ужин, дети ужин\n\n"
                "<b>Пример:</b> 2 1 2 1 2 0\n"
                "Введите данные:"
            )
            
            return 'enter_meals_for_day', text, markup
        else:
            # Все дни обработаны, переходим к подтверждению
            return self.step_confirm_registration(message, user_state)
    
    def step_confirm_registration(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Шаг подтверждения регистрации"""
        if message.text == "❌ Отмена":
            return 'cancel', "❌ Регистрация отменена.", None
        
        # Формируем сводку регистрации
        data = user_state.registration_data
        daily_meals = data['daily_meals']
        date_range = data['date_range']
        
        summary = (
            "📋 <b>Сводка регистрации:</b>\n\n"
            f"🏨 Номер: <b>{data['room']}</b>\n"
            f"👤 Имя: <b>{data['name']}</b>\n"
            f"📅 Период: <b>{data['start_date'].strftime('%d.%m.%Y')} - {data['end_date'].strftime('%d.%m.%Y')}</b>\n"
            f"📊 Дней: <b>{len(date_range)}</b>\n\n"
            "🍽️ <b>Питание по дням:</b>\n"
        )
        
        # Добавляем информацию о питании для каждого дня
        for i, date in enumerate(date_range, 1):
            date_key = date.strftime('%Y-%m-%d')
            day_meals = daily_meals.get(date_key, {})
            
            summary += (
                f"\n📅 <b>День {i} ({date.strftime('%d.%m.%Y')}):</b>\n"
                f"• Завтрак: {day_meals.get('зв', 0)} взрослых, {day_meals.get('зд', 0)} детей\n"
                f"• Обед: {day_meals.get('ов', 0)} взрослых, {day_meals.get('од', 0)} детей\n"
                f"• Ужин: {day_meals.get('ув', 0)} взрослых, {day_meals.get('уд', 0)} детей\n"
            )
        
        summary += "\nПодтвердите регистрацию:"
        
        user_state.current_step = 'complete'
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("✅ Подтвердить регистрацию"))
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        return 'complete', summary, markup
    
    def step_complete(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Завершающий шаг - сохранение данных"""
        logger.info(f"step_complete вызван с текстом: '{message.text}'")
        
        if message.text == "❌ Отмена":
            logger.info("Отмена регистрации")
            return 'cancel', "❌ Регистрация отменена.", None
        
        if message.text != "✅ Подтвердить регистрацию":
            logger.warning(f"Неожиданный текст в step_complete: '{message.text}'")
            return 'complete', "❌ Выберите '✅ Подтвердить регистрацию' или '❌ Отмена':", None
        
        logger.info("Начинаем сохранение данных регистрации")
        try:
            # Сохраняем данные в базу
            success = self.save_registration_data(user_state.registration_data)
            logger.info(f"Результат сохранения: {success}")
            
            if success:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(types.KeyboardButton("📝 Регистрация"))
                markup.add(types.KeyboardButton("📊 Таблицы БД"))
                markup.add(types.KeyboardButton("❓ Справка"))
                
                text = (
                    "🎉 <b>Регистрация успешно завершена!</b>\n\n"
                    "Ваши данные сохранены в базе данных.\n"
                    "Вы можете просмотреть их в разделе '📊 Таблицы БД'.\n\n"
                    "Выберите дальнейшее действие:"
                )
                
                return 'success', text, markup
            else:
                return 'error', "❌ Ошибка при сохранении данных. Попробуйте позже.", None
                
        except Exception as e:
            logger.error(f"Ошибка завершения регистрации: {e}")
            return 'error', "❌ Произошла ошибка при сохранении данных.", None
    
    def save_registration_data(self, data: Dict[str, Any]) -> bool:
        """Сохранение данных регистрации в базу и резервную копию"""
        try:
            if db_manager.demo_mode:
                logger.info("Демо-режим: данные не сохраняются")
                return True
            
            # Получаем данные
            room = data['room']
            name = data['name']
            date_range = data['date_range']
            daily_meals = data['daily_meals']
            
            # Отладочная информация
            logger.info(f"Сохранение данных для: комната={room}, имя={name}")
            logger.info(f"Тип date_range: {type(date_range)}")
            logger.info(f"Количество дат: {len(date_range)}")
            logger.info(f"Первая дата: {date_range[0]} (тип: {type(date_range[0])})")
            logger.info(f"Тип daily_meals: {type(daily_meals)}")
            logger.info(f"Ключи daily_meals: {list(daily_meals.keys())}")
            
            saved_count = 0
            skipped_count = 0
            backup_records = []  # Список записей для резервного копирования
            
            # Создаем записи для каждой даты
            for date in date_range:
                logger.info(f"Обрабатываем дату: {date} (тип: {type(date)})")
                try:
                    date_key = date.strftime('%Y-%m-%d')
                    logger.info(f"Создан ключ даты: {date_key}")
                except AttributeError as e:
                    logger.error(f"Ошибка при создании ключа даты: {e}")
                    logger.error(f"Дата: {date}, тип: {type(date)}")
                    raise e
                
                day_meals = daily_meals.get(date_key, {})
                logger.info(f"Данные о питании для {date_key}: {day_meals}")
                
                record = {
                    'номер': room,
                    'дата': date_key,
                    'ФИО': name,
                    'зд': day_meals.get('зд', 0),
                    'зв': day_meals.get('зв', 0),
                    'од': day_meals.get('од', 0),
                    'ов': day_meals.get('ов', 0),
                    'уд': day_meals.get('уд', 0),
                    'ув': day_meals.get('ув', 0)
                }
                
                try:
                    # Вставляем запись в таблицу
                    result = db_manager.insert_record('посетители', record)
                    if result > 0:  # Запись успешно вставлена
                        saved_count += 1
                        logger.info(f"Сохранена запись для {room}, {date_key}, {name}")
                        # Добавляем запись в список для резервного копирования
                        backup_records.append(record)
                    else:
                        logger.warning(f"Запись не была вставлена для {room}, {date_key}, {name}")
                        
                except Exception as insert_error:
                    # Проверяем, является ли ошибка дублированием
                    error_msg = str(insert_error).lower()
                    if 'duplicate' in error_msg or 'unique' in error_msg or 'already exists' in error_msg:
                        logger.warning(f"Запись уже существует для {room}, {date_key}, {name}")
                        skipped_count += 1
                    else:
                        # Если это не ошибка дублирования, логируем и продолжаем
                        logger.error(f"Ошибка вставки записи для {room}, {date_key}, {name}: {insert_error}")
                        # Не прерываем процесс, продолжаем с другими записями
            
            # Резервное копирование SQLite3 (только для успешно сохраненных записей)
            if backup_records:
                try:
                    backup_path = sqlite_backup_manager.create_backup()
                    if backup_path:
                        logger.info(f"Создана резервная копия: {backup_path}")
                    else:
                        logger.warning("Не удалось создать резервную копию")
                except Exception as backup_error:
                    logger.error(f"Ошибка резервного копирования: {backup_error}")
                    # Не прерываем основной процесс из-за ошибки резервного копирования
            
            # Формируем итоговый результат
            if saved_count > 0:
                logger.info(f"Сохранено {saved_count} записей для клиента {name}")
                if skipped_count > 0:
                    logger.info(f"Пропущено {skipped_count} дублирующих записей")
                return True
            elif skipped_count > 0:
                logger.warning(f"Все записи для клиента {name} уже существуют (пропущено {skipped_count})")
                return True  # Считаем успехом, так как записи уже есть
            else:
                logger.error(f"Не удалось сохранить ни одной записи для клиента {name}")
                return False
            
        except Exception as e:
            logger.error(f"Критическая ошибка сохранения данных регистрации: {e}")
            return False
    
    def process_step(self, message, user_state) -> tuple[str, str, types.ReplyKeyboardMarkup]:
        """Обработка текущего шага регистрации"""
        current_step = user_state.current_step
        
        if current_step in self.registration_steps:
            return self.registration_steps[current_step](message, user_state)
        else:
            return 'error', "❌ Неизвестный шаг регистрации.", None


# Создание глобального экземпляра менеджера регистрации
registration_manager = RegistrationManager()
