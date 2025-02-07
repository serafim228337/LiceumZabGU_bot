import os

from aiogram import F
from aiogram import Router
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("config", "cfg.env"))  # Загружаем переменные окружения из файла .env

router = Router()

# Список для хранения групп (dummy-данные)
GROUPS = []


@router.chat_member()
async def on_chat_member_updated(chat_member_update: ChatMemberUpdated):
    print(f"Получено обновление: {chat_member_update}")
    # Проводим дополнительные проверки и логи


@router.message(F.text == '/list_groups')
async def list_groups(message: Message):
    if not GROUPS:
        await message.answer("Группы ещё не добавлены.")
    else:
        response = "Добавленные группы:\n"
        for group in GROUPS:
            response += f"{group['group_name']} (chat_id: {group['chat_id']})\n"
        await message.answer(response)


