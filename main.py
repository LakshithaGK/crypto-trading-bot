from flask import Flask
import threading
import os
import sys
import time
import requests
import ccxt
import pandas as pd
import numpy as np

# --- 🌐 වෙබ් සර්වර් සැකසුම ---
app = Flask('')

@app.route('/')
def home():
    return "Crypto Scalping Bot with TP/SL is running 24/7 live!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

sys.stdout.reconfigure(encoding='utf-8')

# --- 🔑 API සහ Telegram සැකසුම් ---
BYBIT_API_KEY = "2iWIcFsQp4SCxwGOy8"
BYBIT_SECRET_KEY = "SujfI2OohVJZKWReeISLTJL2pr2ZsshAIioS"
TELEGRAM_BOT_TOKEN = "8872491990:AAF37Vvpln7xYhB0wvJYcxuzHKnYVHjzMEc"
TELEGRAM_CHAT_ID = "1421079683"

# --- 📊 Futures Risk Management & Scalping Settings ---
SYMBOL = 'BTC/USDT:USDT'
TIMEFRAME = '1m'
TRADE_MARGIN_USDT = 10.0
LEVERAGE = 10

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
        print(f"Leverage Error: {e}")

def calculate_indicators(df):
    df['EMA_Fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_Slow'] = df['close'].ewm(span=21, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def check_market_and_trade():
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df = calculate_indicators(df)
        
        current_price = df['close'].iloc[-1]
        fast_ema = df['EMA_Fast'].iloc[-1]
        slow_ema = df['EMA_Slow'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        print(f"📊 Price: {current_price} | RSI: {rsi:.2f}")

        positions = exchange.fetch_positions([SYMBOL])
        active_position = False
        for pos in positions:
            if float(pos['contracts']) > 0:
                active_position = True
                break

        if not active_position:
            # 🚀 BUY / LONG KONDISHN
            if fast_ema > slow_ema and rsi < 40:
                print("🟢 Buy signal detected! Executing LONG order with TP/SL...")
                
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    # Take Profit (+0.6%) සහ Stop Loss (-0.3%) ගණනය කිරීම
                    tp_price = round(current_price * 1.006, 2)
                    sl_price = round(current_price * 0.997, 2)
                    
                    params = {
                        'takeProfit': tp_price,
                        'stopLoss': sl_price
                    }
                    
                    order = exchange.create_market_buy_order(SYMBOL, amount, params=params)
                    
                    msg = (
                        f"🐋 *ULTIMATE WHALE ENTRY (FUTURES)* 🐋\n\n"
                        f"🟢 දිශාව: **BUY (LONG)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"ෙ TP (Take Profit): **${tp_price}**\n"
                        f"🛑 SL (Stop Loss): **${sl_price}**\n"
                        f"📈 RSI: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ Long order with TP/SL executed successfully!")
                else:
                    print("⚠️ Available balance not enough for new order!")

            # 🔻 SELL / SHORT KONDISHN
            elif fast_ema < slow_ema and rsi > 60:
                print("🔴 Sell signal detected! Executing SHORT order with TP/SL...")
                
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    # Short සඳහා TP සහ SL ගණනය කිරීම
                    tp_price = round(current_price * 0.994, 2)
                    sl_price = round(current_price * 1.003, 2)
                    
                    params = {
                        'takeProfit': tp_price,
                        'stopLoss': sl_price
                    }
                    
                    order = exchange.create_market_sell_order(SYMBOL, amount, params=params)
                    
                    msg = (
                        f"🐋 *ULTIMATE WHALE ENTRY (FUTURES)* 🐋\n\n"
                        f"🔴 දිශාව: **SELL (SHORT)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"🎯 TP (Take Profit): **${tp_price}**\n"
                        f"🛑 SL (Stop Loss): **${sl_price}**\n"
                        f"📉 RSI: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ Short order with TP/SL executed successfully!")
                else:
                    print("⚠️ Available balance not enough for new order!")

    except Exception as e:
        error_msg = f"⚠️ *Trade Error!*\n`{str(e)}`"
        print(error_msg)

def trading_bot_loop():
    print("🚀 Ultimate Scalping Trading Bot Loop Started Successfully...")
    send_telegram_message("🚀 *Crypto Scalping Bot with TP/SL Started 24/7 Live!*")
    
    while True:
        try:
            check_market_and_trade()
            time.sleep(20)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(20)

if __name__ == "__main__":
    keep_alive()
    print("🌐 Web server background thread started...")
    
    bot_thread = threading.Thread(target=trading_bot_loop)
    bot_thread.daemon = True
    bot_thread.start()
    
    while True:
        time.sleep(1)