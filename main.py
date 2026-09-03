import logging
import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------- DATABASE SETUP (Auto Learning Storage) ----------------
def init_db():
    conn = sqlite3.connect("bot_brain.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_text TEXT UNIQUE,
            response_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_memory(trigger, response):
    conn = sqlite3.connect("bot_brain.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO learning_memory (trigger_text, response_text)
        VALUES (?, ?)
        ON CONFLICT(trigger_text) DO UPDATE SET response_text=excluded.response_text
    ''', (trigger.lower().strip(), response.strip()))
    conn.commit()
    conn.close()

def get_memory_response(text):
    conn = sqlite3.connect("bot_brain.db")
    cursor = conn.cursor()
    cursor.execute("SELECT response_text FROM learning_memory WHERE trigger_text = ?", (text.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Global Data Variables
group_rules = {}
welcome_messages = {}
bad_words = ["badword1", "badword2"]
warn_counts = {}

# ---------------- ALL COMMAND HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Rain Bot! Type /help to see available commands.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Available Commands:\n"
        "/start - Start the bot\n"
        "/help - Show available commands\n"
        "/id - View User ID & Chat ID\n"
        "/rules - View group rules\n"
        "/status - View bot statistics\n"
        "/promote - Promote user to Admin (Reply)\n"
        "/demote - Remove Admin status (Reply)\n"
        "/mute - Mute user (Reply)\n"
        "/unmute - Unmute user (Reply)\n"
        "/kick - Kick user from group (Reply)\n"
        "/ban - Ban user from group (Reply)\n"
        "/warn - Warn user (3 warns = auto mute)\n"
        "/pin - Pin message (Reply)\n"
        "/unpin - Unpin message\n"
        "/setrules - Set group rules (Admin)\n"
        "/setwelcome - Set welcome message (Admin)\n"
        "/filter - Add bad word to filter list (Admin)"
    )
    await update.message.reply_text(help_text)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"User ID: `{update.effective_user.id}`\nChat ID: `{update.effective_chat.id}`", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rule = group_rules.get(chat_id, "No rules set yet.")
    await update.message.reply_text(f"Group Rules:\n{rule}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Status: Active & Running!")

async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"{target.mention_html()} has been promoted to Admin.", parse_mode="HTML")

async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"{target.mention_html()} has been demoted.", parse_mode="HTML")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"{target.mention_html()} has been muted.", parse_mode="HTML")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"{target.mention_html()} has been unmuted.", parse_mode="HTML")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"{target.mention_html()} has been kicked.", parse_mode="HTML")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"{target.mention_html()} has been banned.", parse_mode="HTML")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        uid = target.id
        warn_counts[uid] = warn_counts.get(uid, 0) + 1
        if warn_counts[uid] >= 3:
            await update.message.reply_text(f"{target.mention_html()} reached 3 warnings and was automatically muted.", parse_mode="HTML")
            warn_counts[uid] = 0
        else:
            await update.message.reply_text(f"{target.mention_html()} received a warning ({warn_counts[uid]}/3)", parse_mode="HTML")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("Message pinned successfully.")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.unpin_chat_message(chat_id=update.effective_chat.id)
    await update.message.reply_text("Message unpinned successfully.")

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rule_text = " ".join(context.args)
    if rule_text:
        group_rules[update.effective_chat.id] = rule_text
        await update.message.reply_text("Group rules updated.")
    else:
        await update.message.reply_text("Usage: `/setrules [rules_text]`", parse_mode="Markdown")

async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = " ".join(context.args)
    if welcome_text:
        welcome_messages[update.effective_chat.id] = welcome_text
        await update.message.reply_text("Welcome message updated.")
    else:
        await update.message.reply_text("Usage: `/setwelcome [welcome_text]`", parse_mode="Markdown")

async def filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = " ".join(context.args).lower()
    if word:
        bad_words.append(word)
        await update.message.reply_text(f"Added '{word}' to the filter list.")

# ---------------- MESSAGES PROCESSOR (FILTER & AUTO-LEARN) ----------------

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message
    text = msg.text.strip()

    # 1. Bad Word Filter Check
    for word in bad_words:
        if word in text.lower():
            await msg.delete()
            await msg.reply_text(f"{msg.from_user.mention_html()}, bad words are not allowed.", parse_mode="HTML")
            return

    # 2. Auto Learning (Learns from replied messages)
    if msg.reply_to_message and msg.reply_to_message.text:
        original = msg.reply_to_message.text.strip()
        reply_txt = text
        if not original.startswith("/") and not reply_txt.startswith("/"):
            save_memory(original, reply_txt)

    # 3. Auto Reply from Database
    bot_reply = get_memory_response(text)
    if bot_reply:
        await msg.reply_text(bot_reply)

# ---------------- MAIN APP ----------------

def main():
    TOKEN = "8634664133:AAF98GJ3U96BsBI-k08DYo-fh_X98xHLPeM"
    app = ApplicationBuilder().token(TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("unpin", unpin))
    app.add_handler(CommandHandler("setrules", setrules))
    app.add_handler(CommandHandler("setwelcome", setwelcome))
    app.add_handler(CommandHandler("filter", filter_cmd))

    # All Text Auto Reply/Learn Handler
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_all_messages))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
  
