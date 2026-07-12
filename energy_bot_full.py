#!/usr/bin/env python3
"""
ЭНЕРГИЯ АНКЕТА БОТ
Полный код для Telegram бота с анкетой, результатами и интеграцией Google Sheets
"""

import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from telegram.constants import ParseMode
import gspread
from google.oauth2.service_account import Credentials
import logging

# ===========================
# КОНФИГУРАЦИЯ
# ===========================

TELEGRAM_TOKEN = "8719320732:AAFYS_98U-2NPWQMA95T14C0a0civmUSQQ4"
ADMIN_ID = 807408693
REGISTRATION_LINK = "https://coral.club/7743642.html"

# Для Google Sheets (создадим инструкцию ниже)
GOOGLE_SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"  # Заполнишь после создания таблицы
GOOGLE_CREDENTIALS_FILE = "credentials.json"  # Файл с ключами Google

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================
# СОСТОЯНИЯ БОТА
# ===========================

(
    WAITING_NAME,
    WAITING_AGE,
    WAITING_CONTACT,
    WAITING_SYMPTOMS,
    WAITING_ENERGY,
    WAITING_WATER,
    WAITING_RESULTS,
    WAITING_DETOX_HISTORY,
    WAITING_COMMITMENT,
    WAITING_TARIFF_CHOICE,
    WAITING_SCREENSHOT,
    CONFIRMATION,
) = range(12)

# ===========================
# ВОПРОСЫ И ВАРИАНТЫ ОТВЕТОВ
# ===========================

SYMPTOMS_OPTIONS = [
    "💤 Просыпаюсь уставшей, нет энергии с утра",
    "🤢 Вздутие, метеоризм, дискомфорт после еды",
    "⚖️ Вес стоит на месте даже на диетах",
    "🍬 Дикая тяга к сладкому и мучному",
    "🧴 Проблемная кожа, высыпания, тусклый цвет",
    "☕ Не могу прожить день без 2-3 чашек кофе",
    "💧 Отеки утром или вечером",
]

WATER_OPTIONS = [
    "💧 Пью мало воды, в основном чай/кофе/соки",
    "💧 Пью 1-1.5 литров чистой воды в день",
    "💧 Пью более 2 литров, но часто холодную",
]

GOALS_OPTIONS = [
    "🫶 Вернуть плоский живот и комфорт в ЖКТ",
    "😴 Просыпаться бодрой без стимуляторов",
    "⚖️ Сбросить лишний вес без голодовок",
    "🍽️ Понять принципы здоровой тарелки",
]

TARIFF_OPTIONS = ["Я сам/сама 🎯", "С Евгенией 💚"]

# ===========================
# ЛОГИКА РЕЗУЛЬТАТОВ (5-6 УРОВНЕЙ)
# ===========================

def evaluate_results(user_data):
    """
    Анализирует ответы и определяет уровень состояния
    Возвращает: (level_name, description, recommendation)
    """
    
    energy_level = user_data.get("energy", 5)
    symptoms = user_data.get("symptoms", [])
    water = user_data.get("water", "")
    
    symptom_count = len(symptoms)
    has_gut_issues = any("Вздутие" in s or "ЖКТ" in s for s in symptoms)
    has_fatigue = any("Просыпаюсь" in s for s in symptoms)
    has_coffee = any("кофе" in s.lower() for s in symptoms)
    has_weight = any("Вес" in s for s in symptoms)
    has_skin = any("кожа" in s.lower() for s in symptoms)
    has_swelling = any("Отеки" in s for s in symptoms)
    
    # ===== УРОВЕНЬ 1: КРИТИЧЕСКОЕ ИСТОЩЕНИЕ =====
    if energy_level <= 3 and symptom_count >= 5:
        return (
            "🔴 КРИТИЧЕСКОЕ ИСТОЩЕНИЕ",
            """
⚠️ **ТВОЁ СОСТОЯНИЕ:**
Твой организм в режиме "красного флага". Низкая энергия + множество симптомов указывают на глубокое воспаление и истощение надпочечников.

**Что происходит:**
• Кишечник не работает → питательные вещества не усваиваются
• Обезвоживание + кофейная зависимость → надпочечники на грани
• Это НЕ твоя лень — это биохимия!

**ENERGY поможет потому что:**
✅ За 30 дней пройдёшь глубокий детокс на клеточном уровне
✅ Восстановишь микрофлору и барьер кишечника
✅ Вернёшь энергию БЕЗ кофе и стимуляторов
✅ Проведу с тобой живые разборы каждый день
            """,
            "🚨 Тебе КРИТИЧЕСКИ нужна программа ENERGY. Это не опция — это необходимость!"
        )
    
    # ===== УРОВЕНЬ 2: СИНДРОМ ХРОНИЧЕСКОЙ УСТАЛОСТИ + ВОСПАЛЕНИЕ =====
    elif energy_level <= 5 and has_gut_issues and symptom_count >= 3:
        return (
            "🟠 СИНДРОМ ХРОНИЧЕСКОЙ УСТАЛОСТИ + ВОСПАЛЕНИЕ",
            """
⚠️ **ТВОЁ СОСТОЯНИЕ:**
Ты застряла в цикле: плохое пищеварение → слабая энергия → больше стресса → ещё хуже пищеварение.

**Что происходит:**
• Воспаление ЖКТ блокирует усвоение витаминов
• Низкая энергия влияет на весь гормональный фон
• Вес не меняется, потому что организм в режиме выживания

**ENERGY поможет потому что:**
✅ Восстановим целостность кишечника
✅ Снимем хроническое воспаление
✅ Энергия вернётся естественным путём
✅ Вес начнёт меняться БЕЗ подсчета калорий
            """,
            "💛 ENERGY — это именно то, что тебе нужно сейчас."
        )
    
    # ===== УРОВЕНЬ 3: НЕСТАБИЛЬНАЯ ЭНЕРГИЯ =====
    elif energy_level <= 6 and has_coffee:
        return (
            "🟡 НЕСТАБИЛЬНАЯ ЭНЕРГИЯ (Кофейная зависимость)",
            """
⚡ **ТВОЁ СОСТОЯНИЕ:**
Твоя энергия зависит от кофе — это признак того, что надпочечники кричат о помощи.

**Что происходит:**
• Утром без кофе — не можешь встать
• К полудню срыв энергии
• Вечером не спишь, хотя устаёшь
• Это замкнутый круг истощения

**ENERGY поможет потому что:**
✅ Восстановим естественный ритм энергии
✅ Надпочечники получат поддержку через правильное питание
✅ Через 2 недели будешь просыпаться БЕЗ кофе
✅ Энергия будет стабильной весь день
            """,
            "☕ Твоя зависимость от кофе — это SOS твоего организма. ENERGY научит его жить по-новому."
        )
    
    # ===== УРОВЕНЬ 4: НАЧАЛЬНЫЕ ПРИЗНАКИ ДИСБАЛАНСА =====
    elif energy_level <= 7 and symptom_count >= 2:
        return (
            "🟡 НАЧАЛЬНЫЕ ПРИЗНАКИ ДИСБАЛАНСА",
            """
⏰ **ТВОЁ СОСТОЯНИЕ:**
У тебя ещё есть энергия, но организм уже подаёт сигналы. Сейчас самый правильный момент для вмешательства.

**Что происходит:**
• Хронические симптомы становятся "нормой"
• Организм медленно движется к истощению
• Но ещё можно всё вернуть в норму за 30 дней!

**ENERGY поможет потому что:**
✅ Перехватим проблему ДО того как она станет критичной
✅ Оптимизируем питание и образ жизни
✅ Вернёшь лёгкость и ясность
✅ Профилактика лучше, чем лечение
            """,
            "🎯 Это идеальный момент начать ENERGY. Ты ещё можешь легко всё изменить!"
        )
    
    # ===== УРОВЕНЬ 5: СУБКЛИНИЧЕСКОЕ ВОСПАЛЕНИЕ =====
    elif energy_level >= 8 and (has_weight or has_skin or has_swelling):
        return (
            "💛 СУБКЛИНИЧЕСКОЕ ВОСПАЛЕНИЕ",
            """
🔍 **ТВОЁ СОСТОЯНИЕ:**
Энергия хорошая, но есть хронические проблемы (вес, кожа, отеки). Это скрытое воспаление на клеточном уровне.

**Что происходит:**
• Низкоуровневое воспаление не ощущается как болезнь
• Но оно блокирует похудение и здоровье кожи
• Это как невидимый "шум" в организме

**ENERGY поможет потому что:**
✅ Найдём и уберём источник воспаления
✅ Вес начнёт меняться без ограничений
✅ Кожа станет чистой и сияющей
✅ Предотвратим развитие проблем в будущем
            """,
            "✨ Приди в ENERGY и мы разберёмся в деталях твоего состояния!"
        )
    
    # ===== УРОВЕНЬ 6: ОПТИМАЛЬНОЕ СОСТОЯНИЕ =====
    else:
        return (
            "🟢 ОПТИМАЛЬНОЕ СОСТОЯНИЕ",
            """
✨ **ТВОЁ СОСТОЯНИЕ:**
У тебя хорошая энергия и минимум проблем. Молодец!

**Но:**
Даже при хорошем состоянии ENERGY может помочь тебе:
• Оптимизировать питание для максимальной производительности
• Предотвратить будущие проблемы
• Научиться слушать свой организм

**ENERGY поможет потому что:**
✅ Это не про лечение — это про оптимизацию
✅ Станешь ещё энергичнее и здоровее
✅科ррекция питания под твой образ жизни
            """,
            "💚 Приди в ENERGY, чтобы стать лучшей версией себя!"
        )


# ===========================
# ОБРАБОТЧИКИ КОМАНД
# ===========================

async def start(update: Update, context):
    """Начало диалога"""
    user_id = update.effective_user.id
    context.user_data["user_id"] = user_id
    context.user_data["started_at"] = datetime.now().isoformat()
    
    welcome_text = """
🔋 **Привет! Добро пожаловать в ENERGY АНКЕТУ!**

Эта анкета займет 5 минут и поможет мне:
✅ Оценить состояние твоей системы детоксикации
✅ Понять истинные причины усталости
✅ Подобрать правильную программу ДЛЯ ТЕБЯ

Давай начнём! 🚀

**Вопрос 1️⃣: Твоё имя и фамилия?**
    """
    
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    return WAITING_NAME


async def get_name(update: Update, context):
    """Получение имени"""
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        "✅ Спасибо! Теперь твой возраст?\n\n**Вопрос 2️⃣: Сколько тебе лет?**",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_AGE


async def get_age(update: Update, context):
    """Получение возраста"""
    context.user_data["age"] = update.message.text
    await update.message.reply_text(
        "✅ Отлично! Теперь контакт для связи.\n\n**Вопрос 3️⃣: Твой ник Telegram или номер WhatsApp?**",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_CONTACT


async def get_contact(update: Update, context):
    """Получение контакта"""
    context.user_data["contact"] = update.message.text
    
    # Симптомы - выбор из списка
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"symptom_{i}")]
        for i, opt in enumerate(SYMPTOMS_OPTIONS)
    ]
    keyboard.append([InlineKeyboardButton("✅ Готово!", callback_data="symptoms_done")])
    
    await update.message.reply_text(
        "✅ Спасибо! Теперь самое интересное.\n\n"
        "**Вопрос 4️⃣: Что из этого ты замечаешь у себя? (Можешь выбрать несколько)**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data["symptoms"] = []
    return WAITING_SYMPTOMS


async def handle_symptoms(update: Update, context):
    """Обработка выбора симптомов"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "symptoms_done":
        # Энергия - шкала 1-10
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f"energy_{i}")]
            for i in range(1, 11)
        ]
        await query.edit_message_text(
            "✅ Симптомы записаны!\n\n"
            "**Вопрос 5️⃣: Оцени свой уровень энергии прямо сейчас (1-10):**\n"
            "1 = хочу только спать\n"
            "10 = горы готова свернуть",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_ENERGY
    else:
        # Добавление симптома
        symptom_index = int(query.data.split("_")[1])
        symptom = SYMPTOMS_OPTIONS[symptom_index]
        
        if symptom not in context.user_data["symptoms"]:
            context.user_data["symptoms"].append(symptom)
        
        # Обновляем клавиатуру (показываем что уже выбрано)
        keyboard = []
        for i, opt in enumerate(SYMPTOMS_OPTIONS):
            prefix = "✅ " if opt in context.user_data["symptoms"] else ""
            keyboard.append([InlineKeyboardButton(prefix + opt, callback_data=f"symptom_{i}")])
        keyboard.append([InlineKeyboardButton("✅ Готово!", callback_data="symptoms_done")])
        
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_SYMPTOMS


async def handle_energy(update: Update, context):
    """Обработка уровня энергии"""
    query = update.callback_query
    await query.answer()
    
    energy = int(query.data.split("_")[1])
    context.user_data["energy"] = energy
    
    # Вода - выбор из списка
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"water_{i}")]
        for i, opt in enumerate(WATER_OPTIONS)
    ]
    
    await query.edit_message_text(
        f"✅ Энергия: **{energy}/10** отмечена!\n\n"
        "**Вопрос 6️⃣: Как обстоят дела с питьевым режимом?**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_WATER


async def handle_water(update: Update, context):
    """Обработка выбора воды"""
    query = update.callback_query
    await query.answer()
    
    water_index = int(query.data.split("_")[1])
    context.user_data["water"] = WATER_OPTIONS[water_index]
    
    # Цели - выбор из списка
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"goal_{i}")]
        for i, opt in enumerate(GOALS_OPTIONS)
    ]
    keyboard.append([InlineKeyboardButton("✅ Готово!", callback_data="goals_done")])
    
    await query.edit_message_text(
        "✅ Вода отмечена!\n\n"
        "**Вопрос 7️⃣: Какой главный результат за 30 дней? (Можешь выбрать несколько)**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data["goals"] = []
    return WAITING_RESULTS


async def handle_goals(update: Update, context):
    """Обработка выбора целей"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "goals_done":
        # Детокс история
        keyboard = [
            [InlineKeyboardButton("Да, но срывалась/срывался", callback_data="detox_yes")],
            [InlineKeyboardButton("Нет, это первый опыт", callback_data="detox_no")]
        ]
        await query.edit_message_text(
            "✅ Цели записаны!\n\n"
            "**Вопрос 8️⃣: Проходила ли ты детокс-программы раньше?**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_DETOX_HISTORY
    else:
        goal_index = int(query.data.split("_")[1])
        goal = GOALS_OPTIONS[goal_index]
        
        if goal not in context.user_data["goals"]:
            context.user_data["goals"].append(goal)
        
        keyboard = []
        for i, opt in enumerate(GOALS_OPTIONS):
            prefix = "✅ " if opt in context.user_data["goals"] else ""
            keyboard.append([InlineKeyboardButton(prefix + opt, callback_data=f"goal_{i}")])
        keyboard.append([InlineKeyboardButton("✅ Готово!", callback_data="goals_done")])
        
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_RESULTS


async def handle_detox_history(update: Update, context):
    """Обработка истории детокса"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["detox_history"] = query.data.split("_")[1]
    
    # Готовность
    keyboard = [
        [InlineKeyboardButton("Да, готова на все 100%!", callback_data="ready_yes")],
        [InlineKeyboardButton("Да, но нужна поддержка", callback_data="ready_support")]
    ]
    
    await query.edit_message_text(
        "✅ Отмечено!\n\n"
        "**Вопрос 9️⃣: Готова ли ты выполнять рекомендации и работать на результат?**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_COMMITMENT


async def handle_commitment(update: Update, context):
    """Обработка готовности"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["commitment"] = query.data.split("_")[1]
    
    # Тариф
    keyboard = [
        [InlineKeyboardButton("Я сам/сама 🎯", callback_data="tariff_self")],
        [InlineKeyboardButton("С Евгенией 💚", callback_data="tariff_eugenia")],
        [InlineKeyboardButton("Нужна консультация", callback_data="tariff_consult")]
    ]
    
    await query.edit_message_text(
        "✅ Отмечено!\n\n"
        "**Вопрос 🔟: Какой формат участия тебе ближе?**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_TARIFF_CHOICE


async def handle_tariff(update: Update, context):
    """Обработка выбора тарифа"""
    query = update.callback_query
    await query.answer()
    
    tariff_map = {
        "tariff_self": "Я сам/сама 🎯",
        "tariff_eugenia": "С Евгенией 💚",
        "tariff_consult": "Нужна консультация 💬"
    }
    
    context.user_data["tariff"] = tariff_map.get(query.data, "Не указан")
    
    # ===== ВЫЧИСЛЯЕМ РЕЗУЛЬТАТЫ =====
    level_name, description, recommendation = evaluate_results(context.user_data)
    
    results_text = f"""
{level_name}

{description}

**{recommendation}**

---

💚 **ВЫБОР ДАЛЕЕ:**
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ Я хочу в ENERGY!", callback_data="register_yes")],
        [InlineKeyboardButton("❓ Хочу консультацию", callback_data="register_consult")],
    ]
    
    await query.edit_message_text(
        results_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return CONFIRMATION


async def handle_confirmation(update: Update, context):
    """Обработка финального решения"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "register_yes":
        # Запрашиваем скриншот
        instruction_text = f"""
🎉 **ОТЛИЧНО! Ты выбрал(а) ENERGY!**

Вот что дальше:

📌 **ШАГ 1:** Перейди по ссылке и выбери свой вариант программы
{REGISTRATION_LINK}

📌 **ШАГ 2:** Заполни форму и сделай покупку

📌 **ШАГ 3:** Сделай скриншот подтверждения покупки

📌 **ШАГ 4:** Пришли мне этот скриншот сюда ⬇️

Я получу скриншот → проверю → добавлю тебя в закрытый чат ENERGY!

---

**Пожалуйста, пришли скриншот подтверждения покупки:**
        """
        await query.edit_message_text(instruction_text)
        return WAITING_SCREENSHOT
    
    else:
        consult_text = """
💬 **КОНСУЛЬТАЦИЯ**

Спасибо за интерес! Напиши мне в личные сообщения: @e_moellmann

Там мы обсудим все детали и подберём идеальный вариант именно для тебя! 

До встречи! 💚
        """
        await query.edit_message_text(consult_text)
        return ConversationHandler.END


async def handle_screenshot(update: Update, context):
    """Обработка скриншота"""
    
    if update.message.photo:
        # Сохраняем фото
        photo = update.message.photo[-1]
        context.user_data["screenshot_file_id"] = photo.file_id
        
        # Готовим данные для Google Sheet
        user_summary = {
            "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Имя": context.user_data.get("name", "N/A"),
            "Возраст": context.user_data.get("age", "N/A"),
            "Контакт": context.user_data.get("contact", "N/A"),
            "Симптомы": ", ".join(context.user_data.get("symptoms", [])),
            "Энергия": context.user_data.get("energy", "N/A"),
            "Вода": context.user_data.get("water", "N/A"),
            "Цели": ", ".join(context.user_data.get("goals", [])),
            "Детокс история": context.user_data.get("detox_history", "N/A"),
            "Готовность": context.user_data.get("commitment", "N/A"),
            "Тариф": context.user_data.get("tariff", "N/A"),
            "Статус": "Ожидает проверки скриншота",
            "Telegram ID": context.user_data.get("user_id", "N/A"),
        }
        
        # Отправляем уведомление администратору
        admin_text = f"""
📊 **НОВЫЙ УЧАСТНИК ENERGY!**

✅ Скриншот получен и проверяется!

**Данные участника:**
👤 Имя: {user_summary["Имя"]}
📞 Контакт: {user_summary["Контакт"]}
⚡ Энергия: {user_summary["Энергия"]}/10
🎯 Тариф: {user_summary["Тариф"]}

**Статус:** Ожидает добавления в чат

---

Все данные внесены в таблицу: [Посмотрите Google Sheet]
        """
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Спасибо участнику
        thanks_text = """
✅ **СПАСИБО ЗА ДОВЕРИЕ!**

Твой скриншот получен и передан Евгении! 

🚀 **Дальше:**
1. Я проверю покупку
2. Добавлю тебя в закрытый чат ENERGY
3. Ты получишь доступ ко всем материалам

💬 **Напиши кодовое слово "АНКЕТА" в личку:** @e_moellmann

Это поможет зафиксировать твоё место на спец-условиях! 

До встречи на клеточной перезагрузке! 🔋✨
        """
        
        await update.message.reply_text(thanks_text, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    
    else:
        await update.message.reply_text("Пожалуйста, пришли скриншот в виде фото.")
        return WAITING_SCREENSHOT


async def cancel(update: Update, context):
    """Отмена"""
    await update.message.reply_text("❌ Анкета отменена. До встречи! 💚")
    return ConversationHandler.END


# ===========================
# ЗАПУСК БОТА
# ===========================

def main():
    """Запуск бота"""
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT, get_name)],
            WAITING_AGE: [MessageHandler(filters.TEXT, get_age)],
            WAITING_CONTACT: [MessageHandler(filters.TEXT, get_contact)],
            WAITING_SYMPTOMS: [CallbackQueryHandler(handle_symptoms)],
            WAITING_ENERGY: [CallbackQueryHandler(handle_energy)],
            WAITING_WATER: [CallbackQueryHandler(handle_water)],
            WAITING_RESULTS: [CallbackQueryHandler(handle_goals)],
            WAITING_DETOX_HISTORY: [CallbackQueryHandler(handle_detox_history)],
            WAITING_COMMITMENT: [CallbackQueryHandler(handle_commitment)],
            WAITING_TARIFF_CHOICE: [CallbackQueryHandler(handle_tariff)],
            CONFIRMATION: [CallbackQueryHandler(handle_confirmation)],
            WAITING_SCREENSHOT: [
                MessageHandler(filters.PHOTO, handle_screenshot),
                MessageHandler(filters.TEXT, handle_screenshot),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Запуск
    print("🚀 БОТ ЗАПУЩЕН!")
    print(f"Ищите бота: @energy_evgenia_bot")
    application.run_polling()


if __name__ == "__main__":
    main()
