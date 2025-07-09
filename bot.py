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

async def conflict_resolver():
    """حل مشكلة الـ conflict من خلال حذف webhook وتنظيف التحديثات المعلقة"""
    try:
        from telegram import Bot
        import asyncio
        
        bot = Bot(token=BOT_TOKEN)
        
        # حذف webhook مع معالجة flood control
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("🔧 Webhook deleted and pending updates cleared")
        except Exception as webhook_error:
            if "flood control" in str(webhook_error).lower():
                logger.warning("⚠️ Flood control detected, waiting...")
                await asyncio.sleep(2)
            else:
                logger.warning(f"⚠️ Webhook deletion failed: {webhook_error}")
        
        # فاصل زمني قصير قبل التحقق
        await asyncio.sleep(1)
        
        # الحصول على معلومات البوت
        try:
            bot_info = await bot.get_me()
            logger.info(f"✅ Bot ready: @{bot_info.username}")
        except Exception as info_error:
            logger.warning(f"⚠️ Could not get bot info: {info_error}")
        
        # إغلاق البوت بهدوء
        try:
            await bot.close()
        except Exception as close_error:
            logger.warning(f"⚠️ Bot close warning: {close_error}")
        
    except Exception as e:
        logger.warning(f"⚠️ Conflict resolver failed: {e}")

async def async_main():
    """تشغيل البوت بطريقة async"""
    logger.info("🚀 Starting Simple Smart Chatbot...")
    
    # حل مشاكل الـ conflict
    try:
        await conflict_resolver()
    except Exception as resolver_error:
        logger.warning(f"⚠️ Conflict resolver failed: {resolver_error}")
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل البوت
    logger.info("✅ Bot is running with polling!")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # الانتظار بلا نهاية
    import signal
    import asyncio
    
    stop_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        logger.info("🚨 Received shutdown signal")
        stop_event.set()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        logger.info("🚨 Keyboard interrupt received")
    finally:
        logger.info("🚪 Shutting down...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def main():
    """نقطة الدخول الرئيسية"""
    import asyncio
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("🚪 Program terminated by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    main()
