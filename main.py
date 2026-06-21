"""
Точка входа для Railway.
Запускает бота Энди.
"""

import asyncio

if __name__ == "__main__":
    from bot import main as bot_main
    asyncio.run(bot_main())
