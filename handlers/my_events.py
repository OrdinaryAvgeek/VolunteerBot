# handlers/my_events.py
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import async_session_maker
from services import VolunteerService, ParticipationService


async def my_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мои мероприятия — список записей пользователя"""
    user = update.effective_user

    async with async_session_maker() as session:
        volunteer = await VolunteerService.get_by_telegram_id(session, user.id)

        if not volunteer:
            await update.message.reply_text("Вы не зарегистрированы. Используйте /register")
            return

        events = await ParticipationService.get_user_events(session, volunteer.id)

    if not events:
        await update.message.reply_text(
            "Вы пока не записаны ни на одно мероприятие.\n"
            "Используйте /events для просмотра доступных."
        )
        return

    text = "*Ваши мероприятия:*\n\n"
    for i, event in enumerate(events, 1):
        date_str = event.date_time.strftime("%d.%m.%Y %H:%M")
        status = "" if event.date_time < datetime.now() else ""
        text += f"{status} {i}. *{event.title}*\n"
        text += f"   {event.location}\n"
        text += f"   {date_str}\n"
        text += f"   ID: `{event.id}`\n\n"

    text += "Для отмены записи: /cancel_event <ID>"
    await update.message.reply_text(text)