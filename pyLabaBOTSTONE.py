
import logging
import json
import os
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler, 
    filters  
)
import random


STATS_FILE = "stats.json"


if os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'r') as f:
        stats = json.load(f)
else:
    stats = {}



def save_stats():
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)


def get_reply_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Play"), KeyboardButton("Stats")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}!\n"
        "Я бот для игры в 'Камень, ножницы, бумага'!\n\n"
        "Используй кнопки ниже:",
        reply_markup=get_reply_keyboard()
    )


async def play(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Камень 🗿", callback_data='rock'),
            InlineKeyboardButton("Ножницы ✂️", callback_data='scissors'),
            InlineKeyboardButton("Бумага 📜", callback_data='paper'),
        ]
    ]
    await update.message.reply_text(
        "Сделайте выбор:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def stats_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_stats = stats.get(str(user_id), {"wins": 0, "losses": 0, "draws": 0})
    await update.message.reply_text(
        f"📊 Ваша статистика:\n"
        f"Побед: {user_stats['wins']}\n"
        f"Поражений: {user_stats['losses']}\n"
        f"Ничьих: {user_stats['draws']}",
        reply_markup=get_reply_keyboard()
    )
   
    stats[str(user_id)] = user_stats
    save_stats()


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_choice = query.data
    bot_choice = random.choice(['rock', 'scissors', 'paper'])

    result = get_result(user_choice, bot_choice)

   
    user_id_str = str(user_id)
    if user_id_str not in stats:
        stats[user_id_str] = {"wins": 0, "losses": 0, "draws": 0}

    if result == "win":
        stats[user_id_str]["wins"] += 1
    elif result == "lose":
        stats[user_id_str]["losses"] += 1
    else:
        stats[user_id_str]["draws"] += 1

    save_stats() 

    choices = {'rock': '🗿 Камень', 'scissors': '✂️ Ножницы', 'paper': '📜 Бумага'}
    results = {"win": "Вы победили! 🎉", "lose": "Вы проиграли! 😢", "draw": "Ничья! 🤝"}

    await query.edit_message_text(
        text=f"Ваш выбор: {choices[user_choice]}\n"
             f"Мой выбор: {choices[bot_choice]}\n\n"
             f"<b>{results[result]}</b>",
        parse_mode='HTML'
    )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Сыграем ещё?",
        reply_markup=get_reply_keyboard()
    )


def get_result(user, bot):
    if user == bot:
        return "draw"
    elif (user == 'rock' and bot == 'scissors') or \
            (user == 'scissors' and bot == 'paper') or \
            (user == 'paper' and bot == 'rock'):
        return "win"
    return "lose"

async def text_handler(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()
    if text == "play":
        await play(update, context)
    elif text == "stats":
        await stats_command(update, context)
    else:
        await update.message.reply_text(
            "Используй кнопки Play или Stats для управления",
            reply_markup=get_reply_keyboard()
        )


def main() -> None:
    application = Application.builder().token("token").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    application.run_polling()


if name == 'main':
    main()
