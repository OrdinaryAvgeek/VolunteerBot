# handlers/events.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import async_session_maker
from services import EventService, VolunteerService, ParticipationService


async def events_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список мероприятий"""
    async with async_session_maker() as session:
        events = await EventService.get_published_events(session)

    if not events:
        await update.message.reply_text("На данный момент нет доступных мероприятий.")
        return

    text = "*Доступные мероприятия:*\n\n"
    for i, event in enumerate(events, 1):
        date_str = event.date_time.strftime("%d.%m.%Y %H:%M")
        text += f"{i}. *{event.title}*\n"
        text += f"   {event.location}\n"
        text += f"   {date_str}\n"
        text += f"   ID: `{event.id}`\n\n"

    text += "Для просмотра подробностей используйте:\n/view <ID>"
    await update.message.reply_text(text, parse_mode="Markdown")


async def view_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр мероприятия по ID"""
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text("Укажите ID мероприятия.\nПример: /view 5")
        return

    try:
        event_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return

    async with async_session_maker() as session:
        volunteer = await VolunteerService.get_by_telegram_id(session, user.id)
        event = await EventService.get_by_id(session, event_id)

        if not event:
            await update.message.reply_text(f"Мероприятие с ID {event_id} не найдено.")
            return

        # Проверяем, записан ли пользователь
        participation = await ParticipationService.get_active_participation(session, volunteer.id, event_id) if volunteer else None
        is_registered = participation is not None

        date_str = event.date_time.strftime("%d.%m.%Y %H:%M")

        text = f"*{event.title}*\n\n"
        text += f"{event.description or 'Описание отсутствует'}\n\n"
        text += f"*Место:* {event.location}\n"
        text += f"*Дата и время:* {date_str}\n"
        text += f"*Сфера:* {event.sphere or 'не указана'}"

        # Клавиатура
        keyboard = [
            [InlineKeyboardButton("Подробнее", callback_data=f"details_{event_id}")]
        ]
        if not is_registered and volunteer:
            keyboard[0].insert(0, InlineKeyboardButton("Записаться", callback_data=f"join_{event_id}"))
        elif is_registered:
            keyboard.append([InlineKeyboardButton("Отменить запись", callback_data=f"cancel_join_{event_id}")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data.startswith("join_"):
        event_id = int(data.split("_")[1])

        async with async_session_maker() as session:
            volunteer = await VolunteerService.get_by_telegram_id(session, user.id)
            if not volunteer:
                await query.edit_message_text("Вы не зарегистрированы.")
                return

            event = await EventService.get_by_id(session, event_id)
            if not event:
                await query.edit_message_text("Мероприятие не найдено.")
                return

            participation = await ParticipationService.register(session, volunteer.id, event_id)
            if participation:
                await query.edit_message_text(f"Вы записались на «{event.title}»!")
            else:
                await query.edit_message_text("Вы уже записаны на это мероприятие.")

    elif data.startswith("details_"):
        event_id = int(data.split("_")[1])
        await query.edit_message_text(f"Подробности об ID {event_id}\nИспользуйте /view {event_id}")

    elif data.startswith("cancel_join_"):
        event_id = int(data.split("_")[2])
        await query.edit_message_text(f"Отмена записи на ID {event_id}\nФункция в разработке.")