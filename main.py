import os
import subprocess
import sys
import re
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

app_web = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except:
        return False

def extract_imports(code):
    imports = re.findall(r"^\s*import\s+(\w+)", code, re.MULTILINE)
    from_imports = re.findall(r"^\s*from\s+(\w+)", code, re.MULTILINE)
    return list(set(imports + from_imports))

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.endswith(".py"):
        await update.message.reply_text("Sadece .py dosyası gönder.")
        return

    file = await document.get_file()
    file_path = f"./{document.file_name}"
    await file.download_to_drive(file_path)

    await update.message.reply_text("Dosya alındı. Paketler kontrol ediliyor...")

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    packages = extract_imports(code)

    for package in packages:
        try:
            __import__(package)
        except ImportError:
            await update.message.reply_text(f"{package} indiriliyor...")
            install_package(package)

    await update.message.reply_text("Bot çalıştırılıyor...")
    subprocess.Popen([sys.executable, file_path])
    await update.message.reply_text("Bot başlatıldı.")

application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

@app_web.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.json, application.bot)
    await application.process_update(update)
    return "ok"

@app_web.route("/")
def home():
    return "Bot çalışıyor."

if __name__ == "__main__":
    import asyncio
    asyncio.run(application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}"))
    app_web.run(host="0.0.0.0", port=10000)
