import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

BOT_TOKEN = '8349449129:AAGJBSWjpX-KikP3jxTaRK3F0a5Uv2CV5vw'  # Replace with your actual bot token
SHORTENED_LINK_URL = 'https://yourshort.link/example'  # Replace with your actual shortened link
DAILY_CODE = 'DAILYC0DE123'  # The daily code users get after completing the task

# Single Minecraft premium account to distribute daily; update this manually each day
current_minecraft_account = {'username': 'dailyuser@example.com', 'password': 'dailyPass123'}

user_claims = {}  # Tracks last claim time per user to limit 1 claim/24 hours


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Get Daily Code", url=SHORTENED_LINK_URL)],
        [InlineKeyboardButton("🔐 Enter Code", callback_data='enter_code')],
        [InlineKeyboardButton("♻️ Restart Session", callback_data='restart')]
    ])


def can_claim(user_id: int) -> bool:
    last_claim = user_claims.get(user_id)
    if last_claim is None:
        return True
    elapsed_seconds = (datetime.datetime.now() - last_claim).total_seconds()
    return elapsed_seconds > 86400  # 24 hours


async def send_and_track_message(update_or_query, context, text, reply_markup=None, parse_mode=None):
    if hasattr(update_or_query, 'message') and update_or_query.message:
        sent = await update_or_query.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    else:
        sent = await update_or_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    context.user_data.setdefault('bot_messages', []).append(sent.message_id)
    return sent


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['awaiting_code'] = False
    text = (
        "✨ *Welcome to Aura Alts*\n\n"
        "To claim your Minecraft premium account, just follow these steps:\n\n"
        "➤ Step 1: Click the [Get Daily Code]({}) button below and complete the short task.\n"
        "➤ Step 2: Receive your unique daily code.\n"
        "➤ Step 3: Click the Enter Code button below and submit your code to receive today's premium account.\n\n"
        "⚠️ You can claim only *one* account every 24 hours.\n\n"
        "Use the buttons below to get started!"
    ).format(SHORTENED_LINK_URL)
    await send_and_track_message(update, context, text, reply_markup=main_keyboard(), parse_mode='Markdown')


async def enter_code_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data['awaiting_code'] = True
    cancel_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data='cancel')]])
    text = (
        "⌨️ Please enter your daily code below and send it here.\n\n"
        "Or press Cancel to return to the main menu."
    )
    await update.callback_query.edit_message_text(text, reply_markup=cancel_keyboard, parse_mode='Markdown')


async def cancel_code_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data['awaiting_code'] = False
    await update.callback_query.edit_message_text(
        "⚪ Code entry cancelled.\n\nUse the buttons below to continue.",
        reply_markup=main_keyboard(),
        parse_mode='Markdown'
    )


async def handle_code_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_code', False):
        await update.message.reply_text("⚠️ Please press the 'Enter Code' button before submitting your code.")
        return

    user_code = update.message.text.strip()
    user_id = update.effective_user.id

    if user_code != DAILY_CODE:
        await update.message.reply_text("❌ Invalid code. Please check your code and try again.")
        return

    if not can_claim(user_id):
        await update.message.reply_text(
            "⏳ You have already claimed an account in the last 24 hours.\n"
            "Please come back later."
        )
        return

    account = current_minecraft_account
    user_claims[user_id] = datetime.datetime.now()
    context.user_data['awaiting_code'] = False

    text = (
        "🎉 *Congratulations!*\n\n"
        "Here is today's Minecraft premium account:\n"
        f"▫️ Username: `{account['username']}`\n"
        f"▫️ Password: `{account['password']}`\n\n"
        "🔒 Please keep it safe and do not share your account details.\n"
        "⚠️ Connect to a VPN before logging in to avoid issues.\n\n"
        "⏰ You may claim again after 24 hours."
    )
    await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode='Markdown')


async def restart_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id

    # Delete the restart session message to keep the chat clean
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

    await context.bot.send_message(
        chat_id=chat_id,
        text="♻️ *Session ended.* To start fresh, please send /start.",
        parse_mode='Markdown'
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(enter_code_prompt, pattern='enter_code'))
    app.add_handler(CallbackQueryHandler(cancel_code_entry, pattern='cancel'))
    app.add_handler(CallbackQueryHandler(restart_session, pattern='restart'))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_code_submission))
    app.run_polling()


if __name__ == '__main__':
    main()
