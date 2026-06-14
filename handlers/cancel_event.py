# handlers/cancel_event.py
from telegram import Update
from telegram.ext import ContextTypes
from database import async_session_maker
from services import VolunteerService, EventService, ParticipationService


async def cancel_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена записи на мероприятие: /cancel_event <ID>"""
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text(
            "Укажите ID мероприятия.\n"
            "Пример: /cancel_event 5\n\n"
            "Узнать ID можно через /my_events"
        )
        return

    try:
        event_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return

    async with async_session_maker() as session:
        volunteer = await VolunteerService.get_by_telegram_id(session, user.id)

        if not volunteer:
            await update.message.reply_text("Вы не зарегистрированы.")
            return

        event = await EventService.get_by_id(session, event_id)
        if not event:
            await update.message.reply_text(f"Мероприятие с ID {event_id} не найдено.")
            return

        # Проверяем, записан ли пользователь
        participation = await ParticipationService.get_active_participation(
            session, volunteer.id, event_id
        )

        if not participation:
            await update.message.reply_text(
                f"Вы не записаны на мероприятие «{event.title}».\n"
                f"Проверьте ID через /my_events"
            )
            return

        # Отменяем запись
        success = await ParticipationService.cancel_registration(
            session, volunteer.id, event_id
        )

        if success:
            await update.message.reply_text(
                f"Вы отменили запись на «{event.title}»\n"
                f"{event.date_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"{event.location}"
            )
        else:
            await update.message.reply_text("Не удалось отменить запись.")