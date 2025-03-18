from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from filters.is_admin import admins


def main_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="О наc"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="Каталог")],
        [KeyboardButton(text="📅 Расписание")]
    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️ Админ панель")])
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    return keyboard


def catalog_kb():
    kb_list = [
        [KeyboardButton(text="Учителя")],
        [KeyboardButton(text="Предстоящие события")],
        [KeyboardButton(text="Главное меню")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите опцию каталога:"
    )
    return keyboard


def skip_kb(*buttons) -> ReplyKeyboardMarkup:
    skip_button = KeyboardButton(text="Пропустить")
    cancel_button = KeyboardButton(text="/cancel")

    keyboard = [[skip_button], [cancel_button]]


    if buttons:
        keyboard = [[KeyboardButton(text=btn)] for btn in buttons] + keyboard

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)