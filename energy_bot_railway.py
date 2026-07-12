#!/usr/bin/env python3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, filters
from telegram.constants import ParseMode
import logging

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
REGISTRATION_LINK = os.getenv("REGISTRATION_LINK", "https://coral.club/7743642.html")

if not TELEGRAM_TOKEN or ADMIN_ID == 0:
    raise ValueError("❌ TELEGRAM_TOKEN и ADMIN_ID обязательны!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUESTIONS = [
    {
        "num": 1,
        "text": "🌅 КАК ТЫ ПРОСЫПАЕШЬСЯ?",
        "options": [
            ("✅ Просыпаюсь бодрая, сразу встаю", 0),
            ("🟡 Просыпаюсь, но еще 30 минут в полусне", 1),
            ("🟠 Встаю с трудом, ничего не хочется", 2),
            ("🔴 Просыпаюсь разбитой, как не спала", 3),
        ]
    },
    {
        "num": 2,
        "text": "☕ ЧТО ТЫ ПЬЕШЬ С УТРА?",
        "options": [
            ("✅ Стакан воды и потом завтрак", 0),
            ("🟡 Сразу кофе/чай, потом завтрак", 1),
            ("🟠 Только кофе/чай, без завтрака", 2),
            ("🔴 Ничего не пью, жду пока 'проснусь'", 3),
        ]
    },
    {
        "num": 3,
        "text": "🍽️ ЗАВТРАКАЕШЬ ЛИ ТЫ?",
        "options": [
            ("✅ Да, полноценный (каша, белки, овощи)", 0),
            ("🟡 Быстрый завтрак (тосты, йогурт)", 1),
            ("🟠 Только напиток, завтрака нет", 2),
            ("🔴 Пропускаю завтрак совсем", 3),
        ]
    },
    {
        "num": 4,
        "text": "😴 КАК ТЫ ЧУВСТВУЕШЬ СЕБЯ ПОСЛЕ ЕДЫ?",
        "options": [
            ("✅ Энергичная, могу работать часы", 0),
            ("🟡 Небольший подъем, потом опять усталость", 1),
            ("🟠 Вздутие, тяжесть, хочется спать", 2),
            ("🔴 Скачок сахара и потом падение энергии", 3),
        ]
    },
    {
        "num": 5,
        "text": "💧 СКОЛЬКО ВОДЫ ПЬЕШЬ В ДЕНЬ?",
        "options": [
            ("✅ 2+ литра чистой воды регулярно", 0),
            ("🟡 1.5-2 литра воды", 1),
            ("🟠 1-1.5 литра чистой воды", 2),
            ("🔴 Меньше литра (чай, кофе, соки вместо воды)", 3),
        ]
    },
    {
        "num": 6,
        "text": "☕ КАК ЧАСТО ПЬЕШЬ КОФЕ/ЧАЙ?",
        "options": [
            ("✅ Не пью совсем или очень редко", 0),
            ("🟡 1 чашка с утра", 1),
            ("🟠 2-3 чашки в день", 2),
            ("🔴 Целый день кофе, не могу без этого", 3),
        ]
    },
    {
        "num": 7,
        "text": "⚡ ЧТО ПРОИСХОДИТ ПОСЛЕ КОФЕ?",
        "options": [
            ("✅ Ничего особенного, просто пью", 0),
            ("🟡 Небольшой подъем на часик", 1),
            ("🟠 Скачок энергии, потом падение", 2),
            ("🔴 Зависима, без кофе не функционирую", 3),
        ]
    },
    {
        "num": 8,
        "text": "😴 КАК У ТЕБЯ СО СНОМ?",
        "options": [
            ("✅ Сплю 7-8 часов, просыпаюсь отдохнувшей", 0),
            ("🟡 Сплю неплохо, но иногда вскакиваю", 1),
            ("🟠 Сплю мало (5-6 часов) или часто просыпаюсь", 2),
            ("🔴 Спать трудно, но даже много сна не помогает", 3),
        ]
    },
    {
        "num": 9,
        "text": "🤢 ПРОБЛЕМЫ С ПИЩЕВАРЕНИЕМ?",
        "options": [
            ("✅ Нет проблем, все нормально", 0),
            ("🟡 Иногда вздутие после еды", 1),
            ("🟠 Постоянное вздутие, газы, дискомфорт", 2),
            ("🔴 Запоры или диарея, нарушение стула", 3),
        ]
    },
    {
        "num": 10,
        "text": "🏃 ФИЗИЧЕСКАЯ АКТИВНОСТЬ?",
        "options": [
            ("✅ Занимаюсь спортом 3+ раз в неделю", 0),
            ("🟡 Активный образ жизни, хожу пешком", 1),
            ("🟠 Минимум движения, сидячая работа", 2),
            ("🔴 Вообще не двигаюсь, везде на авто/транспорте", 3),
        ]
    },
]

async def start(update: Update, context):
    context.user_data["scores"] = []
    context.user_data["current_question"] = 0
    
    welcome = """
🔋 **ПРИВЕТ! Я ТВЯ ПОМОЩНИЦА ДЛЯ ЭНЕРГИИ!** 💚

Это быстрый тест чтобы понять, почему ты устаёшь.

Всего 10 простых вопросов - и ты получишь персональное заключение!

⏱️ Займет всего 5 минут!
"""
    
    keyboard = [[InlineKeyboardButton("✅ Поехали!", callback_data="start_test")]]
    
    await update.message.reply_text(
        welcome, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return 0

async def start_test(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    context.user_data["current_question"] = 0
    await show_question(query, context, 0)
    return 1

async def show_question(query, context, q_idx):
    q = QUESTIONS[q_idx]
    
    keyboard = [
        [InlineKeyboardButton(opt[0], callback_data=f"ans_{q_idx}_{opt[1]}")]
        for opt in q["options"]
    ]
    
    await query.edit_message_text(
        f"{q['text']}\n\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_answer(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    q_idx = int(data[1])
    score = int(data[2])
    
    context.user_data["scores"].append(score)
    context.user_data["current_question"] += 1
    
    next_q = context.user_data["current_question"]
    
    if next_q < len(QUESTIONS):
        await show_question(query, context, next_q)
        return 1
    else:
        await show_results(query, context)
        return -1

async def show_results(query, context):
    total_score = sum(context.user_data.get("scores", []))
    
    if total_score <= 12:
        result = f"""
✨ **ОТЛИЧНО! ХОРОШЕЕ СОСТОЯНИЕ!** ✨

Твой результат: **{total_score}/30 баллов** 🟢

💚 Твой организм работает хорошо!
✓ Энергия на уровне
✓ Сон в норме
✓ Пищеварение в порядке

🎯 **Если хочешь МАКСИМАЛЬНОЙ энергии:**
Я готова помочь тебе сделать это еще ЛУЧШЕ!

📱 **Напиши мне в Telegram:**
@e_moellmann

Расскажешь свои цели, и мы создадим персональный план 
для абсолютной энергии! 💪🚀
"""
    
    elif total_score <= 20:
        result = f"""
⚠️ **ОРГАНИЗМ ПРОСИТ ПОМОЩИ!** ⚠️

Твой результат: **{total_score}/30 баллов** 🟡

🔍 **ВОТ ЧТО Я ВИЖУ:**
✗ Твой организм явно просит помощи
✗ Вспомни, что именно хромает в твоих ответах

Это еще не критично, но ждать нельзя!

💚 **ENERGY создана ДЛЯ ТАКИХ СИТУАЦИЙ!**

За 30 дней мы:
✓ Восстановим твою энергию
✓ Наладим пищеварение
✓ Избавимся от усталости

📱 **НАПИШИ МНЕ СЕЙЧАС:**
@e_moellmann

Мы разберемся вместе! 💪
"""
    
    else:
        result = f"""
🚨 **СТОП! ТВОЕ СОСТОЯНИЕ КРИТИЧЕСКОЕ!** 🚨

Твой результат: **{total_score}/30 баллов** 🔴

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
Это серьезно, не откладывай! 🔴
"""
    
    await query.edit_message_text(result, parse_mode=ParseMode.MARKDOWN)
    
    admin_msg = f"📊 Новый результат анкеты: {total_score}/30 баллов\nПользователь: {query.from_user.first_name}"
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
    except:
        pass

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            0: [CallbackQueryHandler(start_test, pattern="^start_test$")],
            1: [CallbackQueryHandler(handle_answer, pattern="^ans_")],
        },
        fallbacks=[],
    )
    
    application.add_handler(conv_handler)
    logger.info("🚀 БОТ ЗАПУЩЕН!")
    application.run_polling()

if __name__ == "__main__":
    main()
