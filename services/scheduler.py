import os
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database.db import get_db
from database.models import Event

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


async def send_event_reminders():
    async for db in get_db():
        events = await db.execute(
            select(Event).where(
                Event.date.between(
                    datetime.now(),
                    datetime.now() + timedelta(hours=1)
                )
            )
        )
        events = events.scalars().all()

        for event in events:
            try:
                await bot.send_message(
                    chat_id=event.created_by,
                    text=f"Напоминание: событие '{event.title}' начнётся через час!"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления: {e}")


# Запускаем задачу каждые 30 минут
scheduler.add_job(send_event_reminders, 'interval', minutes=30)


def start():
    scheduler.start()
