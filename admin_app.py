#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError
from datetime import datetime, timedelta
import logging
import os
from database import db_manager
from sqlite_backup import sqlite_backup_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin-secret-key-here'
app.config['WTF_CSRF_ENABLED'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Инициализация менеджеров
db_manager_instance = db_manager
backup_manager = sqlite_backup_manager

# Формы
class RegistrationForm(FlaskForm):
    """Форма регистрации на питание"""
    building = SelectField('Корпус', validators=[DataRequired(message='Выберите корпус')])
    room = SelectField('Номер', validators=[DataRequired(message='Выберите номер')])
    check_in_date = DateField('Дата заезда', validators=[DataRequired(message='Выберите дату заезда')])
    check_out_date = DateField('Дата отъезда', validators=[DataRequired(message='Выберите дату отъезда')])
    representative_name = StringField('ФИО представителя', validators=[
        DataRequired(message='Введите ФИО представителя'),
        Length(min=2, max=100, message='ФИО должно содержать от 2 до 100 символов')
    ])
    
    def validate_check_out_date(self, field):
        """Проверка, что дата отъезда не раньше даты заезда"""
        if field.data and self.check_in_date.data:
            if field.data <= self.check_in_date.data:
                raise ValidationError('Дата отъезда должна быть позже даты заезда')
    
    def validate_check_in_date(self, field):
        """Проверка, что дата заезда не в прошлом"""
        if field.data and field.data < datetime.now().date():
            raise ValidationError('Дата заезда не может быть в прошлом')
    
    def validate_check_out_date(self, field):
        """Проверка, что дата отъезда не в прошлом и не раньше даты заезда"""
        if field.data:
            if field.data < datetime.now().date():
                raise ValidationError('Дата отъезда не может быть в прошлом')
            if self.check_in_date.data and field.data <= self.check_in_date.data:
                raise ValidationError('Дата отъезда должна быть позже даты заезда')

# Маршруты
@app.route('/')
def index():
    """Главная страница администратора"""
    try:
        # Получаем статистику
        stats = get_statistics()
        return render_template('index.html', stats=stats, version='1.1')
    except Exception as e:
        logger.error(f"Ошибка на главной странице: {e}")
        flash('Ошибка загрузки данных', 'error')
        return render_template('index.html', stats={}, version='1.1')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    form = RegistrationForm()
    
    # Заполняем выбор корпусов и номеров
    buildings = get_available_buildings()
    form.building.choices = [('', 'Выберите корпус')] + [(b, b) for b in buildings]
    
    if form.building.data:
        rooms = get_rooms_in_building(form.building.data)
        form.room.choices = [('', 'Выберите номер')] + [(r, r) for r in rooms]
    else:
        form.room.choices = [('', 'Сначала выберите корпус')]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Проверяем доступность номера
                room_available = check_room_availability(
                    form.room.data,
                    form.check_in_date.data,
                    form.check_out_date.data
                )
                
                if not room_available['available']:
                    flash(f'Номер занят: {room_available["conflicts"]}', 'error')
                    return render_template('register.html', form=form, datetime=datetime)
                
                # Сохраняем данные в сессии для следующего шага
                session['registration_data'] = {
                    'building': form.building.data,
                    'room': form.room.data,
                    'check_in_date': form.check_in_date.data.strftime('%Y-%m-%d'),
                    'check_out_date': form.check_out_date.data.strftime('%Y-%m-%d'),
                    'representative_name': form.representative_name.data
                }
                
                return redirect(url_for('meals'))
                
            except Exception as e:
                logger.error(f"Ошибка при регистрации: {e}")
                flash('Произошла ошибка. Попробуйте позже.', 'error')
    
    return render_template('register.html', form=form, datetime=datetime)

@app.route('/meals', methods=['GET', 'POST'])
def meals():
    """Страница заполнения питания"""
    if 'registration_data' not in session:
        flash('Сначала заполните данные регистрации', 'error')
        return redirect(url_for('register'))
    
    reg_data = session['registration_data']
    
    # Генерируем даты для заполнения
    start_date = datetime.strptime(reg_data['check_in_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(reg_data['check_out_date'], '%Y-%m-%d').date()
    
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    if request.method == 'POST':
        try:
            # Обрабатываем данные питания
            meals_data = {}
            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                meals_data[date_str] = {
                    'breakfast_adults': int(request.form.get(f'breakfast_adults_{date_str}', 0)),
                    'breakfast_children': int(request.form.get(f'breakfast_children_{date_str}', 0)),
                    'lunch_adults': int(request.form.get(f'lunch_adults_{date_str}', 0)),
                    'lunch_children': int(request.form.get(f'lunch_children_{date_str}', 0)),
                    'dinner_adults': int(request.form.get(f'dinner_adults_{date_str}', 0)),
                    'dinner_children': int(request.form.get(f'dinner_children_{date_str}', 0))
                }
            
            # Сохраняем регистрацию
            result = save_registration(reg_data, meals_data)
            
            if result['success']:
                # Очищаем сессию
                session.pop('registration_data', None)
                flash('Регистрация успешно завершена!', 'success')
                return redirect(url_for('success'))
            else:
                flash(f'Ошибка при сохранении: {result["error"]}', 'error')
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении питания: {e}")
            flash('Произошла ошибка. Попробуйте позже.', 'error')
    
    return render_template('meals.html', 
                         registration_data=reg_data, 
                         dates=dates)

@app.route('/success')
def success():
    """Страница успешной регистрации"""
    return render_template('success.html')

@app.route('/admin')
def admin():
    """Административная панель"""
    try:
        stats = get_statistics()
        return render_template('admin.html', stats=stats)
    except Exception as e:
        logger.error(f"Ошибка в админ панели: {e}")
        flash('Ошибка загрузки данных', 'error')
        return render_template('admin.html', stats={})

@app.route('/api/check_room')
def check_room():
    """API для проверки доступности номера"""
    try:
        room = request.args.get('room')
        check_in = datetime.strptime(request.args.get('check_in'), '%Y-%m-%d').date()
        check_out = datetime.strptime(request.args.get('check_out'), '%Y-%m-%d').date()
        
        result = check_room_availability(room, check_in, check_out)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка проверки номера: {e}")
        return jsonify({'available': False, 'error': str(e)})

@app.route('/api/get_rooms/<building>')
def get_rooms(building):
    """API для получения номеров в корпусе"""
    try:
        rooms = get_rooms_in_building(building)
        return jsonify(rooms)
    except Exception as e:
        logger.error(f"Ошибка получения номеров: {e}")
        return jsonify([])

# Вспомогательные функции
def get_available_buildings():
    """Получение списка доступных корпусов"""
    try:
        cursor = db_manager_instance.connection.cursor()
        cursor.execute('SELECT DISTINCT SUBSTRING(номер, 1, POSITION(\'/\' IN номер)-1) as building FROM "справочник номеров" ORDER BY building')
        buildings = [row[0] for row in cursor.fetchall()]
        return buildings
    except Exception as e:
        logger.error(f"Ошибка получения корпусов: {e}")
        return []

def get_rooms_in_building(building):
    """Получение номеров в корпусе"""
    try:
        cursor = db_manager_instance.connection.cursor()
        cursor.execute('SELECT номер FROM "справочник номеров" WHERE номер LIKE %s ORDER BY номер', (f"{building}/%",))
        rooms = [row[0] for row in cursor.fetchall()]
        return rooms
    except Exception as e:
        logger.error(f"Ошибка получения номеров: {e}")
        return []

def check_room_availability(room, check_in, check_out):
    """Проверка доступности номера"""
    try:
        cursor = db_manager_instance.connection.cursor()
        cursor.execute("""
            SELECT ФИО, дата FROM посетители 
            WHERE номер = %s AND дата BETWEEN %s AND %s
        """, (room, check_in.strftime('%Y-%m-%d'), check_out.strftime('%Y-%m-%d')))
        
        conflicts = cursor.fetchall()
        if conflicts:
            conflict_dates = [f"{conflict[1]} ({conflict[0]})" for conflict in conflicts]
            return {
                'available': False, 
                'conflicts': ', '.join(conflict_dates)
            }
        return {'available': True}
    except Exception as e:
        logger.error(f"Ошибка проверки доступности: {e}")
        return {'available': False, 'error': str(e)}

def save_registration(reg_data, meals_data):
    """Сохранение регистрации в базу данных"""
    try:
        cursor = db_manager_instance.connection.cursor()
        
        for date_str, meals in meals_data.items():
            cursor.execute("""
                INSERT INTO посетители (номер, дата, ФИО, зд, зв, од, ов, уд, ув)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                reg_data['room'],
                date_str,
                reg_data['representative_name'],
                meals['breakfast_adults'],
                meals['breakfast_children'],
                meals['lunch_adults'],
                meals['lunch_children'],
                meals['dinner_adults'],
                meals['dinner_children']
            ))
        
        db_manager_instance.connection.commit()
        logger.info(f"Регистрация сохранена: {reg_data['representative_name']} в {reg_data['room']}")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Ошибка сохранения регистрации: {e}")
        return {'success': False, 'error': str(e)}

def get_statistics():
    """Получение статистики"""
    try:
        cursor = db_manager_instance.connection.cursor()
        
        # Общее количество записей
        cursor.execute("SELECT COUNT(*) FROM посетители")
        total_records = cursor.fetchone()[0]
        
        # Количество номеров
        cursor.execute('SELECT COUNT(*) FROM "справочник номеров"')
        total_rooms = cursor.fetchone()[0]
        
        # Записи за сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM посетители WHERE дата = %s", (today,))
        today_records = cursor.fetchone()[0]
        
        return {
            'total_records': total_records,
            'total_rooms': total_rooms,
            'today_records': today_records
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {}

# Обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    try:
        # Инициализация базы данных
        if not db_manager_instance.is_connected():
            db_manager_instance.connect()
        
        # Создание резервной копии
        backup_manager.create_backup()
        
        print("✅ Административное приложение запущено")
        print("✅ Подключение к базе данных установлено")
        print("✅ Резервная копия создана")
        print("🌐 Административный интерфейс доступен по адресу: http://127.0.0.1:5000")
        
        # Запуск административного приложения на порту 5000
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        logger.error(f"Ошибка запуска административного приложения: {e}")
        print(f"❌ Ошибка запуска: {e}")

