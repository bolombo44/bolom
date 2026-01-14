import logging
import os
import json
import time
import random
import string
import requests

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

API_BASE_URL = "http://localhost:5000"
TOKEN = "7770017168:AAFQ8DUaoRcff3cSKQVf7qm1FfJOczpRIRg"

SITES_FILE = "sites.txt"
USERS_FILE = "users.json"
KEYS_FILE = "Keys.txt"

ADMIN_USERNAME = "rashunter44"

# ================= LOGGING =================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================= SITE SYSTEM =================

def load_sites():
    if os.path.exists(SITES_FILE):
        with open(SITES_FILE, "r") as f:
            return [s.strip() for s in f if s.strip()]
    return []

def save_sites(sites):
    with open(SITES_FILE, "w") as f:
        for s in sites:
            f.write(s + "\n")

def add_site(site):
    sites = load_sites()
    if site not in sites:
        sites.append(site)
        save_sites(sites)
        return True
    return False

def remove_site(site):
    sites = load_sites()
    if site in sites:
        sites.remove(site)
        save_sites(sites)
        return True
    return False

# ================= USER / PREMIUM =================

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user_status(user_id):
    users = load_users()
    user = users.get(str(user_id))

    if not user:
        return "Free"

    if user["status"] == "Premium" and time.time() > user["expires_at"]:
        users[str(user_id)] = {"status": "Free", "expires_at": None}
        save_users(users)
        return "Free"

    return user["status"]

def set_premium(user_id, days):
    users = load_users()
    users[str(user_id)] = {
        "status": "Premium",
        "expires_at": int(time.time() + days * 86400),
    }
    save_users(users)

# ================= KEY SYSTEM =================

def generate_keys():
    durations = [7, 14, 30]
    keys = set()

    while len(keys) < 8:
        key = (
            "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            + "-"
            + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        )
        keys.add(f"{key}|{random.choice(durations)}")

    with open(KEYS_FILE, "w") as f:
        for k in keys:
            f.write(k + "\n")

def load_keys():
    keys = {}
    if not os.path.exists(KEYS_FILE):
        return keys

    with open(KEYS_FILE, "r") as f:
        for line in f:
            if "|" in line:
                key, days = line.strip().split("|")
                keys[key] = int(days)
    return keys

# ================= HELPERS =================

def premium_only_message():
    return (
        "🚫 Premium Feature\n\n"
        "This command is for Premium users only.\n"
        f"Contact @{ADMIN_USERNAME} to upgrade."
    )

def format_cc_result(result):
    return (
        f"{result.get('status', 'UNKNOWN')} | "
        f"{result.get('cc', 'N/A')} | "
        f"{result.get('message', '')}"
    )

def is_admin(update: Update):
    return update.effective_user.username == ADMIN_USERNAME

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Welcome to BobbyCC Bot\n\n"
        "/sh cc|mm|yy|cvv → Single check (Free)\n"
        "/msh → Mass check (Premium)\n"
        "/mtxt → Mass file check (Premium)\n"
        "/redeem KEY\n"
        "/add site.com → Admin only\n"
        "/rm site.com → Admin only\n"
        "/info → Show user info"
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    sites = load_sites()
    users = load_users()

    user_data = users.get(str(user.id))
    status = get_user_status(user.id)

    expiry_text = "N/A"
    if user_data and user_data.get("expires_at"):
        expiry_text = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(user_data["expires_at"])
        )

    await update.message.reply_text(
        f"👤 User Info\n\n"
        f"🆔 User ID: {user.id}\n"
        f"👤 Username: @{user.username}\n"
        f"⭐ Status: {status}\n"
        f"⏳ Premium Expires: {expiry_text}\n"
        f"🌐 Registered Sites: {len(sites)}"
    )

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /redeem KEY")
        return

    keys = load_keys()
    key = context.args[0]

    if key not in keys:
        await update.message.reply_text("❌ Invalid or used key.")
        return

    set_premium(update.effective_user.id, keys[key])
    del keys[key]

    with open(KEYS_FILE, "w") as f:
        for k, d in keys.items():
            f.write(f"{k}|{d}\n")

    await update.message.reply_text("✅ Premium Activated!")

async def add_site_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /add site.com")
        return

    if add_site(context.args[0]):
        await update.message.reply_text("✅ Site added.")
    else:
        await update.message.reply_text("⚠️ Site already exists.")

async def rm_site_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /rm site.com")
        return

    if remove_site(context.args[0]):
        await update.message.reply_text("✅ Site removed.")
    else:
        await update.message.reply_text("❌ Site not found.")

async def single_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /sh cc|mm|yy|cvv")
        return

    sites = load_sites()
    if not sites:
        await update.message.reply_text("No Shopify sites added. Please use /add first.")
        return

    cc = context.args[0].split("|")
    payload = {
        "site_url": sites[0],
        "cc_number": cc[0],
        "exp_month": cc[1],
        "exp_year": cc[2],
        "cvv": cc[3],
    }

    r = requests.post(f"{API_BASE_URL}/check_cc", json=payload)
    await update.message.reply_text(format_cc_result(r.json()))

# ================= MASS CHECK FILE =================

async def mass_card_check_from_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if get_user_status(update.effective_user.id) != "Premium":
        await update.message.reply_text(premium_only_message())
        return

    if not update.message.document:
        await update.message.reply_text("❌ Upload a .txt file.")
        return

    file = await context.bot.get_file(update.message.document.file_id)
    content = (await file.download_as_bytearray()).decode(errors="ignore")

    cards = [c.strip() for c in content.replace(",", "\n").splitlines() if c.strip()]

    if len(cards) > 100:
        await update.message.reply_text("❌ Max 100 cards allowed.")
        return

    sites = load_sites()
    if not sites:
        await update.message.reply_text(
            "No Shopify sites added. Please use /add first."
        )
        return

    site_url = sites[0]

    await update.message.reply_text(
        f"🚀 Auto Shopify:\n"
        f"Mass Check Started from file! "
        f"Processing {len(cards)} cards on {site_url}..."
    )

    payload = {
        "site_url": site_url,
        "cards": cards,
        "proxies": []
    }

    response = requests.post(f"{API_BASE_URL}/mass_check_cc", json=payload)
    results = response.json()

    summary = (
        f"✅ Mass Check Complete! Processed {len(results)} cards.\n"
        f"\nLIVE: {sum(1 for r in results if r.get('status') == 'LIVE')}"
        f"\nDECLINED: {sum(1 for r in results if r.get('status') == 'DECLINED')}"
        f"\nAVS: {sum(1 for r in results if r.get('status') == 'AVS')}"
        f"\nCCN: {sum(1 for r in results if r.get('status') == 'CCN')}"
        f"\nDEAD: {sum(1 for r in results if r.get('status') == 'DEAD')}"
    )

    await update.message.reply_text(summary)

# ================= MAIN =================

def main():
    generate_keys()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("add", add_site_cmd))
    app.add_handler(CommandHandler("rm", rm_site_cmd))
    app.add_handler(CommandHandler("sh", single_check))
    app.add_handler(MessageHandler(filters.Document.TEXT, mass_card_check_from_file))

    app.run_polling()

if __name__ == "__main__":
    main()
