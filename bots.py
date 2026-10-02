import logging
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration settings
BOT_TOKEN = "8824812075:AAGX4PtZ-7_T6VuuAwLlQuQ4_tDRZ7nn71E"
DELETE_DELAY_SECONDS = 300  # Auto-delete delay in seconds (300 = 5 min)

# Regex pattern to match URLs / Links
URL_REGEX = re.compile(
    r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?)',
    re.IGNORECASE
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot active hai! Group mein message auto-delete aur link control chal raha hai.")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check karta hai ki message bhejne wala Admin/Owner hai ya nahi."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Private chat mein har user ko allow karein
    if update.effective_chat.type == "private":
        return True

    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ['administrator', 'creator']

async def delayed_delete(context: ContextTypes.DEFAULT_TYPE):
    """JobQueue function to delete original message after delay."""
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        logging.warning(f"Could not delete message {job.data}: {e}")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    text = update.message.text or update.message.caption or ""

    user_is_admin = await is_admin(update, context)

    # 1. Link Detection for Non-Admins
    if not user_is_admin and URL_REGEX.search(text):
        try:
            # Silent delete (koi notice ya reply nahi bhejega)
            await update.message.delete()
            return
        except Exception as e:
            logging.warning(f"Failed to delete link message: {e}")
            return

    # 2. Auto-Delete Scheduled Task (for all other messages)
    context.job_queue.run_once(
        delayed_delete,
        DELETE_DELAY_SECONDS,
        chat_id=chat_id,
        data=message_id
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_messages))

    # Run Bot
    application.run_polling()
