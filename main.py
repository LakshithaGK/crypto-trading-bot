from flask import Flask
import threading
import os
import sys
import time
import requests
import ccxt
import pandas as pd
import numpy as np

# --- 🌐 වෙබ් සර්වර් සැකසුම (Render Free Tier එක නිදාගැනීම වැළැක්වීමට) ---
app = Flask('')

@app.route('/')
def home():
    return "Crypto Scalping Bot is running 24/7 live!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --- ⚙️ ටර්මිනල් කෝඩින්ග් සඳහා UTF-8 සෙටප් එක ---
sys.stdout.reconfigure(encoding='utf-8')

# --- 🔑 API සහ Telegram සැකසුම් ---
BYBIT_API_KEY = "2iWIcFsQp4SCxwGOy8"
BYBIT_SECRET_KEY = "SujfI2OohVJZKWReeISLTJL2pr2ZsshAIioS"
TELEGRAM_BOT_TOKEN = "8965234283:AAHz0KpVqnjm1uBSm9e80xI0_9P-Ut0wnbI"
TELEGRAM_CHAT_ID = "8965234283"

# --- 📊 Futures Risk Management & Scalping Settings ---
TRADE_MARGIN_USDT = 10.0
LEVERAGE = 10

# Bybit এক্সচেන්ජ් එක සම්බන්ධ කිරීම (CCXT)
exchange = ccxt.bybit({
    'apiKey': BYBIT_API_KEY,
    'secret': BYBIT_SECRET_KEY,
    'options': {
        'defaultType': 'future',
    },
})

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ==========================================
# 🚀 ලෝකයේ සුපිරිම ස්කැල්පින් ස්ට්‍රැටජි ප්‍රධාන ලූප් එක
# ==========================================
def trading_bot_loop():
    print("🚀 Ultimate Scalping Trading Bot Loop Started Successfully...")
    send_telegram_message("🚀 *Crypto Scalping Bot Started 24/7 Live on Cloud!*")
    
    loop_count = 0
    while True:
        try:
            loop_count += 1
            print(f"🔄 Bot checking market data... Loop cycle: {loop_count}")
            
            # --- මෙතනට ඔයාගේ ස්ට්‍රැටජි කෝඩ් එක (Indicators, Market Analysis, Entry/Exit Logic) වැටේ ---
            
            # 10 තත්පරයකට වරක් ලූප් එක ක්‍රියාත්මක වේ
            time.sleep(10)
            
        except Exception as e:
            error_msg = f"⚠️ *Trade Error!*\n`{str(e)}`"
            print(error_msg)
            send_telegram_message(error_msg)
            time.sleep(10)

if __name__ == "__main__":
    # 1. බැග්‍රවුන්ඩ් එකෙන් වෙබ් සර්වර් එක ස්ටාර්ට් කරයි (UptimeRobot එකට රెస్පොන්ස් කිරීමට)
    keep_alive()
    print("🌐 Web server background thread started...")
    
    # 2. සුපිරි ට්‍රේඩිං බොට් ස්ට්‍රැටජි ලූප් එක වෙනම ත්‍රේඩ් එකක ක්‍රියාත්මක කරයි
    bot_thread = threading.Thread(target=trading_bot_loop)
    bot_thread.daemon = True
    bot_thread.start()
    
    # ප්‍රධාන ප්‍රෝග්‍රෑම් එක නතර නොවී අඛණ්ඩව පවත්වා ගැනීමට
    while True:
        time.sleep(1)