from flask import Flask
import threading
import os
import sys
import time
import requests
import ccxt
import pandas as pd
import numpy as np

# --- 🌐 වෙබ් සර්වර් සැකසුම (Render එක වෙනුවෙන්) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Render එකෙන් Environment එකේ දෙන Port එක නැත්නම් 8080 පාවිච්චි කරයි
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# --- ⚙️ ටර්මිනල් කෝඩින්ග් සඳහා UTF-8 සෙටප් එක ---
sys.stdout.reconfigure(encoding='utf-8')

# --- 🔑 API සහ Telegram සැකසුම් ---
BYBIT_API_KEY = "2iWIcFsQp4SCxwGOy8"
BYBIT_SECRET_KEY = "SujfI2OohVJZKWReeISLTJL2pr2ZsshAIioS"
TELEGRAM_BOT_TOKEN = "8965234283:AAHZ0kV9anlm1URSm9e8AxTQ9P-UtOwnhT"
TELEGRAM_CHAT_ID = "1421079683"

# --- 📊 Futures Risk Management ---
TRADE_MARGIN_USDT = 10.0
LEVERAGE = 10

# ==========================================
# බොට්ගේ ප්‍රධාන ලූප් සහ ට්‍රේඩිං කෝඩ් එක මෙතනින් පහළට තියෙන්න දෙන්න
# ==========================================

if __name__ == "__main__":
    # වෙබ් සර්වර් එක බැක්ග්‍රাউন্ড එකෙන් ස්ටාර්ට් කරයි
    keep_alive()
    
    # ඔයාගේ බොට්ගේ ප්‍රධාන ලූප් එක මෙතැනින් වැඩ කරන්න පටන් ගනී
    print("Trading bot started successfully...")
    while True:
        try:
            # මෙතනට ඔයාගේ ලූප් කෝඩ් එක දාන්න
            time.sleep(15)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)