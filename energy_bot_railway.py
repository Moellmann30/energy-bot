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
    
    text = "🔋 <b>ПРИВЕТ! Я ТВОЯ ПОМОЩНИЦА ДЛЯ ЭНЕРГИИ!</b> 💚\n\nЭто быстрый тест чтобы понять, почему ты устаёшь.\n\nВсего 10 простых вопросов - и ты получишь персональное заключение!\n\n⏱️ Займет всего 5 минут!\n\nПоехали? 🚀"
    kb = [[InlineKeyboardButton("✅ Начинаем!", callback_data="go")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    return 0

async def ask_question(query, context, q_idx):
    if q_idx >= len(QUESTIONS):
        # Важно: вызываем show_results через await напрямую
        await show_results(query, context)
        return ConversationHandler.END
        
    q = QUESTIONS[q_idx]
    kb = [[InlineKeyboardButton(opt[0], callback_data=f"ans_{opt[1]}_{q_idx}")] for opt in q["options"]]
    
    msg = f"<b>Вопрос {q_idx + 1}/{len(QUESTIONS)}</b>\n\n{q['text']}"
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    return 0

async def handle_answer(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "go":
        return await ask_question(query, context, 0)
    
    try:
        parts = query.data.split("_")
        score = int(parts[1])
        q_idx = int(parts[2])
    except (ValueError, IndexError):
        return 0

    if "scores" not in context.user_data:
        context.user_data["scores"] = []
        
    context.user_data["scores"].append(score)
    next_idx = q_idx + 1
    
    return await ask_question(query, context, next_idx)

async def show_results(query, context):
    scores = context.user_data.get("scores", [])
    total = sum(scores)
    
    # Переписали разметку на безопасный HTML
    if total <= 12:
        text = f"""✨ <b>ОТЛИЧНО! ХОРОШЕЕ СОСТОЯНИЕ!</b> ✨

Твой результат: <b>{total}/30 баллов</b> 🟢

💚 Твой организм работает хорошо!
✓ Энергия на уровне
✓ Сон в норме
✓ Пищеварение в порядке

🎯 <b>Если хочешь МАКСИМАЛЬНОЙ энергии:</b>
Я готова помочь тебе сделать это еще ЛУЧШЕ!

📱 <b>Напиши мне в Telegram:</b>
@e_moellmann

Расскажешь свои цели, и мы создадим персональный план для абсолютной энергии! 💪🚀"""
    
    elif total <= 20:
        text = f"""⚠️ <b>ОРГАНИЗМ ПРОСИТ ПОМОЩИ!</b> ⚠️

Твой результат: <b>{total}/30 баллов</b> 🟡

🔍 <b>ВОТ ЧТО Я ВИЖУ:</b>
Твой организм явно просит помощи!
Это еще не критично, но ждать нельзя!

💚 <b>ENERGY создана ДЛЯ ТАКИХ СИТУАЦИЙ!</b>

За 30 дней мы:
✓ Восстановим твою энергию
✓ Наладим пищеварение
✓ Избавимся от усталости

📱 <b>НАПИШИ МНЕ СЕЙЧАС:</b>
@e_moellmann

Мы разберемся вместе! 💪"""
    
    else:
        text = f"""🚨 <b>СТОП! ТВОЕ СОСТОЯНИЕ КРИТИЧЕСКОЕ!</b> 🚨

Твой результат: <b>{total}/30 баллов</b> 🔴

⚠️ <b>ВОТ ЧТО ПРОИСХОДИТ:</b>
✗ Критическая усталость
✗ Организм истощен
✗ Нужна срочная помощь

❌ Это не нормально! Это срочно!

💚 <b>ENERGY - ЭТО ТВОЕ СПАСЕНИЕ!</b>

За 30 дней:
✓ Вернешь энергию БЕЗ кофе
✓ Восстановишь кишечник
✓ Наладишь сон
✓ Избавишься от усталости

⚡ <b>ДЕЙСТВУЙ СЕЙЧАС:</b>
📱 <b>Telegram: @e_moellmann</b>

Напиши мне прямо сейчас!
Это серьезно, не откладывай! 🔴"""
    
    try:
        # Пробуем обновить текущее сообщение
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Не удалось отредактировать сообщение, отправляем новое: {e}")
        # Если Telegram капризничает из-за замены клавиатуры на текст, отправляем результат новым сообщением
        await context.bot.send_message(chat_id=query.message.chat_id, text=text, parse_mode=ParseMode.HTML)
    
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📊 Результат: {total}/30")
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
        
    context.user_data.pop("scores", None)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={0: [CallbackQueryHandler(handle_answer)]},
        fallbacks=[CommandHandler("start", start)],
        per_message=False # Гарантирует стабильность состояний для кнопок
    )
    
    app.add_handler(handler)
    logger.info("✅ БОТ ГОТОВ!")
    app.run_polling()

if __name__ == "__main__":
    main()
