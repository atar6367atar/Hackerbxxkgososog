import os
import subprocess
import sys
import re
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

app_web = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except:
        pass

def extract_imports(code):
    imports = re.findall(r"^\s*import\s+(\w+)", code, re.MULTILINE)
    from_imports = re.findall(r"^\s*from\s+(\w+)", code, re.MULTILINE)
    return list(set(imports + from_imports))

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.endswith(".py"):
        await update.message.reply_text("Sadece .py gönder.")
        return

    file = await document.get_file()
    file_path = document.file_name
    await file.download_to_drive(file_path)

    await update.message.reply_text("Paketler kontrol ediliyor...")

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    packages = extract_imports(code)

    for package in packages:
        try:
            __import__(package)
        except ImportError:
            install_package(package)

    subprocess.Popen([sys.executable, file_path])
    await update.message.reply_text("Bot başlatıldı.")

application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

@app_web.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "ok"

@app_web.route("/")
def home():
    return "Bot çalışıyor"

if __name__ == "__main__":
    asyncio.run(application.bot.set_webhook(f"{RENDER_URL}/{TOKEN}"))
    app_web.run(host="0.0.0.0", port=10000)
