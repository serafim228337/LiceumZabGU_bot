from aiogram import Router, F
from aiogram.types import Message
from services.db_operations import get_user_by_id, add_user_to_db
from database.db import get_db

router = Router()

@router.message(F.text == '/start')
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Получаем сессию из генератора get_db()
    async for db in get_db():
        user = await get_user_by_id(db, user_id)
        if not user:
            # Если пользователя нет в базе, добавляем его
            user = await add_user_to_db(db, user_id, username, full_name)
            await message.answer(f"Привет, {full_name}! Ты зарегистрирован!")
        else:
            await message.answer(f"Добро пожаловать снова, {full_name}!")
