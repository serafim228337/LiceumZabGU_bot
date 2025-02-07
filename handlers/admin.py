import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from services.group_utils import GROUPS  # Импортируем общий список групп

router = Router()

@router.message(Command("send_notification"))
async def send_notification(message: Message):
    """
    Команда /send_notification <текст уведомления> отправляет уведомление во все добавленные группы.
    Только администраторы (ID которых указаны в переменной ADMINS) могут использовать эту команду.
    """
    # Проверка прав администратора
    if str(message.from_user.id) not in os.getenv("ADMINS").split(","):
        await message.answer("У вас нет прав для использования этой команды.")
        return

    # Извлекаем текст уведомления
    notification_text = message.text.replace("/send_notification", "").strip()
    if not notification_text:
        await message.answer("Введите текст уведомления после команды.")
        return

    # Отправляем уведомление в каждую группу из списка GROUPS
    for group in GROUPS:
        try:
            await message.bot.send_message(chat_id=group["chat_id"], text=notification_text)
        except Exception as e:
            print(f"Ошибка отправки уведомления группе {group['group_name']}: {e}")
    await message.answer("Уведомления отправлены.")

@router.message(F.text.startswith("/add_group"))
async def add_group_handler(message: Message):
    """
    Команда /add_group <group_id> проверяет, состоит ли бот в указанной группе,
    и если да, добавляет группу в общий список GROUPS.
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Использование: /add_group <group_id>")
            return

        group_id = int(parts[1])
        from services.group_utils import add_bot_to_group  # Импортируем функцию для проверки группы
        await add_bot_to_group(group_id)
        await message.answer("Проверка группы завершена. Проверьте консоль для подробностей.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@router.message(F.text == "/list_groups")
async def list_groups_handler(message: Message):
    """
    Команда /list_groups выводит список всех добавленных групп.
    """
    if not GROUPS:
        await message.answer("Группы ещё не добавлены.")
    else:
        response = "Добавленные группы:\n"
        for group in GROUPS:
            response += f"{group['group_name']} (chat_id: {group['chat_id']})\n"
        await message.answer(response)
