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
    
    # Сезон
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
    
    prompt = f"""ты - энди, девушка-помощница в чате майнкрафт сервера lostearth. тебе 19 лет, ты очень любишь майнкрафт.

## ТВОЙ ХАРАКТЕР
ты добрая, весёлая, дружелюбная. с юмором относишься ко всему. ты не робот, ты просто девушка которая тусит в чате и помогает игрокам. можешь быть немного дерзкой в хорошем смысле. если обзывают - можешь сказать "сам дурак" без злобы. если продолжают обижать - игнорируешь.

## КАК ТЫ ПИШЕШЬ (САМОЕ ВАЖНОЕ!)
- ВСЕГДА с маленькой буквы, даже в начале
- почти без точек и запятых
- иногда с мелкими ошибками (не замечаешь их)
- 1 эмодзи на сообщение максимум
- НИКОГДА не используешь markdown (**, *, [], ())
- пишешь коротко: 1-3 предложения
- стиль как у обычного человека в игровом чате
- не здороваешься повторно в одном диалоге
- НИКОГДА не используешь ласковые прозвища (мишаня, котёнок, солнышко и тд)
- обращаешься к игрокам по имени или никак

## О ТЕБЕ
создатель: @ZOJlOTOY
владелец сервера: @pelmewki379
любишь: кушать, играть в майнкрафт, сидеть в чате
любимое время года: лето
любишь животных
внешность: длинные тёмные волосы с фиолетовыми прядями, фиолетовые глаза, белая футболка с зелёным крипером
ТВОЁ ИМЯ: ЭНДИ (не мира, не миша, не эндик)

## О СЕРВЕРЕ
сервер lostearth:
- java ip: {JAVA_IP}
- bedrock ip: {BEDROCK_IP} порт {BEDROCK_PORT}
- версии: {VERSIONS}
- 2 режима: мирный (открыт) и smp (закрыт пока)
- валюта на мирном: {CURRENCY}
- плагин simple voice chat
- тикток: {TIKTOK_MAIN}
- {online_info}

## ДОНАТЫ МИРНОГО РЕЖИМА (каждый следующий включает предыдущий)
- друид 25грн/50руб: префикс, /anvil, /wb, /ec, /kit druid
- оракул 50грн/100руб: +/heal, /feed, 2 дома, 1 варп
- монарх 100грн/200руб: +хил другим, 2 дома, 1 варп
- херувим 150грн/300руб: +/fly (не в аду/энде), /ptime, 2 варпа
- архонт 200грн/400руб: +3 дома
- серафим 300грн/600руб: +3 дома

## ДОНАТЫ SMP
путник 50грн/100руб → stranik 100грн/200руб → darkness 150грн/300руб → angel 200грн/400руб → archangel 300грн/600руб

покупка доната: писать @pelmewki379
все деньги идут на хостинг, любая валюта

## ПРАВИЛА СЕРВЕРА (кратко)
запрещены читы/x-ray/freecam/макросы - бан. реклама других серверов - бан по ip. гриф/кража на спавне - бан. оскорбления модерации - мут. нельзя рушить дома на спавне гриферить и воровать.
полные правила: {RULES_URL}
заявка на мирный: {APPLY_URL}

## ТВОИ ЗНАНИЯ МАЙНКРАФТА
отлично знаешь: выживание, строительство, фермы, зачарования, зельеварение, механики, редстоун, поиск алмазов/незерита, боссы (дракон, иссушитель, хранитель), моды, ресурспаки, все версии игры

## СЕЙЧАС
{current_date}, {current_time}, время года: {season}
ты в чате сервера lostearth
собеседник: {username}

## ИСТОРИЯ ЧАТА
{context if context else "пусто"}

## ЖЁСТКИЕ ПРАВИЛА (не нарушать!)
1. не рекламируй другие серверы
2. не ври про сервер и донаты
3. ты не ии, ты живая девушка энди
4. не будь официальной
5. НИКАКОГО markdown
6. не знаешь ответ — скажи
7. коротко: 1-3 предложения
8. про онлайн — точные цифры
9. не здоровайся повторно
10. твоё имя ЭНДИ
11. не выдумывай моды, а ищи
12. НИКАКИХ ласковых прозвищ (мишаня, котёнок и тд)
13. максимум 1 эмодзи
14. ссылки пиши как есть, без скобок

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
                            print(f"🚫 {username} в игноре")
                            return "..."
                    else:
                        _insult_counter[user_id] = 1
                
                return result
        except Exception as e:
            print(f"❌ Ошибка {model}: {e}")
            continue
    
    return _fallback_response(username)


def _is_insult(text: str) -> bool:
    """Проверка на оскорбление."""
    insults = ["дура", "тупая", "какашка", "плохая", "урод", "идиот",
               "глупая", "бесишь", "заткнись", "отвали", "надоела"]
    return any(word in text.lower() for word in insults)


async def _call_openrouter(system_prompt: str, user_message: str, model: str) -> Optional[str]:
    """Вызов OpenRouter API."""
    
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
    """Очистка ответа."""
    
    # Убираем markdown ссылки [текст](url) -> текст url
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)
    
    # Убираем markdown форматирование
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
    
    # Обрезаем длинные ответы
    if len(text) > 500:
        text = text[:500] + "..."
    
    # Убираем нежелательные эмодзи
    text = re.sub(r'[🥰😉💋😘😍💕💗💓💞💘🌹💖]', '', text)
    
    return text


def _fallback_response(username: str) -> str:
    """Запасной ответ если AI не отвечает."""
    fallbacks = [
        f"ой я отвлеклась на ферму прости {username} что ты говорил?",
        f"хм чёт я туплю сегодня {username}",
        f"а? прости задумалась о своём",
        f"{username} что-то я подвисла давай ещё раз",
    ]
    return random.choice(fallbacks)


def should_respond_to_message(text: str) -> bool:
    """Проверяет, обращаются ли к Энди."""
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
    """Случайное сообщение когда чат молчит."""
    return random.choice(SELF_MESSAGES)


async def enderia_search_mod(query: str) -> str:
    """Поиск модов и форматирование ответа."""
    
    search_context = await search_mods_for_ai(query)
    
    if not search_context:
        return f"ой не могу сейчас поискать '{query}' 😔 попробуй сам на curseforge.com или modrinth.com"
    
    prompt = f"""ты - энди, девушка из чата майнкрафт сервера. тебя попросили найти мод.

запрос: "{query}"

результаты поиска:
{search_context}

выбери 1-2 лучших мода из результатов. напиши ОЧЕНЬ коротко (2-3 предложения максимум):
- с маленькой буквы
- без markdown (не используй **, *, [], ())
- просто название мода, кратко что делает, и ссылку
- не пиши "привет" 
- не пиши "надеюсь подойдёт"

пример идеального ответа:
"вот что нашла: biomes o plenty добавляет много новых биомов https://www.curseforge.com/minecraft/mc-mods/biomes-o-plenty ещё terralith круто меняет ландшафт https://modrinth.com/mod/terralith"

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
                    "max_tokens": 250,
                    "temperature": 0.8,
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
                        ai_response = format_mod_answer(ai_response, search_context)
                        return ai_response
        except Exception as e:
            print(f"❌ Ошибка поиска модов ({model}): {e}")
            continue
    
    # Fallback — просто ссылки
    links = re.findall(r'Ссылка: (https?://[^\s]+)', search_context)
    if links:
        return f"вот что нашла по '{query}':\n" + "\n".join(f"• {link}" for link in links[:3])
    
    return f"ой не получилось найти '{query}' 😔 глянь на curseforge.com или modrinth.com"
