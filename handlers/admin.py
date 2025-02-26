from datetime import datetime

from aiogram import Bot
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from database.db import get_db
from database.models import Event
from filters.is_admin import is_admin
from keyboards.admin_panel import admin_panel
from keyboards.all_kb import main_kb
from services.group_operations import add_group_to_db, get_all_groups, get_groups_from_db

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

    await message.answer(
        "Админ-панель:",
        reply_markup=admin_panel()
    )


@router.message(Command("add_group"))
async def add_group_handler(message: Message):
    if not is_admin(message.from_user.id):  # Проверка на админа
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
        await message.answer(f"Группа {group.group_name} с chat_id {group.chat_id} добавлена.",
                             reply_markup=admin_panel())


@router.message(Command("list_groups"))
async def list_groups_handler(message: Message):
    if not is_admin(message.from_user.id):  # Проверка на админа
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


@router.message(SendMessageState.waiting_for_message)
async def process_message_to_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        await state.clear()
        return

    # Получаем список групп из базы данных
    async for db in get_db():
        groups = await (get_groups_from_db(db))

        # Отправляем сообщение в каждую группу
        for group_id in groups:
            await bot.send_message(chat_id=group_id, text=message.text)

    await message.answer("Сообщение успешно разослано по группам!")
    await state.clear()


@router.message(F.text == "На главную")
async def back_to_main_handler(message: Message):
    await message.answer(
        "Вы вернулись на главную.",
        reply_markup=main_kb(message.from_user.id)
    )


class AddEventState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_date = State()


@router.message(Command("add_event"))
async def add_event_start(message: Message, state: FSMContext):
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
