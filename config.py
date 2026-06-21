import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
BASE_URL = os.getenv("BASE_URL", "https://localhost:8080")

# Google Custom Search API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# ID чата сервера
GROUP_CHAT_ID = -1003891930776

# Создатель бота и владелец сервера
CREATOR = "@ZOJlOTOY"
OWNER = "@pelmewki379"
OWNER_TG = "pelmewki379"

# AI модели — бесплатные рабочие (июнь 2026)
AI_MODELS = [
    # Основная — лучшая для русского языка и логики
    "openai/gpt-oss-120b:free",          # GPT-OSS 120B — огромная, Chain-of-Thought
    
    # Быстрая для повседневного общения
    "openai/gpt-oss-20b:free",           # GPT-OSS 20B — быстрая, лёгкая
    
    # От Google — отличный русский
    "google/gemma-4-31b-instruct:free",  # Gemma 4 — 256K контекст
    
    # NVIDIA — огромный контекст
    "nvidia/nemotron-3-super:free",      # Nemotron 3 — 1M контекст
]

# Интервал спонтанных сообщений (в секундах)
SPONTANEOUS_MIN = 14400  # 4 часа
SPONTANEOUS_MAX = 28800  # 8 часов

# Глубина памяти чата
CHAT_MEMORY_SIZE = 300

# Сервер Minecraft для mcstatus
MC_SERVER = {
    "java_ip": "150.241.85.40",
    "java_port": 25565,
    "bedrock_ip": "150.241.85.40",
    "bedrock_port": 19132,
    "version": "1.21—1.26+",
}

# Админы для команд
ADMIN_IDS = [8493522297]

# Реакции Энди на сообщения
ENDERIA_REACTIONS = {
    "красиво": "👍", "круто": "🔥", "красота": "❤️", "молодец": "👏",
    "спасибо": "💜", "привет": "👋", "хай": "👋", "пока": "👋",
    "хорошо": "👍", "отлично": "🎉", "класс": "🤩", "топ": "🔥",
    "имба": "🔥", "вау": "😍", "кайф": "😊", "найс": "👍", "збс": "🔥",
    "смешно": "😂", "ахах": "😂", "лол": "😄", "ржу": "😂",
    "угар": "🤣", "прикол": "😁", "ор": "😆",
    "грустно": "😢", "жаль": "😔", "обидно": "😢", "плохо": "😕",
    "ого": "😱", "ничего себе": "😲", "серьёзно": "😳", "реально": "😮",
    "алмаз": "💎", "алмазы": "💎", "незерит": "🟣",
    "победил": "🏆", "умер": "💀", "крипер": "💚", "эндер": "🖤",
    "ферма": "🌾", "шахта": "⛏️", "вкусно": "🍕",
}
