# handlers/organizer.py
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from datetime import datetime
from database import async_session_maker
from services import VolunteerService, EventService
from handlers.notifications import schedule_reminders

NAME, DESCRIPTION, DATETIME, LOCATION = range(4)


async def create_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    async with async_session_maker() as session:
        is_org = await VolunteerService.is_organizer(session, user.id)
        if not is_org:
            await update.message.reply_text("Только для организаторов.")
            return ConversationHandler.END

    await update.message.reply_text("*Создание мероприятия*\n\nШаг 1/4: Введите название:", parse_mode="Markdown")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Шаг 2/4: Введите описание:")
    return DESCRIPTION


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Шаг 3/4: Введите дату и время (ДД.ММ.ГГГГ ЧЧ:ММ):")
    return DATETIME


async def get_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datetime_str = update.message.text.strip()
    try:
        event_datetime = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
        context.user_data["datetime"] = event_datetime
    except ValueError:
        await update.message.reply_text("Неверный формат. Используйте ДД.ММ.ГГГГ ЧЧ:ММ")
        return DATETIME
    await update.message.reply_text("Шаг 4/4: Введите место проведения:")
    return LOCATION


async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text

    async with async_session_maker() as session:
        volunteer = await VolunteerService.get_by_telegram_id(session, update.effective_user.id)

        event = await EventService.create_event(
            session=session,
            title=context.user_data["name"],
            description=context.user_data["description"],
            date_time=context.user_data["datetime"],
            location=context.user_data["location"],
            sphere="Общая",
            organizer_id=volunteer.id
        )

    # Планируем напоминания
    # await schedule_reminders(context.application, event.id, event.date_time)

    date_str = event.date_time.strftime("%d.%m.%Y %H:%M")
    await update.message.reply_text(
        f"*Мероприятие создано!*\n\n"
        f"Название: {event.title}\n"
        f"Описание: {event.description}\n"
        f"Дата/время: {date_str}\n"
        f"Место: {event.location}\n"
        f"ID: `{event.id}`\n\n"
        f"Участникам будут отправлены напоминания за день и за час до начала.",
        parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    context.user_data.clear()
    return ConversationHandler.END


def create_event_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("create_event", create_event_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_datetime)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )