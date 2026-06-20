"""
Основной файл бота Энди.
Обработчики команд и сообщений.
"""

import asyncio
import re
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReactionTypeEmoji
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import config
from memory import chat_memory
from server_info import *
from utils import get_server_online
from enderia_core import (
    enderia_thinks,
    should_respond_to_message,
    enderia_search_mod,
    build_enderia_prompt
)
from spontaneous import spontaneous

# Инициализация
default = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=config.BOT_TOKEN, default=default)
dp = Dispatcher(storage=MemoryStorage())


# ========== Клавиатуры ==========

def get_start_keyboard():
    """Клавиатура для /start (в ЛС)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 IP сервера", callback_data="info_ip")],
        [InlineKeyboardButton(text="📜 Правила", url=config.BASE_URL + "/rules")],
        [InlineKeyboardButton(text="💎 Донат", url=config.BASE_URL + "/donate")],
        [InlineKeyboardButton(text="📝 Заявка на мирный", url=config.BASE_URL + "/apply")],
    ])


# ========== РЕАКЦИИ ==========

async def react_to_message(message: Message):
    """
    Энди ставит реакцию на сообщение если там есть ключевые слова.
    """
    if not message.text:
        return
    
    # Не реагируем на свои сообщения
    if message.from_user.id == bot.id:
        return
    
    text_lower = message.text.lower()
    
    # Проверяем ключевые слова
    for keyword, emoji in config.ENDERIA_REACTIONS.items():
        if keyword in text_lower:
            try:
                # Если сообщение адресовано Энди — тоже ставим реакцию
                await message.react([ReactionTypeEmoji(emoji=emoji)])
                print(f"💜 Энди поставила {emoji} на '{text_lower[:40]}...'")
                return
            except Exception as e:
                print(f"❌ Ошибка реакции: {e}")
                return
    
    # Случайная реакция с шансом 3%
    if random.random() < 0.03:
        random_emoji = random.choice(["💜", "✨", "🌿", "💎", "🏠", "😊", "🎮", "⛏️"])
        try:
            await message.react([ReactionTypeEmoji(emoji=random_emoji)])
        except Exception as e:
            print(f"❌ Ошибка случайной реакции: {e}")


# ========== Обработчики команд ==========

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Команда /start — работает только в ЛС"""
    if message.chat.type != "private":
        return

    username = message.from_user.first_name or "игрок"
    online, max_players = await get_server_online()

    text = f"""приветик {username}! 💜

я энди — помощница в чате сервера lostearth

🎮 ip сервера:
java: {JAVA_IP}
bedrock: {BEDROCK_IP}:{BEDROCK_PORT}
версии: {VERSIONS}

👥 онлайн: {online}/{max_players}

я общаюсь в чате сервера, а тут могу только показать инфу. заходи в чат поболтать!

создал меня @ZOJlOTOY
владелец сервера @pelmewki379"""

    await message.answer(text, reply_markup=get_start_keyboard())


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = """чем я могу помочь:

• рассказать о сервере и донатах
• найти мод или ресурспак
• помочь с майнкрафтом
• просто поболтать

просто напиши мне в чате, я услышу 😊

команды:
/start - главная информация
/ip - адреса сервера
/online - онлайн
/donate - донат
/rules - правила"""

    await message.answer(text)


@dp.message(Command("ip"))
async def cmd_ip(message: Message):
    text = f"""🌐 lostearth

java: {JAVA_IP}
bedrock: {BEDROCK_IP}:{BEDROCK_PORT}
версии: {VERSIONS}"""
    await message.answer(text)


@dp.message(Command("online"))
async def cmd_online(message: Message):
    online, max_players = await get_server_online()
    if online > 0:
        text = f"сейчас на сервере {online} из {max_players} игроков 🎮"
    else:
        text = "сервер сейчас пустой заходи!"
    await message.answer(text)


@dp.message(Command("donate"))
async def cmd_donate(message: Message):
    text = f"""💎 донат lostearth

все деньги идут на хостинг!
каждый донат включает предыдущие

мирный режим:
• друид - 25грн/50руб
• оракул - 50грн/100руб
• монарх - 100грн/200руб
• херувим - 150грн/300руб
• архонт - 200грн/400руб
• серафим - 300грн/600руб

smp (скоро):
• путник - 50грн/100руб
• stranik - 100грн/200руб
• darkness - 150грн/300руб
• angel - 200грн/400руб
• archangel - 300грн/600руб

покупать у @pelmewki379
подробнее: {DONATE_URL}"""

    await message.answer(text)


@dp.message(Command("rules"))
async def cmd_rules(message: Message):
    text = f"""📜 правила lostearth:

• запрещены читы x-ray freecam - бан
• запрещена реклама серверов - бан по ip
• гриф и кража на спавне - бан
• оскорбления модерации - мут
• нельзя рушить дома на спавне

полные правила: {RULES_URL}"""
    await message.answer(text)


@dp.message(Command("apply"))
async def cmd_apply(message: Message):
    text = f"""📝 заявка на мирный режим

чтобы попасть на мирный режим нужна заявка
подать можно тут: {APPLY_URL}

после заявки жди ответа от администрации!"""
    await message.answer(text)


# ========== Вспомогательная функция ==========

def _extract_mod_query(text: str) -> str:
    """Извлекает запрос на поиск мода из сообщения"""
    text_lower = text.lower()
    patterns = [
        r"найди мод (.+)",
        r"какой мод (.+)",
        r"есть мод (.+)",
        r"мод (?:на|для|про) (.+)",
        r"ресурспак (.+)",
        r"посоветуй мод (.+)",
        r"нужен мод (.+)",
        r"порекомендуй мод (.+)",
        r"дай мод (.+)",
        r"моды? (?:на|для|про) (.+)",
        r"найди (.+) мод",
        r"посоветуй (.+) мод",
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            query = match.group(1).strip()
            query = re.sub(r'\b(мод|моды|мне|пожалуйста|плиз|плз)\b', '', query).strip()
            if query:
                return query
    return ""


# ========== Обработчик сообщений в чате ==========

@dp.message()
async def handle_chat_message(message: Message):
    """Обработка всех сообщений."""

    if not message.text:
        return

    if message.chat.type == "private":
        return

    username = message.from_user.first_name or message.from_user.username or "игрок"
    user_id = str(message.from_user.id)
    text = message.text

    # Сохраняем ВСЕ сообщения в память чата
    await chat_memory.add_message(username, user_id, text)

    # 🔥 ЭНДИ СТАВИТ РЕАКЦИИ
    await react_to_message(message)

    # Проверяем, обращаются ли к Энди
    is_directed = should_respond_to_message(text)

    # Проверяем, ответ на сообщение Энди
    is_reply_to_enderia = False
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == bot.id:
            is_reply_to_enderia = True

    if not is_directed and not is_reply_to_enderia:
        return

    # Проверка на запрос поиска мода
    mod_query = _extract_mod_query(text)
    if mod_query:
        await bot.send_chat_action(message.chat.id, action="typing")
        mod_result = await enderia_search_mod(mod_query)
        await message.reply(mod_result)
        return

    # Отвечаем через AI
    await bot.send_chat_action(message.chat.id, action="typing")
    response = await enderia_thinks(text, username, user_id)

    if response:
        await message.reply(response)


# ========== Callback для кнопок ==========

@dp.callback_query(lambda c: c.data == "info_ip")
async def callback_info_ip(callback: types.CallbackQuery):
    online, max_players = await get_server_online()
    text = f"""🌐 lostearth

java: {JAVA_IP}
bedrock: {BEDROCK_IP}:{BEDROCK_PORT}
версии: {VERSIONS}

👥 онлайн: {online}/{max_players}"""
    await callback.message.edit_text(text, reply_markup=get_start_keyboard())
    await callback.answer()


# ========== Периодические задачи ==========

async def spontaneous_loop():
    print("💬 Цикл спонтанных сообщений запущен")
    while True:
        await asyncio.sleep(60)
        try:
            await spontaneous.send_if_needed(bot, config.GROUP_CHAT_ID)
        except Exception as e:
            print(f"❌ Ошибка спонтанного цикла: {e}")


async def memory_cleanup_loop():
    while True:
        await asyncio.sleep(3600)
        await chat_memory.cleanup_old_messages()


# ========== Запуск ==========

async def main():
    print("=" * 50)
    print("💜 Энди — бот чата LostEarth")
    print("=" * 50)

    await chat_memory.connect()

    asyncio.create_task(spontaneous_loop())
    asyncio.create_task(memory_cleanup_loop())

    print("✅ Энди запущена и слушает чат")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await chat_memory.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
