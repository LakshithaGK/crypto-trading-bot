from flask import Flask
import threading
import os
import sys
import time
import requests
import ccxt
import pandas as pd
import numpy as np

# --- 🌐 වෙබ් සර්වර් සැකසුම (24/7 Uptime) ---
app = Flask('')

@app.route('/')
def home():
    return "Ultimate 50x Trailing Sniper Bot is running securely!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

sys.stdout.reconfigure(encoding='utf-8')

# --- 🔑 API සහ Telegram සැකසුම් (සම්පූර්ණයෙන්ම ආරක්ෂිතයි) ---
# මෙම දත්ත ලබාගන්නේ Render Environment Variables හරහා පමණි
BYBIT_API_KEY = os.environ.get("BYBIT_API_KEY")
BYBIT_SECRET_KEY = os.environ.get("BYBIT_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- 📊 Ultimate Strategy Settings ---
SYMBOL = 'BTC/USDT:USDT'
TIMEFRAME = '5m'         # 100% ෂුවර් එන්ට්‍රි සඳහා 5m චාට් එක
TRADE_MARGIN_USDT = 9.0  # බැලන්ස් එක 10ක් නිසා 9ක් පාවිච්චි කරමු
LEVERAGE = 50            # 50x සුපිරි ලීවරේජ් එක (ක්ෂණික ලාභ සඳහා)

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
    # Momentum (කෙටි කාලීන වේගය)
    df['EMA_Fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_Slow'] = df['close'].ewm(span=21, adjust=False).mean()
    # Trend Filter (ප්‍රධාන දිශාව)
    df['EMA_Trend'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # RSI (අධි-මිලදීගැනීම් / අධි-විකිණුම්)
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

        # දැනට ට්‍රේඩ් එකක් රන් වෙන්නේ නැත්නම් පමණක් අලුත් එන්ට්‍රි සෙවීම
        if not active_position:
            
            # 🚀 100% PERFECT LONG ENTRY 🚀
            # කොන්දේසි: ප්‍රයිස් එක Trend EMA එකට උඩින් + Fast EMA > Slow EMA + RSI 35ට අඩුයි (Oversold)
            if current_price > trend_ema and fast_ema > slow_ema and rsi < 35:
                print("🟢 Perfect Buy signal! Executing 50x LONG...")
                
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    # 0.4% TP | 0.2% SL | 0.2% Trailing Stop Distance
                    tp_price = round(current_price * 1.004, 2)
                    sl_price = round(current_price * 0.998, 2)
                    trailing_dist = round(current_price * 0.002, 2)
                    
                    params = {
                        'takeProfit': tp_price,
                        'stopLoss': sl_price,
                        'trailingStop': trailing_dist
                    }
                    
                    order = exchange.create_market_buy_order(SYMBOL, amount, params=params)
                    
                    msg = (
                        f"🚀 *ULTIMATE 50x LONG* 🚀\n\n"
                        f"🟢 දිශාව: **BUY (LONG)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"🎯 Target (TP): **${tp_price}** (+0.4%)\n"
                        f"🛑 Initial SL: **${sl_price}** (-0.2%)\n"
                        f"🛡️ Trailing Stop: සක්‍‍රීයයි! (Distance: {trailing_dist})\n"
                        f"📈 RSI Level: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ 50x Long order with Trailing Stop executed successfully!")
                else:
                    print("⚠️ Available balance not enough!")

            # 🔻 100% PERFECT SHORT ENTRY 🔻
            # කොන්දේසි: ප්‍රයිස් එක Trend EMA එකට යටින් + Fast EMA < Slow EMA + RSI 65ට වැඩියි (Overbought)
            elif current_price < trend_ema and fast_ema < slow_ema and rsi > 65:
                print("🔴 Perfect Sell signal! Executing 50x SHORT...")
                
                balance = exchange.fetch_balance()
                free_usdt = balance['USDT']['free']
                
                if free_usdt >= TRADE_MARGIN_USDT:
                    set_leverage()
                    amount = (TRADE_MARGIN_USDT * LEVERAGE) / current_price
                    
                    # 0.4% TP | 0.2% SL | 0.2% Trailing Stop Distance
                    tp_price = round(current_price * 0.996, 2)
                    sl_price = round(current_price * 1.002, 2)
                    trailing_dist = round(current_price * 0.002, 2)
                    
                    params = {
                        'takeProfit': tp_price,
                        'stopLoss': sl_price,
                        'trailingStop': trailing_dist
                    }
                    
                    order = exchange.create_market_sell_order(SYMBOL, amount, params=params)
                    
                    msg = (
                        f"🚀 *ULTIMATE 50x SHORT* 🚀\n\n"
                        f"🔴 දිශාව: **SELL (SHORT)**\n"
                        f"💰 මාජින්: **${TRADE_MARGIN_USDT} ({LEVERAGE}x)**\n"
                        f"🎯 Entry: **${current_price}**\n"
                        f"🎯 Target (TP): **${tp_price}** (+0.4%)\n"
                        f"🛑 Initial SL: **${sl_price}** (-0.2%)\n"
                        f"🛡️ Trailing Stop: සක්‍රීයයි! (Distance: {trailing_dist})\n"
                        f"📉 RSI Level: `{rsi:.2f}`"
                    )
                    send_telegram_message(msg)
                    print("✅ 50x Short order with Trailing Stop executed successfully!")
                else:
                    print("⚠️ Available balance not enough!")

    except Exception as e:
        error_msg = f"⚠️️ *Trade Error!*\n`{str(e)}`"
        print(error_msg)

def trading_bot_loop():
    print("🚀 Ultimate Sniper 50x Trailing Bot Started...")
    send_telegram_message("🚀 *Ultimate 50x Trailing Sniper Bot Started 24/7 Securely!*")
    
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