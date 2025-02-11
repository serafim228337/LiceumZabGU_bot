import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database.db import init_db
from handlers import user_router, admin_router
import os.path

# Загружаем переменные окружения из файла config/cfg.env
load_dotenv(dotenv_path=os.path.join("config", "cfg.env"))

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализируем базу данных (создаем таблицы, если их еще нет)
    await init_db()

    # Подключаем обработчики (роутеры)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
