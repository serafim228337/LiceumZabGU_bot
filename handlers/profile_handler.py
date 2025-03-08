from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import get_db
from keyboards.all_kb import main_kb
from services.db_operations import get_user_by_id, update_user_profile

# Создаем роутер
router = Router()

# Создаем состояния для ожидания данных профиля
class UserProfileState(StatesGroup):
    waiting_for_role = State()  # Новый шаг для роли
    waiting_for_full_name = State()
    waiting_for_class = State()
    waiting_for_class_letter = State()
    waiting_for_phone_number = State()
    waiting_for_subjects = State()  # Новый шаг для предметов учителя


@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message, state: FSMContext):
    async for db in get_db():
        user = await get_user_by_id(db, message.from_user.id)
        if user:
            role = user.role.capitalize() if user.role else "Не указана"  # Проверка роли
            class_number = user.class_number if user.role == 'ученик' else 'N/A'
            class_letter = user.class_letter if user.role == 'ученик' else 'N/A'
            phone_number = user.phone_number if user.phone_number else 'Не указан'

            profile_text = (
                f"ФИО: {user.full_name}\n"
                f"Класс: {class_number}\n"
                f"Буква класса: {class_letter}\n"
                f"Номер телефона: {phone_number}\n"
                f"Роль: {role}\n"
            )
        else:
            profile_text = "Данные профиля отсутствуют."

        # Создаем кнопку на клавиатуре
        update_button = KeyboardButton(text="Обновить данные профиля")
        reply_kb = ReplyKeyboardMarkup(keyboard=[[update_button]], resize_keyboard=True)

        await message.answer(profile_text, reply_markup=reply_kb)

@router.message(F.text == "Обновить данные профиля")
async def update_profile_callback(message: Message, state: FSMContext):
    # Запрашиваем роль пользователя
    role_button_1 = KeyboardButton(text="Учитель")
    role_button_2 = KeyboardButton(text="Ученик")
    role_button_3 = KeyboardButton(text="Родитель")
    role_kb = ReplyKeyboardMarkup(keyboard=[[role_button_1], [role_button_2], [role_button_3]], resize_keyboard=True)

    await message.answer("Выберите вашу роль (Учитель, Ученик, Родитель):", reply_markup=role_kb)
    await state.set_state(UserProfileState.waiting_for_role)

@router.message(UserProfileState.waiting_for_role)
async def process_role(message: Message, state: FSMContext):
    role = message.text.lower()

    if role == "ученик":
        await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())  # Скрываем клавиатуру
        await state.set_state(UserProfileState.waiting_for_full_name)
    elif role == "родитель":
        # Запрашиваем номер телефона с кнопкой пропуска
        skip_button = KeyboardButton(text="Пропустить")
        phone_kb = ReplyKeyboardMarkup(keyboard=[[skip_button]], resize_keyboard=True)
        await message.answer("Введите ваш номер телефона (можно пропустить):", reply_markup=phone_kb)
        await state.set_state(UserProfileState.waiting_for_phone_number)
    elif role == "учитель":
        await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())  # Скрываем клавиатуру
        await state.set_state(UserProfileState.waiting_for_full_name)

    # Сохраняем роль в состоянии
    await state.update_data(role=role)

@router.message(UserProfileState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)

    # Если роль учителя, пропускаем шаги с классом и буквой
    user_data = await state.get_data()
    role = user_data['role']
    if role == "учитель":
        await message.answer("Введите ваши предметы через запятую:", reply_markup=ReplyKeyboardRemove())  # Скрываем клавиатуру
        await state.set_state(UserProfileState.waiting_for_subjects)
    else:
        # Создаем клавиатуру для выбора класса для ученика
        class_buttons = [
            [KeyboardButton(text="8"), KeyboardButton(text="9")],
            [KeyboardButton(text="10"), KeyboardButton(text="11")]
        ]
        class_kb = ReplyKeyboardMarkup(keyboard=class_buttons, resize_keyboard=True)
        await message.answer("Выберите ваш класс:", reply_markup=class_kb)
        await state.set_state(UserProfileState.waiting_for_class)

@router.message(UserProfileState.waiting_for_class)
async def process_class(message: Message, state: FSMContext):
    # Обрабатываем выбор класса
    await state.update_data(class_number=message.text)

    # Создаем клавиатуру для выбора буквы класса
    class_letter_buttons = [
        [KeyboardButton(text="А"), KeyboardButton(text="Б")],
        [KeyboardButton(text="В"), KeyboardButton(text="Г")]
    ]
    class_letter_kb = ReplyKeyboardMarkup(keyboard=class_letter_buttons, resize_keyboard=True)
    await message.answer("Выберите букву вашего класса:", reply_markup=class_letter_kb)
    await state.set_state(UserProfileState.waiting_for_class_letter)

@router.message(UserProfileState.waiting_for_class_letter)
async def process_class_letter(message: Message, state: FSMContext):
    # Обрабатываем выбор буквы класса
    await state.update_data(class_letter=message.text)

    # Запрашиваем номер телефона с кнопкой пропуска
    skip_button = KeyboardButton(text="Пропустить")
    phone_kb = ReplyKeyboardMarkup(keyboard=[[skip_button]], resize_keyboard=True)
    await message.answer("Введите ваш номер телефона (можно пропустить):", reply_markup=phone_kb)
    await state.set_state(UserProfileState.waiting_for_phone_number)

@router.message(UserProfileState.waiting_for_phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    phone_number = message.text.strip() if message.text and message.text != "Пропустить" else None  # Если "Пропустить", оставляем номер как None

    await state.update_data(phone_number=phone_number)

    # Переходим к следующему шагу
    user_data = await state.get_data()
    role = user_data['role']

    if role == "учитель":
        await message.answer("Введите ваши предметы через запятую:")
        await state.set_state(UserProfileState.waiting_for_subjects)
    else:
        await save_user_profile(message, state)

@router.message(UserProfileState.waiting_for_subjects)
async def process_subjects(message: Message, state: FSMContext):
    await state.update_data(subjects=message.text)
    await save_user_profile(message, state)

async def save_user_profile(message: Message, state: FSMContext):
    # Получаем все данные из состояния
    user_data = await state.get_data()
    role = user_data['role']
    full_name = user_data.get('full_name')
    class_number = user_data.get('class_number')
    class_letter = user_data.get('class_letter')
    phone_number = user_data.get('phone_number')
    subjects = user_data.get('subjects')

    # Сохраняем данные в базу данных
    async for db in get_db():
        print(db, message.from_user.id, full_name, class_number, class_letter, phone_number, role, subjects)
        await update_user_profile(db, message.from_user.id, full_name, class_number, class_letter, phone_number, role, subjects)

    await message.answer("Ваш профиль успешно обновлен!", reply_markup=main_kb(message.from_user.id))
    await state.clear()
