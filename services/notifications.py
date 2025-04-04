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
    """Функция для отправки напоминаний о событиях завтрашнего дня (рассылается в 20:00 JST)."""
    async for db in get_db():
        try:
            # Текущее время в JST
            now = datetime.now(JST)

            # Проверяем, что сейчас ~20:00 (допуск 5 минут)
            if now.hour != 20 or now.minute > 5:
                logger.info("Сейчас не время для отправки напоминаний (не 20:00 JST).")
                return False

            # Определяем начало и конец завтрашнего дня
            tomorrow = now + timedelta(days=1)
            start_of_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_tomorrow = start_of_tomorrow + timedelta(days=1, microseconds=-1)

            # Получаем все события, которые начнутся завтра
            events = await db.execute(
                select(Event).where(
                    Event.date.between(start_of_tomorrow, end_of_tomorrow)
                )
            )
            events = events.scalars().all()

            if not events:
                logger.info("Нет событий для напоминания на завтра.")
                return False

            # Получаем все группы
            groups = await db.execute(select(Group))
            groups = groups.scalars().all()

            for event in events:
                for group in groups:
                    try:
                        await bot.send_message(
                            chat_id=group.chat_id,
                            text=f"⏰ Напоминание: событие '{event.title}' состоится завтра!\n"
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
