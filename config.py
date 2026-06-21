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

# AI модели — бесплатные с большим контекстом (июнь 2025)
AI_MODELS = [
    # Основные — лучшие для общения на русском
    "qwen/qwen3-235b-a22b:free",          # Qwen 3 — лучший русский, 235B
    "meta-llama/llama-3.3-70b-instruct:free", # Llama 3.3 — проверенный стандарт
    "deepseek/deepseek-r1:free",          # DeepSeek R1 — думает перед ответом
    
    # Быстрые и креативные
    "tencent/hy3:preview",                # Hy3 — богатый русский язык
    "stepfun/step-3.5-flash:free",        # Step 3.5 — быстрая и умная
    
    # С большим контекстом
    "google/gemma-4-31b-instruct:free",   # Gemma 4 — 256K контекст
    "nvidia/nemotron-3-super:free",       # Nemotron — 1M контекст
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
