import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "ForsaAI is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("💰 فرص ربح", callback_data="money"),
            InlineKeyboardButton("💼 وظائف", callback_data="jobs")
        ],
        [
            InlineKeyboardButton("🤖 فرص AI", callback_data="ai"),
            InlineKeyboardButton("🧑‍💻 Freelance", callback_data="freelance")
        ],
        [
            InlineKeyboardButton("🔥 بدون رأس مال", callback_data="free")
        ],
        [
            InlineKeyboardButton("🎯 فرص مناسبة لي", callback_data="profile")
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🚀 أهلاً بك في ForsaAI\n\n"
        "أساعدك في العثور على فرص العمل والربح المناسبة لك.\n\n"
        "اختر ما تبحث عنه:",
        reply_markup=reply_markup
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    messages = {
        "money": "💰 سنعرض لك فرص الربح المتاحة.",
        "jobs": "💼 سنعرض لك وظائف أونلاين.",
        "ai": "🤖 سنعرض فرص وأعمال مرتبطة بالذكاء الاصطناعي.",
        "freelance": "🧑‍💻 سنعرض فرص العمل الحر.",
        "free": "🔥 سنعرض فرصًا لا تحتاج رأس مال.",
        "profile": "🎯 قريبًا سيقوم AI بتحليل ملفك وإعطائك أفضل الفرص."
    }

    await query.edit_message_text(
        messages.get(query.data, "اختر من القائمة.")
    )


def main():

    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    threading.Thread(target=run_web, daemon=True).start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    print("ForsaAI is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
