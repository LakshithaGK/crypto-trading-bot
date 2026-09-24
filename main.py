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

# --- 🔑 API සහ Telegram සැකසුම් (ඔයාගේ ඒවා මෙතැනට දාන්න) ---
BYBIT_API_KEY = "2iWIcFsQp4SCxwGOy8"
BYBIT_SECRET_KEY = "SujfI2OohVJZKWReeISLTJL2pr2ZsshAIioS"
TELEGRAM_BOT_TOKEN = "8965234283:AAHz0KpVqnjm1uBSm9e80xI0_9P-Ut0wnbI"
TELEGRAM_CHAT_ID = "1421079683"

# --- 📊 Futures Risk Management & Scalping Settings ---
SYMBOL = 'BTC/USDT:USDT'  # ස්කැල්ප් කරන ක්‍රිප්ටෝ යුගලය
TIMEFRAME = '1m'          # ස්කැල්පින් සඳහා 1 မိနစ် හෝ 5 မိနစ် ටයිම්ෆ්‍රේම් එක
TRADE_MARGIN_USDT = 10.0  # එක් ට්‍රේඩ් එකකට පාවිච්චි කරන මාජින් එක ($)
LEVERAGE = 10             # ලෙවරේජ් එක

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

def set_leverage():
    try:
        exchange.set_leverage(LEVERAGE, SYMBOL)
    except Exception as e:
        print(f"Leverage Error (Already set or ignored): {e}")

# ==========================================
# 📈 ቴክනිකල් ඇනලයිසිස් සහ ස්කැල්පින් ලොජික් එක
# ==========================================
def calculate_indicators(df):
    # උදාහරණයක් ලෙස EMA (Exponential Moving Average) සහ RSI ගණනය කිරීම
    df['EMA_Fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_Slow'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # RSI ගණනය කිරීම
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def check_market_and_trade():
    try:
        # 1. මාකට් කෑන්ඩ්ල් ඩේටා ලබා ගැනීම
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 2. ඉන්ඩිකේටර්ස් ඇඩ් කිරීම
        df = calculate_indicators(df)
        
        current_price = df['close'].iloc[-1]
        fast_ema = df['EMA_Fast'].iloc[-1]
        slow_ema = df['EMA_Slow'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        print(f"📊 Price: {current_price} | RSI: {rsi:.2f}")

        # 3. දැනට ඕපන් වෙච්ච පොසිෂන්ස් තියෙනවද බැලීම (At a time එක ට්‍රේඩ් එකයි පාලනය කිරීමට)
        positions = exchange.fetch_positions([SYMBOL])
        active_position = False
        for pos in positions:
            if float(pos['contracts']) > 0:
                active_position = True
                break

        # දැනට ට්‍රේඩ් එකක් ඕපන් නැත්නම් පමණක් ඇන්ට්‍රි කන්ඩිෂන් චෙක් කරයි
        if not active_position:
            # 🚀 BUY / LONG KONDISHN (උදාහරණයක් ලෙස Fast EMA Slow EMA එකට උඩින් යද්දී සහ RSI Oversold මට්ටමෙන් ඉහළට එද්දී)
            if fast_ema > slow_ema and rsi < 40:
                print("🟢 Buy signal detected! Executing LONG order...")
                
                # බැලන්ස් එක ප්‍රමාණවත්දැයි පරීක්ෂා කිරීම
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    # Bybit එකේ Market Order එකක් දැමීම
                    order = exchange.create_market_buy_order(SYMBOL, amount)
                    
                    msg = (
                        f"🐋 *ULTIMATE WHALE ENTRY (FUTURES)* 🐋\n\n"
                        f"🟢 දිශාව: **BUY (LONG)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"📈 RSI: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ Long order executed successfully!")
                else:
                    print("⚠️ Available balance not enough for new order!")

            # 🔻 SELL / SHORT KONDISHN
            elif fast_ema < slow_ema and rsi > 60:
                print("🔴 Sell signal detected! Executing SHORT order...")
                
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    order = exchange.create_market_sell_order(SYMBOL, amount)
                    
                    msg = (
                        f"🐋 *ULTIMATE WHALE ENTRY (FUTURES)* 🐋\n\n"
                        f"🔴 දිශාව: **SELL (SHORT)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"📉 RSI: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ Short order executed successfully!")
                else:
                    print("⚠️ Available balance not enough for new order!")

    except Exception as e:
        error_msg = f"⚠️ *Trade Error!*\n`{str(e)}`"
        print(error_msg)
        # නිතරම එරර් මැසේජ් ටෙලිග්‍රෑම් එකට ගිහින් ස්පෑම් නොවීමට අවශ්‍ය නම් පහත ලයින් එක කමෙන්ට් කරන්න පුළුවන්
        # send_telegram_message(error_msg)

# ==========================================
# 🚀 ප්‍රධාන බොට් ලූප් එක
# ==========================================
def trading_bot_loop():
    print("🚀 Ultimate Scalping Trading Bot Loop Started Successfully...")
    send_telegram_message("🚀 *Crypto Scalping Bot Started 24/7 Live on Cloud!*")
    
    while True:
        try:
            check_market_and_trade()
            # ස්කැල්පින් සඳහා තත්පර 15කට වරක් මාකට් එක පරික්ෂා කරයි
            time.sleep(15)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(15)

if __name__ == "__main__":
    # 1. වෙබ් සර්වර් එක බැක්ග්‍රাউন্ড එකෙන් ස්ටාර්ට් කරයි
    keep_alive()
    print("🌐 Web server background thread started...")
    
    # 2. ට්‍රේඩිං බොට් ස්ට්‍රැටජි ලූප් එක වෙනම ත්‍රේඩ් එකක ක්‍රියාත්මක කරයි
    bot_thread = threading.Thread(target=trading_bot_loop)
    bot_thread.daemon = True
    bot_thread.start()
    
    # ප්‍රධාන ප්‍රෝග්‍රෑම් එක අඛණ්ඩව පවත්වා ගැනීමට
    while True:
        time.sleep(1)