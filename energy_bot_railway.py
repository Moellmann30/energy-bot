#!/usr/bin/env python3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from telegram.constants import ParseMode
import logging

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
REGISTRATION_LINK = os.getenv("REGISTRATION_LINK", "https://coral.club/7743642.html")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_TOKEN не установлена!")
if ADMIN_ID == 0:
    raise ValueError("❌ ОШИБКА: Переменная ADMIN_ID не установлена!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"✅ Бот запущен с токеном: {TELEGRAM_TOKEN[:20]}...")
logger.info(f"✅ Admin ID: {ADMIN_ID}")

(WAITING_NAME, WAITING_AGE, WAITING_CONTACT, WAITING_SYMPTOMS, WAITING_ENERGY, WAITING_WATER, WAITING_RESULTS, WAITING_DETOX_HISTORY, WAITING_COMMITMENT, WAITING_TARIFF_CHOICE, WAITING_SCREENSHOT, CONFIRMATION,) = range(12)

SYMPTOMS_OPTIONS = [
    "💤 Просыпаюсь уставшей, нет энергии с утра",
    "🤢 Вздутие, метеоризм, дискомфорт после еды",
    "⚖️ Вес стоит на месте даже на диетах",
    "🍬 Дикая тяга к сладкому и мучному",
    "🧴 Проблемная кожа, высыпания, тусклый цвет",
    "☕ Не могу прожить день без 2-3 чашек кофе",
    "💧 Отеки утром или вечером",
]

WATER_OPTIONS = ["💧 Пью мало воды", "💧 Пью 1-1.5 литров", "💧 Пью более 2 литров"]

GOALS_OPTIONS = ["🫶 Плоский живот", "😴 Просыпаться бодрой", "⚖️ Сбросить вес", "🍽️ Здоровая тарелка"]

def evaluate_results(user_data):
    energy_level = user_data.get("energy", 5)
    symptoms = user_data.get("symptoms", [])
    symptom_count = len(symptoms)
    has_gut_issues = any("Вздутие" in s for s in symptoms)
    has_coffee = any("кофе" in s.lower() for s in symptoms)
    
    if energy_level <= 3 and symptom_count >= 5:
        return ("🔴 КРИТИЧЕСКОЕ ИСТОЩЕНИЕ", "Твой организм в режиме красного флага.", "Тебе нужна ENERGY!")
    elif energy_level <= 5 and has_gut_issues and symptom_count >= 3:
        return ("🟠 СИНДРОМ УСТАЛОСТИ", "Ты застряла в цикле.", "ENERGY поможет!")
    elif energy_level <= 6 and has_coffee:
        return ("🟡 НЕСТАБИЛЬНАЯ ЭНЕРГИЯ", "Ты зависишь от кофе.", "Нужна помощь!")
    else:
        return ("🟢 ВСЕ ХОРОШО", "У тебя хорошая энергия.", "Приди в ENERGY!")

async def start(update: Update, context):
    user_id = update.effective_user.id
    context.user_data["user_id"] = user_id
    welcome_text = """
🔋 **Привет! Добро пожаловать в ENERGY АНКЕТУ!**

Эта анкета займет 5 минут.

**Вопрос 1️⃣: Твоё имя и фамилия?**
    """
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    return WAITING_NAME

async def get_name(update: Update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("✅ Спасибо! **Вопрос 2️⃣: Сколько тебе лет?**", parse_mode=ParseMode.MARKDOWN)
    return WAITING_AGE

async def get_age(update: Update, context):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("✅ **Вопрос 3️⃣: Твой ник Telegram?**", parse_mode=ParseMode.MARKDOWN)
    return WAITING_CONTACT

async def get_contact(update: Update, context):
    context.user_data["contact"] = update.message.text
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"symptom_{i}")] for i, opt in enumerate(SYMPTOMS_OPTIONS)]
    keyboard.append([InlineKeyboardButton("✅ Готово!", callback_data="symptoms_done")])
    await update.message.reply_text("**Вопрос 4️⃣: Что ты замечаешь?**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    context.user_data["symptoms"] = []
    return WAITING_SYMPTOMS

async def handle_symptoms(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "symptoms_done":
        keyboard = [[InlineKeyboardButton(str(i), callback_data=f"energy_{i}")] for i in range(1, 11)]
        await query.edit_message_text("**Вопрос 5️⃣: Оцени энергию (1-10):**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return WAITING_ENERGY
    else:
        symptom_index = int(query.data.split("_")[1])
        symptom = SYMPTOMS_OPTIONS[symptom_index]
        if symptom not in context.user_data["symptoms"]:
            context.user_data["symptoms"].append(symptom)
        keyboard = [[InlineKeyboardButton(("✅ " if opt in context.user_data["symptoms"] else "") + opt, callback_data=f"symptom_{i}")] for i, opt in enumerate(SYMPTOMS_OPTIONS)]
        keyboard.append([InlineKeyboardButton("✅ Готово!", callback_data="symptoms_done")])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return WAITING_SYMPTOMS

async def handle_energy(update: Update, context):
    query = update.callback_query
    await query.answer()
    energy = int(query.data.split("_")[1])
    context.user_data["energy"] = energy
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"water_{i}")] for i, opt in enumerate(WATER_OPTIONS)]
    await query.edit_message_text(f"✅ Энергия: **{energy}/10**\n\n**Вопрос 6️⃣: Вода?**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return WAITING_WATER

async def handle_water(update: Update, context):
    query = update.callback_query
    await query.answer()
    water_index = int(query.data.split("_")[1])
    context.user_data["water"] = WATER_OPTIONS[water_index]
    level_name, description, recommendation = evaluate_results(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ Я в ENERGY!", callback_data="register_yes")], [InlineKeyboardButton("❓ Консультация", callback_data="register_consult")]]
    results_text = f"{level_name}\n\n{description}\n\n**{recommendation}**"
    await query.edit_message_text(results_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return CONFIRMATION

async def handle_confirmation(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "register_yes":
        instruction_text = f"""
🎉 **ОТЛИЧНО!**

Перейди по ссылке:
{REGISTRATION_LINK}

Купи продукт и скидай скриншот сюда ⬇️
        """
        await query.edit_message_text(instruction_text)
        return WAITING_SCREENSHOT
    else:
        await query.edit_message_text("💬 Напиши: @e_moellmann")
        return ConversationHandler.END

async def handle_screenshot(update: Update, context):
    if update.message.photo:
        admin_text = f"📊 НОВЫЙ УЧАСТНИК!\n\nИмя: {context.user_data.get('name')}\nКонтакт: {context.user_data.get('contact')}"
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        thanks_text = """
✅ **СПАСИБО!**

Скриншот получен! Скоро добавлю в чат.

💬 Напиши "АНКЕТА" сюда: @e_moellmann

До встречи! 🔋✨
        """
        await update.message.reply_text(thanks_text, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пришли скриншот (фото)")
        return WAITING_SCREENSHOT

async def cancel(update: Update, context):
    await update.message.reply_text("❌ Отменено. До встречи!")
    return ConversationHandler.END

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT, get_name)],
            WAITING_AGE: [MessageHandler(filters.TEXT, get_age)],
            WAITING_CONTACT: [MessageHandler(filters.TEXT, get_contact)],
            WAITING_SYMPTOMS: [CallbackQueryHandler(handle_symptoms)],
            WAITING_ENERGY: [CallbackQueryHandler(handle_energy)],
            WAITING_WATER: [CallbackQueryHandler(handle_water)],
            CONFIRMATION: [CallbackQueryHandler(handle_confirmation)],
            WAITING_SCREENSHOT: [MessageHandler(filters.PHOTO, handle_screenshot), MessageHandler(filters.TEXT, handle_screenshot)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    logger.info("🚀 БОТ ЗАПУЩЕН!")
    application.run_polling()

if __name__ == "__main__":
    main()
