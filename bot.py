#!/usr/bin/env python3
"""
بوت تليجرام - نسخة Render نهائية مُختبرة
"""
import logging
import os
import asyncio
import nest_asyncio

import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Bot
from telegram.error import Conflict

nest_asyncio.apply()

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

async def cleanup_updates():
    """إنشاء بوت مؤقت لتنظيف التحديثات العالقة وإغلاق الاتصالات الشبح."""
    logger.info("🧹 Running cleanup task...")
    try:
        temp_bot = Bot(token=BOT_TOKEN)
        updates = await temp_bot.get_updates(offset=-1, timeout=5)
        if updates:
            last_update_id = updates[-1].update_id
            await temp_bot.get_updates(offset=last_update_id + 1, timeout=5)
            logger.info(f"✅ Cleanup finished. Cleared {len(updates)} pending updates.")
        else:
            logger.info("✅ No pending updates to clear.")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

async def main():
    """النقطة الرئيسية للتشغيل غير المتزامن"""
    # الخطوة 1: محاولة تشغيل التنظيف، مع تجاهل خطأ التضارب إذا حدث
    try:
        await cleanup_updates()
    except Conflict:
        logger.warning("Cleanup task failed due to a conflict. This is normal if a ghost connection is very stubborn. Proceeding to main startup...")
    except Exception as e:
        logger.error(f"An unexpected error occurred during cleanup: {e}")
    
    logger.info("🚀 Starting Final Render Bot after cleanup...")
    
    # الخطوة 2: إنشاء وتشغيل التطبيق الرئيسي
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Bot starting polling asynchronously!")
    
    # التشغيل غير المتزامن - هذا يضمن عدم إغلاق حلقة الأحداث
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        logger.info("🎉 Bot is now running!")
        # إبقاء البرنامج يعمل إلى الأبد
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot shutting down...")
        await application.updater.stop()
        await application.stop()
        logger.info("✅ Bot shutdown complete.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        logger.error(f"RuntimeError on startup: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
