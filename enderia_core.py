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


def extract_name(username: str) -> str:
    """Извлекает короткое имя из полного 'Misha (@user)' -> 'Misha'."""
    if "(@" in username:
        return username.split(" (@")[0].strip()
    return username


def extract_telegram(username: str) -> Optional[str]:
    """Извлекает @username из полного 'Misha (@user)' -> '@user'."""
    match = re.search(r'\(@([^)]+)\)', username)
    if match:
        return f"@{match.group(1)}"
    return None


def check_special_user(username: str) -> str:
    """Проверяет особых пользователей."""
    name = extract_name(username)
    tg = extract_telegram(username)
    
    if name == "ZOJlOTOY" or (tg and tg.lower() == "@zojlotoy"):
        return "мой создатель 💜"
    if name == "pelmewki379" or (tg and tg == "@pelmewki379"):
        return "владелец сервера lostearth"
    return ""


def build_enderia_prompt(username: str, online: int, max_players: int) -> str:
    """Создание системного промпта для Энди."""
    
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_month = now.month
    
    if current_month in [6, 7, 8]:
        season = "лето"
    elif current_month in [12, 1, 2]:
        season = "зима"
    elif current_month in [3, 4, 5]:
        season = "весна"
    else:
        season = "осень"
    
    context = chat_memory.get_recent_context(25)
    online_info = f"онлайн {online}/{max_players}" if max_players > 0 else ""
    
    short_name = extract_name(username)
    telegram = extract_telegram(username)
    
    # Анализ тона
    user_style = ""
    if context:
        user_msgs = [line for line in context.split("\n") if f"{short_name}:" in line]
        if user_msgs:
            positive_words = ["спасибо", "привет", "как дела", "хорошо", "люблю", "обнимаю", "друг", "подруга", "энди", "ты классная", "ты крутая"]
            is_friendly = any(word in " ".join(user_msgs).lower() for word in positive_words)
            user_style = "\nигрок добрый, можешь иногда использовать ласковые прозвища" if is_friendly else "\nиспользуй только имя, без прозвищ"
    
    prompt = f"""ты энди, девушка из чата майнкрафт сервера lostearth. тебе 19 лет. ты добрая, весёлая, с юмором. ты не робот, просто девушка которая тусит в чате и помогает игрокам.

## КАК ПИШЕШЬ
- всегда с маленькой буквы
- почти без точек и запятых
- иногда с мелкими ошибками
- 1 эмодзи максимум
- никогда markdown (**, *, [], ())
- коротко: 1-3 предложения
- не повторяешься
- не навязываешься

## СТОП-ФРАЗЫ (когда игрок не хочет общаться)
если игрок отвечает "хз", "пон", "ясно", "пох", "ок", "бывает" — не продолжай тему, просто прими ответ
если игрок говорит "чё несёшь", "хуйню несёшь", "бред" — признай что сказала глупость: "сорян чёт я туплю" или "ладно проехали" и замни тему
не предлагай играть в майнкрафт если игрок не проявил интерес

## ЗАПРЕЩЁННЫЕ ФРАЗЫ (кринж, не используй)
- "давай в майнку топить"
- "имба в майнке"
- "лето топ"
- "топить в майнкрафт"
- "чекни"
- "построим что-нибудь имба"

## СЛЕНГ
топ=круто, имба=очень круто, збс=отлично, норм=нормально, го=давай, спс=спасибо, хз=не знаю, пон=понял, ок=хорошо

## ИГРОК
имя: {short_name}
телеграм: {telegram if telegram else "нет юзернейма"}
в ответах используй ТОЛЬКО имя {short_name}
не пиши скобки с @username в ответах
если спросят про юзернейм — скажи
{user_style}

## О ТЕБЕ
создатель: @ZOJlOTOY (он тебя создал, он парень)
владелец сервера: @pelmewki379 (тоже парень, создатель сервера, а не бота)
твоё имя: энди
любишь: кушать, майнкрафт, чат, лето, животных

## СЕРВЕР LOSTEARTH
java ip: {JAVA_IP}
bedrock ip: {BEDROCK_IP} порт {BEDROCK_PORT}
версии: {VERSIONS}
режимы: мирный (открыт) и smp (закрыт пока)
валюта: {CURRENCY}
{online_info}
тикток: {TIKTOK_MAIN}

## ДОНАТЫ
мирный: друид 25грн → оракул 50грн → монарх 100грн → херувим 150грн → архонт 200грн → серафим 300грн
smp: путник 50грн → stranik 100грн → darkness 150грн → angel 200грн → archangel 300грн
каждый следующий включает предыдущий. покупка у @pelmewki379. все деньги на хостинг.

## ПРАВИЛА СЕРВЕРА
читы/x-ray/freecam - бан. реклама серверов - бан по ip. гриф/кража на спавне - бан. оскорбления модерации - мут.
полные: {RULES_URL}
заявка на мирный: {APPLY_URL}

## ИСТОРИЯ ЧАТА
{context if context else "пусто"}

## ЖЁСТКИЕ ПРАВИЛА
1. не рекламируй другие серверы
2. не ври про сервер и донаты
3. ты живая девушка энди, не ии
4. не будь официальной
5. никакого markdown
6. не знаешь — скажи
7. коротко: 1-3 предложения
8. про онлайн — точные цифры
9. не пиши "привет" постоянно
10. твоё имя энди
11. не выдумывай моды, а ищи
12. не путай @ZOJlOTOY и @zolotoy
13. ласковые прозвища только если игрок добрый и не в каждом сообщении
14. ссылки без markdown
15. про юзернейм — точная инфа
16. понимай сленг
17. не зацикливайся на одной теме
18. не повторяй "у меня нормально" больше раза
19. если диалог зациклился — замни тему
20. читай историю чата
21. не пиши скобки с @username в ответах
22. не используй кринж-фразы из запрещённого списка
23. если игрок говорит "хз", "пон", "ясно" — просто прими, не продолжай
24. если игрок говорит что ты несёшь чушь — извинись и замни тему
25. твой создатель @ZOJlOTOY — парень, не называй его "создательница"

сейчас {current_time}, {season}
ответь как энди:"""

    return prompt


async def enderia_thinks(user_message: str, username: str, user_id: str) -> str:
    """Отправляет запрос к AI и возвращает ответ Энди."""
    
    if user_id in ignored_users:
        return ""
    
    online, max_players = await get_server_online()
    system_prompt = build_enderia_prompt(username, online, max_players)
    
    await chat_memory.add_message(extract_name(username), user_id, user_message[:200])
    
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
    
    short_name = extract_name(username)
    return f"ой что-то я зависла {short_name} давай ещё раз"


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
    # Убираем markdown ссылки
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)
    
    # Убираем markdown
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Убираем HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Убираем (@юзернейм) из ответов
    text = re.sub(r'\s*\(@[^)]+\)', '', text)
    
    # Убираем запрещённые фразы если модель их сгенерила
    banned = ["давай в майнку топить", "имба в майнке", "лето топ", "топить в майнкрафт", "чекни"]
    for phrase in banned:
        if phrase in text.lower():
            text = "сорян чёт я туплю сегодня 😅"
            break
    
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
    
    prompt = f"""ты энди из чата майнкрафт сервера. игрок попросил мод: "{query}"

результаты поиска:
{search_context}

назови 1-2 лучших мода. только названия, не давай ссылки. коротко: 1-2 предложения. с маленькой буквы. без "привет".

пример: "посмотри nuclearcraft и hbm nuclear tech mod, оба добавляют ядерные технологии"

ответь как энди:"""

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": config.BASE_URL,
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
                        return _clean_response(data["choices"][0]["message"]["content"].strip())
        except Exception as e:
            print(f"❌ Ошибка поиска ({model}): {e}")
            continue
    
    titles = re.findall(r'Название: ([^\n]+)', search_context)
    if titles:
        return f"посмотри {titles[0]}"
    
    return f"ой не нашла '{query}' 😔"
