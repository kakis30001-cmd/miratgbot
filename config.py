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

# AI модели (основная + запасные)
AI_MODELS = [
    "google/gemini-2.0-flash",
    "google/gemini-2.0-flash-exp",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat",
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
    # Позитивные
    "красиво": "👍",
    "круто": "🔥",
    "красота": "❤️",
    "молодец": "👏",
    "спасибо": "💜",
    "привет": "👋",
    "хай": "👋",
    "пока": "👋",
    "люблю": "💋",
    "хорошо": "👍",
    "отлично": "🎉",
    "класс": "🤩",
    "топ": "🔥",
    "имба": "🔥",
    "вау": "😍",
    "кайф": "😊",
    "найс": "👍",
    "збс": "🔥",
    
    # Смешные
    "смешно": "😂",
    "ахах": "😂",
    "ахахах": "😂",
    "лол": "😄",
    "ржу": "😂",
    "угар": "🤣",
    "прикол": "😁",
    "ор": "😆",
    "ору": "😆",
    
    # Грустные
    "грустно": "😢",
    "жаль": "😔",
    "обидно": "😢",
    "плохо": "😕",
    "печаль": "😢",
    
    # Удивление
    "ого": "😱",
    "ничего себе": "😲",
    "серьёзно": "😳",
    "реально": "😮",
    "офигеть": "😱",
    "шок": "😱",
    
    # Игровые
    "алмаз": "💎",
    "алмазы": "💎",
    "незерит": "🟣",
    "победил": "🏆",
    "победа": "🏆",
    "умер": "💀",
    "смерть": "💀",
    "крипер": "💚",
    "эндер": "🖤",
    "дракон": "🐉",
    "деревня": "🏘️",
    "ферма": "🌾",
    "шахта": "⛏️",
    
    # Еда
    "вкусно": "🍕",
    "готовлю": "🍳",
    "ем": "🍽️",
    "кушать": "🍽️",
    "еда": "🍕",
}
