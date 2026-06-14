import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверьте файл .env")

SPHERES = ["Социальная помощь", "Экология", "Образование", "Чрезвычайные ситуации"]

DATABASE_URL = "sqlite+aiosqlite:///volunteers.db"