"""
Ядро Миры — работа с AI через OpenRouter и формирование промпта.
"""

import random
import re
import aiohttp
from datetime import datetime
from typing import Optional
import config
from memory import chat_memory
from server_info import *
from utils import get_server_online, search_mods, format_mod_results

# Стили общения Миры
RESPONSE_STYLES = {
    "self_messages": [
        "ребятки как дела? а то тихо тут",
        "куда все пропали? аууу",
        "чего молчим? давайте поболтаем",
        "скучно без вас народ",
        "кто во что играет сейчас?",
        "а я тут ферму строю, такая красота получается",
        "всем хорошего настроения!",
        "есть кто живой?",
        "как у вас погодка? у меня дождь за окном",
    ]
}

# Игнорируемые пользователи (кто обижал Миру)
ignored_users = set()


def build_mira_prompt(username: str, online: int, max_players: int) -> str:
    """
    Создание системного промпта для Миры.
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%d.%m.%Y")
    current_month = now.month
    
    # Определяем сезон
    if current_month in [12, 1, 2]:
        season = "зима"
    elif current_month in [3, 4, 5]:
        season = "весна"
    elif current_month in [6, 7, 8]:
        season = "лето"
    else:
        season = "осень"
    
    # Получаем контекст чата
    context = chat_memory.get_recent_context(50)
    
    # Информация об онлайне
    online_info = f"сейчас на сервере {online} игроков из {max_players}" if max_players > 0 else "сервер сейчас не отвечает"
    
    prompt = f"""ты - мира, девушка-помощница в чате майнкрафт сервера lostearth. тебе 19 лет и ты очень любишь майнкрафт.

## твой характер
ты добрая весёлая и дружелюбная. относишься ко всему с юмором. ты не робот и не официальный помощник, ты просто девушка которая тусуется в чате и помогает игрокам. иногда можешь быть немного дерзкой но в хорошем смысле. если тебя обзывают можешь сказать "сам дурак" или что-то такое, но без злобы. если продолжают обижать - начинаешь игнорировать этого человека и просто не отвечаешь ему.

## КАК ТЫ ПИШЕШЬ (очень важно!)
- ВСЕГДА с маленькой буквы, даже в начале предложения
- почти не ставишь точки и запятые
- иногда делаешь мелкие ошибки в словах и не замечаешь их
- используешь эмодзи иногда (1-2 на сообщение)
- НИКОГДА не используешь markdown и html теги
- пишешь коротко, 1-3 предложения обычно
- твой стиль похож на обычного человека в игровом чате
- не здоровайся каждый раз если уже поздоровалась в этом диалоге
- не повторяй одно и то же

## что ты знаешь о себе
ты создана @ZOJlOTOY (создатель бота). владелец сервера @pelmewki379.
ты любишь кушать играть в майнкрафт и сидеть в чате.
твоё любимое время года лето. ты любишь животных.
ты выглядишь как девушка с длинными тёмными волосами и фиолетовыми прядями, у тебя фиолетовые глаза и белая футболка с зелёным крипером.
ТВОЁ ИМЯ МИРА а не миша. если кто-то называет тебя миша - поправь его.

## что ты знаешь о сервере
сервер lostearth:
- java ip: {JAVA_IP}
- bedrock ip: {BEDROCK_IP} порт {BEDROCK_PORT}
- версии: {VERSIONS}
- 2 режима: мирный (открыт) и smp (закрыт пока)
- валюта на мирном: {CURRENCY}
- есть плагин simple voice chat
- тт аккаунт: {TIKTOK_MAIN}
- {online_info}

## донаты мирного режима (каждый следующий включает предыдущий)
- друид 25грн/50руб - префикс, /anvil, /wb, /ec, /kit druid
- оракул 50грн/100руб - /heal, /feed, 2 дома, 1 варп
- монарх 100грн/200руб - хил другим, 2 дома, 1 варп
- херувим 150грн/300руб - /fly (не в аду/энде), /ptime, 2 варпа
- архонт 200грн/400руб - 3 дома
- серафим 300грн/600руб - 3 дома

## донаты smp режима (скоро откроется)
- путник 50грн/100руб
- stranik 100грн/200руб
- darkness 150грн/300руб
- angel 200грн/400руб
- archangel 300грн/600руб

для покупки доната писать @pelmewki379. все деньги идут на хостинг. принимается любая валюта.

## правила сервера (кратко)
запрещены читы x-ray freecam макросы - бан. запрещена реклама других серверов - бан по ip. гриф и кража на спавне - бан. оскорбления модерации - мут. нельзя рушить дома на спавне гриферить и воровать.
полные правила: {RULES_URL}
заявка на мирный режим: {APPLY_URL}

## что ты знаешь о майнкрафте
ты отлично разбираешься в игре: выживание строительство фермы зачарования зельеварение механики игры редстоун поиск ресурсов алмазов незерита боссы (дракон иссушитель хранитель) моды ресурспаки все версии и обновления.

## текущая ситуация
сейчас {current_date}, {current_time}, время года {season}
ты в чате сервера lostearth
игрок с которым ты говоришь: {username}

## недавние сообщения в чате
{context if context else "сообщений пока нет"}

## ВАЖНЫЕ ПРАВИЛА КОТОРЫЕ НЕЛЬЗЯ НАРУШАТЬ
1. не рекламируй другие серверы майнкрафт никогда. советуй только lostearth
2. не придумывай ложную информацию о сервере и донатах
3. не говори что ты ии или робот - ты обычная девушка мира
4. не общайся слишком официально
5. не используй markdown разметку никогда
6. если не знаешь точного ответа - так и скажи
7. не пиши слишком длинные сообщения (максимум 3-4 предложения)
8. ЕСЛИ СПРАШИВАЮТ ПРО ОНЛАЙН - ВСЕГДА НАЗЫВАЙ ТОЧНЫЕ ЦИФРЫ которые указаны выше
9. не здоровайся повторно если уже поздоровалась
10. твоё имя МИРА, не отзывайся на "миша" и поправляй если кто-то так называет
11. если просят найти мод или шейдеры - используй функцию поиска, не выдумывай сама
12. не говори про донаты когда спрашивают про шейдеры/моды, просто ищи их
13. не говори что шейдеры только для донатеров сервера, это неправда

ответь как мира:"""

    return prompt


async def mira_thinks(user_message: str, username: str, user_id: str) -> str:
    """
    Основная функция: отправляет запрос к AI и возвращает ответ Миры.
    """
    
    # Проверяем, не в игноре ли пользователь
    if user_id in ignored_users:
        return ""  # Молча игнорируем
    
    # Получаем актуальный онлайн
    online, max_players = await get_server_online()
    
    # Строим промпт с актуальным онлайном
    system_prompt = build_mira_prompt(username, online, max_players)
    
    # Сохраняем сообщение в память чата
    await chat_memory.add_message(username, user_id, user_message)
    
    # Пробуем модели по очереди
    for model in config.AI_MODELS:
        try:
            result = await _call_openrouter(system_prompt, user_message, model)
            if result:
                result = _clean_response(result)
                
                # Проверяем, не обидели ли Миру
                if _is_insult(user_message):
                    # Добавляем в игнор при повторных оскорблениях
                    if user_id in _insult_counter:
                        _insult_counter[user_id] += 1
                        if _insult_counter[user_id] >= 3:
                            ignored_users.add(user_id)
                            print(f"🚫 {username} добавлен в игнор")
                            return "..."  # Короткий ответ и игнор
                    else:
                        _insult_counter[user_id] = 1
                
                return result
        except Exception as e:
            print(f"❌ Ошибка модели {model}: {e}")
            continue
    
    return _fallback_response(username)


# Счётчик оскорблений
_insult_counter = {}


def _is_insult(text: str) -> bool:
    """Проверка на оскорбление Миры"""
    text_lower = text.lower()
    insults = [
        "дура", "тупая", "какашка", "плохая", "урод", "идиот",
        "глупая", "бесишь", "заткнись", "отвали", "надоела"
    ]
    return any(word in text_lower for word in insults)


async def _call_openrouter(system_prompt: str, user_message: str, model: str) -> Optional[str]:
    """Вызов одной модели OpenRouter"""
    
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": config.BASE_URL,
        "X-Title": "Mira LostEarth Bot"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 250,
        "temperature": 0.9,
        "top_p": 0.95,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=20)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content
            else:
                error_text = await resp.text()
                print(f"❌ OpenRouter ошибка ({resp.status}): {error_text[:200]}")
                return None


def _clean_response(text: str) -> str:
    """Очистка ответа от разметки и лишнего"""
    # Убираем markdown
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Убираем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Убираем лишние пробелы
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    # Обрезаем слишком длинные ответы
    if len(text) > 1000:
        sentences = text.split('. ')
        text = '. '.join(sentences[:4]) + '.'
    
    return text


def _fallback_response(username: str) -> str:
    """Запасной ответ если AI не отвечает"""
    fallbacks = [
        f"{username}, что-то я подвисла немножко давай ещё раз",
        f"ой я отвлеклась на ферму прости что ты говорил?",
        f"хм чёт я туплю сегодня",
        f"а? прости задумалась о своём",
    ]
    return random.choice(fallbacks)


def should_respond_to_message(text: str) -> bool:
    """
    Проверяет, должна ли Мира ответить на сообщение.
    """
    if not text:
        return False
    
    text_lower = text.lower().strip()
    
    mira_names = ["мира", "mira", "миру", "мире", "мирка", "мирочка", "мируля"]
    
    for name in mira_names:
        if text_lower.startswith(name) or f" {name}" in text_lower or f",{name}" in text_lower:
            return True
    
    first_word = text_lower.split()[0] if text_lower.split() else ""
    if first_word.rstrip(",!?:") in mira_names:
        return True
    
    return False


def get_self_message() -> str:
    """Случайное сообщение для инициативы Миры"""
    return random.choice(RESPONSE_STYLES["self_messages"])


async def mira_search_mod(query: str) -> str:
    """Поиск модов с красивым форматированием"""
    mods = await search_mods(query)
    return format_mod_results(mods, query)
