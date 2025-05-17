from aiogram.enums import ChatType
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from filters.is_admin import admins


def should_disable_keyboard(chat_type: ChatType, command: str = None) -> bool:
    """Определяет, нужно ли отключать клавиатуру"""
    allowed_commands = ['/events', '/schedule']
    if command in allowed_commands:
        return False
    return chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]


def main_kb(user_telegram_id: int, chat_type: ChatType = None):
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return ReplyKeyboardRemove()

    kb_list = [
        [KeyboardButton(text="О наc"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="Каталог")],
        [KeyboardButton(text="📅 Расписание")]
    ]

    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️ Админ панель")])

    return ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )


def catalog_kb():
    kb_list = [
        [KeyboardButton(text="Учителя")],
        [KeyboardButton(text="Погода в Чите")],
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
