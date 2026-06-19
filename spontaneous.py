"""
Спонтанные сообщения Миры.
Она может писать в чат сама раз в 4-8 часов, если там тихо.
"""

import asyncio
import random
from datetime import datetime, timedelta
from memory import chat_memory
from mira_core import get_self_message, mira_thinks
import config

class SpontaneousMessages:
    def __init__(self):
        self.last_self_message: datetime = datetime.now()
        self.enabled = True
        self.min_interval = config.SPONTANEOUS_MIN  # 4 часа
        self.max_interval = config.SPONTANEOUS_MAX  # 8 часов
        self.next_message_time: datetime = self._calculate_next()
    
    def _calculate_next(self) -> datetime:
        """Вычисляет время следующего сообщения"""
        interval = random.randint(self.min_interval, self.max_interval)
        return datetime.now() + timedelta(seconds=interval)
    
    def should_send(self) -> bool:
        """Проверяет, пора ли отправлять спонтанное сообщение"""
        if not self.enabled:
            return False
        
        now = datetime.now()
        
        # Проверяем время
        if now < self.next_message_time:
            return False
        
        # Проверяем, тихо ли в чате последние 2 часа
        if not chat_memory.is_chat_dead(2.0):
            # Если в чате активно — откладываем
            self.next_message_time = now + timedelta(seconds=random.randint(1800, 7200))
            return False
        
        return True
    
    async def send_if_needed(self, bot, chat_id: int):
        """Отправляет сообщение если нужно"""
        if self.should_send():
            # Генерируем сообщение через AI для естественности
            context = chat_memory.get_recent_context(30)
            
            if context:
                # Используем AI для генерации уместного сообщения
                ai_message = await mira_thinks(
                    "напиши что-то в чат чтобы разрядить тишину, ты видишь что все молчат уже пару часов",
                    "Мира",
                    "mira_bot"
                )
                if ai_message:
                    try:
                        await bot.send_message(chat_id, ai_message)
                    except Exception as e:
                        print(f"❌ Ошибка отправки спонтанного: {e}")
            else:
                # Если нет контекста — используем заготовки
                message = get_self_message()
                try:
                    await bot.send_message(chat_id, message)
                except Exception as e:
                    print(f"❌ Ошибка отправки: {e}")
            
            # Обновляем таймер
            self.last_self_message = datetime.now()
            self.next_message_time = self._calculate_next()
            print(f"💬 Отправлено спонтанное сообщение, следующее в {self.next_message_time.strftime('%H:%M')}")

# Глобальный экземпляр
spontaneous = SpontaneousMessages()
