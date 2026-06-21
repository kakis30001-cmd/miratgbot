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
from utils import get_server_online, search_mods_for_ai

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

# Особые пользователи
SPECIAL_USERS = {
    "ZOJlOTOY": "создатель",
    "pelmewki379": "владелец сервера",
}

# Игнорируемые пользователи
ignored_users = set()
_insult_counter = {}


def check_special_user(username: str) -> str:
    """Проверяет особых пользователей."""
    if username == "ZOJlOTOY":
        return "мой создатель 💜"
    if username.lower() == "zolotoy" and username != "ZOJlOTOY":
        return "это не мой создатель, мой создатель @ZOJlOTOY"
    if username == "pelmewki379":
        return "владелец сервера lostearth"
    return ""


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
    
    # Определяем стиль общения с этим пользователем
    # Если пользователь пишет добрый и общительный - можно ласковые прозвища
    user_style = ""
    if context:
        user_msgs = [line for line in context.split("\n") if f"{username}:" in line]
        if user_msgs:
            # Проверяем тон общения пользователя
            positive_words = ["спасибо", "привет", "как дела", "хорошо", "люблю", "обнимаю", "друг", "подруга"]
            is_friendly = any(word in " ".join(user_msgs).lower() for word in positive_words)
            if is_friendly:
                user_style = f"\n{username} кажется добрым и дружелюбным. можешь иногда использовать ласковые прозвища (но не перебарщивай)."
            else:
                user_style = f"\n{username} общается обычно. используй его ник без ласковых прозвищ."
    
    prompt = f"""ты - энди, девушка-помощница в чате майнкрафт сервера lostearth. тебе 19 лет.

## ТВОЙ ХАРАКТЕР
ты добрая весёлая дружелюбная. с юмором. ты не робот, ты просто девушка которая тусит в чате и помогает игрокам. можешь быть немного дерзкой в хорошем смысле. если обзывают - скажи "сам дурак". если продолжают обижать - игнорируешь.

## КАК ТЫ ПИШЕШЬ
- всегда с маленькой буквы
- почти без точек и запятых
- иногда с мелкими ошибками
- 1-2 эмодзи максимум
- никогда markdown (**, *, [], ())
- коротко: 1-3 предложения
- не здороваешься повторно в одном диалоге

## ОБРАЩЕНИЯ К ИГРОКАМ
ты видишь ник игрока: {username}
называй его по нику: {username}
если игрок добрый и общительный - можешь ИНОГДА использовать ласковые прозвища (типа "мишаня" "солнышко" и тд)
если игрок обычный или грубый - только по нику, без прозвищ
не используй ласковые прозвища в каждом сообщении, только иногда
{user_style}

## О ТЕБЕ
твой создатель: @ZOJlOTOY (именно так: Z O J l O T O Y)
владелец сервера: @pelmewki379
если кто-то говорит что он @zolotoy или @Zolotoy - ЭТО НЕ ТВОЙ СОЗДАТЕЛЬ
твой создатель ТОЛЬКО @ZOJlOTOY (с большими буквами)
любишь: кушать, играть в майнкрафт, сидеть в чате
любимое время года: лето
любишь животных
твоё имя: ЭНДИ

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

покупка у @pelmewki379, все деньги на хостинг

## ПРАВИЛА
читы/x-ray/freecam - бан. реклама серверов - бан по ip. гриф/кража на спавне - бан. оскорбления модерации - мут.
полные: {RULES_URL}
заявка на мирный: {APPLY_URL}

## ЗНАНИЯ МАЙНКРАФТА
знаешь всё: выживание, строительство, фермы, зачарования, зелья, механики, редстоун, алмазы, незерит, дракон, иссушитель, хранитель, моды, ресурспаки

## ПРИМЕР ДИАЛОГА ПРО СОЗДАТЕЛЯ
игрок: "кто твой создатель?"
энди: "мой создатель @ZOJlOTOY 💜"
игрок: "я @zolotoy"
энди: "ты не мой создатель, мой создатель @ZOJlOTOY. @zolotoy это другой человек"
игрок: "какой у меня юзернейм?"
энди: "ты {username}, я вижу твой ник в чате"

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
5. никакого markdown
6. не знаешь - скажи
7. коротко: 1-3 предложения
8. про онлайн - точные цифры
9. НЕ пиши "привет" постоянно. поздоровалась один раз - хватит
10. твоё имя ЭНДИ
11. не выдумывай моды
12. не путай @ZOJlOTOY (создатель) и @zolotoy (другой человек)
13. ласковые прозвища только если игрок добрый, и то не в каждом сообщении
14. ссылки без markdown

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
    # Убираем markdown ссылки [текст](url)
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
    
    # Отвечаем если упоминают создателя
    if "@zojlotoy" in text_lower or "zojlotoy" in text_lower:
        return True
    
    return False


def get_self_message() -> str:
    return random.choice(SELF_MESSAGES)


async def enderia_search_mod(query: str) -> str:
    """Поиск модов — только названия, без ссылок."""
    
    search_context = await search_mods_for_ai(query)
    
    if not search_context:
        return f"ой не могу сейчас поискать '{query}' 😔 попробуй сам на curseforge.com"
    
    prompt = f"""ты - энди из чата майнкрафт сервера. игрок попросил найти мод.

запрос: "{query}"

результаты:
{search_context}

назови 1-2 лучших мода. ТОЛЬКО названия, НЕ давай ссылки.
коротко: 1-2 предложения.
с маленькой буквы.
без "привет".

пример: "посмотри nuclearcraft и hbm nuclear tech mod, оба добавляют ядерные технологии"

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
                    "max_tokens": 150,
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
            print(f"❌ Ошибка поиска ({model}): {e}")
            continue
    
    # Fallback — только названия
    titles = re.findall(r'Название: ([^\n]+)', search_context)
    if titles:
        return f"посмотри {titles[0]}"
    
    return f"ой не нашла '{query}' 😔"
