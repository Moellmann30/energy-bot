#!/usr/bin/env python3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
import logging

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TELEGRAM_TOKEN or ADMIN_ID == 0:
    raise ValueError("ОШИБКА: переменные не установлены!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUESTIONS = [
    {
        "text": "🌅 Как ты просыпаешься?",
        "options": [
            ("✅ Бодрая, сразу встаю", 0),
            ("🟡 В полусне 30 минут", 1),
            ("🟠 С трудом, ничего не хочется", 2),
            ("🔴 Разбитая, как не спала", 3),
        ]
    },
    {
        "text": "☕ Что пьешь с утра?",
        "options": [
            ("✅ Вода и завтрак", 0),
            ("🟡 Кофе, потом завтрак", 1),
            ("🟠 Только кофе", 2),
            ("🔴 Ничего", 3),
        ]
    },
    {
        "text": "🍽️ Завтракаешь?",
        "options": [
            ("✅ Полноценный завтрак", 0),
            ("🟡 Быстрый завтрак", 1),
            ("🟠 Только напиток", 2),
            ("🔴 Пропускаю совсем", 3),
        ]
    },
    {
        "text": "😴 Как чувствуешь себя после еды?",
        "options": [
            ("✅ Энергичная", 0),
            ("🟡 Подъем, потом усталость", 1),
            ("🟠 Вздутие, хочется спать", 2),
            ("🔴 Скачок, потом падение", 3),
        ]
    },
    {
        "text": "💧 Сколько воды в день?",
        "options": [
            ("✅ 2+ литра", 0),
            ("🟡 1.5-2 литра", 1),
            ("🟠 1-1.5 литра", 2),
            ("🔴 Меньше литра", 3),
        ]
    },
    {
        "text": "☕ Как часто кофе/чай?",
        "options": [
            ("✅ Не пью", 0),
            ("🟡 1 чашка с утра", 1),
            ("🟠 2-3 чашки в день", 2),
            ("🔴 Целый день", 3),
        ]
    },
    {
        "text": "⚡ Что после кофе?",
        "options": [
            ("✅ Ничего", 0),
            ("🟡 Подъем на часик", 1),
            ("🟠 Скачок, потом падение", 2),
            ("🔴 Зависима без кофе", 3),
        ]
    },
    {
        "text": "😴 Как дела со сном?",
        "options": [
            ("✅ 7-8 часов, отдохнула", 0),
            ("🟡 Неплохо, но вскакиваю", 1),
            ("🟠 Мало сна, просыпаюсь", 2),
            ("🔴 Трудно спать", 3),
        ]
    },
    {
        "text": "🤢 Проблемы с пищеварением?",
        "options": [
            ("✅ Нет проблем", 0),
            ("🟡 Иногда вздутие", 1),
            ("🟠 Постоянное вздутие", 2),
            ("🔴 Запоры/диарея", 3),
        ]
    },
    {
        "text": "🏃 Физическая активность?",
        "options": [
            ("✅ Спорт 3+ раз", 0),
            ("🟡 Активный образ жизни", 1),
            ("🟠 Минимум движения", 2),
            ("🔴 Везде на авто", 3),
        ]
    },
]

async def start(update: Update, context):
    context.user_data["scores"] = []
    context.user_data["q_num"] = 0
    
    text = "🔋 **ПРИВЕТ! Я ТВЯ ПОМОЩНИЦА ДЛЯ ЭНЕРГИИ!** 💚\n\nЭто быстрый тест чтобы понять, почему ты устаёшь.\n\nВсего 10 простых вопросов - и ты получишь персональное заключение!\n\n⏱️ Займет всего 5 минут!\n\nПоехали? 🚀"
    kb = [[InlineKeyboardButton("✅ Начинаем!", callback_data="go")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    return 0

async def ask_question(query, context, q_idx):
    if q_idx >= 10:
        await show_results(query, context)
        return 1
    
    q = QUESTIONS[q_idx]
    kb = [[InlineKeyboardButton(opt[0], callback_data=f"ans_{opt[1]}_{q_idx}")] for opt in q["options"]]
    
    msg = f"**Вопрос {q_idx + 1}/10**\n\n{q['text']}"
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    return 0

async def handle_answer(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "go":
        return await ask_question(query, context, 0)
    
    parts = query.data.split("_")
    score = int(parts[1])
    q_idx = int(parts[2])
    
    context.user_data["scores"].append(score)
    next_idx = q_idx + 1
    
    return await ask_question(query, context, next_idx)

async def show_results(query, context):
    total = sum(context.user_data["scores"])
    
    if total <= 12:
        text = f"""✨ **ОТЛИЧНО! ХОРОШЕЕ СОСТОЯНИЕ!** ✨

Твой результат: **{total}/30 баллов** 🟢

💚 Твой организм работает хорошо!
✓ Энергия на уровне
✓ Сон в норме
✓ Пищеварение в порядке

🎯 **Если хочешь МАКСИМАЛЬНОЙ энергии:**
Я готова помочь тебе сделать это еще ЛУЧШЕ!

📱 **Напиши мне в Telegram:**
@e_moellmann

Расскажешь свои цели, и мы создадим персональный план для абсолютной энергии! 💪🚀"""
    
    elif total <= 20:
        text = f"""⚠️ **ОРГАНИЗМ ПРОСИТ ПОМОЩИ!** ⚠️

Твой результат: **{total}/30 баллов** 🟡

🔍 **ВОТ ЧТО Я ВИЖУ:**
Твой организм явно просит помощи!
Это еще не критично, но ждать нельзя!

💚 **ENERGY создана ДЛЯ ТАКИХ СИТУАЦИЙ!**

За 30 дней мы:
✓ Восстановим твою энергию
✓ Наладим пищеварение
✓ Избавимся от усталости

📱 **НАПИШИ МНЕ СЕЙЧАС:**
@e_moellmann

Мы разберемся вместе! 💪"""
    
    else:
        text = f"""🚨 **СТОП! ТВОЕ СОСТОЯНИЕ КРИТИЧЕСКОЕ!** 🚨

Твой результат: **{total}/30 баллов** 🔴

⚠️ **ВОТ ЧТО ПРОИСХОДИТ:**
✗ Критическая усталость
✗ Организм истощен
✗ Нужна срочная помощь

❌ Это не нормально! Это срочно!

💚 **ENERGY - ЭТО ТВО СПАСЕНИЕ!**

За 30 дней:
✓ Вернешь энергию БЕЗ кофе
✓ Восстановишь кишечник
✓ Наладишь сон
✓ Избавишься от усталости

⚡ **ДЕЙСТВУЙ СЕЙЧАС:**
📱 **Telegram: @e_moellmann**

Напиши мне прямо сейчас!
Это серьезно, не откладывай! 🔴"""
    
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📊 Результат: {total}/30")
    except:
        pass
    
    return ConversationHandler.END

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={0: [CallbackQueryHandler(handle_answer)]},
        fallbacks=[]
    )
    
    app.add_handler(handler)
    logger.info("✅ БОТ ГОТОВ!")
    app.run_polling()

if __name__ == "__main__":
    main()
