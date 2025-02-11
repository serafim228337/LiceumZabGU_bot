from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import User

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def add_user_to_db(db: AsyncSession, user_id: int, username: str, full_name: str):
    new_user = User(id=user_id, username=username, full_name=full_name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
