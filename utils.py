"""
Утилиты для Энди: проверка онлайна, поиск модов.
"""

import asyncio
import aiohttp
import re
from datetime import datetime
from typing import Tuple
from urllib.parse import quote_plus
from mcstatus import JavaServer
import config
from memory import chat_memory

# Кэш онлайна
_online_cache = {"online": 0, "max": 0, "updated": None}


async def get_server_online() -> Tuple[int, int]:
    """
    Получение онлайна сервера Minecraft.
    Возвращает (online, max_players). Кэш на 60 секунд.
    """
    now = datetime.now()
    
    if _online_cache["updated"]:
        if (now - _online_cache["updated"]).total_seconds() < 60:
            return _online_cache["online"], _online_cache["max"]
    
    try:
        server = JavaServer(config.MC_SERVER["java_ip"], config.MC_SERVER["java_port"])
        status = await server.async_status()
        
        _online_cache["online"] = status.players.online
        _online_cache["max"] = status.players.max
        _online_cache["updated"] = now
        
        return status.players.online, status.players.max
        
    except Exception as e:
        print(f"❌ Ошибка получения онлайна: {e}")
        return (
            _online_cache["online"] if _online_cache["updated"] else 0,
            _online_cache["max"] if _online_cache["updated"] else 0
        )


# ========== ПОИСК МОДОВ ==========

async def search_mods_google_api(query: str) -> str:
    """
    Поиск модов через Google Custom Search API.
    Возвращает текст с результатами для AI.
    """
    if not config.GOOGLE_API_KEY or not config.GOOGLE_SEARCH_CX:
        print("⚠️ Google API ключи не настроены")
        return ""
    
    search_query = f"minecraft mod {query}"
    
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "key": config.GOOGLE_API_KEY,
                "cx": config.GOOGLE_SEARCH_CX,
                "q": search_query,
                "num": 5,
            }
            
            async with session.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ Google API ошибка ({resp.status}): {error_text[:300]}")
                    return ""
                
                data = await resp.json()
                items = data.get("items", [])
                
                if not items:
                    print("❌ Google API: ничего не найдено")
                    return ""
                
                lines = []
                for i, item in enumerate(items[:5], 1):
                    title = item.get("title", "").strip()
                    snippet = item.get("snippet", "").strip()
                    link = item.get("link", "").strip()
                    
                    # Чистим HTML-сущности
                    for char, repl in [("&amp;", "&"), ("&#x27;", "'"), ("&quot;", '"')]:
                        title = title.replace(char, repl)
                        snippet = snippet.replace(char, repl)
                    
                    # Обрезаем " - CurseForge" и подобное
                    title = re.sub(r'\s*[-–|]\s*(CurseForge|Modrinth|Minecraft).*$', '', title)
                    
                    lines.append(f"Результат {i}:")
                    lines.append(f"Название: {title}")
                    if snippet:
                        lines.append(f"Описание: {snippet[:200]}")
                    lines.append(f"Ссылка: {link}")
                    lines.append("")
                
                print(f"✅ Google API: найдено {len(items)} результатов")
                return "\n".join(lines)
                
    except Exception as e:
        print(f"❌ Ошибка Google API: {e}")
    
    return ""


async def search_mods_modrinth(query: str) -> str:
    """
    Поиск через Modrinth API (бесплатный, без ключа).
    """
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "query": query,
                "limit": 3,
                "facets": '[["project_type:mod"]]',
            }
            headers = {"User-Agent": "EnderiaBot/1.0"}
            
            async with session.get(
                "https://api.modrinth.com/v2/search",
                params=params,
                headers=headers,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    return ""
                
                data = await resp.json()
                hits = data.get("hits", [])
                
                if not hits:
                    return ""
                
                lines = []
                for i, hit in enumerate(hits[:3], 1):
                    title = hit.get("title", "")
                    desc = hit.get("description", "")[:200]
                    slug = hit.get("slug", "")
                    
                    lines.append(f"Результат {i}:")
                    lines.append(f"Название: {title}")
                    if desc:
                        lines.append(f"Описание: {desc}")
                    lines.append(f"Ссылка: https://modrinth.com/mod/{slug}")
                    lines.append("")
                
                print(f"✅ Modrinth: найдено {len(hits)} модов")
                return "\n".join(lines)
                
    except Exception as e:
        print(f"⚠️ Modrinth: {e}")
    
    return ""


async def search_mods_for_ai(query: str) -> str:
    """
    Поиск модов: Google API → Modrinth → ссылки на поиск.
    """
    # 1. Google Custom Search
    result = await search_mods_google_api(query)
    if result:
        return result
    
    # 2. Modrinth API
    print("⚠️ Google API не сработал, пробую Modrinth")
    result = await search_mods_modrinth(query)
    if result:
        return result
    
    # 3. Ссылки на прямой поиск
    print("⚠️ Всё не сработало, даю ссылки на поиск")
    encoded = quote_plus(query)
    lines = [
        "Результат 1:",
        f"Название: Поиск '{query}' на CurseForge",
        f"Ссылка: https://www.curseforge.com/minecraft/search?search={encoded}&class=mods",
        "",
        "Результат 2:",
        f"Название: Поиск '{query}' на Modrinth",
        f"Ссылка: https://modrinth.com/mods?q={encoded}",
        ""
    ]
    return "\n".join(lines)


def format_mod_answer(ai_response: str, search_context: str) -> str:
    """
    Добавляет ссылку только если AI её не дал.
    """
    # Если AI уже дал ссылки — не трогаем
    if re.findall(r'https?://[^\s]+', ai_response):
        return ai_response
    
    # Ищем первую нормальную ссылку
    links = re.findall(r'Ссылка: (https?://[^\s]+)', search_context)
    for link in links:
        if "/search?" not in link:
            return f"{ai_response}\n{link}"
    
    return ai_response
