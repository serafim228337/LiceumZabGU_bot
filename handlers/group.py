import datetime

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy import select
from config.config import schedule_link
from database.db import get_db
from database.models import Event
from .user import get_week_type

router = Router()
router.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))

@router.message(Command("schedule"))
async def send_schedule_link_in_group(message: Message):
    week_type = get_week_type()

    await message.answer(
        f"*🗓️ Текущая неделя: {week_type.upper()}*\n"
        f"[Открыть расписание 📅]({schedule_link})",
        parse_mode="MarkdownV2"
    )

@router.message(Command("events"))
async def events_in_group(message: Message):
    async for db in get_db():
        events = await db.execute(select(Event).where(Event.date >= datetime.datetime.now()).order_by(Event.date))
        events = events.scalars().all()

        if not events:
            await message.answer("Предстоящих событий нет.")
            return

        response = "Предстоящие события:\n"
        for event in events:
            response += (
                f"📅 {event.title}\n"
                f"📝 {event.description}\n"
                f"⏰ {event.date.strftime('%Y-%m-%d %H:%M')}\n\n"
            )
        await message.answer(
            response,
            reply_markup=ReplyKeyboardRemove()
        )
