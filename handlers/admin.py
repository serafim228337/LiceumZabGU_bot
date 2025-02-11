import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.db import get_db
from services.group_operations import add_group_to_db, get_all_groups

router = Router()

@router.message(Command("add_group"))
async def add_group_handler(message: Message):
    """
    Команда: /add_group <chat_id> <group_name>
    Добавляет группу в базу данных для последующей рассылки уведомлений.
    """
    admin_ids = os.getenv("ADMINS", "").split(",")
    if str(message.from_user.id) not in admin_ids:
        await message.answer("У вас нет прав для этой команды.")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /add_group <chat_id> <group_name>")
        return

    chat_id = parts[1]
    group_name = parts[2]

    async for db in get_db():
        group = await add_group_to_db(db, chat_id, group_name)
        await message.answer(f"Группа {group.group_name} с chat_id {group.chat_id} добавлена.")

@router.message(Command("list_groups"))
async def list_groups_handler(message: Message):
    """
    Команда: /list_groups
    Выводит список добавленных групп для уведомлений.
    """
    async for db in get_db():
        groups = await get_all_groups(db)
        if not groups:
            await message.answer("Группы не найдены.")
            return
        response = "Добавленные группы:\n"
        for group in groups:
            response += f"{group.group_name} (chat_id: {group.chat_id})\n"
        await message.answer(response)

@router.message(Command("send_notification"))
async def send_notification_handler(message: Message):
    """
    Команда: /send_notification <текст уведомления>
    Отправляет уведомление во все добавленные группы.
    """
    admin_ids = os.getenv("ADMINS", "").split(",")
    if str(message.from_user.id) not in admin_ids:
        await message.answer("У вас нет прав для использования этой команды.")
        return

    notification_text = message.text.replace("/send_notification", "").strip()
    if not notification_text:
        await message.answer("Введите текст уведомления после команды.")
        return

    async for db in get_db():
        groups = await get_all_groups(db)
        if not groups:
            await message.answer("Группы не найдены.")
            return
        for group in groups:
            try:
                await message.bot.send_message(chat_id=group.chat_id, text=notification_text)
            except Exception as e:
                print(f"Ошибка отправки уведомления группе {group.group_name}: {e}")
        await message.answer("Уведомления отправлены.")
