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
        return (
            _online_cache["online"] if _online_cache["updated"] else 0,
            _online_cache["max"] if _online_cache["updated"] else 0
        )


async def search_mods_modrinth(query: str) -> List[dict]:
    """
    Поиск модов через Modrinth API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.modrinth.com/v2/search"
            params = {
                "query": query,
                "limit": 5,
                "facets": '[["project_type:mod"]]',
            }
            
            headers = {
                "User-Agent": "MiraBot/1.0 (LostEarth Minecraft Server)"
            }
            
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
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
                else:
                    print(f"❌ Modrinth API ошибка: {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка Modrinth: {e}")
    
    return []


async def search_mods_google(query: str) -> List[dict]:
    """
    Поиск модов через прямое обращение к поиску CurseForge.
    Парсим страницу поиска.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Используем поиск CurseForge напрямую
            search_url = f"https://www.curseforge.com/minecraft/search"
            params = {
                "search": query,
                "class": "mods"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml"
            }
            
            async with session.get(search_url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # Простой парсинг результатов
                    results = _parse_curseforge_html(html, query)
                    return results
    except Exception as e:
        print(f"❌ Ошибка поиска через Google: {e}")
    
    return []


def _parse_curseforge_html(html: str, query: str) -> List[dict]:
    """Парсинг HTML страницы поиска CurseForge"""
    import re
    
    results = []
    
    # Ищем ссылки на моды
    pattern = r'href="(/minecraft/mc-mods/[^"]+)"[^>]*>\s*<[^>]+>([^<]+)</'
    matches = re.findall(pattern, html)
    
    seen = set()
    for url, name in matches:
        name = name.strip()
        if name and name not in seen and len(name) > 1:
            seen.add(name)
            results.append({
                "name": name,
                "url": f"https://www.curseforge.com{url}",
                "summary": "",
                "downloads": 0
            })
            if len(results) >= 5:
                break
    
    return results


# ========== База популярных модов (если API не работает) ==========

POPULAR_MODS = {
    "выживание": [
        {"name": "Tough As Nails", "url": "https://www.curseforge.com/minecraft/mc-mods/tough-as-nails", "summary": "усложняет выживание: жажда, температура, времена года"},
        {"name": "Survive", "url": "https://www.curseforge.com/minecraft/mc-mods/survive", "summary": "реалистичное выживание с жаждой и температурой"},
        {"name": "Minecraft Comes Alive", "url": "https://www.curseforge.com/minecraft/mc-mods/minecraft-comes-alive-mca", "summary": "оживляет деревни, добавляет общение с жителями"},
    ],
    "зомби": [
        {"name": "Zombie Awareness", "url": "https://www.curseforge.com/minecraft/mc-mods/zombie-awareness", "summary": "зомби умнеют: реагируют на звук, свет, кровь"},
        {"name": "The Zombie Apocalypse", "url": "https://www.curseforge.com/minecraft/mc-mods/the-zombie-apocalypse", "summary": "полный зомби апокалипсис с ордами зомби"},
        {"name": "Decimation", "url": "https://www.curseforge.com/minecraft/mc-mods/decimation", "summary": "зомби апокалипсис с оружием и базами"},
        {"name": "Last Days of Humanity", "url": "https://www.curseforge.com/minecraft/mc-mods/last-days-of-humanity", "summary": "выживание в зомби апокалипсисе"},
    ],
    "ферм": [
        {"name": "Pam's HarvestCraft 2", "url": "https://www.curseforge.com/minecraft/mc-mods/pams-harvestcraft-2", "summary": "огромное разнообразие еды и ферм"},
        {"name": "Farmer's Delight", "url": "https://www.curseforge.com/minecraft/mc-mods/farmers-delight", "summary": "расширенное фермерство и кулинария"},
        {"name": "Croptopia", "url": "https://www.curseforge.com/minecraft/mc-mods/croptopia", "summary": "новые культуры и еда"},
    ],
    "магия": [
        {"name": "Ars Nouveau", "url": "https://www.curseforge.com/minecraft/mc-mods/ars-nouveau", "summary": "создание своих заклинаний"},
        {"name": "Botania", "url": "https://www.curseforge.com/minecraft/mc-mods/botania", "summary": "магия цветов и природы"},
        {"name": "Thaumcraft", "url": "https://www.curseforge.com/minecraft/mc-mods/thaumcraft", "summary": "изучение магии и алхимии"},
        {"name": "Blood Magic", "url": "https://www.curseforge.com/minecraft/mc-mods/blood-magic", "summary": "магия крови и ритуалы"},
    ],
    "техника": [
        {"name": "Create", "url": "https://www.curseforge.com/minecraft/mc-mods/create", "summary": "механизмы и автоматизация"},
        {"name": "Thermal Expansion", "url": "https://www.curseforge.com/minecraft/mc-mods/thermal-expansion", "summary": "технические машины и энергия"},
        {"name": "Mekanism", "url": "https://www.curseforge.com/minecraft/mc-mods/mekanism", "summary": "продвинутая техника и фабрики"},
        {"name": "Industrial Foregoing", "url": "https://www.curseforge.com/minecraft/mc-mods/industrial-foregoing", "summary": "автоматизация всего"},
    ],
    "декор": [
        {"name": "MrCrayfish's Furniture", "url": "https://www.curseforge.com/minecraft/mc-mods/mrcrayfish-furniture-mod", "summary": "мебель и декор для дома"},
        {"name": "Macaw's Furniture", "url": "https://www.curseforge.com/minecraft/mc-mods/macaws-furniture", "summary": "красивая мебель"},
        {"name": "Chisel", "url": "https://www.curseforge.com/minecraft/mc-mods/chisel", "summary": "множество вариантов блоков"},
    ],
    "приключения": [
        {"name": "Twilight Forest", "url": "https://www.curseforge.com/minecraft/mc-mods/the-twilight-forest", "summary": "новое измерение с боссами и данжами"},
        {"name": "When Dungeons Arise", "url": "https://www.curseforge.com/minecraft/mc-mods/when-dungeons-arise", "summary": "огромные данжи в мире"},
        {"name": "YUNG's Better Dungeons", "url": "https://www.curseforge.com/minecraft/mc-mods/yungs-better-dungeons", "summary": "улучшенные подземелья"},
    ],
    "оптимизация": [
        {"name": "Sodium", "url": "https://modrinth.com/mod/sodium", "summary": "оптимизация графики, больше FPS"},
        {"name": "OptiFine", "url": "https://optifine.net/home", "summary": "оптимизация и шейдеры"},
        {"name": "Lithium", "url": "https://modrinth.com/mod/lithium", "summary": "оптимизация серверной части"},
        {"name": "Phosphor", "url": "https://modrinth.com/mod/phosphor", "summary": "оптимизация освещения"},
    ],
    "карты": [
        {"name": "Xaero's World Map", "url": "https://www.curseforge.com/minecraft/mc-mods/xaeros-world-map", "summary": "карта мира"},
        {"name": "JourneyMap", "url": "https://www.curseforge.com/minecraft/mc-mods/journeymap", "summary": "карта в реальном времени"},
        {"name": "Xaero's Minimap", "url": "https://www.curseforge.com/minecraft/mc-mods/xaeros-minimap", "summary": "миникарта в углу экрана"},
    ],
    "ресурспак": [
        {"name": "Faithful", "url": "https://modrinth.com/resourcepack/faithful-32x", "summary": "улучшенные текстуры 32x в стиле ванили"},
        {"name": "Bare Bones", "url": "https://modrinth.com/resourcepack/bare-bones", "summary": "простые и чистые текстуры"},
        {"name": "Mizuno's 16 Craft", "url": "https://www.curseforge.com/minecraft/texture-packs/mizunos-16-craft", "summary": "красивый японский стиль"},
    ],
    "шейдеры": [
        {"name": "Complementary Shaders", "url": "https://modrinth.com/shader/complementary-reimagined", "summary": "красивые шейдеры без потери FPS"},
        {"name": "BSL Shaders", "url": "https://modrinth.com/shader/bsl-shaders", "summary": "популярные шейдеры с красивым светом"},
        {"name": "Sildur's Shaders", "url": "https://sildurs-shaders.github.io", "summary": "шейдеры на любой вкус и ПК"},
    ],
}


def find_mods_in_base(query: str) -> List[dict]:
    """Поиск модов в нашей базе по ключевым словам"""
    query_lower = query.lower()
    results = []
    
    # Ищем по всем категориям
    for category, mods in POPULAR_MODS.items():
        if category in query_lower:
            results.extend(mods)
    
    # Если не нашли по категориям — ищем по отдельным словам в названиях
    if not results:
        for category, mods in POPULAR_MODS.items():
            for mod in mods:
                if query_lower in mod["name"].lower() or query_lower in mod.get("summary", "").lower():
                    results.append(mod)
    
    # Убираем дубликаты
    seen = set()
    unique_results = []
    for mod in results:
        if mod["name"] not in seen:
            seen.add(mod["name"])
            unique_results.append(mod)
    
    return unique_results[:5]


async def search_mods(query: str) -> List[dict]:
    """
    Поиск модов: сначала Modrinth API, потом наша база.
    Возвращает список модов.
    """
    # 1. Пробуем Modrinth API
    results = await search_mods_modrinth(query)
    if results:
        print(f"✅ Найдено через Modrinth: {len(results)} модов")
        return results
    
    # 2. Ищем в нашей базе
    results = find_mods_in_base(query)
    if results:
        print(f"✅ Найдено в базе: {len(results)} модов")
        return results
    
    # 3. Ничего не нашли
    return []


def format_mod_results(mods: List[dict], query: str) -> str:
    """Форматирует результаты поиска модов для ответа Миры"""
    if not mods:
        return f"ой не нашла ничего по запросу '{query}' 😔 попробуй поискать сам:\n• curseforge.com\n• modrinth.com\n\nили напиши по другому, может я пойму что тебе нужно"
    
    lines = [f"вот что я нашла по запросу '{query}':"]
    
    for i, mod in enumerate(mods[:4], 1):
        name = mod["name"]
        url = mod["url"]
        summary = mod.get("summary", "")
        
        if summary:
            lines.append(f"\n{i}. {name} — {summary}\n   {url}")
        else:
            lines.append(f"\n{i}. {name}\n   {url}")
    
    if len(mods) > 4:
        lines.append(f"\nи ещё {len(mods) - 4} модов... уточни запрос если надо")
    
    return "\n".join(lines)
