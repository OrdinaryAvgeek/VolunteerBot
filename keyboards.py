# keyboards.py
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import SPHERES


def main_menu(role: str = "volunteer"):
    buttons = [
        ["Мероприятия", "Мои мероприятия"],
        ["Профиль"]
    ]
    if role in ["organizer", "admin"]:
        buttons.insert(1, ["Создать мероприятие"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def contact_request_keyboard():
    button = KeyboardButton("Отправить номер", request_contact=True)
    return ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)


def preferences_keyboard():
    keyboard = [[InlineKeyboardButton(s, callback_data=f"pref_{s}")] for s in SPHERES]
    keyboard.append([InlineKeyboardButton("Готово", callback_data="pref_done")])
    return InlineKeyboardMarkup(keyboard)


def event_detail_keyboard(event_id: int, is_registered: bool = False):
    keyboard = [[InlineKeyboardButton("Подробнее", callback_data=f"details_{event_id}")]]
    if not is_registered:
        keyboard[0].insert(0, InlineKeyboardButton("Записаться", callback_data=f"join_{event_id}"))
    else:
        keyboard.append([InlineKeyboardButton("Отменить запись", callback_data=f"cancel_join_{event_id}")])
    return InlineKeyboardMarkup(keyboard)