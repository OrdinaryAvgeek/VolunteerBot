# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from config import DATABASE_URL

# Создаём движок базы данных
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаём фабрику сессий
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()


async def init_db():
    """Инициализация базы данных: создание всех таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Возвращает сессию базы данных (для dependency injection)"""
    async with async_session_maker() as session:
        yield session