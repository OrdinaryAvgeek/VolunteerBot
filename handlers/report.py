# handlers/report.py
import csv
import io
from telegram import Update
from telegram.ext import ContextTypes
from database import async_session_maker
from services import VolunteerService, EventService, ParticipationService


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экспорт отчёта по мероприятию в CSV: /report <event_id>"""
    user = update.effective_user
    args = context.args

    # Проверка, что указан ID мероприятия
    if not args:
        await update.message.reply_text(
            "Укажите ID мероприятия.\n"
            "Пример: /report 5\n\n"
            "Узнать ID можно через /events (команда для организатора)"
        )
        return

    try:
        event_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return

    async with async_session_maker() as session:
        # Проверка прав (только организатор или админ)
        is_org = await VolunteerService.is_organizer(session, user.id)
        if not is_org:
            await update.message.reply_text("Только для организаторов.")
            return

        # Проверяем, существует ли мероприятие
        event = await EventService.get_by_id(session, event_id)
        if not event:
            await update.message.reply_text(f"Мероприятие с ID {event_id} не найдено.")
            return

        # Проверяем, что пользователь — организатор этого мероприятия
        volunteer = await VolunteerService.get_by_telegram_id(session, user.id)
        if event.organizer_id != volunteer.id:
            await update.message.reply_text(
                "Вы можете получить отчёт только по своим мероприятиям.\n"
                "Используйте /my_events для просмотра ваших мероприятий."
            )
            return

        # Получаем данные для отчёта
        report_data = await ParticipationService.get_event_report(session, event_id)

    if not report_data:
        await update.message.reply_text(
            f"На мероприятие «{event.title}» никто не записан.\n\n"
            f"{event.date_time.strftime('%d.%m.%Y %H:%M')}"
        )
        return

    # Создаём CSV файл
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["full_name", "phone", "status", "registered_at", "checked_in_at", "checked_out_at"],
        delimiter=';'  # точка с запятой для Excel
    )
    writer.writeheader()
    writer.writerows(report_data)

    # Отправляем файл
    await update.message.reply_document(
        document=io.BytesIO(output.getvalue().encode('utf-8-sig')),
        filename=f"report_{event.title}_{event_id}.csv",
        caption=(
            f"*Отчёт по мероприятию*\n\n"
            f"{event.title}\n"
            f"{event.date_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"{event.location}\n\n"
            f"Всего участников: {len(report_data)}"
        ),
        parse_mode="Markdown"
    )