from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from database.db import get_db
from keyboards.all_kb import main_kb
from keyboards.all_kb import skip_keyboard
from services.db_operations import get_user_by_id, update_user_profile

# Создаем роутер
router = Router()


# Создаем состояния для ожидания данных профиля
class UserProfileState(StatesGroup):
    waiting_for_role = State()  # Новый шаг для роли
    waiting_for_full_name = State()
    waiting_for_class = State()
    waiting_for_class_letter = State()
    waiting_for_subjects = State()
    waiting_for_contact_info = State()


# Функция обработки команды /cancel
@router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Заполнение профиля отменено.", reply_markup=main_kb(message.from_user.id))


@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message, state: FSMContext):
    async for db in get_db():
        user = await get_user_by_id(db, message.from_user.id)
        if user:
            role = user.role.capitalize() if user.role else "Не указана"  # Проверка роли
            class_number = user.class_number if user.role == 'ученик' else 'N/A'
            class_letter = user.class_letter if user.role == 'ученик' else 'N/A'
            contact_info = user.contact_info if user.contact_info else 'Не указан'

            profile_text = (
                f"ФИО: {user.full_name}\n"
                f"Класс: {class_number}\n"
                f"Буква класса: {class_letter}\n"
                f"Контактные данные: {contact_info}\n"
                f"Роль: {role}\n"
            )
        else:
            profile_text = "Данные профиля отсутствуют."

        # Создаем кнопку на клавиатуре
        update_button = KeyboardButton(text="Обновить данные профиля")
        main_menu_button = KeyboardButton(text="Главное меню")
        reply_kb = ReplyKeyboardMarkup(
            keyboard=[[update_button, main_menu_button]],
            resize_keyboard=True
        )
        await message.answer(profile_text, reply_markup=reply_kb)


@router.message(F.text == "Главное меню")
async def return_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_kb(message.from_user.id))


@router.message(F.text == "Обновить данные профиля")
async def update_profile_callback(message: Message, state: FSMContext):
    # Запрашиваем роль пользователя
    role_button_1 = KeyboardButton(text="Учитель")
    role_button_2 = KeyboardButton(text="Ученик")
    role_button_3 = KeyboardButton(text="Родитель")
    cancel_button = KeyboardButton(text="/cancel")
    role_kb = ReplyKeyboardMarkup(keyboard=[[role_button_1], [role_button_2], [role_button_3], [cancel_button]],
                                  resize_keyboard=True)
    await message.answer("Выберите вашу роль (Учитель, Ученик, Родитель):", reply_markup=role_kb)
    await state.set_state(UserProfileState.waiting_for_role)


@router.message(UserProfileState.waiting_for_role)
async def process_role(message: Message, state: FSMContext):
    role = message.text.lower()
    await state.update_data(role=role)
    if role == "ученик":
        await message.answer("Введите ваше ФИО или нажмите 'Пропустить' для сохранения текущего значения:",
                             reply_markup=skip_keyboard())
        await state.set_state(UserProfileState.waiting_for_full_name)
    elif role == "родитель":
        # Запрашиваем контактные данные с возможностью пропуска
        await message.answer(
            "Введите ваши контактные данные. Это может быть:\n"
            "- Номер телефона\n"
            "- Telegram-аккаунт\n"
            "- Ссылка на ВКонтакте\n"
            "- Адрес электронной почты\n"
            "Или нажмите 'Пропустить', если данные не меняются.",
            reply_markup=skip_keyboard()
        )
        await state.set_state(UserProfileState.waiting_for_contact_info)
    elif role == "учитель":
        await message.answer("Введите ваше ФИО или нажмите 'Пропустить' для сохранения текущего значения:",
                             reply_markup=skip_keyboard())
        await state.set_state(UserProfileState.waiting_for_full_name)


# --- Обработка ФИО ---
@router.message(UserProfileState.waiting_for_full_name, F.text == "Пропустить")
async def skip_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=None)
    user_data = await state.get_data()
    role = user_data['role']
    if role == "учитель":
        await message.answer("Введите ваши предметы через запятую", reply_markup=skip_keyboard())
        await state.set_state(UserProfileState.waiting_for_subjects)
    else:
        # Для ученика переходим к выбору класса
        class_buttons = [
            [KeyboardButton(text="8"), KeyboardButton(text="9")],
            [KeyboardButton(text="10"), KeyboardButton(text="11")]
        ]
        class_kb = ReplyKeyboardMarkup(keyboard=class_buttons + skip_keyboard(),
                                       resize_keyboard=True)
        await message.answer("Выберите ваш класс или нажмите 'Пропустить':", reply_markup=class_kb)
        await state.set_state(UserProfileState.waiting_for_class)


@router.message(UserProfileState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    user_data = await state.get_data()
    role = user_data['role']
    if role == "учитель":
        await message.answer("Введите ваши предметы через запятую", reply_markup=skip_keyboard())
        await state.set_state(UserProfileState.waiting_for_subjects)
    else:
        class_buttons = [
            [KeyboardButton(text="8"), KeyboardButton(text="9")],
            [KeyboardButton(text="10"), KeyboardButton(text="11")]
        ]
        class_kb = ReplyKeyboardMarkup(keyboard=class_buttons + skip_keyboard(),
                                       resize_keyboard=True)
        await message.answer("Выберите ваш класс или нажмите 'Пропустить':", reply_markup=class_kb)
        await state.set_state(UserProfileState.waiting_for_class)


# --- Обработка выбора класса ---
@router.message(UserProfileState.waiting_for_class, F.text == "Пропустить")
async def skip_class(message: Message, state: FSMContext):
    await state.update_data(class_number=None)
    class_letter_buttons = [
        [KeyboardButton(text="А"), KeyboardButton(text="Б")],
        [KeyboardButton(text="В"), KeyboardButton(text="Г")]
    ]
    class_letter_kb = ReplyKeyboardMarkup(
        keyboard=class_letter_buttons + skip_keyboard(), resize_keyboard=True)
    await message.answer("Выберите букву вашего класса", reply_markup=class_letter_kb)
    await state.set_state(UserProfileState.waiting_for_class_letter)


@router.message(UserProfileState.waiting_for_class)
async def process_class(message: Message, state: FSMContext):
    await state.update_data(class_number=message.text)
    class_letter_buttons = [
        [KeyboardButton(text="А"), KeyboardButton(text="Б")],
        [KeyboardButton(text="В"), KeyboardButton(text="Г")]
    ]

    class_letter_kb = ReplyKeyboardMarkup(
        keyboard=class_letter_buttons + skip_keyboard(), resize_keyboard=True)
    await message.answer("Выберите букву вашего класса", reply_markup=class_letter_kb)
    await state.set_state(UserProfileState.waiting_for_class_letter)


# --- Обработка выбора буквы класса ---
@router.message(UserProfileState.waiting_for_class_letter, F.text == "Пропустить")
async def skip_class_letter(message: Message, state: FSMContext):
    await state.update_data(class_letter=None)
    await message.answer(
        "Введите ваши контактные данные. Это может быть:\n"
        "- Номер телефона\n"
        "- Telegram-аккаунт\n"
        "- Ссылка на ВКонтакте\n"
        "- Адрес электронной почты\n"
        "Или нажмите 'Пропустить':",
        reply_markup=skip_keyboard()
    )
    await state.set_state(UserProfileState.waiting_for_contact_info)


@router.message(UserProfileState.waiting_for_class_letter)
async def process_class_letter(message: Message, state: FSMContext):
    await state.update_data(class_letter=message.text)
    await message.answer(
        "Введите ваши контактные данные. Это может быть:\n"
        "- Номер телефона\n"
        "- Telegram-аккаунт\n"
        "- Ссылка на ВКонтакте\n"
        "- Адрес электронной почты\n"
        "Или нажмите 'Пропустить':",
        reply_markup=skip_keyboard()
    )
    await state.set_state(UserProfileState.waiting_for_contact_info)


# --- Обработка контактной информации ---
@router.message(UserProfileState.waiting_for_contact_info)
async def process_contact_info(message: Message, state: FSMContext):
    contact_info = message.text.strip() if message.text and message.text != "Пропустить" else None
    await state.update_data(contact_info=contact_info)
    user_data = await state.get_data()
    role = user_data['role']
    if role == "учитель":
        await message.answer("Введите ваши предметы через запятую", reply_markup=skip_keyboard())
        await state.set_state(UserProfileState.waiting_for_subjects)
    else:
        await save_user_profile(message, state)


# --- Обработка предметов ---
@router.message(UserProfileState.waiting_for_subjects, F.text == "Пропустить")
async def skip_subjects(message: Message, state: FSMContext):
    await state.update_data(subjects=None)
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
    contact_info = user_data.get('contact_info')
    subjects = user_data.get('subjects')

    async for db in get_db():
        # Получаем текущие данные пользователя из базы
        current_user = await get_user_by_id(db, message.from_user.id)
        # Если пользователь пропустил ввод, сохраняем текущее значение
        if full_name is None:
            full_name = current_user.full_name
        if class_number is None:
            class_number = current_user.class_number
        if class_letter is None:
            class_letter = current_user.class_letter
        if contact_info is None:
            contact_info = current_user.contact_info
        if subjects is None and hasattr(current_user, "subjects"):
            subjects = current_user.subjects

        await update_user_profile(db, message.from_user.id, full_name, class_number, class_letter, contact_info, role,
                                  subjects)

    await message.answer("Ваш профиль успешно обновлен!", reply_markup=main_kb(message.from_user.id))
    await state.clear()
