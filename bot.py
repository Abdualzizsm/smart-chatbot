import logging
import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from flask import Flask, request
from wsgi_adapter import WsgiToAsgi
from dotenv import load_dotenv
import yt_dlp

# --- Setup ---
load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", 8000))

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_html(
        f"أهلاً {update.effective_user.mention_html()}!\n\n"
        f"أرسل لي رابط يوتيوب لتحميله."
    )

async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles YouTube links, extracts formats, and shows download buttons."""
    url = update.message.text
    message = await update.message.reply_text("🔍 جاري تحليل الرابط...")

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        formats = info.get('formats', [])
        video_formats = []
        # Get best video and audio formats
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('height') in [1080, 720, 480, 360]:
                video_formats.append(f)
        
        # Sort by quality
        video_formats.sort(key=lambda f: f.get('height'), reverse=True)
        
        keyboard = []
        if video_formats:
            for f in video_formats[:3]: # Show top 3 qualities
                size_mb = f.get('filesize') or f.get('filesize_approx') or 0
                size_str = f" (~{size_mb/1024/1024:.1f} MB)" if size_mb > 0 else ""
                keyboard.append([InlineKeyboardButton(f"📹 {f['height']}p{size_str}", url=f['url'])])
        
        # Add audio option
        audio_format = info.get('audio_ext', 'm4a')
        keyboard.append([InlineKeyboardButton(f"🎵 صوت ({audio_format})", url=next(f['url'] for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none'))])

        if not keyboard:
            await message.edit_text("❌ لم أجد صيغ تحميل مناسبة.")
            return

        await message.edit_text(
            f"🎬 *{info['title']}*\n\n📥 اختر صيغة للتحميل المباشر:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error handling youtube link: {e}")
        await message.edit_text("❌ حدث خطأ أثناء معالجة الرابط. تأكد من أنه رابط يوتيوب صحيح.")

# --- Flask Webhook Server ---
# The WSGI app (Flask)
_flask_app = Flask(__name__)

# The ASGI app that Gunicorn will run
app = WsgiToAsgi(_flask_app)

@_flask_app.route("/")
def index():
    return "Bot is running!"

@_flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update_data = request.get_json()
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
    return 'ok', 200

# --- Main Application Logic ---
async def main():
    """Sets up the bot and the webhook."""
    global application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))

    # Set webhook
    if WEBHOOK_URL:
        try:
            await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
            logger.info(f"Webhook set to {WEBHOOK_URL}")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
    else:
        logger.info("WEBHOOK_URL not found, running in polling mode.")
        await application.run_polling()

# --- Bot Initialization ---
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set!")

# In production (on Render), Gunicorn runs the app. We just need to initialize the bot.
# The `main` function sets up the application and webhook.
if WEBHOOK_URL:
    asyncio.run(main())

# For local development, you can run this file directly:
if __name__ == "__main__" and not WEBHOOK_URL:
    logger.info("Running bot in polling mode for local development.")
    # The main() function will handle polling when WEBHOOK_URL is not set.
    asyncio.run(main())
