import os
import subprocess
import venv
import uuid
import re
import signal

BASE_DIR = "bots"
VENV_DIR = "venvs"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(VENV_DIR, exist_ok=True)

running_bots = {}

def extract_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    imports = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE)
    return list(set(imports))


def auto_install_and_run(py_path):
    bot_id = str(uuid.uuid4())

    venv_path = os.path.join(VENV_DIR, bot_id)
    venv.create(venv_path, with_pip=True)

    python_path = os.path.join(venv_path, "bin", "python")
    pip_path = os.path.join(venv_path, "bin", "pip")

    # importları yükle
    packages = extract_imports(py_path)

    for package in packages:
        try:
            subprocess.run(
                [pip_path, "install", package],
                timeout=20,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except:
            pass  # yüklenmeyeni atla

    # max 3 deneme
    for attempt in range(3):
        process = subprocess.Popen(
            [python_path, py_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            return bot_id, "Timeout oldu."

        # eksik paket yakala
        if "ModuleNotFoundError" in stderr:
            missing = re.findall(r"No module named '(.+?)'", stderr)
            if missing:
                try:
                    subprocess.run(
                        [pip_path, "install", missing[0]],
                        timeout=20
                    )
                    continue
                except:
                    continue

        # başka pip hatası varsa
        if "ImportError" in stderr:
            continue

        # hata yoksa çalıştırmaya devam
        running_bots[bot_id] = process.pid
        return bot_id, "Bot çalıştı."

    return bot_id, "3 denemede hata çözülemedi."


def stop_bot(bot_id):
    pid = running_bots.get(bot_id)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except:
            return False
    return False
