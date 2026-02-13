import os
import subprocess
import sys
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

# ---- Paket Kurma ----
def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except:
        pass

def extract_imports(code):
    imports = re.findall(r"^\s*import\s+(\w+)", code, re.MULTILINE)
    from_imports = re.findall(r"^\s*from\s+(\w+)", code, re.MULTILINE)
    return list(set(imports + from_imports))

# ---- Dosya Handler ----
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return

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
            await update.message.reply_text(f"{package} indiriliyor...")
            install_package(package)

    subprocess.Popen([sys.executable, file_path])
    await update.message.reply_text("Bot başlatıldı.")

# ---- Test Mesajı ----
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif.")

# ---- Application ----
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ---- Polling Başlat ----
if __name__ == "__main__":
    print("Bot polling ile başlatılıyor...")
    app.run_polling(drop_pending_updates=True)
