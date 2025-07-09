#!/usr/bin/env python3
"""
شات بوت ذكي بسيط - نسخة مستقرة
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعداد logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# المتغيرات
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# التحقق من المفاتيح
if not BOT_TOKEN or not GEMINI_API_KEY:
    logger.error("❌ Missing API keys!")
    exit(1)

# إعداد Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# تخزين المحادثات
user_chats = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "صديق"
    
    welcome_msg = f"""
🤖 مرحباً {user_name}!

أنا بوت ذكي يستخدم تقنية Gemini AI
يمكنني مساعدتك في:

✨ الإجابة على أسئلتك
📚 شرح المفاهيم المختلفة  
💡 تقديم اقتراحات مفيدة
🗣️ المحادثة باللغة العربية والإنجليزية

أرسل لي أي رسالة وسأجيبك فوراً! 🚀
"""
    
    await update.message.reply_text(welcome_msg)
    logger.info(f"User {user_id} started the bot")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    try:
        logger.info(f"Processing message from user {user_id}: {user_message[:50]}...")
        
        # الحصول على محادثة المستخدم أو إنشاء جديدة
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
        
        chat = user_chats[user_id]
        
        # إرسال الرسالة للذكاء الاصطناعي
        response = chat.send_message(user_message)
        
        # إرسال الرد
        await update.message.reply_text(response.text)
        logger.info(f"Reply sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            "عذراً، حدث خطأ في المعالجة. 😔\nيرجى المحاولة مرة أخرى."
        )

def main():
    """تشغيل البوت"""
    logger.info("🚀 Starting Simple Smart Chatbot...")
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل البوت
    logger.info("✅ Bot is running with polling!")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
