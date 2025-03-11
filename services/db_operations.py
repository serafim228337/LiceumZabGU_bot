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


async def add_user_to_db(db, user_id, username, full_name):
    existing_user = await db.get(User, user_id)

    if existing_user:
        # Обновляем существующего пользователя
        existing_user.username = username
        existing_user.full_name = full_name
        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    else:
        # Создаем нового пользователя
        new_user = User(id=user_id, username=username, full_name=full_name)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user


async def update_user_profile(db: AsyncSession, user_id: int, full_name: str, class_number: str,
                              class_letter: str, contact_info: str, role: str, subjects: str):
    try:
        # Запрос к базе данных для получения пользователя по user_id
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            # Обновляем данные пользователя в базе данных
            user.full_name = full_name
            user.class_number = class_number
            user.class_letter = class_letter
            user.contact_info = contact_info
            user.role = role
            user.subjects = subjects  # Для учителей

            # Применяем изменения в базе данных
            await db.commit()

            return True
        else:
            # Если пользователя не найдено
            return False
    except Exception as e:
        print(f"Ошибка обновления профиля: {e}")
        await db.rollback()  # Откатываем изменения в случае ошибки
        return False
