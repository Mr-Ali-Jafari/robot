import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext

# تنظیمات پایگاه داده
DB_PATH = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            username TEXT PRIMARY KEY,
            resume TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            photo_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            service TEXT,
            price TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# متغیرها
SUPER_ADMIN = 'ali_j4fari'


# توابع پایگاه داده
def add_admin_to_db(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def is_admin(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_resume_to_db(username, resume):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO resumes (username, resume) VALUES (?, ?)", (username, resume))
    conn.commit()
    conn.close()

def get_resumes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, resume FROM resumes")
    result = cursor.fetchall()
    conn.close()
    return result

def add_portfolio_to_db(username, photo_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO portfolios (username, photo_id) VALUES (?, ?)", (username, photo_id))
    conn.commit()
    conn.close()

def get_portfolios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, photo_id FROM portfolios")
    result = cursor.fetchall()
    conn.close()
    return result

def add_pricing_to_db(username, service, price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pricings (username, service, price) VALUES (?, ?, ?)", (username, service, price))
    conn.commit()
    conn.close()

def get_pricings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, service, price FROM pricings")
    result = cursor.fetchall()
    conn.close()
    return result


# توابع ربات
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    buttons = [
        [InlineKeyboardButton("📄 رزومه‌ها", callback_data='show_resumes')],
        [InlineKeyboardButton("🖼️ نمونه‌کارها", callback_data='show_portfolios')],
        [InlineKeyboardButton("💰 تعرفه‌ها", callback_data='show_pricing')],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(
        f"سلام {user.first_name}! به ربات خوش آمدید.", reply_markup=reply_markup
    )


def admin_menu(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not is_admin(user.username):
        update.message.reply_text("شما دسترسی ادمین ندارید.")
        return

    buttons = [
        [InlineKeyboardButton("📄 ثبت رزومه", callback_data='add_resume')],
        [InlineKeyboardButton("🖼️ ارسال نمونه‌کار", callback_data='add_portfolio')],
        [InlineKeyboardButton("💰 ثبت تعرفه", callback_data='add_pricing')],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text("منوی ادمین:", reply_markup=reply_markup)


def add_resume(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.user_data['waiting_for_resume'] = True
    update.callback_query.message.reply_text("رزومه خود را ارسال کنید.")


def handle_resume(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if context.user_data.get('waiting_for_resume'):
        add_resume_to_db(user.username, update.message.text)
        context.user_data['waiting_for_resume'] = False
        update.message.reply_text("رزومه شما ثبت شد.")


def add_portfolio(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.user_data['waiting_for_portfolio'] = True
    update.callback_query.message.reply_text("عکس نمونه‌کار خود را ارسال کنید.")


def handle_portfolio(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if context.user_data.get('waiting_for_portfolio') and update.message.photo:
        photo_id = update.message.photo[-1].file_id
        add_portfolio_to_db(user.username, photo_id)
        context.user_data['waiting_for_portfolio'] = False
        update.message.reply_text("نمونه‌کار شما ثبت شد.")


def add_pricing(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.user_data['waiting_for_pricing'] = True
    update.callback_query.message.reply_text("تعرفه خدمات خود را به صورت زیر وارد کنید:\n\n`نوع خدمات - مبلغ`")


def handle_pricing(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if context.user_data.get('waiting_for_pricing'):
        service, price = update.message.text.split('-')
        add_pricing_to_db(user.username, service.strip(), price.strip())
        context.user_data['waiting_for_pricing'] = False
        update.message.reply_text("تعرفه شما ثبت شد.")


def show_resumes(update: Update, context: CallbackContext) -> None:
    resumes = get_resumes()
    response = "📄 رزومه‌ها:\n"
    for username, resume in resumes:
        response += f"@{username}: {resume}\n\n"
    update.callback_query.message.reply_text(response if resumes else "رزومه‌ای ثبت نشده است.")


def show_portfolios(update: Update, context: CallbackContext) -> None:
    user = update.callback_query.from_user
    portfolios = get_portfolios()
    media_group = []
    for username, photo_id in portfolios:
        media_group.append(InputMediaPhoto(photo_id, caption=f"نمونه‌کار از: @{username}"))
    if media_group:
        context.bot.send_media_group(chat_id=user.id, media=media_group)
    else:
        update.callback_query.message.reply_text("نمونه‌کاری ثبت نشده است.")


def show_pricing(update: Update, context: CallbackContext) -> None:
    pricings = get_pricings()
    response = "💰 تعرفه‌ها:\n"
    for username, service, price in pricings:
        response += f"@{username}: {service} - {price}\n"
    update.callback_query.message.reply_text(response if pricings else "تعرفه‌ای ثبت نشده است.")


# راه‌اندازی ربات
def main() -> None:
    updater = Updater("7282127792:AAF3mzkVRXzfKSjbxQ0LrIYoNx0L2iiJC5k")

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("admin", admin_menu))
    updater.dispatcher.add_handler(CallbackQueryHandler(add_resume, pattern='add_resume'))
    updater.dispatcher.add_handler(CallbackQueryHandler(add_portfolio, pattern='add_portfolio'))
    updater.dispatcher.add_handler(CallbackQueryHandler(add_pricing, pattern='add_pricing'))
    updater.dispatcher.add_handler(CallbackQueryHandler(show_resumes, pattern='show_resumes'))
    updater.dispatcher.add_handler(CallbackQueryHandler(show_portfolios, pattern='show_portfolios'))
    updater.dispatcher.add_handler(CallbackQueryHandler(show_pricing, pattern='show_pricing'))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_resume))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_pricing))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, handle_portfolio))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
