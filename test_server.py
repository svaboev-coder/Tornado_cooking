#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Тестовый сервер работает!</h1><p>Если вы видите это сообщение, значит Flask работает корректно.</p>'

if __name__ == '__main__':
    print("🚀 Запуск тестового сервера...")
    print("🌐 Откройте в браузере: http://localhost:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
