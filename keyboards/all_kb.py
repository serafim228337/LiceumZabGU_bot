from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from filters.is_admin import admins
def main_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="О наc"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text=""), KeyboardButton(text="Каталог")],
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