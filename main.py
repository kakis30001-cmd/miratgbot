"""
Точка входа для Railway.
Запускает Flask (веб) и бота Энди одновременно.
"""

import asyncio
import os
from threading import Thread
from flask import Flask, send_from_directory

# Flask приложение
app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/rules')
@app.route('/rules.html')
def rules():
    return send_from_directory('static', 'rules.html')

@app.route('/donate')
@app.route('/donate.html')
def donate():
    return send_from_directory('static', 'donate.html')

@app.route('/apply')
@app.route('/apply.html')
def apply():
    return send_from_directory('static', 'apply.html')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# Запуск всего
if __name__ == "__main__":
    from bot import main as bot_main
    
    # Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Веб запущен на порту {os.environ.get('PORT', 8080)}")
    
    # Бот Энди в главном потоке
    asyncio.run(bot_main())
