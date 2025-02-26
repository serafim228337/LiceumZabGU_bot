from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import get_db
from keyboards.all_kb import main_kb
from services.db_operations import get_user_by_id, update_user_profile

# Создаем роутер
router = Router()

# Создаем состояния для ожидания данных профиля
class UserProfileState(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_class = State()
    waiting_for_class_letter = State()
    waiting_for_phone_number = State()

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message, state: FSMContext):
    async for db in get_db():
        user = await get_user_by_id(db, message.from_user.id)
        if user:
            profile_text = (
                f"ФИО: {user.full_name}\n"
                f"Класс: {user.class_number}\n"
                f"Буква класса: {user.class_letter}\n"
                f"Номер телефона: {user.phone_number}\n"
            )
        else:
            profile_text = "Данные профиля отсутствуют."

        update_button = InlineKeyboardButton(text="Обновить данные профиля", callback_data="update_profile")
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[[update_button]])

        await message.answer(profile_text, reply_markup=inline_kb)

@router.callback_query(F.data == "update_profile")
async def update_profile_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите ваше ФИО:")
    await state.set_state(UserProfileState.waiting_for_full_name)
    await callback_query.answer()

@router.message(UserProfileState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Введите ваш класс (например, 10):")
    await state.set_state(UserProfileState.waiting_for_class)

@router.message(UserProfileState.waiting_for_class)
async def process_class(message: Message, state: FSMContext):
    await state.update_data(class_number=message.text)
    await message.answer("Введите букву вашего класса (например, А):")
    await state.set_state(UserProfileState.waiting_for_class_letter)

@router.message(UserProfileState.waiting_for_class_letter)
async def process_class_letter(message: Message, state: FSMContext):
    await state.update_data(class_letter=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(UserProfileState.waiting_for_phone_number)

@router.message(UserProfileState.waiting_for_phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text)

    # Получаем все данные из состояния
    user_data = await state.get_data()
    full_name = user_data['full_name']
    class_number = user_data['class_number']
    class_letter = user_data['class_letter']
    phone_number = user_data['phone_number']

    # Сохраняем данные в базу данных
    async for db in get_db():
        await update_user_profile(db, message.from_user.id, full_name, class_number, class_letter, phone_number)

    await message.answer("Ваш профиль успешно обновлен!", reply_markup=main_kb(message.from_user.id))
    await state.clear()
