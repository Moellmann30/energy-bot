#!/usr/bin/env python3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
import logging

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
REGISTRATION_LINK = os.getenv("REGISTRATION_LINK", "https://coral.club/7743642.html")

if not TELEGRAM_TOKEN or ADMIN_ID == 0:
    raise ValueError("ОШИБКА: TELEGRAM_TOKEN и ADMIN_ID не установлены!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUESTIONS = [
    {
        "text": "🌅 КАК ТЫ ПРОСЫПАЕШЬСЯ?",
        "options": [
            ("Просыпаюсь бодрая, сразу встаю", 0),
            ("Просыпаюсь, но 30 мин в полусне", 1),
            ("Встаю с трудом, ничего не хочется", 2),
            ("Просыпаюсь разбитой, как не спала", 3),
        ]
    },
    {
        "text": "☕ ЧТО ТЫ ПЬЕШЬ С УТРА?",
        "options": [
            ("Стакан воды и потом завтрак", 0),
            ("Сразу кофе/чай, потом завтрак", 1),
            ("Только кофе/чай, без завтрака", 2),
            ("Ничего, жду пока проснусь", 3),
        ]
    },
    {
        "text": "🍽️ ЗАВТРАКАЕШЬ ЛИ ТЫ?",
        "options": [
            ("Полноценный (каша, белки, овощи)", 0),
            ("Быстрый завтрак (тосты, йогурт)", 1),
            ("Только напиток, завтрака нет", 2),
            ("Пропускаю завтрак совсем", 3),
        ]
    },
    {
        "text": "😴 ПОСЛЕ ЕДЫ КАК СЕБЯ ЧУВСТВУЕШЬ?",
        "options": [
            ("Энергичная, работать часы", 0),
            ("Подъем, потом опять усталость", 1),
            ("Вздутие, тяжесть, хочется спать", 2),
            ("Скачок сахара и падение энергии", 3),
        ]
    },
    {
        "text": "💧 СКОЛЬКО ВОДЫ В ДЕНЬ?",
        "options": [
            ("2+ литра чистой воды", 0),
            ("1.5-2 литра воды", 1),
            ("1-1.5 литра воды", 2),
            ("Меньше литра (чай, кофе вместо воды)", 3),
        ]
    },
    {
        "text": "☕ КАК ЧАСТО КОФЕ/ЧАЙ?",
        "options": [
            ("Не пью совсем", 0),
            ("1 чашка с утра", 1),
            ("2-3 чашки в день", 2),
            ("Целый день, не могу без", 3),
        ]
    },
    {
        "text": "⚡ ЧТО ПОСЛЕ КОФЕ?",
        "options": [
            ("Ничего особенного", 0),
            ("Подъем на часик", 1),
            ("Скачок, потом падение", 2),
            ("Зависима, без кофе не функционирую", 3),
        ]
    },
    {
        "text": "😴 КАК СО СНОМ?",
        "options": [
            ("7-8 часов, просыпаюсь отдохнувшей", 0),
            ("Неплохо, но иногда вскакиваю", 1),
            ("Мало (5-6) или часто просыпаюсь", 2),
            ("Трудно спать, даже сон не помогает", 3),
        ]
    },
    {
        "text": "🤢 ПРОБЛЕМЫ С ПИЩЕВАРЕНИЕМ?",
        "options": [
            ("Нет проблем, все нормально", 0),
            ("Иногда вздутие после еды", 1),
            ("Постоянное вздутие, газы, дискомфорт", 2),
            ("Запоры или диарея, нарушение стула", 3),
        ]
    },
    {
        "text": "🏃 ФИЗИЧЕСКАЯ АКТИВНОСТЬ?",
        "options": [
            ("Спорт 3+ раз в неделю", 0),
            ("Активный образ жизни, хожу пешком", 1),
            ("Минимум движения, сидячая работа", 2),
            ("Везде на авто/транспорте, не двигаюсь", 3),
        ]
    },
]

async def start(update: Update, context):
    context.user_data["scores"] = []
    context.user_data["q_idx"] = -1
    
    text = """
🔋 **ПРИВЕТ! Я ТВЯ ПОМОЩНИЦА!** 💚

Быстрый тест - всего 10 вопросов
Ты узнаешь, почему устаёшь!

⏱️ Займет 5 минут - поехали?
"""
    
    kb = [[InlineKeyboardButton("✅ Поехали!", callback_data="start")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    return 0

async def next_question(query, context):
    idx = context.user_data["q_idx"]
    
    if idx >= len(QUESTIONS):
        await show_results(query, context)
        return
    
    q = QUESTIONS[idx]
    kb = [[InlineKeyboardButton(opt[0], callback_data=f"a{opt[1]}")] for opt in q["options"]]
    
    text = f"**Вопрос {idx + 1}/10**\n\n{q['text']}"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "start":
        context.user_data["q_idx"] = 0
        await next_question(query, context)
    elif query.data.startswith("a"):
        score = int(query.data[1])
        context.user_data["scores"].append(score)
        context.user_data["q_idx"] += 1
        
        if context.user_data["q_idx"] < len(QUESTIONS):
            await next_question(query, context)
        else:
            await show_results(query, context)

async def show_results(query, context):
    total = sum(context.user_data.get("scores", []))
    
    if total <= 12:
        text = f"""
✨ **ОТЛИЧНО! ХОРОШЕЕ СОСТОЯНИЕ!** ✨

Твой результат: **{total}/30 баллов** 🟢

💚 Твой организм работает хорошо!
✓ Энергия на уровне
✓ Сон в норме
✓ Пищеварение в порядке

🎯 **Если хочешь МАКСИМАЛЬНОЙ энергии:**
Я готова помочь сделать это еще ЛУЧШЕ!

📱 **Напиши мне в Telegram:**
@e_moellmann

Расскажешь свои цели, и мы создадим персональный план для абсолютной энергии! 💪🚀
"""
    
    elif total <= 20:
        text = f"""
⚠️ **ОРГАНИЗМ ПРОСИТ ПОМОЩИ!** ⚠️

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

Мы разберемся вместе! 💪
"""
    
    else:
        text = f"""
🚨 **СТОП! ТВОЕ СОСТОЯНИЕ КРИТИЧЕСКОЕ!** 🚨

Твой результат: **{total}/30 баллов** 🔴

⚠️ **ВОТ ЧТО ПРОИСХОДИТ:**
Критическая усталость и истощение организма
Нужна срочная помощь!

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
    
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    try:
        admin_msg = f"📊 Новый результат: {total}/30 баллов\nПользователь: {query.from_user.first_name} (@{query.from_user.username})"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
    except:
        pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            0: [CallbackQueryHandler(handle_callback)]
        },
        fallbacks=[]
    )
    
    app.add_handler(handler)
    logger.info("✅ БОТ ЗАПУЩЕН И ГОТОВ!")
    app.run_polling()

if __name__ == "__main__":
    main()
