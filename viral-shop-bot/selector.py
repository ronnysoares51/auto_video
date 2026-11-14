"""Seleção determinística de oportunidades com métricas verificáveis do feed autorizado."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def product_key(product):
    origin = str(product.get("product_url", "")).split("?")[0].rstrip("/")
    return hashlib.sha256((origin or str(product.get("name", ""))).encode()).hexdigest()[:16]


def rank(product):
    """Score heurístico; NÃO representa dados reais de venda se o feed não fornecer."""
    views = max(0, float(product.get("views") or 0))
    likes = max(0, float(product.get("likes") or 0))
    sales = max(0, float(product.get("sales") or 0))
    growth = max(0, float(product.get("growth_pct") or 0))
    engagement = likes / max(views, 1)
    # Uso de funções crescentes com retornos decrescentes.
    import math
    return round(
        2.0 * math.log1p(views)
        + 10.0 * min(engagement, 0.25)
        + 3.0 * math.log1p(sales)
        + 0.04 * min(growth, 500),
        2,
    )


def select(products, delivered, limit=3):
    eligible = []
    seen = set()
    for item in products:
        if not isinstance(item, dict):
            continue
        key = product_key(item)
        if key in seen or key in delivered:
            continue
        seen.add(key)
        if item.get("image_rights_confirmed") is not True or not item.get("image_urls"):
            continue
        url = urlparse(str(item.get("product_url", "")))
        if url.scheme != "https" or not url.hostname:
            continue
        eligible.append(item)
    return sorted(eligible, key=lambda x: (-rank(x), product_key(x)))[:limit]


def read_history(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Histórico inválido")
    return data


def record_delivery(path, delivered, product):
    delivered[product_key(product)] = {
        "date": datetime.now(timezone.utc).isoformat(),
        "name": str(product.get("name", ""))[:150],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(delivered, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
