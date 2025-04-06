import logging

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from database.db import get_db
from database.models import User
from keyboards.all_kb import main_kb, skip_kb
from services.db_operations import get_user_by_id

router = Router()
logger = logging.getLogger(__name__)
router.message.filter(F.chat.type == ChatType.PRIVATE)


class UserProfileState(StatesGroup):
    waiting_for_role = State()
    waiting_for_full_name = State()
    waiting_for_class = State()
    waiting_for_class_letter = State()
    waiting_for_subjects = State()
    waiting_for_contact_info = State()


async def clear_user_subjects(db, user_id: int):
    """Очищает список предметов у пользователя"""
    user = await get_user_by_id(db, user_id)
    if user:
        user.subjects = None
        await db.commit()
        await db.refresh(user)
    return user


@router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Заполнение профиля отменено.", reply_markup=main_kb(message.from_user.id))


@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message, state: FSMContext):
    await state.clear()
    async for db in get_db():
        user = await get_user_by_id(db, message.from_user.id)
        if not user:
            await message.answer("Данные профиля отсутствуют.")
            return

        profile_fields = []

        if user.full_name:
            profile_fields.append(f"ФИО: {user.full_name}")

        if user.role:
            role_display = {
                'ученик': '👨‍🎓 Ученик',
                'учитель': '👩‍🏫 Учитель',
                'родитель': '👪 Родитель'
            }.get(user.role.lower(), user.role.capitalize())
            profile_fields.append(f"Роль: {role_display}")

        if user.role == 'ученик':
            class_info = []
            if user.class_number:
                class_info.append(user.class_number)
            if user.class_letter:
                class_info.append(user.class_letter)
            if class_info:
                profile_fields.append(f"Класс: {' '.join(class_info)}")

        if user.contact_info:
            profile_fields.append(f"Контакты: {user.contact_info}")

        if user.role == 'учитель' and user.subjects:
            profile_fields.append(f"Предметы: {user.subjects}")

        profile_text = "📌 Ваш профиль:\n\n" + "\n".join(profile_fields) if profile_fields else "Ваш профиль пуст."

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
    await state.clear()
    role_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Учитель")],
            [KeyboardButton(text="Ученик")],
            [KeyboardButton(text="Родитель")],
            [KeyboardButton(text="/cancel")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите вашу роль:", reply_markup=role_kb)
    await state.set_state(UserProfileState.waiting_for_role)


@router.message(UserProfileState.waiting_for_role)
async def process_role(message: Message, state: FSMContext):
    role = message.text.lower()
    if role not in ["учитель", "ученик", "родитель"]:
        await message.answer("Пожалуйста, выберите одну из предложенных ролей.")
        return

    # Очищаем предметы при смене с учителя на другую роль
    current_data = await state.get_data()
    if current_data.get('role') == 'учитель' and role != 'учитель':
        async for db in get_db():
            await clear_user_subjects(db, message.from_user.id)

    await state.update_data(role=role)

    if role == "ученик":
        await message.answer("Введите ваше ФИО или нажмите 'Пропустить':",
                             reply_markup=skip_kb())
        await state.set_state(UserProfileState.waiting_for_full_name)
    elif role == "родитель":
        await message.answer("Введите ваши контактные данные:",
                             reply_markup=skip_kb())
        await state.set_state(UserProfileState.waiting_for_contact_info)
    elif role == "учитель":
        await message.answer("Введите ваше ФИО или нажмите 'Пропустить':",
                             reply_markup=skip_kb())
        await state.set_state(UserProfileState.waiting_for_full_name)


@router.message(F.text == "Назад", UserProfileState.waiting_for_full_name)
@router.message(F.text == "Назад", UserProfileState.waiting_for_contact_info)
async def back_to_role_selection(message: Message, state: FSMContext):
    # Очищаем предметы, если были в режиме учителя
    data = await state.get_data()
    if data.get('role') == 'учитель':
        async for db in get_db():
            await clear_user_subjects(db, message.from_user.id)

    # Возвращаем к выбору роли
    role_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Учитель")],
            [KeyboardButton(text="Ученик")],
            [KeyboardButton(text="Родитель")],
            [KeyboardButton(text="/cancel")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите вашу роль:", reply_markup=role_kb)
    await state.set_state(UserProfileState.waiting_for_role)


@router.message(UserProfileState.waiting_for_full_name, F.text == "Пропустить")
async def skip_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=None)
    user_data = await state.get_data()
    role = user_data['role']

    if role == "учитель":
        await message.answer("Введите ваши контактные данные:",
                             reply_markup=skip_kb())
        await state.set_state(UserProfileState.waiting_for_contact_info)
    else:
        await message.answer("Выберите ваш класс:",
                             reply_markup=skip_kb("8", "9", "10", "11"))
        await state.set_state(UserProfileState.waiting_for_class)


@router.message(UserProfileState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    user_data = await state.get_data()
    role = user_data['role']

    if role == "учитель":
        await message.answer("Введите ваши контактные данные:",
                             reply_markup=skip_kb())
        await state.set_state(UserProfileState.waiting_for_contact_info)
    else:
        await message.answer("Выберите ваш класс:",
                             reply_markup=skip_kb("8", "9", "10", "11"))
        await state.set_state(UserProfileState.waiting_for_class)


@router.message(UserProfileState.waiting_for_class, F.text == "Пропустить")
async def skip_class(message: Message, state: FSMContext):
    await state.update_data(class_number=None)
    await message.answer("Выберите букву класса:",
                         reply_markup=skip_kb("А", "Б", "В", "Г"))
    await state.set_state(UserProfileState.waiting_for_class_letter)


@router.message(UserProfileState.waiting_for_class)
async def process_class(message: Message, state: FSMContext):
    if message.text not in ["8", "9", "10", "11"]:
        await message.answer("Пожалуйста, выберите корректный класс.")
        return

    await state.update_data(class_number=message.text)
    await message.answer("Выберите букву класса:",
                         reply_markup=skip_kb("А", "Б", "В", "Г"))
    await state.set_state(UserProfileState.waiting_for_class_letter)


@router.message(UserProfileState.waiting_for_class_letter, F.text == "Пропустить")
async def skip_class_letter(message: Message, state: FSMContext):
    await state.update_data(class_letter=None)
    await message.answer("Введите ваши контактные данные:",
                         reply_markup=skip_kb())
    await state.set_state(UserProfileState.waiting_for_contact_info)


@router.message(UserProfileState.waiting_for_class_letter)
async def process_class_letter(message: Message, state: FSMContext):
    if message.text not in ["А", "Б", "В", "Г"]:
        await message.answer("Пожалуйста, выберите корректную букву класса.")
        return

    await state.update_data(class_letter=message.text)
    await message.answer("Введите ваши контактные данные:",
                         reply_markup=skip_kb())
    await state.set_state(UserProfileState.waiting_for_contact_info)


@router.message(UserProfileState.waiting_for_contact_info)
async def process_contact_info(message: Message, state: FSMContext):
    contact_info = message.text if message.text != "Пропустить" else None
    await state.update_data(contact_info=contact_info)

    user_data = await state.get_data()
    if user_data['role'] == 'учитель':
        await message.answer("Введите ваши предметы через запятую:",
                             reply_markup=skip_kb())
        await state.set_state(UserProfileState.waiting_for_subjects)
    else:
        await save_user_profile(message, state)


@router.message(UserProfileState.waiting_for_subjects, F.text == "Пропустить")
async def skip_subjects(message: Message, state: FSMContext):
    await state.update_data(subjects=None)
    await save_user_profile(message, state)


@router.message(UserProfileState.waiting_for_subjects)
async def process_subjects(message: Message, state: FSMContext):
    await state.update_data(subjects=message.text)
    await save_user_profile(message, state)


async def save_user_profile(message: Message, state: FSMContext):
    user_data = await state.get_data()

    # Очищаем предметы, если роль не учитель
    if user_data.get('role') != 'учитель':
        user_data['subjects'] = None

    async for db in get_db():
        current_user = await get_user_by_id(db, message.from_user.id)

        update_data = {
            'full_name': user_data.get('full_name', current_user.full_name if current_user else None),
            'class_number': user_data.get('class_number'),
            'class_letter': user_data.get('class_letter'),
            'contact_info': user_data.get('contact_info'),
            'role': user_data['role'],
            'subjects': user_data.get('subjects')
        }

        if current_user:
            # Обновляем существующего пользователя
            for key, value in update_data.items():
                setattr(current_user, key, value)
        else:
            # Создаем нового пользователя
            current_user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                **update_data
            )
            db.add(current_user)

        await db.commit()
        await db.refresh(current_user)

    await message.answer("✅ Профиль успешно обновлен!", reply_markup=main_kb(message.from_user.id))
    await state.clear()
