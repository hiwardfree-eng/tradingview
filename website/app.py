import os, sys, time, json, threading, hashlib, urllib.parse, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from flask import Flask, render_template, jsonify, request, redirect, session, url_for, send_from_directory, make_response
from models import db, Log, init_db, Key
from config import BASE_DIR, DB_PATH, ADMIN_USER, DASH_PASSWORD, ENV, PORT, PUBLIC_BASE_URL, BOT_TOKEN, ADMIN_ID, BOT_ENABLED, SUPABASE_ENABLED, SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD, DATABASE_URL
import secrets, string

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tradingview.web")

app = Flask(__name__)
app.secret_key = os.environ.get("TV_WEB_SECRET", secrets.token_hex(32))

DB_URI = DATABASE_URL
if not DB_URI and SUPABASE_ENABLED and SUPABASE_DB_HOST:
    DB_URI = f"postgresql://{SUPABASE_DB_USER}:{urllib.parse.quote_plus(SUPABASE_DB_PASSWORD)}@{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}?sslmode=require"
DB_FALLBACK = "sqlite:///" + os.path.join(os.path.dirname(__file__), "tradingview.db")

def _setup_db(uri):
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600
    return uri

try:
    _setup_db(DB_URI or DB_FALLBACK)
    db.init_app(app)
    with app.app_context():
        init_db(app)
except Exception as e:
    log.warning(f"PostgreSQL failed ({e}), falling back to SQLite")
    app.extensions.pop('sqlalchemy', None)
    _setup_db(DB_FALLBACK)
    db.init_app(app)
    with app.app_context():
        init_db(app)

bot_thread_started = False
watchdog_enabled = True
_start_time = time.time()

def _gen_key(length=16):
    return "TV-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def _get_client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff: return xff.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"

def auth_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ─── API ────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    keys = Key.query.all()
    total = len(keys)
    active = sum(1 for k in keys if k.active)
    used = sum(1 for k in keys if k.used_count > 0)
    return jsonify({"total": total, "active": active, "used": used, "uptime": int(time.time() - _start_time)})

@app.route("/api/keys")
@auth_required
def api_keys():
    keys = Key.query.order_by(Key.id.desc()).all()
    return jsonify([{"code": k.code, "label": k.label, "active": k.active, "used": k.used_count, "created": k.created_at, "expires": k.expires_at, "notes": k.notes} for k in keys])

@app.route("/api/key/generate", methods=["POST"])
@auth_required
def api_key_generate():
    data = request.get_json(silent=True) or {}
    code = _gen_key()
    key = Key(code=code, label=data.get("label", ""), notes=data.get("notes", ""), expires_at=data.get("expires_at", 0))
    db.session.add(key)
    db.session.commit()
    db.session.add(Log(event="key_generated", detail=code))
    db.session.commit()
    return jsonify({"ok": True, "code": code})

@app.route("/api/key/toggle", methods=["POST"])
@auth_required
def api_key_toggle():
    code = (request.get_json(silent=True) or {}).get("code", "")
    key = Key.query.filter_by(code=code).first()
    if not key: return jsonify({"ok": False, "error": "not found"}), 404
    key.active = not key.active
    db.session.commit()
    return jsonify({"ok": True, "active": key.active})

@app.route("/api/key/delete", methods=["POST"])
@auth_required
def api_key_delete():
    code = (request.get_json(silent=True) or {}).get("code", "")
    key = Key.query.filter_by(code=code).first()
    if not key: return jsonify({"ok": False, "error": "not found"}), 404
    db.session.delete(key)
    db.session.commit()
    db.session.add(Log(event="key_deleted", detail=code))
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/verify-key", methods=["POST"])
def api_verify_key():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    key = Key.query.filter_by(code=code).first()
    if not key: return jsonify({"ok": False, "error": "invalid"}), 401
    if not key.active: return jsonify({"ok": False, "error": "disabled"}), 403
    key.used_count += 1
    key.last_used = time.time()
    db.session.commit()
    return jsonify({"ok": True, "label": key.label})

@app.route("/api/logs")
@auth_required
def api_logs():
    logs = Log.query.order_by(Log.id.desc()).limit(50).all()
    return jsonify([{"event": l.event, "detail": l.detail, "level": l.level, "time": l.timestamp} for l in logs])

@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "uptime": int(time.time() - _start_time), "keys": Key.query.count(), "platform": "tradingview"})

# ─── Auth ──────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user", "")
        pwd = request.form.get("pass", "")
        if user == ADMIN_USER and pwd == DASH_PASSWORD:
            session["logged_in"] = True
            session.permanent = True
            return redirect("/admin")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ─── Pages ─────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/admin")
@auth_required
def admin():
    return render_template("admin.html", base_url=PUBLIC_BASE_URL)

@app.route("/terminal")
def terminal():
    return render_template("terminal.html", base_url=PUBLIC_BASE_URL)

@app.route("/downloads")
def downloads():
    return render_template("downloads.html", base_url=PUBLIC_BASE_URL)

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), "assets"), filename)

# ─── Bot ───────────────────────────────────────────────

def ensure_bot():
    global bot_thread_started
    if bot_thread_started or not BOT_ENABLED or not BOT_TOKEN: return
    bot_thread_started = True
    t = threading.Thread(target=_run_bot, daemon=True)
    t.start()
    log.info("Bot started")

def _run_bot():
    import requests as req
    offset = 0
    while True:
        try:
            r = req.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            if r.ok:
                for u in r.json().get("result", []):
                    offset = u["update_id"] + 1
                    msg = u.get("message", {})
                    text = msg.get("text", "")
                    chat_id = msg.get("chat", {}).get("id", 0)
                    if text == "/start":
                        _bot_send(chat_id, "TradingView Terminal\n\nComandos:\n/start - Info\n/stats - Estadisticas\n/keys - Total de keys\n/health - Estado")
                    elif text == "/stats":
                        keys = Key.query.all()
                        total = len(keys); active = sum(1 for k in keys if k.active)
                        _bot_send(chat_id, f"Keys: {total} total, {active} activas")
                    elif text == "/keys":
                        _bot_send(chat_id, f"Keys totales: {Key.query.count()}")
                    elif text == "/health":
                        _bot_send(chat_id, f"OK | uptime: {int(time.time() - _start_time)}s | keys: {Key.query.count()}")
        except Exception as e:
            log.error(f"Bot error: {e}")
        time.sleep(1)

def _bot_send(chat_id, text):
    try:
        import requests as req
        req.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        log.error(f"Bot send error: {e}")

# ─── Startup ───────────────────────────────────────────

ensure_bot()

if __name__ == "__main__":
    cert_file = os.path.join(BASE_DIR, "ssl", "cert.pem")
    key_file = os.path.join(BASE_DIR, "ssl", "key.pem")
    use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)
    log.info(f"TradingView Web starting on :{PORT} {'HTTPS' if use_ssl else 'HTTP'}")
    app.run(host="0.0.0.0", port=PORT, ssl_context=(cert_file, key_file) if use_ssl else None, debug=(ENV == "development"))
