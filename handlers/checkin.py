# handlers/checkin.py
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from database import async_session_maker
from services import VolunteerService, EventService, ParticipationService


async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметка о прибытии на мероприятие: /checkin <event_id>"""
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text(
            "Укажите ID мероприятия.\n"
            "Пример: /checkin 5"
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
            await update.message.reply_text("Вы не зарегистрированы. Используйте /register")
            return

        event = await EventService.get_by_id(session, event_id)
        if not event:
            await update.message.reply_text(f"Мероприятие с ID {event_id} не найдено.")
            return

        participation = await ParticipationService.get_active_participation(session, volunteer.id, event_id)
        if not participation:
            await update.message.reply_text(
                f"Вы не записаны на мероприятие «{event.title}».\n"
                f"Используйте /view {event_id}, чтобы записаться."
            )
            return

        if participation.checked_in_at:
            await update.message.reply_text(
                f"Вы уже отметили прибытие на «{event.title}»\n"
                f"Время: {participation.checked_in_at.strftime('%d.%m.%Y %H:%M')}"
            )
            return

        now = datetime.now()
        time_diff = (event.date_time - now).total_seconds() / 60
        if time_diff > 30:
            await update.message.reply_text(
                f"Отметка будет доступна за 30 минут до начала мероприятия.\n"
                f"Мероприятие начнётся: {event.date_time.strftime('%d.%m.%Y %H:%M')}"
            )
            return

        if time_diff < -60:
            await update.message.reply_text(
                f"Мероприятие «{event.title}» уже закончилось.\n"
                f"Вы можете отметить уход, если ещё не сделали этого."
            )
            return

        participation.checked_in_at = datetime.now()
        await session.commit()

        await update.message.reply_text(
            f"Вы отметили прибытие на «{event.title}»!\n"
            f"Место: {event.location}\n"
            f"Дата: {event.date_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"По окончании мероприятия используйте /checkout {event_id}"
        )


async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметка об уходе с мероприятия: /checkout <event_id>"""
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text(
            "Укажите ID мероприятия.\n"
            "Пример: /checkout 5"
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

        participation = await ParticipationService.get_active_participation(session, volunteer.id, event_id)
        if not participation:
            await update.message.reply_text(f"Вы не записаны на мероприятие «{event.title}».")
            return

        if not participation.checked_in_at:
            await update.message.reply_text(
                f"Вы ещё не отметили прибытие на «{event.title}».\n"
                f"Используйте /checkin {event_id} сначала."
            )
            return

        if participation.checked_out_at:
            await update.message.reply_text(
                f"Вы уже отметили уход с «{event.title}»\n"
                f"Время: {participation.checked_out_at.strftime('%d.%m.%Y %H:%M')}"
            )
            return

        participation.checked_out_at = datetime.now()
        await session.commit()

        duration = int((participation.checked_out_at - participation.checked_in_at).total_seconds() / 60)
        hours = duration // 60
        minutes = duration % 60

        await update.message.reply_text(
            f"Вы отметили уход с «{event.title}»!\n\n"
            f"Ваше участие длилось: {hours} ч {minutes} мин\n"
            f"Спасибо за вашу работу!"
        )