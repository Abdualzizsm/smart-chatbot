#!/usr/bin/env python3
"""
بوت تليجرام - نسخة Render نهائية مُختبرة
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

# تحميل المتغيرات
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# المتغيرات
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not BOT_TOKEN or not GEMINI_API_KEY:
    logger.error("❌ Missing API keys!")
    exit(1)

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
user_chats = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء"""
    user_name = update.effective_user.first_name or "صديق"
    welcome_msg = f"""🤖 مرحباً {user_name}!

أنا بوت ذكي يستخدم Gemini AI
أرسل لي أي رسالة وسأجيبك! 🚀"""
    
    await update.message.reply_text(welcome_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    try:
        logger.info(f"Message from {user_id}: {user_message[:30]}...")
        
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
        
        response = user_chats[user_id].send_message(user_message)
        await update.message.reply_text(response.text)
        
        logger.info(f"Reply sent to {user_id}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("عذراً، حدث خطأ 😔")

def main():
    """النقطة الرئيسية"""
    logger.info("🚀 Starting Final Render Bot...")
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل البوت
    logger.info("✅ Bot running with polling!")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message']
    )

if __name__ == '__main__':
    main()
