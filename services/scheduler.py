import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

scheduler = AsyncIOScheduler()
bot = Bot(token=os.getenv('BOT_TOKEN'))

async def send_reminders():
    # Dummy-данные для пользователей и олимпиад (в будущем заменить данными из БД)
    dummy_users = [
        {"user_id": 111111, "olympiad_name": "Олимпиада 1"},
        {"user_id": 222222, "olympiad_name": "Олимпиада 2"},
    ]
    for user in dummy_users:
        try:
            await bot.send_message(
                chat_id=user["user_id"],
                text=f"Напоминание: Олимпиада {user['olympiad_name']} начинается скоро!"
            )
        except Exception as e:
            print(f"Ошибка отправки напоминания пользователю {user['user_id']}: {e}")

# Запускаем задачу, которая выполняется каждый час
scheduler.add_job(send_reminders, 'interval', hours=1)

def start():
    scheduler.start()
