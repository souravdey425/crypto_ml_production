# =========================
# BACKTEST SCRIPT (FINAL)
# =========================

import os
from dotenv import load_dotenv
import psycopg2
import numpy as np

from ml_predict import predict

# =========================
# LOAD ENV
# =========================
load_dotenv()

# =========================
# CONFIG
# =========================
INITIAL_CAPITAL = 10_000
TIMEFRAME = "1d"

SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "AVAX/USDT",
    "XRP/USDT"
]

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
def build_features(price_window):
    prices = np.array(price_window, dtype=float)

    returns = (prices[1:] - prices[:-1]) / prices[:-1]

    features = np.array([
        prices[-1],          # current price
        prices[-2],          # lag 1
        prices[-3],          # lag 2
        returns.mean(),      # avg return
        returns.std(),       # volatility
        returns[-1]          # last return
    ]).reshape(1, -1)

    return features

# =========================
# BACKTEST
# =========================
capital = INITIAL_CAPITAL
total_pnl = 0.0
total_trades = 0
total_wins = 0

print("\n📊 BACKTEST STARTED")
print(f"Initial Capital: {capital} USDT\n")

for symbol in SYMBOLS:
    print(f"🔍 Testing {symbol}")

    cur.execute(
        """
        SELECT price
        FROM prices
        WHERE symbol = %s
        ORDER BY fetched_time ASC
        """,
        (symbol,)
    )

    rows = cur.fetchall()
    prices = [float(r[0]) for r in rows]

    if len(prices) < 30:
        print("⚠️ Not enough data\n")
        continue

    symbol_pnl = 0.0
    symbol_trades = 0
    symbol_wins = 0

    for i in range(5, len(prices) - 1):
        window = prices[i - 5 : i + 1]
        features = build_features(window)

        result = predict(features)
        predicted_return = result["predicted_return"]

        # Ignore very tiny predictions (noise)
        if abs(predicted_return) < 0.0001:
            continue

        entry_price = prices[i]
        exit_price = prices[i + 1]

        # Directional trade
        if predicted_return > 0:
            pnl = exit_price - entry_price
        else:
            pnl = entry_price - exit_price

        symbol_pnl += pnl
        symbol_trades += 1

        if pnl > 0:
            symbol_wins += 1

    win_rate = (symbol_wins / symbol_trades * 100) if symbol_trades else 0

    print(f"Trades: {symbol_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"PnL: {symbol_pnl:.2f} USDT\n")

    total_pnl += symbol_pnl
    total_trades += symbol_trades
    total_wins += symbol_wins

# =========================
# FINAL RESULT
# =========================
final_capital = capital + total_pnl
overall_win_rate = (total_wins / total_trades) if total_trades else 0

print("📈 BACKTEST RESULT")
print(f"Initial Capital: {capital} USDT")
print(f"Final Capital:   {final_capital:.2f} USDT")
print(f"Net PnL:         {total_pnl:.2f} USDT")
print(f"Total Trades:    {total_trades}")
print(f"Overall WinRate: {overall_win_rate * 100:.2f}%")

# =========================
# SAVE METRICS (IMPORTANT)
# =========================
with conn.cursor() as cur:
    cur.execute(
        """
        INSERT INTO model_metrics (
            timeframe,
            total_trades,
            win_rate,
            pnl
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            TIMEFRAME,
            total_trades,
            overall_win_rate,
            total_pnl
        )
    )

conn.commit()
print("✅ Backtest metrics saved to database")

# =========================
# CLEANUP
# =========================
cur.close()
conn.close()
