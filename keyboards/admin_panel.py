from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_panel():
    admin_kb_list = [
        [KeyboardButton(text="/add_group"), KeyboardButton(text="/list_groups")],
        [KeyboardButton(text="/send_message"), KeyboardButton(text="/add_event")],
        [KeyboardButton(text="На главную")]
    ]
    admin_kb = ReplyKeyboardMarkup(
        keyboard=admin_kb_list,
        one_time_keyboard=True,
        resize_keyboard=True,
        is_persistent=True
    )
    return admin_kb
