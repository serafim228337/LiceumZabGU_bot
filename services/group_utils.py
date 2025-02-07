import os
from aiogram import Bot
from aiogram.types import ChatMember
from aiogram.types.chat import Chat
from dotenv import load_dotenv

# Загружаем переменные из файла конфигурации
load_dotenv(os.path.join("config", "cfg.env"))

# Инициализация бота (используйте один экземпляр бота в проекте)
bot = Bot(token=os.getenv("BOT_TOKEN"))

# Глобальный список для хранения добавленных групп
GROUPS = []

async def add_bot_to_group(group_id: int):
    """
    Проверяет, состоит ли бот в группе с заданным group_id,
    и если да, добавляет группу в список GROUPS.
    """
    try:
        # Получаем информацию о членстве бота в чате
        chat_member: ChatMember = await bot.get_chat_member(group_id, bot.id)
        if chat_member.status != "left":
            # Получаем информацию о чате отдельно
            chat: Chat = await bot.get_chat(group_id)
            group_name = chat.title

            # Если такой группы ещё нет в списке, добавляем её
            if not any(group["chat_id"] == str(group_id) for group in GROUPS):
                GROUPS.append({"chat_id": str(group_id), "group_name": group_name})
                print(f"Группа добавлена: {group_name} ({group_id})")
            else:
                print(f"Группа {group_name} ({group_id}) уже добавлена.")
        else:
            print("Бот не является участником данной группы.")
    except Exception as e:
        print(f"Ошибка при проверке группы: {e}")
