from datetime import datetime, timedelta

import pytz
from aiogram import Bot, Router, F, types
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from sqlalchemy import select

from database.db import get_db
from database.models import Event, Group
from filters.is_admin import is_admin
from keyboards.admin_panel import admin_panel
from keyboards.all_kb import main_kb
from services.group_operations import get_all_groups, get_groups_from_db
from services.notifications import send_forced_event_reminders

router = Router()
storage = MemoryStorage()


# Создаем состояние для ожидания сообщения
class SendMessageState(StatesGroup):
    waiting_for_message = State()


@router.message(F.text == "⚙️ Админ панель")
async def admin_panel_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён!")
        return

    await message.answer("Админ-панель:", reply_markup=admin_panel())


@router.message(Command("send_reminders"))
async def on_forced_reminder_command(message: Message, bot: Bot):
    """Обработчик команды принудительной рассылки уведомлений через команду /send_reminders."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    # Вызываем функцию принудительной рассылки уведомлений
    result = await send_forced_event_reminders(bot)
    if result:
        await message.answer("Напоминание успешно отправлено!")
    else:
        await message.answer("Событий на завтра нет.")


@router.message(F.text == "Разослать уведомление о предстоящем событии")
async def on_forced_reminder_command_text(message: Message, bot: Bot):
    """Обработчик кнопки для принудительной рассылки уведомлений."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    result = await send_forced_event_reminders(bot)
    if result:
        await message.answer("Напоминание успешно отправлено!")
    else:
        await message.answer("Событий на завтра нет.")


@router.message(Command("add_group"))
async def add_group_handler(message: Message):
    """Добавляет группу в базу данных."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для этой команды.")
        return

    # Проверяем, отправлена ли команда в группе
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        chat_id = str(message.chat.id)
        group_name = message.chat.title

        async for db in get_db():
            # Проверяем, есть ли группа в базе данных
            group = await db.execute(select(Group).where(Group.chat_id == chat_id))
            group = group.scalar_one_or_none()

            if group:
                await message.answer(f"Группа '{group_name}' уже добавлена.")
            else:
                # Добавляем группу в базу данных
                new_group = Group(chat_id=chat_id, group_name=group_name)
                db.add(new_group)
                await db.commit()
                await db.refresh(new_group)
                await message.answer(f"Группа '{group_name}' добавлена в базу данных.")
    else:
        # Если команда отправлена в личном чате, запрашиваем данные вручную
        await message.answer("Использование: /add_group <chat_id> <group_name>")


@router.message(F.text == "Добавить группу")
async def add_group_handler_text(message: Message):
    """Добавляет группу в базу данных."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для этой команды.")
        return

    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        chat_id = str(message.chat.id)
        group_name = message.chat.title

        async for db in get_db():
            group = await db.execute(select(Group).where(Group.chat_id == chat_id))
            group = group.scalar_one_or_none()

            if group:
                await message.answer(f"Группа '{group_name}' уже добавлена.")
            else:
                new_group = Group(chat_id=chat_id, group_name=group_name)
                db.add(new_group)
                await db.commit()
                await db.refresh(new_group)
                await message.answer(f"Группа '{group_name}' добавлена в базу данных.")
    else:
        await message.answer("Использование: /add_group <chat_id> <group_name>")


@router.message(Command("list_groups"))
async def list_groups_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для этой команды.")
        return

    async for db in get_db():
        groups = await get_all_groups(db)
        if not groups:
            await message.answer("Группы не найдены.")
            return
        response = "Добавленные группы:\n"
        for group in groups:
            response += f"{group.group_name} (chat_id: {group.chat_id})\n"
        await message.answer(response, reply_markup=admin_panel())


@router.message(F.text == "Список групп")
async def list_groups_handler_text(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для этой команды.")
        return

    async for db in get_db():
        groups = await get_all_groups(db)
        if not groups:
            await message.answer("Группы не найдены.")
            return
        response = "Добавленные группы:\n"
        for group in groups:
            response += f"{group.group_name} (chat_id: {group.chat_id})\n"
        await message.answer(response, reply_markup=admin_panel())


@router.message(Command("send_message"))
async def send_message_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Отправьте сообщение, которое нужно разослать по группам:")
    await state.set_state(SendMessageState.waiting_for_message)


@router.message(F.text == "Разослать сообщение")
async def send_message_command_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Отправьте сообщение, которое нужно разослать по группам:")
    await state.set_state(SendMessageState.waiting_for_message)


@router.message(SendMessageState.waiting_for_message)
async def process_message_to_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        await state.clear()
        return

    async for db in get_db():
        groups = await get_groups_from_db(db)
        for group_id in groups:
            try:
                await bot.send_message(chat_id=group_id, text=message.text)
            except Exception as e:
                # Если отправка в какую-то группу не удалась, логируем ошибку
                logger.error(f"Ошибка при отправке сообщения в группу {group_id}: {e}")

    await message.answer("Сообщение успешно разослано по группам!")
    await state.clear()


@router.message(F.text == "На главную")
async def back_to_main_handler(message: Message):
    await message.answer("Вы вернулись на главную.", reply_markup=main_kb(message.from_user.id))


class AddEventState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_date = State()


@router.message(Command("add_event"))
async def add_event_start(message: Message, state: FSMContext):
    await message.answer("Введите название события:")
    await state.set_state(AddEventState.waiting_for_title)


@router.message(F.text == "Добавить событие")
async def add_event_start_text(message: Message, state: FSMContext):
    await message.answer("Введите название события:")
    await state.set_state(AddEventState.waiting_for_title)


@router.message(AddEventState.waiting_for_title)
async def add_event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание события:")
    await state.set_state(AddEventState.waiting_for_description)


@router.message(AddEventState.waiting_for_description)
async def add_event_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите дату и время события (в формате ГГГГ-ММ-ДД ЧЧ:ММ):")
    await state.set_state(AddEventState.waiting_for_date)


@router.message(AddEventState.waiting_for_date)
async def add_event_date(message: Message, state: FSMContext):
    try:
        event_date = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Попробуйте снова.")
        return

    data = await state.get_data()
    async for db in get_db():
        new_event = Event(
            title=data["title"],
            description=data["description"],
            date=event_date,
            created_by=message.from_user.id
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)

    await message.answer(f"Событие '{data['title']}' добавлено!")
    await state.clear()
