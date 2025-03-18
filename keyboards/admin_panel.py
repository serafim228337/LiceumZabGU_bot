from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_panel():
    admin_kb_list = [
        [KeyboardButton(text="Добавить группу"), KeyboardButton(text="Список групп")],
        [KeyboardButton(text="Разослать сообщение"), KeyboardButton(text="Добавить событие")],
        [KeyboardButton(text="Разослать уведомление о предстоящем событии"), KeyboardButton(text="На главную")]
    ]
    admin_kb = ReplyKeyboardMarkup(
        keyboard=admin_kb_list,
        one_time_keyboard=True,
        resize_keyboard=True,
        is_persistent=True
    )
    return admin_kb

