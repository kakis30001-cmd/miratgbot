"""
Память чата для Миры.
Хранит последние 300 сообщений из группового чата.
Использует PostgreSQL для персистентности.
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, List, Dict
import config

class ChatMemory:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        # Кэш в оперативной памяти
        self.messages: deque = deque(maxlen=config.CHAT_MEMORY_SIZE)
        self.last_message_time: Optional[datetime] = None
        self.online_cache: Dict[str, int] = {"online": 0, "max": 0}
        self.online_updated: Optional[datetime] = None
    
    async def connect(self):
        """Подключение к PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                config.DATABASE_URL,
                min_size=1,
                max_size=5
            )
            await self._create_tables()
            await self._load_recent_messages()
            print("✅ Память чата подключена (PostgreSQL)")
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            print("⚠️ Работаю без БД, только оперативная память")
    
    async def _create_tables(self):
        """Создание таблиц если их нет"""
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_created 
                ON chat_messages(created_at DESC)
            """)
    
    async def _load_recent_messages(self):
        """Загрузка последних сообщений из БД"""
        if not self.pool:
            return
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT username, user_id, message, created_at 
                    FROM chat_messages 
                    ORDER BY created_at DESC 
                    LIMIT $1
                """, config.CHAT_MEMORY_SIZE)
                
                for row in reversed(rows):
                    self.messages.append({
                        "username": row["username"],
                        "user_id": row["user_id"],
                        "message": row["message"],
                        "time": row["created_at"]
                    })
                
                if rows:
                    self.last_message_time = rows[0]["created_at"]
                
                print(f"📝 Загружено {len(self.messages)} сообщений из истории")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки истории: {e}")
    
    async def add_message(self, username: str, user_id: str, message: str):
        """Добавление сообщения в память"""
        now = datetime.now()
        
        msg_data = {
            "username": username,
            "user_id": user_id,
            "message": message,
            "time": now
        }
        
        self.messages.append(msg_data)
        self.last_message_time = now
        
        # Сохраняем в БД если доступна
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO chat_messages (username, user_id, message, created_at)
                        VALUES ($1, $2, $3, $4)
                    """, username, user_id, message, now)
            except Exception as e:
                print(f"⚠️ Ошибка сохранения в БД: {e}")
    
    def get_recent_context(self, limit: int = 50) -> str:
        """Получить последние сообщения для контекста AI"""
        if not self.messages:
            return ""
        
        recent = list(self.messages)[-limit:]
        lines = []
        for msg in recent:
            time_str = msg["time"].strftime("%H:%M")
            lines.append(f"[{time_str}] {msg['username']}: {msg['message']}")
        
        return "\n".join(lines)
    
    def time_since_last_message(self) -> float:
        """Сколько секунд прошло с последнего сообщения"""
        if not self.last_message_time:
            return float('inf')
        return (datetime.now() - self.last_message_time).total_seconds()
    
    def is_chat_dead(self, hours: float = 2.0) -> bool:
        """Проверяет, не затих ли чат"""
        return self.time_since_last_message() > hours * 3600
    
    async def cleanup_old_messages(self):
        """Удаление старых сообщений (старше 7 дней) из БД"""
        if not self.pool:
            return
        try:
            cutoff = datetime.now() - timedelta(days=7)
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM chat_messages WHERE created_at < $1
                """, cutoff)
                deleted = int(result.split()[-1]) if result else 0
                if deleted > 0:
                    print(f"🧹 Удалено {deleted} старых сообщений")
        except Exception as e:
            print(f"⚠️ Ошибка очистки: {e}")
    
    async def close(self):
        """Закрытие соединения с БД"""
        if self.pool:
            await self.pool.close()

# Глобальный экземпляр памяти
chat_memory = ChatMemory()
