from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == '/start')
async def start(message: Message):
    # Заглушка вместо регистрации пользователя в БД
    await message.answer(
        "Добро пожаловать! Функционал регистрации временно недоступен. Попробуйте позже."
    )
