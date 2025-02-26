import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database.db import init_db
from handlers import user_router, admin_router, profile_handler
from services.notifications import send_daily_notifications
from handlers.bot_commands import set_commands
import os.path

# Загружаем переменные окружения из файла config/cfg.env
load_dotenv(dotenv_path=os.path.join("config", "cfg.env"))

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализируем базу данных (создаем таблицы, если их еще нет)
    await init_db()
    await set_commands(bot)
    asyncio.create_task(send_daily_notifications(bot))

    # Подключаем обработчики (роутеры)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(profile_handler.router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())