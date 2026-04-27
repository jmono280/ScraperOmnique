import logging
import logging.handlers
import os
import requests
from datetime import datetime
from config import ZAPIER_WEBHOOK_URL

# ── Logging a archivo + consola ───────────────────────────────────────────────

LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("omnique")
logger.setLevel(logging.DEBUG)

# Formato
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler: archivo rotativo (máx 5 MB, guarda 7 archivos)
file_handler = logging.handlers.RotatingFileHandler(
    f"{LOG_DIR}/omnique.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=7,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Handler: consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ── Notificaciones Zapier ─────────────────────────────────────────────────────

def notify_zapier(event: str, status: str, details: str = "", archivos: list = None):
    """
    Envía una notificación al webhook de Zapier.

    Parámetros:
        event   : nombre del evento (ej. "pipeline_start", "pipeline_success", "scraper_error")
        status  : "ok" | "error" | "info"
        details : mensaje descriptivo
        archivos: lista de archivos procesados (opcional)
    """
    if not ZAPIER_WEBHOOK_URL:
        return

    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "status": status,
        "details": details,
        "archivos": ", ".join(archivos) if archivos else "",
    }

    try:
        response = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.debug(f"Zapier notificado: {event} ({status})")
    except Exception as e:
        logger.warning(f"No se pudo notificar a Zapier: {e}")
