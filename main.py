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
    return "Ultra Sniper Crypto Scalping Bot (5m) is running 24/7 securely!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

sys.stdout.reconfigure(encoding='utf-8')

# --- 🔑 API සහ Telegram සැකසුම් (සම්පූර්ණයෙන්ම ආරක්ෂිතයි) ---
BYBIT_API_KEY = os.environ.get("BYBIT_API_KEY")
BYBIT_SECRET_KEY = os.environ.get("BYBIT_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- 📊 Futures Risk Management & Sniper Settings ---
SYMBOL = 'BTC/USDT:USDT'
TIMEFRAME = '5m'
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
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
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
    # ප්‍රධාන ට්‍රෙන්ඩ් එක බලාගැනීම සඳහා දිගු EMA (EMA 50)
    df['EMA_Trend'] = df['close'].ewm(span=50, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def check_market_and_trade():
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df = calculate_indicators(df)
        
        current_price = df['close'].iloc[-1]
        fast_ema = df['EMA_Fast'].iloc[-1]
        slow_ema = df['EMA_Slow'].iloc[-1]
        trend_ema = df['EMA_Trend'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        print(f"📊 Price: {current_price} | Trend EMA: {trend_ema:.2f} | RSI: {rsi:.2f}")

        positions = exchange.fetch_positions([SYMBOL])
        active_position = False
        for pos in positions:
            if float(pos['contracts']) > 0:
                active_position = True
                break

        if not active_position:
            # 🚀 100% KANFIRM LONG (Uptrend + RSI < 35)
            if current_price > trend_ema and fast_ema > slow_ema and rsi < 35:
                print("🟢 100% Confirmed Buy signal detected! Executing LONG order...")
                
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    # TP +1.0% | SL -0.5%
                    tp_price = round(current_price * 1.01, 2)
                    sl_price = round(current_price * 0.995, 2)
                    
                    params = {
                        'takeProfit': tp_price,
                        'stopLoss': sl_price
                    }
                    
                    order = exchange.create_market_buy_order(SYMBOL, amount, params=params)
                    
                    msg = (
                        f"🎯 *SNIPER LONG ENTRY (5m)* 🎯\n\n"
                        f"🟢 දිශාව: **BUY (LONG)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"🎯 TP (1.0%): **${tp_price}**\n"
                        f"🛑 SL (0.5%): **${sl_price}**\n"
                        f"📈 RSI: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ Sniper Long order executed successfully!")
                else:
                    print("⚠️ Available balance not enough!")

            # 🔻 100% KANFIRM SHORT (Downtrend + RSI > 65)
            elif current_price < trend_ema and fast_ema < slow_ema and rsi > 65:
                print("🔴 100% Confirmed Sell signal detected! Executing SHORT order...")
                
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    # TP -1.0% | SL +0.5%
                    tp_price = round(current_price * 0.99, 2)
                    sl_price = round(current_price * 1.005, 2)
                    
                    params = {
                        'takeProfit': tp_price,
                        'stopLoss': sl_price
                    }
                    
                    order = exchange.create_market_sell_order(SYMBOL, amount, params=params)
                    
                    msg = (
                        f"🎯 *SNIPER SHORT ENTRY (5m)* 🎯\n\n"
                        f"🔴 දිශාව: **SELL (SHORT)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"🎯 TP (1.0%): **${tp_price}**\n"
                        f"🛑 SL (0.5%): **${sl_price}**\n"
                        f"📉 RSI: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ Sniper Short order executed successfully!")
                else:
                    print("⚠️ Available balance not enough!")

    except Exception as e:
        error_msg = f"⚠️ *Trade Error!*\n`{str(e)}`"
        print(error_msg)

def trading_bot_loop():
    print("🚀 Ultra Sniper Trading Bot (5m) Loop Started Successfully...")
    send_telegram_message("🚀 *Ultra Sniper Scalping Bot (5m) Started 24/7 Securely!*")
    
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