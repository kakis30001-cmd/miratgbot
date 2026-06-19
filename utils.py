"""
Утилиты для Миры: проверка онлайна, поиск модов.
"""

import asyncio
import aiohttp
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from urllib.parse import quote_plus
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


# ========== НАСТОЯЩИЙ ПОИСК МОДОВ ==========

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
            
            headers = {
                "User-Agent": "MiraBot/1.0 (LostEarth Minecraft Server; mira@lostearth.com)"
            }
            
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for hit in data.get("hits", []):
                        results.append({
                            "name": hit["title"],
                            "url": f"https://modrinth.com/mod/{hit['slug']}",
                            "summary": hit.get("description", "")[:200],
                            "downloads": hit.get("downloads", 0),
                            "source": "Modrinth"
                        })
                    if results:
                        print(f"✅ Modrinth: найдено {len(results)} модов")
                    return results
                else:
                    print(f"❌ Modrinth API ошибка: {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка Modrinth: {e}")
    
    return []


async def search_mods_curseforge_scrape(query: str) -> List[dict]:
    """
    Поиск через прямую страницу поиска CurseForge.
    Парсим HTML страницу с результатами.
    """
    try:
        async with aiohttp.ClientSession() as session:
            search_url = "https://www.curseforge.com/minecraft/search"
            params = {
                "search": query,
                "class": "mods",
                "page": 1
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru,en;q=0.9",
            }
            
            async with session.get(search_url, params=params, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    results = _parse_curseforge_search(html)
                    if results:
                        print(f"✅ CurseForge парсинг: найдено {len(results)} модов")
                    return results
                else:
                    print(f"❌ CurseForge страница: статус {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка парсинга CurseForge: {e}")
    
    return []


def _parse_curseforge_search(html: str) -> List[dict]:
    """Парсинг результатов поиска CurseForge"""
    results = []
    
    # Ищем карточки модов - паттерн для новых версий сайта
    # Ищем ссылки вида /minecraft/mc-mods/название-мода
    pattern = r'/minecraft/mc-mods/([^/"]+)[^"]*"[^>]*>\s*(?:<[^>]*>)*\s*([^<]{2,100})\s*(?:</[^>]*>\s*)*</a>'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    if not matches:
        # Альтернативный паттерн
        pattern2 = r'href="(/minecraft/mc-mods/[^"]+)"[^>]*>\s*<[^>]+class="[^"]*name[^"]*"[^>]*>([^<]+)</'
        matches = re.findall(pattern2, html, re.IGNORECASE)
    
    seen = set()
    for slug_or_url, name in matches:
        name = name.strip()
        if not name or len(name) < 3:
            continue
        
        # Нормализуем имя
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'&amp;', '&', name)
        name = re.sub(r'&#x27;', "'", name)
        
        if name.lower() in seen:
            continue
        
        seen.add(name.lower())
        
        # Формируем URL
        if slug_or_url.startswith('/'):
            url = f"https://www.curseforge.com{slug_or_url}"
        else:
            url = f"https://www.curseforge.com/minecraft/mc-mods/{slug_or_url}"
        
        results.append({
            "name": name,
            "url": url,
            "summary": "",
            "downloads": 0,
            "source": "CurseForge"
        })
        
        if len(results) >= 5:
            break
    
    return results


async def search_mods_duckduckgo(query: str) -> List[dict]:
    """
    Поиск через DuckDuckGo Instant Answer API.
    Бесплатно, без ключа.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # DuckDuckGo имеет неофициальный API для instant answers
            url = "https://api.duckduckgo.com/"
            params = {
                "q": f"minecraft mod {query} site:curseforge.com OR site:modrinth.com",
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    results = []
                    
                    # Проверяем RelatedTopics
                    for topic in data.get("RelatedTopics", [])[:5]:
                        if "Text" in topic and "FirstURL" in topic:
                            text = topic["Text"]
                            url = topic["FirstURL"]
                            
                            # Извлекаем название из текста
                            name = re.sub(r'<[^>]+>', '', text)
                            name = name.split(' - ')[0].strip()
                            if len(name) > 50:
                                name = name[:50] + "..."
                            
                            if "curseforge.com" in url or "modrinth.com" in url:
                                results.append({
                                    "name": name,
                                    "url": url,
                                    "summary": "",
                                    "downloads": 0,
                                    "source": "DuckDuckGo"
                                })
                    
                    if results:
                        print(f"✅ DuckDuckGo: найдено {len(results)} ссылок")
                        return results
    except Exception as e:
        print(f"❌ Ошибка DuckDuckGo: {e}")
    
    return []


async def search_mods_google_scrape(query: str) -> List[dict]:
    """
    Поиск через Google (парсинг результатов).
    Ищет только на curseforge.com и modrinth.com.
    """
    try:
        search_query = f'site:curseforge.com/minecraft/mc-mods OR site:modrinth.com/mod {query}'
        encoded_query = quote_plus(search_query)
        
        async with aiohttp.ClientSession() as session:
            url = f"https://www.google.com/search?q={encoded_query}&num=10"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru-RU,ru;q=0.9",
            }
            
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    results = _parse_google_results(html)
                    if results:
                        print(f"✅ Google: найдено {len(results)} ссылок")
                    return results
                elif resp.status == 429:
                    print("❌ Google заблокировал (429)")
                else:
                    print(f"❌ Google: статус {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка Google: {e}")
    
    return []


def _parse_google_results(html: str) -> List[dict]:
    """Парсинг результатов Google"""
    results = []
    
    # Ищем ссылки и заголовки в результатах Google
    # Паттерн для современных результатов Google
    pattern = r'<a[^>]*href="(https?://(?:www\.)?(?:curseforge\.com/minecraft/mc-mods/[^"]+|modrinth\.com/mod/[^"]+))"[^>]*>(?:<[^>]*>)*([^<]{5,200})</a>'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    if not matches:
        # Альтернативный паттерн
        pattern2 = r'href="(https?://[^"]*(?:curseforge\.com/minecraft/mc-mods|modrinth\.com/mod)[^"]*)"[^>]*>(?:<[^>]+>)*([^<]+)</'
        matches = re.findall(pattern2, html, re.IGNORECASE)
    
    seen = set()
    for url, title in matches[:10]:
        # Очищаем заголовок
        title = re.sub(r'<[^>]+>', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'&amp;', '&', title)
        title = re.sub(r'&#x27;', "'", title)
        
        if not title or len(title) < 3:
            continue
        
        # Убираем мусор из заголовка
        title = re.sub(r' - Minecraft.*$', '', title)
        title = re.sub(r' \| CurseForge.*$', '', title)
        
        if title.lower() in seen or url in seen:
            continue
        
        seen.add(title.lower())
        seen.add(url)
        
        source = "CurseForge" if "curseforge" in url else "Modrinth"
        
        results.append({
            "name": title[:100],
            "url": url,
            "summary": "",
            "downloads": 0,
            "source": source
        })
    
    return results[:5]


# ========== Основная функция поиска ==========

async def search_mods(query: str) -> List[dict]:
    """
    Многоуровневый поиск модов.
    Пробуем разные источники пока не найдём.
    """
    results = []
    
    # Уровень 1: Modrinth API (самый надёжный)
    results = await search_mods_modrinth(query)
    if len(results) >= 2:
        return results
    
    # Уровень 2: Google поиск
    google_results = await search_mods_google_scrape(query)
    if google_results:
        # Объединяем результаты
        seen_names = {r["name"].lower() for r in results}
        for r in google_results:
            if r["name"].lower() not in seen_names:
                results.append(r)
                seen_names.add(r["name"].lower())
        
        if len(results) >= 2:
            return results
    
    # Уровень 3: Парсинг CurseForge напрямую
    curse_results = await search_mods_curseforge_scrape(query)
    if curse_results:
        seen_names = {r["name"].lower() for r in results}
        for r in curse_results:
            if r["name"].lower() not in seen_names:
                results.append(r)
                seen_names.add(r["name"].lower())
    
    # Уровень 4: DuckDuckGo
    if len(results) < 2:
        ddg_results = await search_mods_duckduckgo(query)
        if ddg_results:
            seen_names = {r["name"].lower() for r in results}
            for r in ddg_results:
                if r["name"].lower() not in seen_names:
                    results.append(r)
    
    # Уровень 5: Прямая ссылка на поиск
    if not results:
        results.append({
            "name": f"Поиск '{query}' на CurseForge",
            "url": f"https://www.curseforge.com/minecraft/search?search={quote_plus(query)}&class=mods",
            "summary": "открой ссылку чтобы посмотреть все моды по твоему запросу",
            "downloads": 0,
            "source": "CurseForge Search"
        })
        results.append({
            "name": f"Поиск '{query}' на Modrinth",
            "url": f"https://modrinth.com/mods?q={quote_plus(query)}",
            "summary": "открой ссылку чтобы посмотреть все моды",
            "downloads": 0,
            "source": "Modrinth Search"
        })
    
    return results[:5]


def format_mod_results(mods: List[dict], query: str) -> str:
    """Форматирует результаты поиска модов для ответа Миры"""
    if not mods:
        return f"ой не нашла ничего по запросу '{query}' 😔 попробуй поискать сам на curseforge.com или modrinth.com"
    
    # Если только ссылки на поиск
    if all(m["name"].startswith("Поиск") for m in mods):
        lines = [f"по запросу '{query}' вот что могу предложить:"]
        for mod in mods:
            lines.append(f"\n🔗 {mod['name']}\n   {mod['url']}")
        return "\n".join(lines)
    
    # Нормальные результаты
    lines = [f"вот что я нашла по запросу '{query}':"]
    
    for i, mod in enumerate(mods[:4], 1):
        name = mod["name"]
        url = mod["url"]
        summary = mod.get("summary", "")
        source = mod.get("source", "")
        
        if summary and len(summary) > 10:
            if len(summary) > 120:
                summary = summary[:120] + "..."
            lines.append(f"\n{i}. {name} [{source}]\n   {summary}\n   {url}")
        else:
            lines.append(f"\n{i}. {name} [{source}]\n   {url}")
    
    if len(mods) > 4:
        search_url = f"https://www.curseforge.com/minecraft/search?search={quote_plus(query)}&class=mods"
        lines.append(f"\n...и ещё результаты, глянь тут: {search_url}")
    
    return "\n".join(lines)
