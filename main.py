import os
import json
import socket
import threading
import requests
import random
import string
import time
from datetime import datetime
from flask import Flask, send_file, jsonify, request
from flask_cors import CORS

# ════════════════════════════════════════════════
#   SOZLAMALAR
# ════════════════════════════════════════════════
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
ADMIN_TG_ID = os.environ.get("ADMIN_TG_ID", "7861699284")
GEMINI_KEY  = os.environ.get("GEMINI_KEY", "")
SERVER_PORT = int(os.environ.get("PORT", 5000))
# ════════════════════════════════════════════════

BASE   = os.path.dirname(os.path.abspath(__file__))
HTML   = os.path.join(BASE, "MathSolver_Complete.html")
DATA   = os.environ.get("DATA_PATH", os.path.join("/tmp", "storage.json"))
TG_URL = "https://api.telegram.org/bot" + BOT_TOKEN

# ── GROQ AI ──────────────────────────────────────
def ask_gemini(prompt, system="Siz matematik va umumiy bilim bo'yicha yordamchisiz. O'zbek tilida qisqa va aniq javob bering."):
    key = GEMINI_KEY
    # Serverdan ham olishga harakat
    raw = db_get("ms_ai_key")
    if raw and len(str(raw)) > 10:
        key = str(raw)
    if not key or key == "YOUR_GROQ_KEY_HERE":
        return None, (
            "❌ Groq API kalit sozlanmagan!\n\n"
            "Admin sifatida:\n"
            "/setkey gsk_... yuboring\n\n"
            "Kalit olish: console.groq.com → API Keys (BEPUL)"
        )
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            },
            timeout=20
        )
        if not r.ok:
            return None, "❌ Groq xatosi: " + str(r.status_code)
        data = r.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return text, None
    except Exception as e:
        return None, "❌ Xato: " + str(e)


app = Flask(__name__)
CORS(app)
lock = threading.Lock()


def load_db():
    if os.path.exists(DATA):
        try:
            with open(DATA, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_db(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


db = load_db()


def db_get(key):
    with lock:
        return db.get(key)


def db_set(key, value):
    with lock:
        db[key] = value
        save_db(db)


def db_del(key):
    with lock:
        db.pop(key, None)
        save_db(db)


# ── FLASK ───────────────────────────────────────
@app.route("/")
def index():
    if os.path.exists(HTML):
        return send_file(HTML)
    return "<h2>MathSolver_Complete.html topilmadi!</h2>", 404


@app.route("/api/get/<key>")
def api_get(key):
    value = db_get(key)
    # ms_ai_key yo'q bo'lsa env dan olish
    if key == "ms_ai_key" and not value:
        value = os.environ.get("GEMINI_KEY", "")
    # ms_admin_pass yo'q bo'lsa default
    if key == "ms_admin_pass" and not value:
        value = "asadbek"
    return jsonify({"value": value})


@app.route("/api/set", methods=["POST"])
def api_set():
    d = request.get_json()
    if d and "key" in d:
        db_set(d["key"], d.get("value", ""))
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 400


@app.route("/api/remove/<key>", methods=["DELETE"])
def api_remove(key):
    db_del(key)
    return jsonify({"ok": True})


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})


# ── YORDAMCHILAR ────────────────────────────────
def get_users():
    raw = db_get("ms_users")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {}


def set_users(u):
    db_set("ms_users", json.dumps(u))


def get_codes():
    raw = db_get("ms_pyramid_codes")
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            pass
    return []


def set_codes(c):
    db_set("ms_pyramid_codes", json.dumps(c))


def is_admin(chat_id):
    if str(chat_id) == str(ADMIN_TG_ID):
        return True
    uid = "tg_" + str(chat_id)
    return get_users().get(uid, {}).get("isAdmin", False)


# ── TELEGRAM ────────────────────────────────────
def tg(method, data):
    try:
        r = requests.post(TG_URL + "/" + method, json=data, timeout=10)
        return r.json()
    except Exception as e:
        print("TG xato:", e)
        return {}


def send(cid, text, kb=None):
    d = {"chat_id": cid, "text": text, "parse_mode": "HTML"}
    if kb:
        d["reply_markup"] = json.dumps(kb)
    tg("sendMessage", d)


def edit(cid, mid, text, kb=None):
    d = {"chat_id": cid, "message_id": mid, "text": text, "parse_mode": "HTML"}
    if kb:
        d["reply_markup"] = json.dumps(kb)
    tg("editMessageText", d)


def answer(cid, txt=""):
    tg("answerCallbackQuery", {"callback_query_id": cid, "text": txt})


def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "localhost"


def kb_main(admin=False):
    # Render manzilini env dan olish, bo'lmasa local IP
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if render_url:
        url = render_url
    else:
        ip = get_ip()
        url = "http://" + ip + ":" + str(SERVER_PORT)

    rows = [
        [{"text": "🌐 Ilovani ochish", "url": url}],
        [{"text": "📊 Statistika", "callback_data": "stats"},
         {"text": "🔑 Pirami kod", "callback_data": "activate"}],
        [{"text": "❓ Yordam", "callback_data": "help"}],
    ]
    if admin:
        rows.append([{"text": "⚙️ Admin panel", "callback_data": "admin"}])
    return {"inline_keyboard": rows}


def kb_admin():
    return {"inline_keyboard": [
        [{"text": "Foydalanuvchilar", "callback_data": "adm_users"},
         {"text": "Kodlar", "callback_data": "adm_codes"}],
        [{"text": "Kod yaratish", "callback_data": "adm_create"},
         {"text": "Ellon", "callback_data": "adm_announce"}],
        [{"text": "AI limitni reset", "callback_data": "adm_reset"}],
        [{"text": "Orqaga", "callback_data": "main"}],
    ]}


def kb_back(to="main"):
    return {"inline_keyboard": [[{"text": "Orqaga", "callback_data": to}]]}

def kb_ai_actions():
    return {"inline_keyboard": [
        [{"text": "🔄 Yana so'ra", "callback_data": "ai_again"},
         {"text": "🏠 Menyu", "callback_data": "main"}]
    ]}

def checkAiLimitBot(cid):
    uid = "tg_" + str(cid)
    users = get_users()
    u = users.get(uid, {})
    if u.get("aiUnlimited"):
        return True
    used = u.get("aiUsed", 0)
    if used >= 20:
        send(cid,
            "❌ AI limitingiz tugadi! (20/20)\n\n"
            "Davom etish uchun Pirami kod kiriting:",
            {"inline_keyboard": [[{"text": "🔑 Kod faollashtirish", "callback_data": "activate"}]]}
        )
        return False
    return True

def useAiCountBot(cid):
    uid = "tg_" + str(cid)
    users = get_users()
    if uid not in users:
        users[uid] = {"id": uid, "aiUsed": 0, "isAdmin": False}
    users[uid]["aiUsed"] = users[uid].get("aiUsed", 0) + 1
    set_users(users)


states = {}


def do_start(cid, tg_user):
    name = tg_user.get("first_name", "Foydalanuvchi")
    uid  = "tg_" + str(cid)
    adm  = is_admin(cid)
    users = get_users()
    now   = datetime.now().isoformat()
    if uid not in users:
        users[uid] = {
            "id": uid, "name": name, "tgId": str(cid),
            "aiUsed": 0, "isAdmin": adm, "aiUnlimited": adm,
            "joinDate": now, "lastSeen": now
        }
    else:
        users[uid]["lastSeen"] = now
        users[uid]["name"]     = name
    set_users(users)
    txt = (
        "Salom, <b>" + name + "</b>!\n\n"
        "MathSolver Pro ga xush kelibsiz!\n\n"
        "🤖 Menga istalgan savol yuboring — AI javob beradi!\n"
        "📱 Ilovani ochish uchun tugmani bosing.\n"
        "🔑 Pirami kod orqali cheksiz AI oling.\n\n"
        + ("👑 Admin huquqlari faol." if adm else "⚡ AI limit: 20 ta savol.")
    )
    send(cid, txt, kb_main(adm))


def do_stats(cid, mid):
    uid   = "tg_" + str(cid)
    u     = get_users().get(uid, {})
    codes = get_codes()
    used  = u.get("aiUsed", 0)
    unl   = u.get("aiUnlimited", False)
    left  = "Cheksiz" if unl else str(max(0, 20 - used)) + " ta"
    faol  = len([c for c in codes if not c.get("used")])
    txt = (
        "<b>Statistika</b>\n\n"
        "Ism: <b>" + u.get("name", "?") + "</b>\n"
        "AI ishlatildi: <b>" + str(used) + " ta</b>\n"
        "Qolgan: <b>" + left + "</b>\n"
        "Qoshilgan: <b>" + u.get("joinDate", "?")[:10] + "</b>\n\n"
        "Jami: " + str(len(get_users())) + " user | " + str(faol) + " faol kod"
    )
    edit(cid, mid, txt, kb_back())


def do_activate_prompt(cid, mid=None):
    states[cid] = "code"
    txt = "<b>Pirami kodni kiriting:</b>\n\nFormat: <code>MATH-XXXX-XX</code>"
    if mid:
        edit(cid, mid, txt, kb_back())
    else:
        send(cid, txt, kb_back())


def do_activate(cid, code_text):
    code  = code_text.strip().upper()
    codes = get_codes()
    users = get_users()
    uid   = "tg_" + str(cid)
    idx   = None
    for i, c in enumerate(codes):
        if c.get("code") == code:
            idx = i
            break
    if idx is None:
        send(cid, "Kod topilmadi!")
        return
    if codes[idx].get("used"):
        send(cid, "Bu kod allaqachon ishlatilgan!")
        return
    codes[idx]["used"]   = True
    codes[idx]["usedBy"] = uid
    codes[idx]["usedAt"] = datetime.now().isoformat()
    set_codes(codes)
    if uid not in users:
        users[uid] = {"id": uid, "aiUsed": 0, "isAdmin": False}
    users[uid]["aiUnlimited"] = True
    set_users(users)
    send(cid, "Kod faollashtirildi!\nEndi sizda <b>cheksiz AI</b> bor!\nIlovani yangilang.")


def do_help(cid, mid):
    txt = (
        "<b>Yordam</b>\n\n"
        "Ilovani ochish - MathSolver Pro\n"
        "Statistika - AI limitingiz\n"
        "Pirami kod - Cheksiz AI\n\n"
        "<b>Ilovada:</b>\n"
        "Tenglamalar, Grafik, Geometriya\n"
        "AI bilan masala yechish\n"
        "Rasmdan masala o'qish\n"
        "4 kishilik Duel oyini"
    )
    edit(cid, mid, txt, kb_back())


def do_admin(cid, mid):
    if not is_admin(cid):
        return
    users = get_users()
    codes = get_codes()
    faol  = len([c for c in codes if not c.get("used")])
    ish   = len([c for c in codes if c.get("used")])
    txt = (
        "<b>Admin panel</b>\n\n"
        "Foydalanuvchilar: <b>" + str(len(users)) + "</b>\n"
        "Faol kodlar: <b>" + str(faol) + "</b>\n"
        "Ishlatilgan: <b>" + str(ish) + "</b>"
    )
    edit(cid, mid, txt, kb_admin())


def do_adm_users(cid, mid):
    if not is_admin(cid):
        return
    users = get_users()
    if not users:
        edit(cid, mid, "Foydalanuvchilar yoq", kb_back("admin"))
        return
    lines = ["<b>Foydalanuvchilar:</b>\n"]
    for uid, u in list(users.items())[:20]:
        ai    = "Cheksiz" if u.get("aiUnlimited") else str(u.get("aiUsed", 0)) + "/20"
        badge = " (Admin)" if u.get("isAdmin") else ""
        lines.append("- " + u.get("name", "?") + badge + " | AI: " + ai)
    if len(users) > 20:
        lines.append("\n... yana " + str(len(users) - 20) + " ta")
    edit(cid, mid, "\n".join(lines), kb_back("admin"))


def do_adm_codes(cid, mid):
    if not is_admin(cid):
        return
    codes = get_codes()
    if not codes:
        edit(cid, mid, "Kodlar yoq", kb_back("admin"))
        return
    lines = ["<b>Kodlar (oxirgi 15):</b>\n"]
    for c in codes[-15:]:
        st = "ishlatildi" if c.get("used") else "faol"
        lines.append("<code>" + c.get("code", "?") + "</code> - " + st)
    edit(cid, mid, "\n".join(lines), kb_back("admin"))


def do_adm_create_prompt(cid, mid):
    if not is_admin(cid):
        return
    states[cid] = "create_code"
    edit(cid, mid, "Nechta kod yaratish? (1-20 son yuboring):", kb_back("admin"))


def do_adm_create(cid, qty_text):
    try:
        qty = max(1, min(20, int(qty_text.strip())))
    except Exception:
        send(cid, "Son kiriting (1-20)")
        return
    codes = get_codes()
    new_list = []
    for _ in range(qty):
        p1   = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        p2   = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
        code = "MATH-" + p1 + "-" + p2
        codes.append({"code": code, "used": False, "created": datetime.now().isoformat()})
        new_list.append(code)
    set_codes(codes)
    lines = [str(qty) + " ta kod yaratildi:\n"]
    for c in new_list:
        lines.append("<code>" + c + "</code>")
    send(cid, "\n".join(lines), kb_admin())


def do_adm_announce_prompt(cid, mid):
    if not is_admin(cid):
        return
    states[cid] = "announce"
    edit(cid, mid,
         "<b>Ellon matnini yuboring:</b>\n\nIlovada banner sifatida korinadi.",
         kb_back("admin"))


def do_adm_announce(cid, text):
    platform = db_get("ms_platform") or {}
    if isinstance(platform, str):
        try:
            platform = json.loads(platform)
        except Exception:
            platform = {}
    platform["announce"]   = text
    platform["announceId"] = int(datetime.now().timestamp())
    db_set("ms_platform", json.dumps(platform))
    send(cid, "Ellon joylashtirildi!\n\n<i>" + text + "</i>", kb_admin())


def do_adm_reset(cid, mid):
    if not is_admin(cid):
        return
    users = get_users()
    for uid in users:
        users[uid]["aiUsed"]      = 0
        users[uid]["aiUnlimited"] = users[uid].get("isAdmin", False)
    set_users(users)
    edit(cid, mid, str(len(users)) + " ta foydalanuvchi reset qilindi!", kb_back("admin"))


def process(update):
    try:
        if "message" in update:
            msg   = update["message"]
            cid   = msg["chat"]["id"]
            tgu   = msg.get("from", {})
            text  = msg.get("text", "")
            state = states.get(cid)

            if state == "code" and text and not text.startswith("/"):
                states.pop(cid, None)
                do_activate(cid, text)
                return
            if state == "create_code" and text and not text.startswith("/"):
                states.pop(cid, None)
                do_adm_create(cid, text)
                return
            if state == "announce" and text and not text.startswith("/"):
                states.pop(cid, None)
                do_adm_announce(cid, text)
                return

            if text == "/start":
                do_start(cid, tgu)
            elif text == "/admin" and is_admin(cid):
                send(cid, "Admin panel:", kb_admin())
            elif text and text.startswith("/setkey") and is_admin(cid):
                # Admin Groq kalitni o'rnatishi
                parts = text.split(" ", 1)
                if len(parts) == 2 and len(parts[1]) > 10:
                    db_set("ms_ai_key", parts[1].strip())
                    send(cid, "✅ Groq API kalit saqlandi!")
                else:
                    send(cid, "Format: /setkey AIzaSy...")
            elif text and not text.startswith("/") and not state:
                # AI chat — har qanday xabar AI ga yuboriladi
                if not checkAiLimitBot(cid):
                    return
                send(cid, "⏳ AI javob yozmoqda...")
                reply, err = ask_gemini(text)
                if err:
                    send(cid, err)
                else:
                    useAiCountBot(cid)
                    send(cid, "🤖 " + reply, kb_ai_actions())

        elif "callback_query" in update:
            cb   = update["callback_query"]
            cid  = cb["from"]["id"]
            mid  = cb["message"]["message_id"]
            data = cb.get("data", "")
            answer(cb["id"])
            adm  = is_admin(cid)

            acts = {
                "stats":    lambda: do_stats(cid, mid),
                "activate": lambda: do_activate_prompt(cid, mid),
                "help":     lambda: do_help(cid, mid),
                "main":     lambda: edit(cid, mid, "Asosiy menyu:", kb_main(adm)),
                "ai_again": lambda: edit(cid, mid, "💬 Savolingizni yuboring:", kb_back()),
            }
            adm_acts = {
                "admin":        lambda: do_admin(cid, mid),
                "adm_users":    lambda: do_adm_users(cid, mid),
                "adm_codes":    lambda: do_adm_codes(cid, mid),
                "adm_create":   lambda: do_adm_create_prompt(cid, mid),
                "adm_announce": lambda: do_adm_announce_prompt(cid, mid),
                "adm_reset":    lambda: do_adm_reset(cid, mid),
            }
            if data in acts:
                acts[data]()
            elif data in adm_acts and adm:
                adm_acts[data]()
    except Exception as e:
        print("Process xato:", e)


def self_ping():
    """Render uxlab qolmasin — har 14 daqiqada o'zini ping qiladi"""
    time.sleep(60)  # Ishga tushgandan 1 daqiqa keyin boshlaydi
    while True:
        try:
            port = os.environ.get("PORT", "10000")
            requests.get("http://localhost:" + port + "/ping", timeout=5)
            print("  Self-ping: OK")
        except Exception:
            pass
        time.sleep(14 * 60)  # 14 daqiqada bir

def bot_polling():
    print("  Bot: polling boshlandi...")
    offset = 0
    while True:
        try:
            r = requests.get(TG_URL + "/getUpdates", params={
                "offset": offset, "timeout": 30,
                "allowed_updates": ["message", "callback_query"]
            }, timeout=35)
            if r.status_code != 200:
                time.sleep(2)
                continue
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                threading.Thread(target=process, args=(upd,)).start()
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            print("Polling xato:", e)
            time.sleep(3)


if __name__ == "__main__":
    ip = get_ip()
    print("=" * 46)
    print("  MathSolver Pro - Server + Bot")
    print("=" * 46)
    print("  Localhost:  http://localhost:" + str(SERVER_PORT))
    print("  Tarmoq IP:  http://" + ip + ":" + str(SERVER_PORT))
    print("  HTML:  " + ("OK" if os.path.exists(HTML) else "TOPILMADI!"))
    print()

    try:
        r = requests.get(TG_URL + "/getMe", timeout=5).json()
        uname = r.get("result", {}).get("username", "?")
        print("  Bot: @" + uname + " — ULANDI")
        threading.Thread(target=bot_polling, daemon=True).start()
    except Exception:
        print("  Bot: TOKEN NOTOGRI yoki internet yoq!")

    threading.Thread(target=self_ping, daemon=True).start()
    print("  Self-ping: YOQILDI (har 14 daqiqa)")
    print("=" * 46)
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False,
            threaded=True, use_reloader=False)

# Gunicorn uchun — modul yuklanganida bot ishga tushadi
else:
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        try:
            threading.Thread(target=bot_polling, daemon=True).start()
            print("  Bot: polling thread ishga tushdi (gunicorn)")
        except Exception as e:
            print("  Bot thread xato:", e)
    # Self-ping — Render uxlab qolmasin
    try:
        threading.Thread(target=self_ping, daemon=True).start()
        print("  Self-ping: YOQILDI (har 14 daqiqa)")
    except Exception as e:
        print("  Self-ping xato:", e)
