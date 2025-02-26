import asyncio
from datetime import datetime
from aiogram import Bot
import pytz
from database.db import get_db
from services.db_operations import get_events_for_tomorrow, get_all_groups

async def send_daily_notifications(bot: Bot):
    """Фоновая задача для отправки уведомлений о событиях за сутки до начала."""
    timezone = pytz.timezone('Europe/Moscow')  # Устанавливаем московский часовой пояс
    last_sent_date = None  # Переменная для отслеживания даты последней отправки

    while True:
        now = datetime.now(timezone)  # Получаем текущее время в московском часовом поясе
        current_date = now.date()  # Получаем текущую дату

        # Проверяем, наступило ли 20:00 и не отправляли ли уже сегодня
        if now.hour == 20 and now.minute == 0 and last_sent_date != current_date:
            async for db in get_db():
                # Получаем события на завтра
                events = await get_events_for_tomorrow(db)
                if events:
                    # Получаем все группы для рассылки
                    groups = await get_all_groups(db)
                    for event in events:
                        # Формируем сообщение
                        message = f"Напоминание: завтра событие '{event.title}' в {event.date.strftime('%H:%M')}"
                        for group_id in groups:
                            try:
                                # Отправляем сообщение в группу
                                await bot.send_message(chat_id=group_id, text=message)
                            except Exception as e:
                                print(f"Ошибка при отправке в {group_id}: {e}")
                    # Обновляем дату последней отправки
                    last_sent_date = current_date

        # Ждем до следующей минуты
        await asyncio.sleep(60 - now.second)