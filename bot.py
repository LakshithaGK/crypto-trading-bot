import ccxt
import time
import requests

# --- Telegram සැකසුම් ---
TELEGRAM_BOT_TOKEN = "8965234283:AAHz0KpVqnjm1uBSm9e80xI0_9P-Ut0wnbI"
TELEGRAM_CHAT_ID = "8965234283"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("📲 ටෙලිග්‍රෑම් වෙත සිග්නල් එක සාර්ථකව යවන ලදී!")
        else:
            print(f"⚠️ ටෙලිග්‍රෑම් යැවීමේ දෝෂයක්: {response.text}")
    except Exception as e:
        print(f"Telegram සම්බන්ධ වීමේ දෝෂයක් ඇති විය: {e}")

# Binance Public API සමඟ සම්බන්ධ වීම
exchange = ccxt.binance()
symbol = 'BTC/USDT'
timeframe = '1m'

print("--- සම්පූර්ණ ස්වයංක්‍රීය Crypto Trading Bot (SL, TP & Telegram සමඟ) ක්‍රියාත්මක විය! ---")

last_signal = None  # එකම සිග්නල් එක මඟින් නැවත නැවත මැසේජ් යැවීම වැළැක්වීමට

def analyze_market():
    global last_signal
    try:
        # කැන්ඩ්ල්ස් 100ක දත්ත ලබා ගැනීම
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        closing_prices = [candle[4] for candle in candles]
        
        current_price = closing_prices[-1]
        sma_20 = sum(closing_prices[-20:]) / 20
        
        print(f"වර්තමාන මිල: ${current_price:.2f} \vert{} SMA(20):${sma_20:.2f}")
        
        # 1:2.5 Risk-to-Reward අනුපාතය මත පදනම් වූ ස්ට්‍රැටජි සහ රිස්ක් මැනේජ්මන්ට්
        if current_price > sma_20 and last_signal != "BUY":
            entry = current_price
            stop_loss = entry * 0.99      # 1% කින් පහළ (Loss සීමාව)
            take_profit = entry * 1.025   # 2.5% කින් උඩ (Profit ඉලක්කය)
            
            msg = (
                "🚨 *CRYPTO BUY SIGNAL* 🚨\n\n"
                f"🪙 යුගලය: `{symbol}`\n"
                "🟢 තත්වය: *BUY (LONG)*\n"
                f"💰 ඇතුළු වන මිල (Entry): *${entry:.2f}*\n"
                f"🛑 Stop Loss (අලාභ සීමාව): *${stop_loss:.2f}* (-1%)\n"
                f"🎯 Take Profit (ලාභ ඉලක්කය): *${take_profit:.2f}* (+2.5%)\n"
                "⚖️ Risk-to-Reward: ~1:2.5"
            )
            print(msg)
            send_telegram_message(msg)
            last_signal = "BUY"
            
        elif current_price < sma_20 and last_signal != "SELL":
            entry = current_price
            stop_loss = entry * 1.01      # 1% කින් උඩ (Loss සීමාව)
            take_profit = entry * 0.975   # 2.5% කින් පහළ (Profit ඉලක්කය)
            
            msg = (
                "🚨 *CRYPTO SELL SIGNAL* 🚨\n\n"
                f"🪙 යුගලය: `{symbol}`\n"
                "🔴 තත්වය: *SELL (SHORT)*\n"
                f"💰 ඇතුළු වන මිල (Entry): *${entry:.2f}*\n"
                f"🛑 Stop Loss (අලාභ සීමාව): *${stop_loss:.2f}* (+1%)\n"
                f"🎯 Take Profit (ලාභ ඉලක්කය): *${take_profit:.2f}* (-2.5%)\n"
                "⚖️ Risk-to-Reward: ~1:2.5"
            )
            print(msg)
            send_telegram_message(msg)
            last_signal = "SELL"
            
    except Exception as e:
        print(f"මාකට් දත්ත ලබාගැනීමේ දෝෂයක් ඇති විය: {e}")

# ප්‍රධාන ලූප් එක - සෑම තත්පර 15කට වරක් මාකට් එක පරීක්ෂා කරයි
while True:
    analyze_market()
    print("-" * 50)
    time.sleep(15)