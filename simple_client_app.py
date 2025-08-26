#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template_string

app = Flask(__name__)

# Простая HTML страница для тестирования
SIMPLE_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Клиентское приложение - Тест</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h3 class="text-center">✅ Клиентское приложение работает!</h3>
                    </div>
                    <div class="card-body">
                        <p class="lead text-center">
                            Если вы видите эту страницу, значит клиентское приложение запущено корректно.
                        </p>
                        <div class="text-center">
                            <a href="/register" class="btn btn-primary">Тест регистрации</a>
                            <a href="/meals" class="btn btn-success">Тест питания</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(SIMPLE_HTML)

@app.route('/register')
def register():
    return '<h2>Страница регистрации</h2><p>Эта страница работает!</p><a href="/">Назад</a>'

@app.route('/meals')
def meals():
    return '<h2>Страница питания</h2><p>Эта страница работает!</p><a href="/">Назад</a>'

if __name__ == '__main__':
    print("🚀 Запуск упрощенного клиентского приложения...")
    print("🌐 Откройте в браузере: http://localhost:5001")
    app.run(host='localhost', port=5001, debug=True)




