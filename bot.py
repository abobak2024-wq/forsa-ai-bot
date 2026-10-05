import os
import logging
from flask import Flask
from threading import Thread

from supabase import create_client

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# =====================================
# SETTINGS
# =====================================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


if not TOKEN:
    raise ValueError("BOT_TOKEN is missing")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing")


# =====================================
# SUPABASE
# =====================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =====================================
# FLASK
# =====================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Forsa AI Bot is running!"


def run_server():

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# =====================================
# ADMIN
# =====================================

def is_admin(user_id):

    return user_id == ADMIN_ID


# =====================================
# MAIN MENU
# =====================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 فرص ربح",
                callback_data="cat_ربح"
            ),

            InlineKeyboardButton(
                "💼 وظائف",
                callback_data="cat_وظائف"
            )
        ],

        [
            InlineKeyboardButton(
                "🤖 فرص AI",
                callback_data="cat_AI"
            ),

            InlineKeyboardButton(
                "🧑‍💻 Freelance",
                callback_data="cat_Freelance"
            )
        ],

        [
            InlineKeyboardButton(
                "🔥 بدون رأس مال",
                callback_data="cat_بدون رأس مال"
            )
        ],

        [
            InlineKeyboardButton(
                "🎯 كل الفرص",
                callback_data="all_jobs"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# =====================================
# START
# =====================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    try:

        supabase.table("users").upsert({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }).execute()

    except Exception as e:

        print(
            "User save error:",
            e
        )

    await update.message.reply_text(

        f"أهلاً {user.first_name} 👋\n\n"

        "أنا Forsa AI 🤖\n"

        "أساعدك في العثور على "
        "الوظائف وفرص الربح والعمل الحر "
        "وفرص الذكاء الاصطناعي.\n\n"

        "اختر نوع الفرصة:",

        reply_markup=main_menu()
    )


# =====================================
# ADMIN PANEL
# =====================================

async def admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

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
        ]

    ]


    await update.message.reply_text(

        "🔐 لوحة تحكم Forsa AI\n\n"
        "اختر العملية:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =====================================
# ADD JOB
# =====================================

async def admin_add_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    if not is_admin(
        query.from_user.id
    ):
        return


    context.user_data[
        "admin_state"
    ] = "title"


    await query.message.reply_text(

        "➕ إضافة فرصة جديدة\n\n"
        "أرسل اسم الفرصة:"
    )


# =====================================
# LIST JOBS
# =====================================

async def admin_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    if not is_admin(
        query.from_user.id
    ):
        return


    try:

        result = (
            supabase
            .table("jobs")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        jobs = result.data

    except Exception as e:

        await query.message.reply_text(
            f"❌ خطأ في قاعدة البيانات:\n{e}"
        )

        return


    if not jobs:

        await query.message.reply_text(
            "📭 لا توجد فرص حالياً."
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


    await query.message.reply_text(
        text
    )


# =====================================
# DELETE JOB
# =====================================

async def admin_delete(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    if not is_admin(
        query.from_user.id
    ):
        return


    context.user_data[
        "admin_state"
    ] = "delete_id"


    await query.message.reply_text(

        "🗑 حذف فرصة\n\n"

        "أرسل رقم الفرصة التي تريد حذفها:"
    )


# =====================================
# STATISTICS
# =====================================

async def admin_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    if not is_admin(
        query.from_user.id
    ):
        return


    try:

        jobs_result = (
            supabase
            .table("jobs")
            .select("id", count="exact")
            .execute()
        )


        users_result = (
            supabase
            .table("users")
            .select("id", count="exact")
            .execute()
        )


        jobs_count = jobs_result.count or 0
        users_count = users_result.count or 0


        await query.message.reply_text(

            "📊 إحصائيات Forsa AI\n\n"

            f"👥 المستخدمين: {users_count}\n"

            f"💼 الفرص: {jobs_count}"

        )

    except Exception as e:

        await query.message.reply_text(
            f"❌ خطأ:\n{e}"
        )


# =====================================
# ADMIN TEXT INPUT
# =====================================

async def admin_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not is_admin(user.id):
        return


    state = context.user_data.get(
        "admin_state"
    )


    if not state:
        return


    text = update.message.text.strip()


    # -----------------------------
    # TITLE
    # -----------------------------

    if state == "title":

        context.user_data[
            "new_title"
        ] = text

        context.user_data[
            "admin_state"
        ] = "description"


        await update.message.reply_text(

            "📝 أرسل وصف الفرصة:"
        )


    # -----------------------------
    # DESCRIPTION
    # -----------------------------

    elif state == "description":

        context.user_data[
            "new_description"
        ] = text

        context.user_data[
            "admin_state"
        ] = "category"


        await update.message.reply_text(

            "📂 أرسل التصنيف:\n\n"

            "مثال:\n"

            "ربح\n"
            "وظائف\n"
            "AI\n"
            "Freelance\n"
            "بدون رأس مال"

        )


    # -----------------------------
    # CATEGORY
    # -----------------------------

    elif state == "category":

        context.user_data[
            "new_category"
        ] = text

        context.user_data[
            "admin_state"
        ] = "link"


        await update.message.reply_text(

            "🔗 أرسل رابط الفرصة:"
        )


    # -----------------------------
    # LINK
    # -----------------------------

    elif state == "link":

        title = context.user_data[
            "new_title"
        ]

        description = context.user_data[
            "new_description"
        ]

        category = context.user_data[
            "new_category"
        ]

        link = text


        try:

            supabase.table(
                "jobs"
            ).insert({

                "title": title,

                "description": description,

                "category": category,

                "link": link

            }).execute()


            context.user_data.clear()


            await update.message.reply_text(

                "✅ تمت إضافة الفرصة بنجاح!\n\n"

                "💾 تم حفظها في قاعدة البيانات."

            )


        except Exception as e:

            await update.message.reply_text(

                f"❌ حدث خطأ:\n{e}"

            )


    # -----------------------------
    # DELETE
    # -----------------------------

    elif state == "delete_id":

        try:

            job_id = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ أرسل رقم صحيح."
            )

            return


        try:

            result = (
                supabase
                .table("jobs")
                .delete()
                .eq(
                    "id",
                    job_id
                )
                .execute()
            )


            context.user_data.clear()


            await update.message.reply_text(

                "✅ تم حذف الفرصة من قاعدة البيانات."

            )


        except Exception as e:

            await update.message.reply_text(

                f"❌ حدث خطأ:\n{e}"

            )


# =====================================
# SHOW JOBS
# =====================================

async def show_jobs(
    update: Update,
    category=None
):

    query = update.callback_query


    try:

        request = (
            supabase
            .table("jobs")
            .select("*")
            .order(
                "id",
                desc=True
            )
        )


        if category:

            request = request.eq(
                "category",
                category
            )


        result = request.execute()

        jobs = result.data


    except Exception as e:

        await query.message.reply_text(
            f"❌ حدث خطأ:\n{e}"
        )

        return


    if not jobs:

        await query.message.reply_text(

            "😔 حالياً لا توجد فرص "
            "في هذا التصنيف."

        )

        return


    for job in jobs:

        text = (

            f"📌 {job['title']}\n\n"

            f"{job['description']}\n\n"

            f"📂 التصنيف: "
            f"{job['category']}"

        )


        keyboard = [

            [

                InlineKeyboardButton(

                    "🚀 فتح الفرصة",

                    url=job["link"]

                )

            ]

        ]


        await query.message.reply_text(

            text,

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )

        )


# =====================================
# BUTTON HANDLER
# =====================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    data = query.data


    # ADMIN

    if data == "admin_add":

        await admin_add_start(
            update,
            context
        )

        return


    if data == "admin_list":

        await admin_list(
            update,
            context
        )

        return


    if data == "admin_delete":

        await admin_delete(
            update,
            context
        )

        return


    if data == "admin_stats":

        await admin_stats(
            update,
            context
        )

        return


    # CATEGORIES

    if data.startswith("cat_"):

        category = data.replace(
            "cat_",
            ""
        )

        await show_jobs(
            update,
            category
        )

        return


    if data == "all_jobs":

        await show_jobs(
            update
        )

        return


# =====================================
# MAIN
# =====================================

def main():

    Thread(
        target=run_server,
        daemon=True
    ).start()


    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    application.add_handler(
        CommandHandler(
            "admin",
            admin
        )
    )


    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            admin_text
        )
    )


    print(
        "Forsa AI Bot is running..."
    )


    application.run_polling()


# =====================================
# RUN
# =====================================

if __name__ == "__main__":

    main()
