"""
Утилиты для Миры: проверка онлайна, поиск модов, etc.
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Tuple
from mcstatus import JavaServer
import config
from memory import chat_memory

async def get_server_online() -> Tuple[int, int]:
    """
    Получение онлайна сервера Minecraft.
    Возвращает (online, max_players).
    Использует кэш на 60 секунд.
    """
    now = datetime.now()
    
    # Используем кэш если он свежий
    if chat_memory.online_updated:
        if (now - chat_memory.online_updated).total_seconds() < 60:
            return chat_memory.online_cache["online"], chat_memory.online_cache["max"]
    
    try:
        server = JavaServer(
            config.MC_SERVER["java_ip"],
            config.MC_SERVER["java_port"]
        )
        status = await server.async_status()
        
        online = status.players.online
        max_players = status.players.max
        
        chat_memory.online_cache = {"online": online, "max": max_players}
        chat_memory.online_updated = now
        
        return online, max_players
        
    except Exception as e:
        print(f"❌ Ошибка получения онлайна: {e}")
        # Возвращаем последний известный онлайн или нули
        return (
            chat_memory.online_cache.get("online", 0),
            chat_memory.online_cache.get("max", 0)
        )

async def search_mod(query: str) -> Optional[str]:
    """
    Поиск мода/ресурспака через CurseForge API или Google.
    Возвращает ссылку или None.
    """
    # Пробуем поискать через CurseForge
    try:
        async with aiohttp.ClientSession() as session:
            search_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&searchFilter={query}"
            async with session.get(search_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data"):
                        mod = data["data"][0]
                        return f"https://www.curseforge.com/minecraft/mc-mods/{mod['slug']}"
    except Exception as e:
        print(f"⚠️ Ошибка поиска мода: {e}")
    
    # Fallback: ссылка на поиск CurseForge
    query_encoded = query.replace(" ", "+")
    return f"https://www.curseforge.com/minecraft/search?search={query_encoded}"

async def get_mod_suggestions(query: str) -> list:
    """Поиск нескольких модов по запросу"""
    try:
        async with aiohttp.ClientSession() as session:
            search_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&searchFilter={query}&pageSize=3"
            async with session.get(search_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for mod in data.get("data", []):
                        results.append({
                            "name": mod["name"],
                            "url": f"https://www.curseforge.com/minecraft/mc-mods/{mod['slug']}",
                            "summary": mod.get("summary", "")
                        })
                    return results
    except:
        pass
    return []

# Кэш для онлайна на 1 минуту
_online_cache = {"online": 0, "max": 0, "updated": None}
