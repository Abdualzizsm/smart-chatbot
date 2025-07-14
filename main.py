import asyncio
import logging
import os

from flask import Flask, request
from telegram import Update

from a2wsgi import WSGIMiddleware
from bot import application # Import the application instance from bot.py

# --- Basic Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

# --- Flask App (Webhook Endpoint) ---
_flask_app = Flask(__name__)

@_flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    """Webhook endpoint to receive updates from Telegram."""
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "OK", 200

# The final ASGI app that Gunicorn will run
app = WSGIMiddleware(_flask_app)

# --- Bot Initialization (The Correct Way) ---
async def initialize_bot():
    """This function runs once when the server starts."""
    if WEBHOOK_URL:
        logger.info("Initializing application...")
        await application.initialize()
        logger.info(f"Setting webhook to {WEBHOOK_URL}/{BOT_TOKEN}")
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
        logger.info("Bot setup complete.")
    else:
        logger.warning("WEBHOOK_URL not set. Bot is not fully configured for production.")

# Run the initialization function when the script is loaded
if __name__ != "__main__": # This ensures it runs on Gunicorn/Render
    asyncio.run(initialize_bot())
