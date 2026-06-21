"""
Точка входа для Railway.
Запускает веб-сервер и бота Энди.
"""

import asynci
import os
from threading import Thread

# Импортируем Flask не как "app" чтобы Railway не цеплялся
from flask import Flask as FlaskClass, send_from_directory

def create_app():
    """Создаём Flask приложение внутри функции."""
    app = FlaskClass(__name__, static_folder='static')
    
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
    
    @app.route('/health')
    def health():
        return "OK", 200
    
    return app

def run_flask():
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    # Используем waitress вместо app.run для продакшена
    try:
        from waitress import serve
        print(f"🌐 Веб (waitress) на порту {port}")
        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        print(f"🌐 Веб (flask) на порту {port}")
        app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    # Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Бот Энди в главном потоке
    from bot import main as bot_main
    asyncio.run(bot_main())
