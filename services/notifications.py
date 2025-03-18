import logging
from datetime import datetime, timedelta

import pytz
from aiogram import Bot
from sqlalchemy import select

from database.db import get_db
from database.models import Event, Group

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Часовой пояс GMT+9 (Asia/Tokyo)
JST = pytz.timezone('Asia/Tokyo')


async def send_event_reminders(bot: Bot) -> bool:
    """Функция для отправки напоминаний о событиях (автоматическая рассылка).
       Возвращает True, если напоминания отправлены, иначе False."""
    async for db in get_db():
        try:
            # Текущее время в UTC и конвертация в JST
            now = datetime.utcnow().replace(tzinfo=pytz.utc)
            jst_time = now.astimezone(JST)

            # Устанавливаем время напоминания на 20:00 по JST
            reminder_time = jst_time.replace(hour=20, minute=0, second=0, microsecond=0)

            if jst_time >= reminder_time and jst_time < reminder_time + timedelta(days=1):
                reminder_time = jst_time  # Отправляем в 20:00 текущего дня

            # Получаем события, которые начнутся через сутки (определяется диапазоном времени)
            events = await db.execute(
                select(Event).where(
                    Event.date.between(
                        reminder_time - timedelta(days=1),
                        reminder_time - timedelta(days=1, minutes=1)
                    )
                )
            )
            events = events.scalars().all()

            if not events:
                logger.info("Нет событий для напоминания.")
                return False

            # Получаем все группы из базы данных
            groups = await db.execute(select(Group))
            groups = groups.scalars().all()

            for event in events:
                for group in groups:
                    try:
                        await bot.send_message(
                            chat_id=group.chat_id,
                            text=f"⏰ Напоминание: событие '{event.title}' начнётся через сутки!\n"
                                 f"📅 Дата: {event.date.strftime('%Y-%m-%d %H:%M')}\n"
                                 f"📝 Описание: {event.description}"
                        )
                        logger.info(f"Напоминание отправлено в группу {group.group_name} для события '{event.title}'.")
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления группе {group.group_name}: {e}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при выполнении функции send_event_reminders: {e}")
            return False


async def send_forced_event_reminders(bot: Bot) -> bool:
    """Функция для принудительной рассылки напоминаний.
       Если событий на завтра нет, возвращает False, иначе – True."""
    async for db in get_db():
        try:
            now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(JST)
            start_of_tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_tomorrow = start_of_tomorrow + timedelta(days=1, microseconds=-1)

            # Получаем события, которые начнутся завтра
            events = await db.execute(
                select(Event).where(
                    Event.date.between(
                        start_of_tomorrow,
                        end_of_tomorrow
                    )
                )
            )
            events = events.scalars().all()

            if not events:
                logger.info("Нет событий для напоминания.")
                return False

            # Получаем все группы из базы данных
            groups = await db.execute(select(Group))
            groups = groups.scalars().all()

            for event in events:
                for group in groups:
                    try:
                        await bot.send_message(
                            chat_id=group.chat_id,
                            text=f"⏰ Напоминание: событие '{event.title}' начнётся завтра!\n"
                                 f"📅 Дата: {event.date.strftime('%Y-%m-%d %H:%M')}\n"
                                 f"📝 Описание: {event.description}"
                        )
                        logger.info(f"Напоминание отправлено в группу {group.group_name} для события '{event.title}'.")
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления группе {group.group_name}: {e}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при выполнении функции send_forced_event_reminders: {e}")
            return False
