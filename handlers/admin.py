import logging
import re
from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from sqlalchemy import select

from database.db import get_db
from database.models import AdminLog, Event, Group
from filters.is_admin import is_admin
from keyboards.admin_panel import admin_panel
from keyboards.all_kb import main_kb
from services.admin_logger import log_admin_action
from services.group_operations import get_all_groups
from services.log_cleaner import clean_old_logs
from services.notifications import send_forced_event_reminders

router = Router()
storage = MemoryStorage()
logger = logging.getLogger(__name__)


# Создаем состояние для ожидания сообщения
class SendMessageState(StatesGroup):
    waiting_for_message = State()


class AddEventState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_date = State()


class SendMessageState(StatesGroup):
    waiting_for_class_number = State()
    waiting_for_class_letter = State()
    waiting_for_message = State()
    waiting_for_confirmation = State()


@router.message(F.text == "⚙️ Админ панель")
async def admin_panel_handler(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён!")
        return

    await message.answer("Админ-панель:", reply_markup=admin_panel())


@router.message(F.text == "Разослать уведомление о предстоящем событии")
@router.message(Command("send_reminders"))
async def on_forced_reminder_command(message: Message, state: FSMContext, bot: Bot):
    """Обработчик команды принудительной рассылки уведомлений через команду /send_reminders."""
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    result = await send_forced_event_reminders(bot)
    if result:
        await message.answer("Напоминание успешно отправлено!")
    else:
        await message.answer("Событий на завтра нет.")

    await log_admin_action(
        message.from_user.id,
        "force_reminder_send",
        f"Принудительная рассылка напоминаний"
    )


@router.message(Command("add_group"))
@router.message(F.text == "Добавить группу")
async def add_group_handler_text(message: Message, state: FSMContext):
    """Добавляет группу в базу данных."""
    await state.clear()
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
@router.message(F.text == "Список групп")
async def list_groups_handler_text(message: Message, state: FSMContext):
    await state.clear()
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


def extract_class_info(group_name: str) -> tuple[str, str]:
    """Извлекает номер и букву класса из названия группы"""
    # Паттерны для поиска: 10А, 10 А, 10-А, 10 - А и т.д.
    match = re.search(r'(\d{1,2})\s*[-]?\s*([А-ГA-Zа-гa-z])', group_name)
    if match:
        return match.group(1), match.group(2).upper()
    return None, None


@router.message(F.text == "Разослать сообщение")
@router.message(Command("send_message"))
async def send_message_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён!")
        await state.clear()
        return

    class_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="8"), KeyboardButton(text="9")],
            [KeyboardButton(text="10"), KeyboardButton(text="11")],
            [KeyboardButton(text="Во все классы"), KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите номер класса для рассылки:", reply_markup=class_kb)
    await state.set_state(SendMessageState.waiting_for_class_number)


@router.message(SendMessageState.waiting_for_class_number)
async def process_class_number(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        return await message.answer("Рассылка отменена", reply_markup=admin_panel())

    valid_classes = ["8", "9", "10", "11", "Во все классы"]
    if message.text not in valid_classes:
        return await message.answer("Пожалуйста, выберите класс из предложенных вариантов")

    await state.update_data(class_number=message.text)

    letter_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="А"), KeyboardButton(text="Б")],
            [KeyboardButton(text="В"), KeyboardButton(text="Г")],
            [KeyboardButton(text="Во все буквы"), KeyboardButton(text="Назад"), KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите букву класса:", reply_markup=letter_kb)
    await state.set_state(SendMessageState.waiting_for_class_letter)


@router.message(SendMessageState.waiting_for_class_letter)
async def process_class_letter(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        return await message.answer("Рассылка отменена", reply_markup=admin_panel())

    if message.text == "Назад":
        return await send_message_command(message, state)

    valid_letters = ["А", "Б", "В", "Г", "Во все буквы"]
    if message.text not in valid_letters:
        return await message.answer("Пожалуйста, выберите букву из предложенных вариантов")

    await state.update_data(class_letter=message.text)
    await message.answer("Введите сообщение для рассылки:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SendMessageState.waiting_for_message)


@router.message(SendMessageState.waiting_for_message)
async def process_message_input(message: Message, state: FSMContext):
    await state.update_data(message_text=message.text)
    data = await state.get_data()

    class_info = ""
    if data['class_number'] != "Во все классы":
        class_info = f"для {data['class_number']} класса"
        if data['class_letter'] != "Во все буквы":
            class_info += f" {data['class_letter']}"

    confirm_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить отправку")],
            [KeyboardButton(text="✏️ Изменить текст")],
            [KeyboardButton(text="🔙 Изменить класс"), KeyboardButton(text="❌ Отменить")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"📝 Подтвердите рассылку {class_info}:\n\n"
        f"---\n"
        f"{message.text}\n"
        f"---\n\n"
        f"Получатели: {class_info or 'Все пользователи'}",
        reply_markup=confirm_kb
    )
    await state.set_state(SendMessageState.waiting_for_confirmation)


@router.message(SendMessageState.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Отменить":
        await state.clear()
        return await message.answer("Рассылка отменена", reply_markup=admin_panel())

    if message.text == "✏️ Изменить текст":
        await message.answer("Введите новый текст:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(SendMessageState.waiting_for_message)
        return

    if message.text == "🔙 Изменить класс":
        await send_message_command(message, state)
        return

    if message.text != "✅ Подтвердить отправку":
        return await message.answer("Пожалуйста, используйте кнопки для подтверждения")

    data = await state.get_data()
    message_text = data['message_text']
    class_number = data.get('class_number')
    class_letter = data.get('class_letter')

    sent_count = 0
    async for db in get_db():
        # Получаем все группы
        groups = await db.execute(select(Group))
        groups = groups.scalars().all()

        # Фильтруем группы по номеру и букве класса
        filtered_groups = []
        for group in groups:
            group_class_num, group_class_letter = extract_class_info(group.group_name)

            # Если номер класса не указан или совпадает
            num_match = (class_number == "Во все классы" or
                         (group_class_num and group_class_num == class_number))

            # Если буква класса не указана или совпадает
            letter_match = (class_letter == "Во все буквы" or
                            (group_class_letter and group_class_letter == class_letter))

            if num_match and letter_match:
                filtered_groups.append(group)

        # Отправляем сообщение в отфильтрованные группы
        for group in filtered_groups:
            try:
                await bot.send_message(
                    chat_id=group.chat_id,
                    text=f"📢 Сообщение для {class_number or 'всех'} класса {class_letter or 'всех букв'}:\n\n{message_text}"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки в группу {group.group_name} (ID: {group.chat_id}): {e}")

        # Логируем действие
        await log_admin_action(
            message.from_user.id,
            "mass_message",
            f"Отправлено в {sent_count} групп. Получатели: класс {class_number or 'все'}{class_letter or ''}"
        )

    await message.answer(
        f"✅ Сообщение успешно отправлено!\n"
        f"• Групп: {sent_count}",
        reply_markup=admin_panel()
    )
    await state.clear()


@router.message(F.text == "На главную")
async def back_to_main_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вернулись на главную.", reply_markup=main_kb(message.from_user.id))


@router.message(Command("add_event"))
@router.message(F.text == "Добавить событие")
async def add_event_start_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        await state.clear()
        return

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

    await log_admin_action(
        message.from_user.id,
        "event_added",
        f"Событие: {data['title']}, дата: {event_date}"
    )

    await message.answer(f"Событие '{data['title']}' добавлено!")
    await state.clear()


@router.message(F.text == "Просмотр логов")
@router.message(Command("logs"))
async def show_logs(message: Message):
    if not is_admin(message.from_user.id):
        return

    async for db in get_db():
        logs = await db.execute(select(AdminLog).order_by(AdminLog.created_at.desc()).limit(50))
        logs = logs.scalars().all()

        if not logs:
            await message.answer("Логи отсутствуют")
            return

        response = "📝 Последние действия администраторов:\n\n"
        for log in logs:
            response += (
                f"🕒 {log.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"👤 ID: {log.admin_id}\n"
                f"⚡ Действие: {log.action}\n"
                f"📄 Детали: {log.details or 'нет'}\n"
                f"──────────────────\n"
            )

        # Разбиваем на части если слишком длинное
        for i in range(0, len(response), 4000):
            await message.answer(response[i:i + 4000])


@router.message(Command("clean_logs"))
@router.message(F.text == "Очистить логи")
async def clean_logs_command(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("Доступ запрещён!")

    try:
        days = 30  # Можно сделать параметром команды
        deleted_count = await clean_old_logs(days)
        await message.answer(f"Очистка логов завершена. Удалено записей: {deleted_count}")
    except Exception as e:
        await message.answer(f"Ошибка при очистке логов: {str(e)}")
