import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
STRING_SESSION = os.getenv("STRING_SESSION", "")
OWNER_ID = int(os.getenv("OWNER_ID") or "0")
DATABASE_URL = os.getenv("DATABASE_URL", "musicbot.db")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
FFMPEG_LOCATION = os.getenv("FFMPEG_LOCATION", "")
YTDLP_COOKIES_FILE = os.getenv("YTDLP_COOKIES_FILE", "")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
DEFAULT_VOLUME = int(os.getenv("DEFAULT_VOLUME", "100"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "50"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")
if not API_ID or not API_HASH:
    raise RuntimeError("API_ID/API_HASH are missing")
if not STRING_SESSION:
    raise RuntimeError("STRING_SESSION is missing")
