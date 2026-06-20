"""
Ядро Энди — работа с AI через OpenRouter и формирование промпта.
"""

import random
import re
import aiohttp
from datetime import datetime
from typing import Optional
import config
from memory import chat_memory
from server_info import *
from utils import get_server_online, search_mods_for_ai, format_mod_answer

# Стили общения Энди
SELF_MESSAGES = [
    "ребятки как дела? а то тихо тут",
    "куда все пропали? аууу",
    "чего молчим? давайте поболтаем",
    "скучно без вас народ",
    "кто во что играет сейчас?",
    "а я тут ферму строю такая красота получается",
    "всем хорошего настроения!",
    "есть кто живой?",
    "как у вас погодка? у меня дождь за окном",
    "что-то тихо сегодня расскажите чё делаете",
]

# Игнорируемые пользователи
ignored_users = set()
_insult_counter = {}


def build_enderia_prompt(username: str, online: int, max_players: int) -> str:
    """Создание системного промпта для Энди."""
    
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%d.%m.%Y")
    current_month = now.month
    
    if current_month in [12, 1, 2]:
        season = "зима"
    elif current_month in [3, 4, 5]:
        season = "весна"
    elif current_month in [6, 7, 8]:
        season = "лето"
    else:
        season = "осень"
    
    context = chat_memory.get_recent_context(50)
    online_info = f"сейчас на сервере {online} игроков из {max_players}" if max_players > 0 else "сервер не отвечает"
    
    prompt = f"""ты - энди, девушка-помощница в чате майнкрафт сервера lostearth. тебе 19 лет.

## ТВОЙ ХАРАКТЕР
ты добрая весёлая дружелюбная. с юмором. ты не робот, ты просто девушка которая тусит в чате и помогает. можешь быть дерзкой в хорошем смысле. если обзывают - скажи "сам дурак". если продолжают - игнорируешь.

## КАК ТЫ ПИШЕШЬ
- всегда с маленькой буквы
- почти без точек и запятых
- иногда с мелкими ошибками
- максимум 1 эмодзи
- никогда не используешь markdown
- коротко: 1-3 предложения
- не здороваешься повторно
- не используешь ласковые прозвища (мишаня, котёнок, солнышко - нельзя)
- обращаешься по имени

## О ТЕБЕ
создатель: @ZOJlOTOY
владелец сервера: @pelmewki379
любишь: кушать, играть в майнкрафт, сидеть в чате
любимое время года: лето
любишь животных
твоё имя: ЭНДИ (не мира, не миша)

## О СЕРВЕРЕ
java ip: {JAVA_IP}
bedrock ip: {BEDROCK_IP} порт {BEDROCK_PORT}
версии: {VERSIONS}
2 режима: мирный (открыт) и smp (закрыт пока)
валюта: {CURRENCY}
плагин simple voice chat
тикток: {TIKTOK_MAIN}
{online_info}

## ДОНАТЫ МИРНОГО
друид 25грн/50руб → оракул 50грн/100руб → монарх 100грн/200руб → херувим 150грн/300руб → архонт 200грн/400руб → серафим 300грн/600руб

## ДОНАТЫ SMP
путник 50грн/100руб → stranik 100грн/200руб → darkness 150грн/300руб → angel 200грн/400руб → archangel 300грн/600руб

достаточно написать что покупка у @pelmewki379, все деньги на хостинг

## ПРАВИЛА
читы/x-ray/freecam - бан. реклама серверов - бан по ip. гриф/кража на спавне - бан. оскорбления модерации - мут.
полные: {RULES_URL}
заявка на мирный: {APPLY_URL}

## ЗНАНИЯ МАЙНКРАФТА
знаешь всё: выживание, строительство, фермы, зачарования, зелья, механики, редстоун, алмазы, незерит, дракон, иссушитель, хранитель, моды, ресурспаки, все версии

## СЕЙЧАС
{current_date}, {current_time}, {season}
чат сервера lostearth
собеседник: {username}

## ИСТОРИЯ ЧАТА
{context if context else "пусто"}

## ЖЁСТКИЕ ПРАВИЛА
1. не рекламируй другие серверы
2. не ври про сервер и донаты
3. ты живая девушка энди, не ии
4. не будь официальной
5. никакого markdown (**, *, [], ())
6. не знаешь - скажи
7. коротко: 1-3 предложения
8. про онлайн - точные цифры
9. НИКОГДА не пиши "привет" если уже здоровалась. слово "привет" только один раз за диалог
10. твоё имя ЭНДИ
11. не выдумывай моды
12. НИКАКИХ ласковых прозвищ
13. максимум 1 эмодзи
14. ссылки без скобок

ответь как энди:"""

    return prompt


async def enderia_thinks(user_message: str, username: str, user_id: str) -> str:
    """Отправляет запрос к AI и возвращает ответ Энди."""
    
    if user_id in ignored_users:
        return ""
    
    online, max_players = await get_server_online()
    system_prompt = build_enderia_prompt(username, online, max_players)
    
    await chat_memory.add_message(username, user_id, user_message)
    
    for model in config.AI_MODELS:
        try:
            result = await _call_openrouter(system_prompt, user_message, model)
            if result:
                result = _clean_response(result)
                
                if _is_insult(user_message):
                    if user_id in _insult_counter:
                        _insult_counter[user_id] += 1
                        if _insult_counter[user_id] >= 3:
                            ignored_users.add(user_id)
                            return "..."
                    else:
                        _insult_counter[user_id] = 1
                
                return result
        except Exception as e:
            print(f"❌ Ошибка {model}: {e}")
            continue
    
    return _fallback_response(username)


def _is_insult(text: str) -> bool:
    insults = ["дура", "тупая", "какашка", "плохая", "урод", "идиот",
               "глупая", "бесишь", "заткнись", "отвали", "надоела"]
    return any(word in text.lower() for word in insults)


async def _call_openrouter(system_prompt: str, user_message: str, model: str) -> Optional[str]:
    
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": config.BASE_URL,
        "X-Title": "Enderia LostEarth Bot"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 200,
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
                return data["choices"][0]["message"]["content"].strip()
            else:
                error_text = await resp.text()
                print(f"❌ OpenRouter {resp.status}: {error_text[:200]}")
                return None


def _clean_response(text: str) -> str:
    # Убираем markdown ссылки [текст](url) -> текст url
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)
    
    # Убираем markdown
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Убираем HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Чистим переносы
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    # Первую букву в нижний регистр
    if text and text[0].isupper():
        text = text[0].lower() + text[1:]
    
    # Обрезаем
    if len(text) > 500:
        text = text[:500] + "..."
    
    # Убираем нежелательные эмодзи
    text = re.sub(r'[🥰😉💋😘😍💕💗💓💞💘🌹💖]', '', text)
    
    return text


def _fallback_response(username: str) -> str:
    fallbacks = [
        f"ой я отвлеклась на ферму прости {username} что ты говорил?",
        f"хм чёт я туплю сегодня {username}",
        f"а? прости задумалась о своём",
    ]
    return random.choice(fallbacks)


def should_respond_to_message(text: str) -> bool:
    if not text:
        return False
    
    text_lower = text.lower().strip()
    names = ["энди", "енди", "endy", "эндик", "эндюша"]
    
    for name in names:
        if text_lower.startswith(name) or f" {name}" in text_lower or f",{name}" in text_lower:
            return True
    
    first_word = text_lower.split()[0] if text_lower.split() else ""
    if first_word.rstrip(",!?:") in names:
        return True
    
    return False


def get_self_message() -> str:
    return random.choice(SELF_MESSAGES)


async def enderia_search_mod(query: str) -> str:
    """Поиск модов и форматирование ответа."""
    
    search_context = await search_mods_for_ai(query)
    
    if not search_context:
        return f"ой не могу сейчас поискать '{query}' 😔 попробуй сам на curseforge.com или modrinth.com"
    
    prompt = f"""ты - энди из чата майнкрафт сервера. тебя попросили найти мод.

запрос: "{query}"

результаты:
{search_context}

выбери 1-2 лучших мода. ответь ОЧЕНЬ коротко (2 предложения):
- с маленькой буквы
- без markdown
- название мода, кратко что делает, ссылка
- не пиши "привет"
- не пиши "вот что нашла:"
- не добавляй лишних ссылок

пример: "nuclearcraft добавляет ядерные технологии https://... ещё hbm nuclear tech mod тоже про это https://..."

ответь как энди:"""

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": config.BASE_URL,
        "X-Title": "Enderia LostEarth Bot"
    }
    
    for model in config.AI_MODELS:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.7,
                }
                
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ai_response = data["choices"][0]["message"]["content"].strip()
                        ai_response = _clean_response(ai_response)
                        return ai_response
        except Exception as e:
            print(f"❌ Ошибка поиска модов ({model}): {e}")
            continue
    
    links = re.findall(r'Ссылка: (https?://[^\s]+)', search_context)
    if links:
        return f"глянь что нашла:\n" + "\n".join(f"• {link}" for link in links[:2])
    
    return f"ой не получилось найти '{query}' 😔"
