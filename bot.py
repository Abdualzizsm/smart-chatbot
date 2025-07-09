#!/usr/bin/env python3
"""
شات بوت ذكي بسيط - يعمل محلياً وعلى Render
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعداد logging بسيط
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# المتغيرات
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# إعداد Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# تخزين المحادثات
user_chats = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    user_name = update.effective_user.first_name or "صديقي"
    
    welcome_message = f"""🤖 **مرحباً {user_name}!**

أنا بوت ذكي مدعوم بـ **Gemini AI** ✨

**ما يمكنني فعله:**
• الإجابة على أسئلتك
• المساعدة في الدراسة والعمل  
• كتابة النصوص والمقالات
• الترجمة بين اللغات
• حل المسائل الرياضية
• والكثير أكثر!

**فقط أرسل لي رسالتك وسأجيبك فوراً!** 💫"""

    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    logger.info(f"New user started: {update.effective_user.id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"Message from {user_id}: {user_message[:50]}...")
    
    # إنشاء محادثة جديدة للمستخدم إذا لم تكن موجودة
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])
        logger.info(f"Created new chat for user {user_id}")
    
    try:
        # إظهار "يكتب..." للمستخدم
        await update.message.chat.send_action('typing')
        
        # إرسال الرسالة إلى Gemini AI
        response = await user_chats[user_id].send_message_async(user_message)
        
        # إرسال الرد للمستخدم
        await update.message.reply_text(response.text)
        
        logger.info(f"Reply sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            "عذراً، حدث خطأ في المعالجة. 😔\nيرجى المحاولة مرة أخرى."
        )

async def conflict_resolver():
    """حل مشكلة الـ conflict من خلال حذف webhook وتنظيف التحديثات المعلقة"""
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        
        # حذف webhook إذا كان موجود
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔧 Webhook deleted and pending updates cleared")
        
        # الحصول على معلومات البوت للتأكد
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot ready: @{bot_info.username}")
        
    except Exception as e:
        logger.warning(f"⚠️ Conflict resolver warning: {e}")

async def async_main():
    """تشغيل البوت بشكل غير متزامن"""
    # حل مشاكل الـ conflict
    await conflict_resolver()
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل البوت
    logger.info("✅ Bot is running!")
    await application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'edited_message']
    )

def main():
    """تشغيل البوت"""
    # التحقق من وجود المفاتيح
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    if not GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY not found!")
        return
    
    logger.info("🚀 Starting Smart Chatbot...")
    
    # تشغيل البوت
    import asyncio
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("🛱 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
