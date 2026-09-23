import sys
sys.stdout.reconfigure(encoding='utf-8')

import ccxt
import time
import requests
import pandas as pd
import numpy as np

# --- 🔒 API සහ Telegram සැකසුම් ---
BYBIT_API_KEY = "2iWIcFsQp4SCxwGOy8"
BYBIT_SECRET_KEY = "SujfI2OohVJZKWReeISLTJL2pr2ZsshAIioS"

TELEGRAM_BOT_TOKEN = "8965234283:AAHz0KpVqnjm1uBSm9e80xI0_9P-Ut0wnbI"
TELEGRAM_CHAT_ID = "1421079683"

# --- 🛡️ Futures Risk Management ---
TRADE_MARGIN_USDT = 10.0      
LEVERAGE = 10                 
DAILY_PROFIT_TARGET = 2.0     
DAILY_TRADE_LIMIT = 5         
MAX_DAILY_LOSS = 4.0          

exchange = ccxt.bybit({
    'apiKey': BYBIT_API_KEY,
    'secret': BYBIT_SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

symbol = 'BTC/USDT:USDT'

print("--- 🐋 ULTIMATE PRODUCTION FUTURES SCALPER ආරම්භ විය! ---")

try:
    exchange.set_margin_mode('cross', symbol)
except:
    pass

try:
    exchange.set_leverage(LEVERAGE, symbol, {'category': 'linear'})
    print(f"✅ Leverage {LEVERAGE}x ලෙස සාර්ථකව සකස් කරන ලදී.")
except Exception as e:
    print(f"ℹ️ Leverage තොරතුරු: {e}")

daily_trades_count = 0
daily_profit_usdt = 0.0
in_trade = False
last_trade_time = 0  

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def execute_futures_trade(side, current_price):
    global in_trade
    try:
        position_size_usdt = TRADE_MARGIN_USDT * LEVERAGE
        amount_in_btc = position_size_usdt / current_price
        
        if amount_in_btc < 0.001:
            amount_in_btc = 0.001
            
        amount_in_btc = round(amount_in_btc, 3)
        
        tp_percent = 0.005 
        sl_percent = 0.002 
        
        if side == 'buy':
            tp_price = current_price * (1 + tp_percent)
            sl_price = current_price * (1 - sl_percent)
        else:
            tp_price = current_price * (1 - tp_percent)
            sl_price = current_price * (1 + sl_percent)

        params = {
            'takeProfit': str(tp_price),
            'stopLoss': str(sl_price),
            'positionIdx': 0,
            'category': 'linear'
        }
        
        exchange.create_order(symbol, 'market', side, amount_in_btc, params=params)
        print(f"✅ Futures {side.upper()} ට්‍රේඩ් එක සාර්ථකයි! Entry: ${current_price:.2f}")
        
        msg = (
            f"🐋 *ULTIMATE WHALE ENTRY (FUTURES)* 🐋\n\n"
            f"🟢 දිශාව: *{side.upper()}*\n"
            f"💰 මාජින්: *${TRADE_MARGIN_USDT}* ({LEVERAGE}x)\n"
            f"🎯 Entry: *${current_price:.2f}*\n"
            f"✅ TP: *${tp_price:.2f}*\n"
            f"🛑 SL: *${sl_price:.2f}*"
        )
        send_telegram_message(msg)
        in_trade = True
        return True
    except Exception as e:
        print(f"❌ Trade Error: {e}")
        send_telegram_message(f"⚠️ *Trade Error!*\n{e}")
        return False

def analyze_market():
    global in_trade, daily_trades_count, daily_profit_usdt, last_trade_time
    
    if daily_trades_count >= DAILY_TRADE_LIMIT:
        print("🛑 දවසේ ට්‍රේඩ් ලිමිට් එක අවසන්! බොට් විවේක ගනී.")
        time.sleep(300)
        return
        
    if daily_profit_usdt <= -MAX_DAILY_LOSS:
        print("🚨 හදිසි ආරක්ෂණ පද්ධතිය ක්‍රියාත්මකයි (Emergency Stop)! දවසේ පාඩුව සීමාව ඉක්මවා ඇත.")
        time.sleep(3600)
        return

    try:
        # Active Position චෙක් කිරීම (මෙතනයි ෆික්ස් කළේ - [symbol] යෙදීම)
        positions = exchange.fetch_positions([symbol], params={'category': 'linear'})
        active_position = False
        for pos in positions:
            if float(pos.get('contracts', 0)) > 0:
                active_position = True
                print(f"👀 Active Position | PNL: ${float(pos.get('unrealizedPnl', 0)):.4f}")
                in_trade = True
                break
                
        if in_trade and not active_position:
            print("🔔 ට්‍රේඩ් එක TP හෝ SL වැදී ක්ලෝස් වී ඇත!")
            send_telegram_message("🔔 *ට්‍රේඩ් එක ක්ලෝස් විය!*")
            in_trade = False
            daily_trades_count += 1
            last_trade_time = time.time() 
            time.sleep(60)
            return

        if in_trade:
            return

        if time.time() - last_trade_time < 300: 
            print("⏳ Cooldown කාලය තුළ ඇත... මාකට් එක නිරීක්ෂණය කරමින් පවතී.")
            time.sleep(15)
            return

        candles_5m = exchange.fetch_ohlcv(symbol, '5m', limit=100)
        df_5m = pd.DataFrame(candles_5m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_5m['ema_50'] = df_5m['close'].ewm(span=50, adjust=False).mean()
        trend_5m = "UP" if df_5m['close'].iloc[-1] > df_5m['ema_50'].iloc[-1] else "DOWN"

        candles_1m = exchange.fetch_ohlcv(symbol, '1m', limit=100)
        df = pd.DataFrame(candles_1m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        current_price = df['close'].iloc[-1]
        
        df['vol_sma'] = df['volume'].rolling(15).mean()
        high_volume = df['volume'].iloc[-1] > (df['vol_sma'].iloc[-1] * 1.5)
        
        df['cum_vol'] = df['volume'].cumsum()
        df['cum_vol_price'] = (df['close'] * df['volume']).cumsum()
        df['vwap'] = df['cum_vol_price'] / df['cum_vol']
        vwap = df['vwap'].iloc[-1]
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        df['rsi'] = 100 - (100 / (1 + (gain.ewm(com=6, adjust=False).mean() / loss.ewm(com=6, adjust=False).mean())))
        rsi = df['rsi'].iloc[-1]

        print(f"Price: ${current_price:.2f} | 5M: {trend_5m} | VWAP: ${vwap:.2f} | RSI(7): {rsi:.1f} | Whale Vol: {high_volume}")
        
        if trend_5m == "UP" and (current_price > vwap) and high_volume and (rsi < 70):
            execute_futures_trade('buy', current_price)
        elif trend_5m == "DOWN" and (current_price < vwap) and high_volume and (rsi > 30):
            execute_futures_trade('sell', current_price)

    except Exception as e:
        print(f"මාකට් දත්ත දෝෂයක්: {e}")

while True:
    analyze_market()
    time.sleep(15)