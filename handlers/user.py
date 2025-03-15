import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from sqlalchemy import select

from database.db import get_db
from database.models import Event, User
from keyboards.all_kb import main_kb, catalog_kb
from services.db_operations import get_user_by_id, add_user_to_db

router = Router()

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    async for db in get_db():
        user = await get_user_by_id(db, user_id)
        if not user:
            user = await add_user_to_db(db, user_id, username, full_name)
            response = f"Привет, {full_name}! Ты зарегистрирован!"
        else:
            response = f"Добро пожаловать, {full_name}!"

        await message.answer(
            response,
            reply_markup=main_kb(message.from_user.id)
        )


@router.message(Command("schedule"))
async def send_schedule_link(message: Message):
    schedule_link = "https://docs.google.com/spreadsheets/d/1SRjuZqP3x1WuEytURp3_-2glduMnRepcRNXF0t5fzZg/edit?gid=0#gid=0"
    await message.answer(
        "📅 Расписание уроков доступно по ссылке:\n"
        f"{schedule_link}"
    )


@router.message(F.text == "📅 Расписание")
async def send_schedule_link_text(message: Message):
    schedule_link = "https://docs.google.com/spreadsheets/d/1SRjuZqP3x1WuEytURp3_-2glduMnRepcRNXF0t5fzZg/edit?gid=0#gid=0"
    await message.answer(
        "📅 Расписание уроков доступно по ссылке:\n"
        f"{schedule_link}"
    )


@router.message(F.text == "О наc")
async def about_us(message: Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сайт ЗабГУ", url="https://zabgu.ru/php/index.php")],
            [InlineKeyboardButton(text="Сообщество ВКонтакте", url="https://vk.com/dear_lyceum")],
            [InlineKeyboardButton(text="Группа в Telegram", url="https://t.me/lyceum_zabgu")],
        ]
    )
    await message.answer("Полезные ссылки:", reply_markup=inline_kb)


@router.message(Command("events"))
async def show_events(message: Message):
    async for db in get_db():
        events = await db.execute(select(Event).where(Event.date >= datetime.now()).order_by(Event.date))
        events = events.scalars().all()

        if not events:
            await message.answer("Предстоящих событий нет.")
            return

        response = "Предстоящие события:\n"
        for event in events:
            response += (
                f"📅 {event.title}\n"
                f"📝 {event.description}\n"
                f"⏰ {event.date.strftime('%Y-%m-%d %H:%M')}\n\n"
            )
        await message.answer(response)


@router.message(F.text == "Каталог")
async def show_catalog(message: Message):
    # Отправляем новую клавиатуру каталога
    await message.answer("Выберите опцию каталога:", reply_markup=catalog_kb())


@router.message(F.text == "Учителя")
async def teachers_list(message: Message):
    async for db in get_db():
        result = await db.execute(select(User).where(User.role == "учитель"))
        teachers = result.scalars().all()

        if not teachers:
            await message.answer("Список учителей пуст.")
            return

        response = "<b>Список учителей:</b>\n"
        for teacher in teachers:
            response += (
                f"\n<b>{teacher.full_name}</b>\n"
                f"Контактная информация: {teacher.contact_info}\n"
            )
        await message.answer(response, parse_mode="HTML")


@router.message(F.text == "Главное меню")
async def return_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_kb(message.from_user.id))
