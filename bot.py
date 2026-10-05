import os
import sqlite3
import logging
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing")

# =========================
# DATABASE
# =========================

DB = "forsa.db"


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            link TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# FLASK SERVER
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Forsa AI Bot is running!"


def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# =========================
# HELPERS
# =========================

def is_admin(user_id):
    return user_id == ADMIN_ID


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 فرص ربح", callback_data="cat_ربح"),
            InlineKeyboardButton("💼 وظائف", callback_data="cat_وظائف"),
        ],
        [
            InlineKeyboardButton("🤖 فرص AI", callback_data="cat_AI"),
            InlineKeyboardButton("🧑‍💻 Freelance", callback_data="cat_Freelance"),
        ],
        [
            InlineKeyboardButton("🔥 بدون رأس مال", callback_data="cat_بدون رأس مال"),
        ],
        [
            InlineKeyboardButton("🎯 فرص مناسبة لي", callback_data="all_jobs"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    conn = db()

    conn.execute("""
        INSERT OR REPLACE INTO users
        (id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"أهلاً {user.first_name} 👋\n\n"
        "أنا Forsa AI 🤖\n"
        "أساعدك في العثور على فرص العمل والربح والعمل الحر وفرص الذكاء الاصطناعي.\n\n"
        "اختر نوع الفرصة:",
        reply_markup=main_menu()
    )


# =========================
# ADMIN PANEL
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ غير مصرح لك بالدخول."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ إضافة فرصة",
                callback_data="admin_add"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 كل الفرص",
                callback_data="admin_list"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 حذف فرصة",
                callback_data="admin_delete"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 الإحصائيات",
                callback_data="admin_stats"
            )
        ],
    ]

    await update.message.reply_text(
        "🔐 لوحة تحكم Forsa AI\n\n"
        "اختر العملية:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ADMIN ADD JOB
# =========================

async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    context.user_data["admin_state"] = "title"

    await query.message.reply_text(
        "➕ إضافة فرصة جديدة\n\n"
        "أرسل اسم الفرصة:"
    )


# =========================
# ADMIN LIST
# =========================

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    conn = db()
    jobs = conn.execute(
        "SELECT * FROM jobs ORDER BY id DESC"
    ).fetchall()
    conn.close()

    if not jobs:
        await query.message.reply_text(
            "📭 لا توجد فرص مضافة حتى الآن."
        )
        return

    text = "📋 قائمة الفرص:\n\n"

    for job in jobs:
        text += (
            f"🆔 {job['id']}\n"
            f"📌 {job['title']}\n"
            f"📂 {job['category']}\n"
            f"🔗 {job['link']}\n"
            "━━━━━━━━━━━━\n"
        )

    await query.message.reply_text(text)


# =========================
# ADMIN DELETE
# =========================

async def admin_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    context.user_data["admin_state"] = "delete_id"

    await query.message.reply_text(
        "🗑 أرسل رقم الفرصة التي تريد حذفها:"
    )


# =========================
# ADMIN STATS
# =========================

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    conn = db()

    jobs = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    conn.close()

    await query.message.reply_text(
        "📊 إحصائيات Forsa AI\n\n"
        f"👥 المستخدمين: {users}\n"
        f"💼 الفرص: {jobs}"
    )


# =========================
# ADMIN TEXT HANDLER
# =========================

async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not is_admin(user.id):
        return

    state = context.user_data.get("admin_state")

    if not state:
        return

    text = update.message.text.strip()

    # TITLE
    if state == "title":

        context.user_data["new_title"] = text
        context.user_data["admin_state"] = "description"

        await update.message.reply_text(
            "📝 أرسل وصف الفرصة:"
        )

    # DESCRIPTION
    elif state == "description":

        context.user_data["new_description"] = text
        context.user_data["admin_state"] = "category"

        await update.message.reply_text(
            "📂 أرسل التصنيف.\n\n"
            "مثال:\n"
            "ربح\n"
            "وظائف\n"
            "AI\n"
            "Freelance\n"
            "بدون رأس مال"
        )

    # CATEGORY
    elif state == "category":

        context.user_data["new_category"] = text
        context.user_data["admin_state"] = "link"

        await update.message.reply_text(
            "🔗 أرسل رابط الفرصة:"
        )

    # LINK
    elif state == "link":

        title = context.user_data["new_title"]
        description = context.user_data["new_description"]
        category = context.user_data["new_category"]
        link = text

        conn = db()

        conn.execute("""
            INSERT INTO jobs
            (title, description, category, link)
            VALUES (?, ?, ?, ?)
        """, (
            title,
            description,
            category,
            link
        ))

        conn.commit()
        conn.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ تم إضافة الفرصة بنجاح!"
        )

    # DELETE
    elif state == "delete_id":

        try:
            job_id = int(text)
        except ValueError:

            await update.message.reply_text(
                "❌ أرسل رقم صحيح."
            )
            return

        conn = db()

        result = conn.execute(
            "DELETE FROM jobs WHERE id = ?",
            (job_id,)
        )

        conn.commit()

        deleted = result.rowcount

        conn.close()

        context.user_data.clear()

        if deleted:
            await update.message.reply_text(
                "✅ تم حذف الفرصة."
            )
        else:
            await update.message.reply_text(
                "❌ لم أجد فرصة بهذا الرقم."
            )


# =========================
# SHOW JOBS
# =========================

async def show_jobs(update: Update, category=None):

    conn = db()

    if category:
        jobs = conn.execute(
            """
            SELECT * FROM jobs
            WHERE category = ?
            ORDER BY id DESC
            """,
            (category,)
        ).fetchall()
    else:
        jobs = conn.execute(
            "SELECT * FROM jobs ORDER BY id DESC"
        ).fetchall()

    conn.close()

    if not jobs:

        await update.callback_query.message.reply_text(
            "😔 حالياً لا توجد فرص في هذا التصنيف."
        )

        return

    for job in jobs:

        text = (
            f"📌 {job['title']}\n\n"
            f"{job['description']}\n\n"
            f"📂 التصنيف: {job['category']}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🚀 فتح الفرصة",
                    url=job["link"]
                )
            ]
        ]

        await update.callback_query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# CALLBACKS
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # ADMIN

    if data == "admin_add":
        await admin_add_start(update, context)
        return

    if data == "admin_list":
        await admin_list(update, context)
        return

    if data == "admin_delete":
        await admin_delete(update, context)
        return

    if data == "admin_stats":
        await admin_stats(update, context)
        return

    # USER CATEGORIES

    if data.startswith("cat_"):

        category = data.replace("cat_", "")

        await show_jobs(update, category)

        return

    if data == "all_jobs":

        await show_jobs(update)

        return


# =========================
# MAIN
# =========================

def main():

    init_db()

    Thread(
        target=run_server,
        daemon=True
    ).start()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("admin", admin)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_text
        )
    )

    print("Forsa AI Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
