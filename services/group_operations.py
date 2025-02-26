from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Group

async def get_group_by_chat_id(db: AsyncSession, chat_id: str):
    result = await db.execute(select(Group).filter(Group.chat_id == chat_id))
    return result.scalar_one_or_none()

async def add_group_to_db(db: AsyncSession, chat_id: str, group_name: str):
    group = await get_group_by_chat_id(db, chat_id)
    if group:
        return group
    new_group = Group(chat_id=chat_id, group_name=group_name)
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group

async def get_all_groups(db: AsyncSession):
    result = await db.execute(select(Group))
    return result.scalars().all()

async def get_groups_from_db(db: AsyncSession):
    result = await db.execute(select(Group.chat_id))
    return result.scalars().all()