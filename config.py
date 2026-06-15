import os

def _int_env(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None: return default
    try: return int(raw)
    except (ValueError, TypeError): return default

BASE_DIR = os.environ.get("TV_BASE_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("TV_DB_PATH", os.path.join(BASE_DIR, "keys.json"))
DATA_DIR = os.environ.get("TV_DATA_DIR", os.path.join(BASE_DIR, "data"))
LOG_DIR = os.environ.get("TV_LOG_DIR", os.path.join(BASE_DIR, "logs"))

BOT_TOKEN = os.environ.get("TV_BOT_TOKEN", "")
ADMIN_ID = _int_env("TV_ADMIN_ID", 0)
BOT_ENABLED = os.environ.get("TV_BOT_ENABLED", "1") == "1"
ADMIN_USER = os.environ.get("TV_ADMIN_USER", "admin")
DASH_PASSWORD = os.environ.get("TV_DASH_PASSWORD", "TradingView2024")
ENV = os.environ.get("TV_ENV", "production")
PORT = _int_env("TV_PORT", 8080)

PUBLIC_BASE_URL = os.environ.get("TV_PUBLIC_BASE_URL", "https://tradingview.onrender.com")
SUPABASE_ENABLED = os.environ.get("SUPABASE_ENABLED", "0") == "1"
SUPABASE_DB_HOST = os.environ.get("SUPABASE_DB_HOST", "")
SUPABASE_DB_PORT = _int_env("SUPABASE_DB_PORT", 6543)
SUPABASE_DB_NAME = os.environ.get("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.environ.get("SUPABASE_DB_USER", "postgres")
SUPABASE_DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD", "")
DATABASE_URL = os.environ.get("TV_DATABASE_URL", "")
