"""Bot konfiguratsiyasi - environment variables'dan o'qiydi."""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str = "") -> str:
    val = os.getenv(key, default)
    return val.strip() if val else default


# Telegram
BOT_TOKEN = _get("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in _get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# Webhook
WEBHOOK_HOST = _get("WEBHOOK_HOST")  # https://your-app.onrender.com
WEBHOOK_PATH = _get("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = _get("WEBHOOK_SECRET", "secret")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEB_SERVER_HOST = _get("WEB_SERVER_HOST", "0.0.0.0")
WEB_SERVER_PORT = int(_get("WEB_SERVER_PORT", "10000"))

# PostgreSQL (Render Internal Database)
DATABASE_URL = _get("DATABASE_URL")

# Gemini API kalitlari (rotatsiya uchun)
GEMINI_API_KEYS = [k.strip() for k in _get("GEMINI_API_KEYS", "").split(",") if k.strip()]
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.0-flash")

# Vaqt zonasi
TIMEZONE = _get("TIMEZONE", "Asia/Tashkent")

# Mavjud tillar
LANGUAGES = ["uz", "ru", "en"]
DEFAULT_LANGUAGE = "uz"


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
