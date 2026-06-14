# handlers/registration.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, \
    filters
from database import async_session_maker
from services import VolunteerService
from utils import validate_name, validate_phone
from config import SPHERES

ASK_NAME, ASK_PHONE, ASK_PREFERENCES = range(3)


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    user = update.effective_user

    async with async_session_maker() as session:
        existing = await VolunteerService.get_by_telegram_id(session, user.id)

    if existing:
        await update.message.reply_text(
            f"Вы уже зарегистрированы, {existing.full_name}!\n"
            "Для просмотра профиля используйте /profile"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"Добро пожаловать, {user.first_name}!\n\n"
        "Давайте пройдём регистрацию.\n\n"
        "Шаг 1 из 3: Как вас зовут? (Имя и фамилия)"
    )
    return ASK_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя"""
    name = update.message.text.strip()
    if not validate_name(name):
        await update.message.reply_text("Введите корректное имя (не менее 2 символов):")
        return ASK_NAME

    context.user_data["full_name"] = name
    await update.message.reply_text(
        f"Спасибо, {name}!\n\n"
        "Шаг 2 из 3: Укажите ваш контактный телефон\n"
        "Например: +7 123 456 78 90"
    )
    return ASK_PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем телефон"""
    phone = update.message.text.strip()
    if not validate_phone(phone):
        await update.message.reply_text(
            "Неверный формат телефона. Введите номер в формате:\n+7 123 456 78 90"
        )
        return ASK_PHONE

    context.user_data["phone"] = phone
    context.user_data["preferences"] = []

    # Создаём клавиатуру
    keyboard = []
    for sphere in SPHERES:
        keyboard.append([InlineKeyboardButton(sphere, callback_data=f"pref_{sphere}")])
    keyboard.append([InlineKeyboardButton("Готово", callback_data="pref_done")])

    await update.message.reply_text(
        "Шаг 3 из 3: Выберите сферы волонтёрства\n"
        "Когда закончите, нажмите «Готово».",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_PREFERENCES


async def preferences_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()

    data = query.data
    prefs = context.user_data.get("preferences", [])

    if data == "pref_done":
        # Завершаем регистрацию
        name = context.user_data.get("full_name")
        phone = context.user_data.get("phone")

        async with async_session_maker() as session:
            volunteer = await VolunteerService.register(
                session,
                telegram_id=query.from_user.id,
                full_name=name,
                phone=phone,
                preferences=prefs
            )
            ###
            if volunteer:
                volunteer.role = "organizer"
                await session.commit()
        #####
        await query.edit_message_text(
            f"Регистрация завершена!\n\n"
            f"Имя: {volunteer.full_name}\n"
            f"Телефон: {volunteer.phone}\n"
            f"Сферы: {', '.join(prefs) if prefs else 'не указаны'}\n\n"
            f"Ожидайте подтверждения организатора."
        )
        context.user_data.clear()
        return ConversationHandler.END

    # Добавляем или удаляем сферу
    sphere = data.replace("pref_", "")
    if sphere in prefs:
        prefs.remove(sphere)
    else:
        prefs.append(sphere)

    context.user_data["preferences"] = prefs

    # Обновляем клавиатуру (показываем выбранные сферы)
    keyboard = []
    for s in SPHERES:
        text = f"{s}" if s in prefs else s
        keyboard.append([InlineKeyboardButton(text, callback_data=f"pref_{s}")])
    keyboard.append([InlineKeyboardButton("Готово", callback_data="pref_done")])

    await query.edit_message_text(
        f"Выбрано: {', '.join(prefs) if prefs else 'пока ничего'}\n\n"
        "Нажмите на сферу, чтобы добавить или удалить.\n"
        "Когда закончите, нажмите «Готово».",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_PREFERENCES


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    await update.message.reply_text("Регистрация отменена.")
    context.user_data.clear()
    return ConversationHandler.END


def registration_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PREFERENCES: [CallbackQueryHandler(preferences_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )