# import ccxt
# import psycopg2
# import os
# from datetime import datetime, timezone
# from dotenv import load_dotenv

# load_dotenv()

# exchange = ccxt.binance({"enableRateLimit": True})

# SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","XRP/USDT"]

# TIMEFRAMES = {
#     "1h": 365 * 24,
#     "4h": 365 * 6,
#     "1d": 365,
#     "1w": 52
# }

# LIMIT = 1000

# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT"))
# )
# cur = conn.cursor()

# for symbol in SYMBOLS:
#     for tf, total in TIMEFRAMES.items():
#         print(f"📥 Fetching {symbol} — {tf}")

#         since = exchange.milliseconds() - (total * exchange.parse_timeframe(tf) * 1000)
#         fetched = 0

#         while fetched < total:
#             candles = exchange.fetch_ohlcv(symbol, tf, since=since, limit=LIMIT)
#             if not candles:
#                 break

#             for c in candles:
#                 ts = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc)
#                 close_price = c[4]

#                 cur.execute("""
#                     INSERT INTO prices (symbol, timeframe, price, fetched_time)
#                     VALUES (%s, %s, %s, %s)
#                     ON CONFLICT DO NOTHING
#                 """, (symbol, tf, close_price, ts))

#             fetched += len(candles)
#             since = candles[-1][0] + 1
#             conn.commit()

#         print(f"✅ {symbol} — {tf} ({fetched} candles)")

# cur.close()
# conn.close()
# print("🚀 Historical data ready")
import ccxt, psycopg2, os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.binance({"enableRateLimit": True})

SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","XRP/USDT"]

TIMEFRAMES = {
    "1h": 3 * 365 * 24,
    "4h": 3 * 365 * 6,
    "1d": 3 * 365,
    "1w": 3 * 52
}

LIMIT = 1000

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT"))
)
cur = conn.cursor()

for symbol in SYMBOLS:
    for tf, total in TIMEFRAMES.items():
        print(f"📥 {symbol} {tf}")
        since = exchange.milliseconds() - total * exchange.parse_timeframe(tf) * 1000
        fetched = 0

        while fetched < total:
            candles = exchange.fetch_ohlcv(symbol, tf, since, LIMIT)
            if not candles:
                break

            for c in candles:
                ts = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc)
                cur.execute("""
                    INSERT INTO prices (symbol, price, fetched_time, timeframe)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                """, (symbol, c[4], ts, tf))

            since = candles[-1][0] + 1
            fetched += len(candles)
            conn.commit()

        print(f"✅ {symbol} {tf} done")

cur.close()
conn.close()
 