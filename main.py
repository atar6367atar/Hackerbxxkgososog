import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from manager import auto_install_and_run, stop_bot

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Manager aktif 🔥")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.endswith(".py"):
        await update.message.reply_text("Sadece .py gönder.")
        return

    file = await document.get_file()
    file_path = f"bots/{document.file_name}"
    await file.download_to_drive(file_path)

    await update.message.reply_text("Kurulum başlıyor...")

    bot_id, status = auto_install_and_run(file_path)

    await update.message.reply_text(f"ID: {bot_id}\nDurum: {status}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Bot ID gir.")
        return

    bot_id = context.args[0]
    result = stop_bot(bot_id)

    if result:
        await update.message.reply_text("Bot durduruldu.")
    else:
        await update.message.reply_text("Bot bulunamadı.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

app.run_polling()
