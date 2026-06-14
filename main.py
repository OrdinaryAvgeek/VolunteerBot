# main.py
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers.report import report
from config import BOT_TOKEN
from database import init_db
from handlers.common import start, help_command, profile, menu_events, menu_my_events, menu_profile, menu_create_event
from handlers.registration import registration_conversation
from handlers.events import events_list, view_event, event_callback
from handlers.organizer import create_event_conversation
from handlers.checkin import checkin, checkout
from handlers.my_events import my_events
from handlers.cancel_event import cancel_event

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def post_init(application: Application):
    await init_db()
    logging.info("База данных инициализирована")


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("events", events_list))
    app.add_handler(CommandHandler("view", view_event))
    app.add_handler(CommandHandler("my_events", my_events))
    app.add_handler(CommandHandler("checkin", checkin))
    app.add_handler(CommandHandler("checkout", checkout))
    app.add_handler(CommandHandler("cancel_event", cancel_event))

    # Диалоги
    app.add_handler(registration_conversation())
    app.add_handler(create_event_conversation())

    # Inline-кнопки
    app.add_handler(CallbackQueryHandler(event_callback, pattern="^(join|details|cancel_join)_"))

    # Кнопки меню
    app.add_handler(MessageHandler(filters.Regex(r'^Мероприятия$'), menu_events))
    app.add_handler(MessageHandler(filters.Regex(r'^Мои мероприятия$'), menu_my_events))
    app.add_handler(MessageHandler(filters.Regex(r'^Профиль$'), menu_profile))
    app.add_handler(MessageHandler(filters.Regex(r'^Создать мероприятие$'), menu_create_event))
    app.add_handler(CommandHandler("report", report))

    print("Бот запущен и слушает сообщения...")
    app.run_polling()


if __name__ == "__main__":
    main()