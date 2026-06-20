"""
Утилиты для Миры: проверка онлайна, поиск модов через Google API.
"""

import asyncio
import aiohttp
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from mcstatus import JavaServer
import config
from memory import chat_memory

# Кэш онлайна
_online_cache = {"online": 0, "max": 0, "updated": None}

async def get_server_online() -> Tuple[int, int]:
    """
    Получение онлайна сервера Minecraft.
    Возвращает (online, max_players).
    Кэш на 60 секунд.
    """
    now = datetime.now()
    
    if _online_cache["updated"]:
        if (now - _online_cache["updated"]).total_seconds() < 60:
            return _online_cache["online"], _online_cache["max"]
    
    try:
        server = JavaServer(
            config.MC_SERVER["java_ip"],
            config.MC_SERVER["java_port"]
        )
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


# ========== ПОИСК МОДОВ ЧЕРЕЗ GOOGLE API ==========

async def search_mods_google_api(query: str) -> str:
    """
    Поиск модов через Google Custom Search API.
    Возвращает отформатированный контекст для AI.
    """
    
    if not config.GOOGLE_API_KEY or not config.GOOGLE_SEARCH_CX:
        print("⚠️ Google API ключи не настроены")
        return ""
    
    try:
        search_query = f"minecraft mod {query}"
        
        async with aiohttp.ClientSession() as session:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": config.GOOGLE_API_KEY,
                "cx": config.GOOGLE_SEARCH_CX,
                "q": search_query,
                "num": 5,
                "lr": "lang_ru|lang_en",
                "safe": "off",
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    
                    if not items:
                        print("❌ Google API: ничего не найдено")
                        return ""
                    
                    context_lines = []
                    for i, item in enumerate(items[:5], 1):
                        title = item.get("title", "").strip()
                        snippet = item.get("snippet", "").strip()
                        link = item.get("link", "").strip()
                        
                        # Чистим
                        title = re.sub(r'&amp;', '&', title)
                        title = re.sub(r'&#x27;', "'", title)
                        snippet = re.sub(r'&amp;', '&', snippet)
                        snippet = re.sub(r'&#x27;', "'", snippet)
                        
                        context_lines.append(f"Результат {i}:")
                        context_lines.append(f"Название: {title}")
                        if snippet:
                            if len(snippet) > 200:
                                snippet = snippet[:200] + "..."
                            context_lines.append(f"Описание: {snippet}")
                        context_lines.append(f"Ссылка: {link}")
                        context_lines.append("")
                    
                    context = "\n".join(context_lines)
                    print(f"✅ Google API: найдено {len(items)} результатов")
                    return context
                    
                elif resp.status == 429:
                    print("❌ Google API: превышен лимит (429)")
                elif resp.status == 403:
                    print("❌ Google API: доступ запрещён (403)")
                else:
                    error_text = await resp.text()
                    print(f"❌ Google API ошибка ({resp.status}): {error_text[:200]}")
                    
    except Exception as e:
        print(f"❌ Ошибка Google API: {e}")
    
    return ""


async def search_mods_fallback(query: str) -> str:
    """
    Запасной поиск если Google API недоступен.
    Ищет через Modrinth API + DuckDuckGo.
    """
    context_lines = []
    
    # 1. Пробуем Modrinth API
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.modrinth.com/v2/search"
            params = {
                "query": query,
                "limit": 3,
                "facets": '[["project_type:mod"]]',
            }
            headers = {
                "User-Agent": "MiraBot/1.0 (LostEarth Minecraft Server)"
            }
            
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for i, hit in enumerate(data.get("hits", [])[:3], 1):
                        title = hit.get("title", "")
                        desc = hit.get("description", "")[:200]
                        slug = hit.get("slug", "")
                        context_lines.append(f"Результат {i} (Modrinth):")
                        context_lines.append(f"Название: {title}")
                        if desc:
                            context_lines.append(f"Описание: {desc}")
                        context_lines.append(f"Ссылка: https://modrinth.com/mod/{slug}")
                        context_lines.append("")
    except Exception as e:
        print(f"⚠️ Modrinth fallback: {e}")
    
    # 2. Если Modrinth не дал результатов — даём ссылки на поиск
    if not context_lines:
        from urllib.parse import quote_plus
        encoded = quote_plus(query)
        context_lines.append("Результат 1 (CurseForge поиск):")
        context_lines.append(f"Название: Поиск модов '{query}' на CurseForge")
        context_lines.append(f"Ссылка: https://www.curseforge.com/minecraft/search?search={encoded}&class=mods")
        context_lines.append("")
        context_lines.append("Результат 2 (Modrinth поиск):")
        context_lines.append(f"Название: Поиск модов '{query}' на Modrinth")
        context_lines.append(f"Ссылка: https://modrinth.com/mods?q={encoded}")
        context_lines.append("")
    
    return "\n".join(context_lines)


async def search_mods_for_ai(query: str) -> str:
    """
    Основная функция поиска модов.
    Возвращает контекст для передачи AI.
    Сначала Google API, потом fallback.
    """
    
    # 1. Google Custom Search
    context = await search_mods_google_api(query)
    if context:
        return context
    
    # 2. Fallback (Modrinth + ссылки на поиск)
    print("⚠️ Google API не сработал, использую fallback")
    context = await search_mods_fallback(query)
    return context


def format_mod_answer(ai_response: str, search_context: str) -> str:
    """
    Форматирует финальный ответ Миры о модах.
    Добавляет ссылки после ответа AI.
    """
    # Извлекаем ссылки из контекста
    links = re.findall(r'Ссылка: (https?://[^\s]+)', search_context)
    
    # Если AI уже дал ссылки — не дублируем
    if links and not any(link in ai_response for link in links):
        # Добавляем только если ответ короткий
        if len(ai_response) < 300:
            ai_response += "\n\nссылки:"
            for link in links[:3]:
                ai_response += f"\n• {link}"
    
    return ai_response
