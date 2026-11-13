"""Bot Telegram privado para controlar a geração de vídeos e receber resultados.

Iniciar: python telegram_bot.py
Comandos: /start, /ajuda, /status, /gerar, /ultimos.
O bot só responde ao TELEGRAM_CHAT_ID e nunca habilita publicação no TikTok.
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"
DOWNLOADS = BASE_DIR / "downloads"
LOGS = BASE_DIR / "logs"
LOGS.mkdir(exist_ok=True)
_lock = threading.Lock()
_job = {"running": False, "started": 0.0, "result": "Nenhuma geração executada."}


def api_call(method, **kwargs):
    response = requests.post(f"{API}/{method}", timeout=65, **kwargs)
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram API error"))
    return result["result"]


def say(message):
    api_call("sendMessage", json={"chat_id": CHAT_ID, "text": message[:4000]})


def videos_since(since=0):
    return sorted(
        (p for p in DOWNLOADS.rglob("*.mp4") if p.is_file() and p.stat().st_mtime >= since),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def send_video(path):
    # Telegram Bot API cloud upload via sendVideo accepts files up to 50 MB.
    if path.stat().st_size > 50 * 1024 * 1024:
        say(f"Vídeo maior que 50 MB; disponível na VPS: {path.name}")
        return
    with path.open("rb") as stream:
        api_call(
            "sendVideo",
            data={"chat_id": CHAT_ID, "caption": f"🎬 Vídeo para revisar: {path.name}"[:1024]},
            files={"video": (path.name, stream, "video/mp4")},
        )


def generate():
    started = time.time()
    with _lock:
        _job.update(running=True, started=started, result="Geração em andamento.")
    try:
        say("🎬 Geração iniciada. A publicação no TikTok permanece desativada.")
        env = os.environ.copy()
        env["ENABLE_TIKTOK_PUBLISH"] = "false"
        env["LOOP_COUNT"] = "1"
        log_file = LOGS / "telegram_generation.log"
        with log_file.open("a", encoding="utf-8") as log:
            log.write(f"\n--- Nova geração: {time.ctime(started)} ---\n")
            process = subprocess.run(
                [sys.executable, str(BASE_DIR / "main.py")],
                cwd=str(BASE_DIR),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        files = videos_since(started - 2)
        if process.returncode != 0:
            result = f"⚠️ Processo terminou com código {process.returncode}. Consulte logs/telegram_generation.log."
            say(result)
        elif files:
            result = f"✅ Processo finalizado, {len(files)} vídeo(s) encontrado(s)."
            say(result)
            for file in ([] if CHANNEL_ID else files[:3]):
                try:
                    send_video(file)
                except Exception as exc:
                    say(f"Não consegui enviar {file.name}: {type(exc).__name__}. O arquivo continua na VPS.")
        else:
            result = "⚠️ Execução terminou, mas nenhum vídeo novo foi encontrado. Confira os logs."
            say(result)
        with _lock:
            _job["result"] = result
    except Exception as exc:
        with _lock:
            _job["result"] = f"Erro: {type(exc).__name__}"
        try:
            say(f"❌ Falha no bot: {type(exc).__name__}. Consulte o log.")
        except requests.RequestException:
            pass
    finally:
        with _lock:
            _job["running"] = False


def handle_command(message):
    chat = str(message.get("chat", {}).get("id", ""))
    if chat != CHAT_ID:
        return  # Ignore all unauthorized chats, including groups.
    text = (message.get("text") or "").strip().split(" ", 1)[0].split("@", 1)[0].lower()
    if text in ("/start", "/ajuda"):
        say("🤖 Auto Video Bot\n/gerar — produzir 1 vídeo para revisão\n/status — verificar execução\n/ultimos — receber até 3 vídeos recentes\n/ajuda — mostrar comandos\n\nTikTok não publica automaticamente.")
    elif text == "/status":
        with _lock:
            say(("🟡 Gerando vídeo. " if _job["running"] else "🟢 Sem tarefa em execução. ") + _job["result"])
    elif text == "/gerar":
        with _lock:
            busy = _job["running"]
            if not busy:
                _job["running"] = True
        if busy:
            say("Já existe uma geração em andamento.")
        else:
            threading.Thread(target=generate, daemon=True).start()
    elif text == "/ultimos":
        files = videos_since()
        if not files:
            say("Nenhum vídeo encontrado na pasta downloads.")
        else:
            for f in files[:3]:
                try:
                    send_video(f)
                except Exception:
                    say(f"Falha ao enviar: {f.name}")


def main():
    if not TOKEN or TOKEN.startswith("your_") or not CHAT_ID or CHAT_ID.startswith("your_"):
        raise SystemExit("Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no arquivo .env.")
    offset = None
    print("Bot Telegram iniciado. Apenas o chat autorizado pode executar comandos.")
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["message"]}
            if offset is not None:
                params["offset"] = offset
            response = requests.get(f"{API}/getUpdates", params=params, timeout=40)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise RuntimeError(data.get("description", "getUpdates failed"))
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                try:
                    handle_command(update.get("message", {}))
                except Exception as exc:
                    print(f"Erro processando comando: {type(exc).__name__}", flush=True)
        except (requests.RequestException, RuntimeError) as exc:
            print(f"Erro Telegram: {type(exc).__name__}. Tentando novamente.", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
