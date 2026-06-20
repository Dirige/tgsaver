import os
from pathlib import Path

# ==================== Telegram Bot ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ALLOWED_USERS = [
    int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()
]

# ==================== Telegram User Client (Pyrogram) ====================
TG_API_ID = int(os.getenv("TG_API_ID", "25214872"))
TG_API_HASH = os.getenv("TG_API_HASH", "c7ec932befac7b4babf1b01d590ec865")
TG_SESSION_STRING = os.getenv("TG_SESSION_STRING", "")

# ==================== Storage ====================
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "/vol1/1000/SSD/影视"))
TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp/tg-saver"))

# ==================== Proxy ====================
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PROXY_PORT", "6891"))
PROXY_SCHEME = os.getenv("PROXY_SCHEME", "socks5")

# ==================== Queue ====================
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))

# ==================== Categories ====================
CATEGORIES = ["电影", "电视剧", "动漫", "cosplay", "其他"]
CATEGORY_EMOJI = {
    "电影": "🎬",
    "电视剧": "📺",
    "动漫": "🎌",
    "cosplay": "🎭",
    "其他": "📁",
}
