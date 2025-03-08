from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Event, Group
from database.models import User


async def get_events_for_tomorrow(db: AsyncSession):
    """Получает события, запланированные на завтра."""
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_after_tomorrow = tomorrow + timedelta(days=1)
    query = select(Event).where(Event.date >= tomorrow, Event.date < day_after_tomorrow)
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_groups(db: AsyncSession):
    """Получает все chat_id групп из базы данных."""
    query = select(Group.chat_id)
    result = await db.execute(query)
    return [row.chat_id for row in result.fetchall()]


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


async def add_user_to_db(db: AsyncSession, user_id: int, username: str, full_name: str):
    new_user = User(id=user_id, username=username, full_name=full_name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_user_profile(
        db: AsyncSession,
        user_id: int,
        full_name: str,
        phone_number: str,
        role: str = None,  # Новая колонка для роли
        class_number: str = None,  # Для учеников
        class_letter: str = None,  # Для учеников
        subjects: str = None  # Для учителей
):
    user = await get_user_by_id(db, user_id)
    if user:
        user.full_name = full_name
        user.phone_number = phone_number

        # Обновляем роль, если она передана
        if role:
            user.role = role

        # Обновляем данные для учеников
        if role == "1":  # Ученик
            user.class_number = class_number
            user.class_letter = class_letter
            user.subjects = None  # Очищаем предметы, если они были

        # Обновляем данные для учителей
        elif role == "3":  # Учитель
            user.subjects = subjects
            user.class_number = None  # Очищаем класс, если он был
            user.class_letter = None  # Очищаем букву класса, если она была

        # Обновляем данные для родителей
        elif role == "2":  # Родитель
            user.class_number = None
            user.class_letter = None
            user.subjects = None

        await db.commit()
