# =========================
# BACKTEST 15 MIN STRATEGY
# =========================

import os
from dotenv import load_dotenv
load_dotenv()

import psycopg2
import numpy as np
from datetime import datetime, timedelta, timezone

# =========================
# CONFIG
# =========================
SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "AVAX/USDT",
    "XRP/USDT"
]

TIMEFRAME = "15m"
HOLD_MINUTES = 15
INITIAL_CAPITAL = 10000
TRADE_SIZE = 1000  # virtual capital per trade

# =========================
# DB CONNECTION
# =========================
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT"))
)

cur = conn.cursor()

# =========================
# FEATURE BUILDER
# =========================
def build_features(prices):
    prices = np.array(prices)

    returns = (prices[1:] - prices[:-1]) / prices[:-1]

    features = np.array([
        prices[-1],            # current
        prices[-2],            # lag 1
        prices[-3],            # lag 2
        returns.mean(),        # avg return
        returns.std(),         # volatility
        returns[-1]            # last return
    ]).reshape(1, -1)

    return features

# =========================
# SIMPLE ML LOGIC (ROBUST)
# =========================
def model_predict(features):
    """
    Predict price movement using returns logic
    """
    last_return = features[0][-1]
    volatility = features[0][4]

    predicted_return = last_return * 0.6

    if predicted_return > volatility * 0.3:
        signal = "BUY"
    elif predicted_return < -volatility * 0.3:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = min(abs(predicted_return) / (volatility + 1e-6), 1.0)

    return predicted_return, signal, confidence

# =========================
# BACKTEST START
# =========================
capital = INITIAL_CAPITAL
total_trades = 0
wins = 0
losses = 0

print("\n📊 BACKTEST 15 MIN STARTED")
print(f"Initial Capital: {capital} USDT\n")

for symbol in SYMBOLS:
    print(f"🔍 Testing {symbol}")

    cur.execute("""
        SELECT price, fetched_time
        FROM prices
        WHERE symbol = %s
        ORDER BY fetched_time
    """, (symbol,))

    rows = cur.fetchall()

    if len(rows) < 20:
        print("❌ Not enough data\n")
        continue

    prices = [float(r[0]) for r in rows]
    times = [r[1] for r in rows]

    for i in range(6, len(prices) - 1):
        entry_price = prices[i]
        entry_time = times[i]

        exit_time = entry_time + timedelta(minutes=HOLD_MINUTES)

        # Find exit price
        exit_price = None
        for j in range(i + 1, len(times)):
            if times[j] >= exit_time:
                exit_price = prices[j]
                break

        if exit_price is None:
            continue

        features = build_features(prices[i-6:i])
        predicted_return, signal, confidence = model_predict(features)

        if signal == "HOLD":
            continue

        total_trades += 1

        # PnL
        actual_return = (exit_price - entry_price) / entry_price
        pnl = TRADE_SIZE * actual_return

        capital += pnl

        if pnl > 0:
            wins += 1
        else:
            losses += 1

        # Store trade result
        cur.execute("""
            INSERT INTO model_metrics (
                run_time,
                timeframe,
                total_trades,
                win_rate,
                pnl
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            datetime.now(timezone.utc),
            TIMEFRAME,
            total_trades,
            (wins / total_trades) if total_trades else 0,
            capital - INITIAL_CAPITAL
        ))

    print(f"Trades so far: {total_trades}")
    print(f"Capital: {capital:.2f} USDT\n")

conn.commit()

# =========================
# FINAL RESULT
# =========================
win_rate = (wins / total_trades) * 100 if total_trades else 0

print("📈 BACKTEST RESULT (15 MIN)")
print(f"Initial Capital: {INITIAL_CAPITAL} USDT")
print(f"Final Capital:   {capital:.2f} USDT")
print(f"Net PnL:         {capital - INITIAL_CAPITAL:.2f} USDT")
print(f"Total Trades:    {total_trades}")
print(f"Win Rate:        {win_rate:.2f}%")

cur.close()
conn.close()
