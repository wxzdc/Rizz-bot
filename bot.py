
import logging
import os
import sqlite3

import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- Configuration from Environment Variables ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "8283330138:AAGGsvMo3go_hFm2BR41W6QIcOKaXyNOGt0")
GOOGLE_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAFyY4-21IVZtcLvRrzRiN1e_VXIiM_qEQ")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Qosimov_Shahzod")
FREE_TRIAL_LIMIT = int(os.getenv("FREE_TRIAL_LIMIT", "3"))
DATABASE_NAME = "bot_users.db"

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Configure Google Gemini API
genai.configure(api_key=GOOGLE_GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Conversation states for registration
ASK_NAME, ASK_PHONE, ASK_GENDER = range(3)

# --- Database Functions ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            phone_number TEXT,
            gender TEXT,
            usage_count INTEGER DEFAULT 0,
            is_premium BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

def register_user(user_id, first_name, last_name, phone_number, gender):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, first_name, last_name, phone_number, gender, usage_count, is_premium) "
        "VALUES (?, ?, ?, ?, ?, COALESCE((SELECT usage_count FROM users WHERE user_id = ?), 0), "
        "COALESCE((SELECT is_premium FROM users WHERE user_id = ?), FALSE))",
        (user_id, first_name, last_name, phone_number, gender, user_id, user_id),
    )
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def update_usage_count(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET usage_count = usage_count + 1 WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()

def grant_premium_access(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = TRUE WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- Helper Functions ---
async def generate_rizz_response(prompt: str, image_path: str = None) -> str:
    """Generates flirty/rizz response using Gemini with 3 levels."""
    try:
        system_prompt = (
            "Sizga chat suhbatining skrinshoti yoki vaziyat berilgan. Suhbatni tahlil qiling va quyidagi ko'rsatmalarga amal qilib, o'zbek tilida 3 xil flirty/rizz javob variantini taklif qiling:\n\n"
            "Javoblar juda ishonchli, jozibali va biroz provokatsion (lekin me'yorida) bo'lsin. Xuddi o'ziga ishongan, gapga usta insondek javob bering.\n\n"
            "Har bir javob variantini aniq belgilang:\n"
            "1️⃣ Oddiy (Sweet/Simple) — Juda muloyim, shirin va do'stona.\n"
            "2️⃣ O'rtacha (Medium) — Flirty, qiziqarli, lekin juda dadil emas.\n"
            "3️⃣ Kuchli Rizz 🔥 — Juda dadil, ishonchli, jozibali, seductive va spicy. Bu variant boshqalaridan sezilarli darajada o'tkirroq bo'lsin.\n\n"
            "Faqat javob variantlarini qaytaring, boshqa ortiqcha matn qo'shmang."
        )

        if image_path:
            image = genai.upload_file(image_path)
            response = model.generate_content([system_prompt, image, prompt])
        else:
            response = model.generate_content(f"{system_prompt}\n\nVaziyat: {prompt}")
        
        return response.text
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return "Kechirasiz, javobni shakllantirishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user = get_user(user_id)

    if user:
        await update.message.reply_text(
            "Salom! Men sizga flirty/rizz javoblar topishga yordam beradigan botman. "
            "Menga vaziyatni yozing yoki chat skrinshotini yuboring, men sizga o'zbek tilida 3 xil javob variantini taklif qilaman!"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Assalomu alaykum! Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n\n"
            "Iltimos, ismingiz va familiyangizni kiriting (masalan: Ali Valiyev):"
        )
        return ASK_NAME

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    context.user_data["first_name"] = parts[0]
    context.user_data["last_name"] = parts[1] if len(parts) > 1 else ""

    await update.message.reply_text("Rahmat! Endi telefon raqamingizni kiriting (masalan: +998901234567):")
    return ASK_PHONE

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone_number"] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("O'g'il bola 👦", callback_data="gender_male")],
        [InlineKeyboardButton("Qiz bola 👧", callback_data="gender_female")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Jinsingizni tanlang:", reply_markup=reply_markup)
    return ASK_GENDER

async def save_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    gender = "O'g'il" if query.data == "gender_male" else "Qiz"

    user_id = query.from_user.id
    first_name = context.user_data.get("first_name", "")
    last_name = context.user_data.get("last_name", "")
    phone_number = context.user_data.get("phone_number", "")

    register_user(user_id, first_name, last_name, phone_number, gender)

    await query.edit_message_text(
        f"Tabriklaymiz, {first_name}! Ro'yxatdan muvaffaqiyatli o'tdingiz. "
        "Endi menga matn yoki rasm yuborishingiz mumkin."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ro'yxatdan o'tish bekor qilindi. Botdan foydalanish uchun /start bosing.")
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = get_user(user_id)

    if not user:
        await update.message.reply_text("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return

    if not user["is_premium"] and user["usage_count"] >= FREE_TRIAL_LIMIT:
        await update.message.reply_text(
            f"Bepul foydalanish tugadi! Davom etish uchun obuna bo'ling. Admin: @{ADMIN_USERNAME} ga yozing."
        )
        return

    await update.message.reply_text("Javob variantlarini shakllantirmoqdaman, iltimos kuting...")
    response_text = await generate_rizz_response(update.message.text)
    await update.message.reply_text(response_text)

    if not user["is_premium"]:
        update_usage_count(user_id)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = get_user(user_id)

    if not user:
        await update.message.reply_text("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return

    if not user["is_premium"] and user["usage_count"] >= FREE_TRIAL_LIMIT:
        await update.message.reply_text(
            f"Bepul foydalanish tugadi! Davom etish uchun obuna bo'ling. Admin: @{ADMIN_USERNAME} ga yozing."
        )
        return

    await update.message.reply_text("Skrinshotni tahlil qilmoqdaman, iltimos kuting...")

    try:
        photo_file = await update.message.photo[-1].get_file()
        file_path = f"{photo_file.file_id}.jpg"
        await photo_file.download_to_drive(file_path)

        caption = update.message.caption if update.message.caption else "Chat skrinshoti tahlili."
        response_text = await generate_rizz_response(caption, image_path=file_path)
        
        if response_text:
            await update.message.reply_text(response_text)
        else:
            await update.message.reply_text("Kechirasiz, tahlil natijasida hech qanday javob olinmadi.")

        if os.path.exists(file_path):
            os.remove(file_path)

        if not user["is_premium"]:
            update_usage_count(user_id)
            
    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
        await update.message.reply_text("Rasm tahlilida xatolik yuz berdi.")

async def grant_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Sizda bu buyruqni ishlatish huquqi yo'q.")
        return

    try:
        target_id = int(context.args[0])
        grant_premium_access(target_id)
        await update.message.reply_text(f"Foydalanuvchi {target_id} ga cheksiz kirish huquqi berildi.")
    except (IndexError, ValueError):
        await update.message.reply_text("Xato! Foydalanish: /grant USER_ID")

def main():
    init_db()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            ASK_GENDER: [CallbackQueryHandler(save_gender)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CommandHandler("grant", grant_access))

    logger.info("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
