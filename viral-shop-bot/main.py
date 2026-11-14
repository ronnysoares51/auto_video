"""Viral Shop Bot MVP: monta slideshow 9:16 com fotos reais autorizadas e entrega via Telegram.
Não minera TikTok/Shopee; precisa de feed de dados autorizado.
"""
import ipaddress
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps
from selector import select, product_key, rank, read_history, record_delivery

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
PRODUCTS = Path(os.getenv("PRODUCTS_JSON", "/app/data/products.json"))
OUTPUT = Path(os.getenv("OUTPUT_DIR", "/app/output"))
MAX_PRODUCTS = max(1, min(10, int(os.getenv("MAX_PRODUCTS", "3"))))
HISTORY = Path(os.getenv("HISTORY_JSON", "/app/output/history.json"))
SESSION = requests.Session()
SESSION.trust_env = False


def safe_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Imagens devem usar HTTPS sem credenciais")
    if parsed.port not in (None, 443):
        raise ValueError("Porta não permitida")
    host = parsed.hostname
    addresses = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    for addr in addresses:
        ip = ipaddress.ip_address(addr[4][0])
        if not ip.is_global:
            raise ValueError("Endereço privado, local ou reservado bloqueado")
    return url


def download_image(url, dest):
    safe_url(url)
    # Redirecionamentos são desativados; o IP resolvido também deve ser filtrado na camada de rede da VPS.
    with SESSION.get(url, timeout=(5, 20), allow_redirects=False, stream=True) as res:
        res.raise_for_status()
        if not res.headers.get("Content-Type", "").lower().startswith("image/"):
            raise ValueError("URL não retornou imagem")
        total = 0
        with open(dest, "wb") as out:
            for chunk in res.iter_content(65536):
                total += len(chunk)
                if total > 12_000_000:
                    raise ValueError("Imagem excede 12MB")
                out.write(chunk)
    with Image.open(dest) as image:
        image.verify()


def render_frame(source, dest):
    with Image.open(source) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((970, 1550))
        frame = Image.new("RGB", (1080, 1920), "#f6f6f6")
        frame.paste(im, ((1080-im.width)//2, (1920-im.height)//2))
        frame.save(dest)


def make_video(images, output):
    with tempfile.TemporaryDirectory() as temp:
        td = Path(temp)
        for idx, src in enumerate(images):
            render_frame(src, td / f"frame_{idx:03d}.png")
        # 15 segundos por vídeo, independentemente da quantidade de imagens.
        per = 15.0 / len(images)
        concat = td / "inputs.txt"
        lines = []
        for idx in range(len(images)):
            frame = td / f"frame_{idx:03d}.png"
            lines += [f"file '{frame}'", f"duration {per:.4f}"]
        lines.append(f"file '{td / ('frame_%03d.png' % (len(images)-1))}'")
        concat.write_text("\n".join(lines) + "\n")
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-safe", "0",
            "-f", "concat", "-i", str(concat), "-t", "15",
            "-r", "25", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-movflags",
            "+faststart", str(output)
        ], check=True, timeout=120)


def send_telegram(video, message):
    if not TOKEN or not CHAT:
        raise RuntimeError("Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID em .env")
    with open(video, "rb") as stream:
        resp = SESSION.post(
            f"https://api.telegram.org/bot{TOKEN}/sendVideo",
            data={"chat_id": CHAT, "caption": message[:1024], "supports_streaming": "true"},
            files={"video": (video.name, stream, "video/mp4")},
            timeout=180,
        )
    resp.raise_for_status()
    if not resp.json().get("ok"):
        raise RuntimeError("Telegram não confirmou entrega")


def main():
    if not TOKEN or not CHAT:
        raise RuntimeError("Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")
    items = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError("O feed deve ser uma lista JSON")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    delivered = read_history(HISTORY)
    candidates = select(items, delivered, limit=len(items))
    produced = 0
    for item in candidates:
        if produced >= MAX_PRODUCTS:
            break
        key = product_key(item)
        try:
            with tempfile.TemporaryDirectory() as temp:
                local = []
                for j, url in enumerate(item["image_urls"][:6]):
                    filepath = Path(temp) / f"img{j}.jpg"
                    download_image(url, filepath)
                    local.append(filepath)
                target = OUTPUT / f"video_{key}.mp4"
                make_video(local, target)
                message = (
                    f"{item['name']}\\n"
                    f"Score estimado: {rank(item)}\\n"
                    f"{item.get('caption', '')}\\n"
                    f"{item.get('product_url', '')}"
                )
                send_telegram(target, message)
                record_delivery(HISTORY, delivered, item)
                produced += 1
                print(f"Entregue: {target.name}", flush=True)
        except Exception as exc:
            print(f"Falha no produto {key}: {type(exc).__name__}: {exc}", flush=True)
    print(f"Total de vídeos enviados: {produced}", flush=True)


if __name__ == "__main__":
    main()
