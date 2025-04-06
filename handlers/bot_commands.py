from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.exceptions import TelegramBadRequest
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Команды для пользователей
user_commands = [
    BotCommand(command="schedule", description="Посмотреть расписание"),
    BotCommand(command="events", description="Посмотреть события")
]

# Команды для администраторов
admin_commands = [
    BotCommand(command="add_group", description="Добавить группу"),
    BotCommand(command="list_groups", description="Список групп"),
    BotCommand(command="send_message", description="Разослать сообщение"),
    BotCommand(command="add_event", description="Добавить событие"),
    BotCommand(command="send_reminders", description="Разослать уведомление о предстоящем событии")
]

async def set_commands(bot: Bot):
    # Устанавливаем команды для пользователей
    await bot.set_my_commands(user_commands)

    # Устанавливаем команды для администраторов
    admin_ids = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    for admin_id in admin_ids:
        try:
            # Проверяем, может ли бот отправить сообщение администратору
            await bot.send_chat_action(chat_id=admin_id, action="typing")
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except TelegramBadRequest as e:
            print(f"Администратор {admin_id} не начал диалог с ботом: {e}")
