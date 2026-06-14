# handlers/notifications.py
from telegram import Bot
from datetime import datetime, timedelta
from database import async_session_maker
from services import EventService


async def send_reminder(bot: Bot, event_id: int, reminder_type: str):
    """Отправляет напоминание участникам мероприятия"""
    async with async_session_maker() as session:
        event = await EventService.get_by_id(session, event_id)
        if not event:
            return

        participants = await EventService.get_participants(session, event_id)
        if not participants:
            return

        date_str = event.date_time.strftime("%d.%m.%Y %H:%M")

        if reminder_type == "day_before":
            message = (
                f"*Напоминание о мероприятии!*\n\n"
                f"{event.title}\n"
                f"Завтра в {event.date_time.strftime('%H:%M')}\n"
                f"{event.location}\n\n"
                f"Пожалуйста, подтвердите своё участие командой /checkin {event_id} "
                f"непосредственно перед началом."
            )
        else:  # hour_before
            message = (
                f"*Скоро начало!*\n\n"
                f"{event.title}\n"
                f"Через 1 час — {date_str}\n"
                f"{event.location}\n\n"
                f"Не забудьте отметиться: /checkin {event_id}"
            )

        for volunteer in participants:
            try:
                await bot.send_message(
                    chat_id=volunteer.telegram_id,
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка отправки {volunteer.telegram_id}: {e}")


async def schedule_reminders(application, event_id: int, event_datetime: datetime):
    """Планирует напоминания для мероприятия"""
    # Напоминание за 1 день
    day_before = event_datetime - timedelta(days=1)
    if day_before > datetime.now():
        application.job_queue.run_once(
            lambda ctx: send_reminder(ctx.bot, event_id, "day_before"),
            when=day_before,
            name=f"reminder_day_{event_id}"
        )
        print(f"Запланировано напоминание за день для мероприятия {event_id} на {day_before}")

    # Напоминание за 1 час
    hour_before = event_datetime - timedelta(hours=1)
    if hour_before > datetime.now():
        application.job_queue.run_once(
            lambda ctx: send_reminder(ctx.bot, event_id, "hour_before"),
            when=hour_before,
            name=f"reminder_hour_{event_id}"
        )
        print(f"Запланировано напоминание за час для мероприятия {event_id} на {hour_before}")