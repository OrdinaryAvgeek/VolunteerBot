# handlers/common.py
from telegram import Update
from telegram.ext import ContextTypes
from database import async_session_maker
from services import VolunteerService
from keyboards import main_menu
from utils import format_preferences


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    async with async_session_maker() as session:
        volunteer = await VolunteerService.get_by_telegram_id(session, user.id)

    if volunteer:
        role = volunteer.role
        text = f"С возвращением, {volunteer.full_name}!"
    else:
        role = "volunteer"
        text = f"Здравствуйте, {user.first_name}!\n\nДля начала работы используйте /register"

    await update.message.reply_text(
        text,
        reply_markup=main_menu(role)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*Доступные команды:*\n\n"
        "/start — Начало работы\n"
        "/help — Эта справка\n"
        "/register — Регистрация\n"
        "/profile — Мой профиль\n"
        "/events — Список мероприятий\n"
        "/view <ID> — Подробнее о мероприятии\n"
        "/cancel_event <ID> — Отменить запись на мероприятие\n"
        "/create_event — Создать мероприятие (организатор)\n"
        "/my_events — Мои мероприятия\n"
        "/checkin <ID> — Отметка о прибытии\n"
        "/checkout <ID> — Отметка об уходе\n\n"
        "/report <ID> — Сформировать отчёт по мероприятию (CSV)\n"
        "*Кнопки меню:*\n"
        "• Мероприятия\n"
        "• Мои мероприятия\n"
        "• Профиль\n"
        "• Создать мероприятие (организатор)\n\n"
        "Для отмены действия — /cancel"
    )
    await update.message.reply_text(help_text)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with async_session_maker() as session:
        volunteer = await VolunteerService.get_by_telegram_id(session, user.id)

    if not volunteer:
        await update.message.reply_text("Вы не зарегистрированы. Используйте /register")
        return

    status_text = {
        "pending": "На подтверждении",
        "active": "Активен",
        "blocked": "Заблокирован"
    }.get(volunteer.status, volunteer.status)

    role_text = {
        "volunteer": "Волонтёр",
        "organizer": "Организатор",
        "admin": "Администратор"
    }.get(volunteer.role, volunteer.role)

    await update.message.reply_text(
        f"*Ваш профиль*\n\n"
        f"Имя: {volunteer.full_name}\n"
        f"Телефон: {volunteer.phone or '—'}\n"
        f"Роль: {role_text}\n"
        f"Статус: {status_text}\n"
        f"Сферы: {format_preferences(volunteer.preferences)}",
        parse_mode="Markdown",
        reply_markup=main_menu(volunteer.role)
    )


async def menu_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.events import events_list
    await events_list(update, context)


async def menu_my_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.my_events import my_events
    await my_events(update, context)


async def menu_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await profile(update, context)


async def menu_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.organizer import create_event_start

    user = update.effective_user
    async with async_session_maker() as session:
        is_org = await VolunteerService.is_organizer(session, user.id)

    if not is_org:
        await update.message.reply_text("Только для организаторов.")
        return

    await create_event_start(update, context)