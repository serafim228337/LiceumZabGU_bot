import logging
import os
import os.path
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.enums import UpdateType
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from database.db import init_db
from handlers import user_router, admin_router, profile_handler, group_router
from handlers.bot_commands import set_commands
from services.log_cleaner import clean_old_logs
from services.notifications import send_event_reminders

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из файла config/cfg.env
load_dotenv(dotenv_path=os.path.join("config", "cfg.env"))


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()
    await set_commands(bot)

    # роутеры
    dp.include_router(group_router)
    dp.include_router(admin_router)
    dp.include_router(profile_handler.router)
    dp.include_router(user_router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        partial(send_event_reminders, bot),
        trigger="interval",
        hours=1,  # Проверка каждые 1 час
    )
    scheduler.add_job(
        clean_old_logs,
        'cron',
        hour=3,
        minute=0,
        kwargs={'days_to_keep': 90}  # Храним логи 90 дней
    )
    scheduler.start()

    # Указываем типы обновлений
    await dp.start_polling(bot, allowed_updates=[UpdateType.MESSAGE, UpdateType.CHAT_MEMBER])


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
