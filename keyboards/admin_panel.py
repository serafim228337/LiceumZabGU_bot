from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ChatType

def admin_panel(chat_type: ChatType = None):
    # Не показываем админ-панель в группах
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return None

    admin_kb_list = [
        [KeyboardButton(text="Добавить группу"), KeyboardButton(text="Список групп")],
        [KeyboardButton(text="Разослать сообщение"), KeyboardButton(text="Добавить событие")],
        [KeyboardButton(text="Разослать уведомление о предстоящем событии"), KeyboardButton(text="Просмотр логов")],
        [KeyboardButton(text="Очистить логи"), KeyboardButton(text="На главную")]
    ]
    admin_kb = ReplyKeyboardMarkup(
        keyboard=admin_kb_list,
        one_time_keyboard=True,
        resize_keyboard=True,
        is_persistent=True
    )
    return admin_kb

