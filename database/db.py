import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os.path

# Загружаем переменные окружения из файла config/cfg.env
load_dotenv(dotenv_path=os.path.join("config", "cfg.env"))

# Формируем строку подключения к базе данных
DATABASE_URL = (
    f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

# Создаем асинхронный двигатель подключения к базе
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий для асинхронных запросов
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Базовый класс для моделей
Base = declarative_base()

# Функция для инициализации базы данных (создание таблиц, если их нет)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Асинхронный генератор для получения сессии (используется в обработчиках)
async def get_db():
    async with async_session() as session:
        yield session
