import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import dictionary
import pig_latin

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command: clear any user state and prompt for text."""
    context.user_data.clear()
    await update.message.reply_text(
        "Welcome! Send the text you want to encrypt; I'll ask next for the shift (integer)."
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Two-step flow:
    - If we are awaiting a shift, interpret the incoming message as the shift and perform encryption.
    - Otherwise, save the incoming text and request the shift from the user.
    """
    text = update.message.text.strip()
    user_data = context.user_data

    # If previous step asked for piglatin input, handle it first
    if user_data.get("awaiting_piglatin"):
        pending = text
        translated = pig_latin.translate_text(pending)
        logger.info(f"PigLatin '{pending}' -> '{translated}'")
        await update.message.reply_text(f"Pig Latin: {translated}")
        user_data.pop("awaiting_piglatin", None)
        return

    # If previous step asked for shift, this message should be the shift value
    if user_data.get("awaiting_shift"):
        try:
            shift = int(text)
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid integer for the shift (e.g. 3 or -2). Try again."
            )
            return

        pending_text = user_data.get("pending_text", "")
        encrypted = dictionary.caesar_encrypt(pending_text, shift)
        logger.info(f"Encrypted '{pending_text}' with shift {shift} -> '{encrypted}'")
        await update.message.reply_text(f"Encrypted: {encrypted}")

        # clear state
        user_data.pop("awaiting_shift", None)
        user_data.pop("pending_text", None)
        return

    # Otherwise treat this message as the text to encrypt and ask for shift
    user_data["pending_text"] = text
    user_data["awaiting_shift"] = True
    await update.message.reply_text(
        "Got your text. Now please send the shift (integer). Example: 3 or -2"
    )


async def piglatin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /piglatin. Usage:
    - /piglatin some text  -> translates immediately
    - /piglatin           -> bot asks for text and waits for user's next message
    """
    user_data = context.user_data
    # If user provided text with the command, translate immediately
    args = context.args
    if args:
        text = " ".join(args)
        translated = pig_latin.translate_text(text)
        await update.message.reply_text(f"Pig Latin: {translated}")
        return

    # Otherwise set state and ask for text
    user_data["awaiting_piglatin"] = True
    await update.message.reply_text("Send the text you want translated to Pig Latin.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any pending multi-step request (shift or piglatin)."""
    context.user_data.pop("awaiting_shift", None)
    context.user_data.pop("pending_text", None)
    context.user_data.pop("awaiting_piglatin", None)
    await update.message.reply_text("Cancelled.")


TELEGRAM_TOKEN = '8178415768:AAHzNHTBl_AUXupLr7RrFAhgEhhhfaEvRTI'
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("piglatin", piglatin_command))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

print("BOT IS RUNNING...")
app.run_polling()



