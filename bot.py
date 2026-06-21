"""
Основной файл бота Энди.
Обработчики команд и сообщений.
"""

import asyncio
import re
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReactionTypeEmoji
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
)
from spontaneous import spontaneous

# Инициализация
default = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=config.BOT_TOKEN, default=default)
dp = Dispatcher(storage=MemoryStorage())


# ========== РЕАКЦИИ ==========

async def react_to_message(message: Message):
    """Энди ставит реакцию на сообщения с ключевыми словами."""
    if not message.text:
        return
    if message.from_user.id == bot.id:
        return

    text_lower = message.text.lower()

    reaction_map = {
        "🔥": ["круто", "топ", "имба", "збс", "огонь"],
        "👍": ["красиво", "молодец", "хорошо", "найс", "ок"],
        "❤️": ["красота", "люблю"],
        "👏": ["поздравляю", "ура", "молодчик"],
        "💜": ["спасибо", "энди"],
        "😂": ["смешно", "ахах", "лол", "ржу", "угар", "прикол", "ор"],
        "😢": ["грустно", "жаль", "обидно", "плохо"],
        "😱": ["ого", "ничего себе", "офигеть", "шок"],
        "💎": ["алмаз", "алмазы"],
        "💀": ["умер", "смерть"],
        "⛏️": ["шахта", "копать"],
        "🌾": ["ферма", "урожай"],
        "🏆": ["победил", "победа", "выиграл"],
        "💚": ["крипер"],
        "🖤": ["эндер"],
        "🐉": ["дракон"],
    }

    for emoji, keywords in reaction_map.items():
        if any(kw in text_lower for kw in keywords):
            try:
                await message.react([ReactionTypeEmoji(emoji=emoji)])
                return
            except Exception:
                return

    # Случайная реакция 5%
    if random.random() < 0.05:
        try:
            emoji = random.choice(["💜", "✨", "🌿", "💎", "⛏️", "👍", "🔥", "😊", "🎮"])
            await message.react([ReactionTypeEmoji(emoji=emoji)])
        except Exception:
            pass


# ========== КОМАНДЫ ==========

@dp.message(CommandStart())
async def cmd_start(message: Message):
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

я общаюсь в чате сервера, а тут могу только показать инфу

создал меня @ZOJlOTOY
владелец сервера @pelmewki379

скоро будет сайт со всей инфой!"""

    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = """чем я могу помочь:

• рассказать о сервере и донатах
• найти мод или ресурспак
• помочь с майнкрафтом
• просто поболтать

команды:
/start /ip /online /donate /rules"""
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
    text = """💎 донат lostearth

все деньги идут на хостинг!
каждый донат включает предыдущие

мирный режим:
друид 25грн/50руб → оракул 50грн/100руб → монарх 100грн/200руб → херувим 150грн/300руб → архонт 200грн/400руб → серафим 300грн/600руб

smp (скоро):
путник → stranik → darkness → angel → archangel

покупать у @pelmewki379"""
    await message.answer(text)


@dp.message(Command("rules"))
async def cmd_rules(message: Message):
    text = """📜 правила lostearth:

• запрещены читы x-ray freecam - бан
• запрещена реклама серверов - бан по ip
• гриф и кража на спавне - бан
• оскорбления модерации - мут
• нельзя рушить дома на спавне

скоро сайт с полными правилами"""
    await message.answer(text)


@dp.message(Command("apply"))
async def cmd_apply(message: Message):
    text = """📝 заявка на мирный режим

чтобы попасть на мирный нужна заявка
пиши @pelmewki379

скоро сайт с формой заявки"""
    await message.answer(text)


# ========== ПОИСК МОДОВ ==========

def _extract_mod_query(text: str) -> str:
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
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            query = match.group(1).strip()
            query = re.sub(r'\b(мод|моды|мне|пожалуйста|плиз|плз)\b', '', query).strip()
            if query:
                return query
    return ""


# ========== ОБРАБОТЧИК СООБЩЕНИЙ ==========

@dp.message()
async def handle_chat_message(message: Message):
    if not message.text:
        return
    if message.chat.type == "private":
        return

    username = message.from_user.first_name or message.from_user.username or "игрок"
    user_id = str(message.from_user.id)
    text = message.text

    # Сохраняем в память
    await chat_memory.add_message(username, user_id, text)

    # Реакции
    await react_to_message(message)

    # Проверяем обращение к Энди
    is_directed = should_respond_to_message(text)
    is_reply = bool(message.reply_to_message and message.reply_to_message.from_user.id == bot.id)

    if not is_directed and not is_reply:
        return

    # Поиск мода
    mod_query = _extract_mod_query(text)
    if mod_query:
        await bot.send_chat_action(message.chat.id, action="typing")
        result = await enderia_search_mod(mod_query)
        await message.reply(result)
        return

    # Ответ через AI
    await bot.send_chat_action(message.chat.id, action="typing")
    response = await enderia_thinks(text, username, user_id)
    if response:
        await message.reply(response)


# ========== ФОНОВЫЕ ЗАДАЧИ ==========

async def spontaneous_loop():
    print("💬 Цикл спонтанных сообщений запущен")
    while True:
        await asyncio.sleep(60)
        try:
            await spontaneous.send_if_needed(bot, config.GROUP_CHAT_ID)
        except Exception as e:
            print(f"❌ Ошибка спонтанного: {e}")


async def memory_cleanup_loop():
    while True:
        await asyncio.sleep(3600)
        await chat_memory.cleanup_old_messages()


# ========== ЗАПУСК ==========

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
