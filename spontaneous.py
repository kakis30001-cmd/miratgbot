"""
Спонтанные сообщения Энди.
Пишет в чат раз в 4-8 часов если тихо.
"""

import asyncio
import random
from datetime import datetime, timedelta
from memory import chat_memory
from enderia_core import get_self_message, enderia_thinks
import config

class SpontaneousMessages:
    def __init__(self):
        self.last_self_message = datetime.now()
        self.enabled = True
        self.min_interval = config.SPONTANEOUS_MIN
        self.max_interval = config.SPONTANEOUS_MAX
        self.next_message_time = self._calculate_next()
    
    def _calculate_next(self):
        interval = random.randint(self.min_interval, self.max_interval)
        return datetime.now() + timedelta(seconds=interval)
    
    def should_send(self):
        if not self.enabled:
            return False
        
        now = datetime.now()
        if now < self.next_message_time:
            return False
        
        if not chat_memory.is_chat_dead(2.0):
            self.next_message_time = now + timedelta(seconds=random.randint(1800, 7200))
            return False
        
        return True
    
    async def send_if_needed(self, bot, chat_id):
        if self.should_send():
            context = chat_memory.get_recent_context(30)
            
            if context:
                prompt = f"""ты - энди, девушка из чата майнкрафт сервера.
в чате тишина уже пару часов. напиши что-то чтобы разрядить обстановку.
спроси как дела или предложи поболтать.

недавний чат:
{context}

одно короткое сообщение, с маленькой буквы, без markdown.
ответь как энди:"""
                
                ai_message = await enderia_thinks(prompt, "чат", "system")
                if ai_message:
                    try:
                        await bot.send_message(chat_id, ai_message)
                    except Exception as e:
                        print(f"❌ Ошибка отправки: {e}")
            else:
                message = get_self_message()
                try:
                    await bot.send_message(chat_id, message)
                except Exception as e:
                    print(f"❌ Ошибка отправки: {e}")
            
            self.last_self_message = datetime.now()
            self.next_message_time = self._calculate_next()

spontaneous = SpontaneousMessages()
