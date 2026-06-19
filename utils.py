"""
Утилиты для Миры: проверка онлайна, поиск модов.
"""

import asyncio
import aiohttp
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
        # Если ошибка — возвращаем последний кэш или 0
        return (
            _online_cache["online"] if _online_cache["updated"] else 0,
            _online_cache["max"] if _online_cache["updated"] else 0
        )


async def search_mods_curseforge(query: str) -> List[dict]:
    """
    Поиск модов через CurseForge API.
    Возвращает список словарей с названием, ссылкой и описанием.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # CurseForge API v1
            url = "https://api.curseforge.com/v1/mods/search"
            params = {
                "gameId": 432,  # Minecraft
                "searchFilter": query,
                "sortField": 2,  # По популярности
                "sortOrder": "desc",
                "pageSize": 5,
                "classId": 6,  # Только моды, не ресурспаки
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for mod in data.get("data", []):
                        results.append({
                            "name": mod["name"],
                            "url": f"https://www.curseforge.com/minecraft/mc-mods/{mod['slug']}",
                            "summary": mod.get("summary", "")[:150],
                            "downloads": mod.get("downloadCount", 0)
                        })
                    return results
                else:
                    print(f"❌ CurseForge API ошибка: {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка поиска модов: {e}")
    
    return []


async def search_mods_modrinth(query: str) -> List[dict]:
    """
    Поиск модов через Modrinth API (бесплатный, без ключа).
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.modrinth.com/v2/search"
            params = {
                "query": query,
                "limit": 5,
                "facets": '[["project_type:mod"]]',
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for hit in data.get("hits", []):
                        results.append({
                            "name": hit["title"],
                            "url": f"https://modrinth.com/mod/{hit['slug']}",
                            "summary": hit.get("description", "")[:150],
                            "downloads": hit.get("downloads", 0)
                        })
                    return results
    except Exception as e:
        print(f"❌ Ошибка Modrinth: {e}")
    
    return []


async def search_mods(query: str) -> List[dict]:
    """
    Поиск модов: сначала Modrinth, потом CurseForge.
    Возвращает список модов.
    """
    # Пробуем Modrinth (не требует API ключа)
    results = await search_mods_modrinth(query)
    if results:
        return results
    
    # Fallback: CurseForge
    results = await search_mods_curseforge(query)
    if results:
        return results
    
    return []


def format_mod_results(mods: List[dict], query: str) -> str:
    """Форматирует результаты поиска модов для ответа Миры"""
    if not mods:
        return f"ничего не нашла по запросу '{query}' попробуй поискать на curseforge сам"
    
    lines = [f"вот что я нашла по запросу '{query}':"]
    
    for i, mod in enumerate(mods[:3], 1):
        name = mod["name"]
        url = mod["url"]
        summary = mod.get("summary", "")
        if summary and len(summary) > 100:
            summary = summary[:100] + "..."
        
        if summary:
            lines.append(f"\n{i}. {name} - {summary}\n{url}")
        else:
            lines.append(f"\n{i}. {name}\n{url}")
    
    if len(mods) > 3:
        lines.append(f"\nи ещё {len(mods) - 3} модов... уточни запрос если надо")
    
    return "\n".join(lines)
