import logging
import os
from dotenv import load_dotenv
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. Setup ---
load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set!")

# --- 2. Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.mention_html()
    await update.message.reply_html(
        f"أهلاً بك {user_name} في بوت تحميل يوتيوب!\n\n"
        f"فقط أرسل لي أي رابط من يوتيوب وسأعطيك خيارات التحميل."
    )

async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    message = await update.message.reply_text("🔍 جاري تحليل الرابط، يرجى الانتظار...")
    try:
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        keyboard = []
        video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4']
        video_formats.sort(key=lambda f: f.get('height', 0), reverse=True)
        
        added_resolutions = set()
        for f in video_formats:
            height = f.get('height')
            if height and height not in added_resolutions:
                size_mb = f.get('filesize') or f.get('filesize_approx') or 0
                size_str = f" (~{size_mb / 1024 / 1024:.1f} MB)" if size_mb > 0 else ""
                keyboard.append([InlineKeyboardButton(f"📹 {height}p{size_str}", url=f['url'])])
                added_resolutions.add(height)
                if len(added_resolutions) >= 4: break
        
        audio_formats = [f for f in info.get('formats', []) if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and 'm4a' in f.get('ext', '')]
        if audio_formats:
            best_audio = max(audio_formats, key=lambda f: f.get('abr', 0))
            if best_audio.get('url'):
                keyboard.append([InlineKeyboardButton(f"🎵 صوت فقط ({best_audio.get('ext', 'm4a')})", url=best_audio['url'])])
        
        if not keyboard:
            await message.edit_text("❌ لم أتمكن من إيجاد أي صيغ تحميل مناسبة لهذا الرابط.")
            return
        
        await message.edit_text(
            f"🎬 *{info.get('title', 'فيديو بدون عنوان')}*\n\n👇 اختر الصيغة التي تريد تحميلها مباشرة:",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error processing link {url}: {e}")
        await message.edit_text("❌ حدث خطأ. يرجى التأكد من أن الرابط صحيح وأنه من يوتيوب.")

# --- 3. Main Application Setup (to be imported by main.py) ---
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))

# --- 4. For Local Testing ---
if __name__ == '__main__':
    logger.info("Starting bot in local polling mode...")
    application.run_polling()
