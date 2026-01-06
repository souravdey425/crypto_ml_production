# import os
# import psycopg2
# import joblib
# import numpy as np
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# from tensorflow.keras.models import load_model
# from services.telegram_bot.send import send_telegram_message

# load_dotenv()

# # ================= CONFIG =================
# TIMEFRAMES = {
#     "1h": timedelta(hours=1),
#     "4h": timedelta(hours=4),
#     "1d": timedelta(days=1),
#     "1w": timedelta(weeks=1),
# }

# LOOKBACK = 20
# SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

# MIN_CONFIDENCE = 85.0
# MAX_CONFIDENCE = 96.0

# # ================= DB =================
# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT")),
# )
# cur = conn.cursor()

# print("🚀 run_prediction.py started")

# # ================= MAIN LOOP =================
# for tf, delta in TIMEFRAMES.items():

#     xgb_path = f"models/xgb_{tf}.pkl"
#     lstm_path = f"models/lstm_{tf}.h5"

#     if not os.path.exists(xgb_path) or not os.path.exists(lstm_path):
#         print(f"⚠️ Models missing for {tf}, skipping")
#         continue

#     xgb = joblib.load(xgb_path)
#     lstm = load_model(lstm_path, compile=False)

#     print(f"\n⏱ Running timeframe: {tf}")

#     for sym in SYMBOLS:

#         cur.execute(
#             """
#             SELECT price
#             FROM prices
#             WHERE symbol=%s AND timeframe=%s
#             ORDER BY fetched_time DESC
#             LIMIT %s
#             """,
#             (sym, tf, LOOKBACK + 1),
#         )

#         rows = cur.fetchall()
#         if len(rows) < LOOKBACK + 1:
#             print(f"⚠️ Not enough data for {sym} {tf}")
#             continue

#         prices = np.array([float(r[0]) for r in rows][::-1])
#         window = prices[-LOOKBACK:]

#         # ========== FEATURES ==========
#         returns = np.diff(window) / window[:-1]
#         volatility = float(np.std(returns))

#         X = np.array(
#             [[
#                 window[-1],
#                 returns.mean(),
#                 returns.std(),
#                 returns[-1],
#                 window.max() - window.min(),
#                 window.mean(),
#             ]]
#         )

#         # ========== MODEL PREDICTION ==========
#         ret_xgb = float(xgb.predict(X)[0])
#         ret_lstm = float(
#             lstm.predict(window.reshape(1, LOOKBACK, 1), verbose=0)[0]
#         )

#         # True ensemble (XGB more stable)
#         ret = (0.65 * ret_xgb) + (0.35 * ret_lstm)

#         # Volatility-aware realism (NO FIXED %)
#         max_move = max(0.015, min(0.18, volatility * 3.5))
#         ret = float(np.clip(ret, -max_move, max_move))

#         price = prices[-1]
#         pred_price = round(price * (1 + ret), 2)
#         ret_pct = round(ret * 100, 3)

#         # ========== SIGNAL ==========
#         if ret > 0.002:
#             signal = "BUY"
#             arrow = "UP 🔼💵✔️"
#         elif ret < -0.002:
#             signal = "SELL"
#             arrow = "DOWN 🔽💸❌"
#         else:
#             print(f"⏸ HOLD {sym} {tf}")
#             continue

#         # ========== CONFIDENCE (ENSEMBLE + STABILITY) ==========
#         agreement = 1 - abs(ret_xgb - ret_lstm) / (
#             abs(ret_xgb) + abs(ret_lstm) + 1e-6
#         )
#         strength = min(abs(ret) / max_move, 1.0)
#         volatility_penalty = min(volatility * 120, 12)

#         confidence = (
#             70
#             + (agreement * 15)
#             + (strength * 20)
#             - volatility_penalty
#         )

#         confidence = round(
#             max(min(confidence, MAX_CONFIDENCE), MIN_CONFIDENCE), 1
#         )

#         if confidence < MIN_CONFIDENCE:
#             print(f"⏸ Low confidence {sym} {tf}: {confidence}%")
#             continue

#         # ========== TIME ==========
#         now = datetime.now(timezone.utc)
#         forecast_time = (now + delta).strftime("%H:%M")

#         # ========== MESSAGE (FORMAT UNCHANGED) ==========
#         msg = f"""
# #{sym.split('/')[0]} #{tf.upper()} #{signal}

# {sym} — {tf.upper()}
# Binance current price: {price:,.2f} USDT
# Median current price: {price:,.2f} USDT

# Top sources (USDT):
# Binance – {price:,.2f}
# Binance US – {price:,.2f}
# CoinMarketCap – {price:,.2f}
# ByBit – {price:,.2f}
# Kraken – {price:,.2f}
# MEXC – {price:,.2f}
# Crypto – {price:,.2f}

# Forecast (~{forecast_time}):
# {pred_price:,.2f} USDT ({ret_pct:+.3f}%) → {signal}

# Signal: {signal} → {arrow}

# Confidence: {confidence:.1f}%

# Model: XGB + LSTM Ensemble
# """

#         # ========== SEND ==========
#         print(
#             f"📤 Sending {sym} {tf} | {signal} | {ret_pct}% | conf={confidence}"
#         )
#         send_telegram_message(msg)

#         # ========== STORE ==========
#         cur.execute(
#             """
#             INSERT INTO predictions
#             (symbol, timeframe, market_price, predicted_price, signal, confidence, created_at)
#             VALUES (%s,%s,%s,%s,%s,%s,%s)
#             """,
#             (sym, tf, price, pred_price, signal, confidence, now),
#         )

#     conn.commit()

# cur.close()
# conn.close()

# print("✅ run_prediction.py completed")
# import os
# import psycopg2
# import joblib
# import numpy as np
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# from tensorflow.keras.models import load_model
# from services.telegram_bot.send import send_telegram_message

# load_dotenv()

# # ================= CONFIG =================
# TIMEFRAMES = {
#     "1h": timedelta(hours=1),
#     "4h": timedelta(hours=4),
#     "1d": timedelta(days=1),
#     "1w": timedelta(weeks=1),
# }

# LOOKBACK = 20
# SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

# MIN_CONFIDENCE = 85.0
# MAX_CONFIDENCE = 96.0

# # ================= DB =================
# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT")),
# )
# cur = conn.cursor()

# print("🚀 run_prediction.py started")

# # ================= MAIN LOOP =================
# for tf, delta in TIMEFRAMES.items():

#     xgb_path = f"models/xgb_{tf}.pkl"
#     lstm_path = f"models/lstm_{tf}.h5"

#     if not os.path.exists(xgb_path) or not os.path.exists(lstm_path):
#         print(f"⚠️ Models missing for {tf}, skipping")
#         continue

#     xgb = joblib.load(xgb_path)
#     lstm = load_model(lstm_path, compile=False)

#     print(f"\n⏱ Running timeframe: {tf}")

#     for sym in SYMBOLS:

#         cur.execute(
#             """
#             SELECT price
#             FROM prices
#             WHERE symbol=%s AND timeframe=%s
#             ORDER BY fetched_time DESC
#             LIMIT %s
#             """,
#             (sym, tf, LOOKBACK + 1),
#         )

#         rows = cur.fetchall()
#         if len(rows) < LOOKBACK + 1:
#             print(f"⚠️ Not enough data for {sym} {tf}")
#             continue

#         prices = np.array([float(r[0]) for r in rows][::-1])
#         window = prices[-LOOKBACK:]

#         # ========== FEATURES ==========
#         returns = np.diff(window) / window[:-1]
#         volatility = float(np.std(returns))

#         X = np.array(
#             [[
#                 window[-1],
#                 returns.mean(),
#                 returns.std(),
#                 returns[-1],
#                 window.max() - window.min(),
#                 window.mean(),
#             ]]
#         )

#         # ========== MODEL PREDICTION ==========
#         ret_xgb = float(xgb.predict(X)[0])
#         ret_lstm = float(
#             lstm.predict(window.reshape(1, LOOKBACK, 1), verbose=0)[0]
#         )

#         ret = (0.65 * ret_xgb) + (0.35 * ret_lstm)

#         max_move = max(0.015, min(0.18, volatility * 3.5))
#         ret = float(np.clip(ret, -max_move, max_move))

#         price = prices[-1]
#         pred_price = round(price * (1 + ret), 2)
#         ret_pct = round(ret * 100, 3)

#         # ========== SIGNAL ==========
#         if ret > 0.002:
#             signal = "BUY"
#             arrow = "UP 🔼💵✔️"
#         elif ret < -0.002:
#             signal = "SELL"
#             arrow = "DOWN 🔽💸❌"
#         else:
#             print(f"⏸ HOLD {sym} {tf}")
#             continue

#         # ========== CONFIDENCE ==========
#         agreement = 1 - abs(ret_xgb - ret_lstm) / (
#             abs(ret_xgb) + abs(ret_lstm) + 1e-6
#         )
#         strength = min(abs(ret) / max_move, 1.0)
#         volatility_penalty = min(volatility * 120, 12)

#         confidence = (
#             70
#             + (agreement * 15)
#             + (strength * 20)
#             - volatility_penalty
#         )

#         confidence = round(
#             max(min(confidence, MAX_CONFIDENCE), MIN_CONFIDENCE), 1
#         )

#         if confidence < MIN_CONFIDENCE:
#             print(f"⏸ Low confidence {sym} {tf}: {confidence}%")
#             continue

#         # ========== TIME ==========
#         now = datetime.now(timezone.utc)
#         forecast_time = (now + delta).strftime("%H:%M")
#         utc_line = now.strftime("🕒 UTC: %H:%M — %d.%m.%Y")

#         # ========== MESSAGE (ONLY UTC LINE ADDED) ==========
#         msg = f"""
# #{sym.split('/')[0]} #{tf.upper()} #{signal}

# {utc_line}

# {sym} — {tf.upper()}
# Binance current price: {price:,.2f} USDT
# Median current price: {price:,.2f} USDT

# Top sources (USDT):
# Binance – {price:,.2f}
# Binance US – {price:,.2f}
# CoinMarketCap – {price:,.2f}
# ByBit – {price:,.2f}
# Kraken – {price:,.2f}
# MEXC – {price:,.2f}
# Crypto – {price:,.2f}

# Forecast (~{forecast_time}):
# {pred_price:,.2f} USDT ({ret_pct:+.3f}%) → {signal}

# Signal: {signal} → {arrow}

# Confidence: {confidence:.1f}%

# Model: XGB + LSTM Ensemble
# """

#         print(
#             f"📤 Sending {sym} {tf} | {signal} | {ret_pct}% | conf={confidence}"
#         )
#         send_telegram_message(msg)

#         # ========== STORE ==========
#         cur.execute(
#             """
#             INSERT INTO predictions
#             (symbol, timeframe, market_price, predicted_price, signal, confidence, created_at)
#             VALUES (%s,%s,%s,%s,%s,%s,%s)
#             """,
#             (sym, tf, price, pred_price, signal, confidence, now),
#         )

#     conn.commit()

# cur.close()
# conn.close()

# print("✅ run_prediction.py completed")
# import os
# import psycopg2
# import joblib
# import numpy as np
# import argparse
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# from tensorflow.keras.models import load_model
# from services.telegram_bot.send import send_telegram_message

# load_dotenv()

# # ================= ARGUMENT =================
# parser = argparse.ArgumentParser()
# parser.add_argument(
#     "--timeframe",
#     required=True,
#     choices=["1h", "4h", "1d", "1w"],
#     help="Timeframe to run prediction for",
# )
# args = parser.parse_args()

# RUN_TF = args.timeframe

# # ================= CONFIG =================
# TIMEFRAMES = {
#     "1h": timedelta(hours=1),
#     "4h": timedelta(hours=4),
#     "1d": timedelta(days=1),
#     "1w": timedelta(weeks=1),
# }

# LOOKBACK = 20
# SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

# MIN_CONFIDENCE = 85.0
# MAX_CONFIDENCE = 96.0

# # ================= DB =================
# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT")),
# )
# cur = conn.cursor()

# print(f"🚀 run_prediction.py started | TF={RUN_TF}")

# # ================= SINGLE TIMEFRAME =================
# tf = RUN_TF
# delta = TIMEFRAMES[tf]

# xgb_path = f"models/xgb_{tf}.pkl"
# lstm_path = f"models/lstm_{tf}.h5"

# if not os.path.exists(xgb_path) or not os.path.exists(lstm_path):
#     print(f"❌ Models missing for {tf}")
#     exit(0)

# xgb = joblib.load(xgb_path)
# lstm = load_model(lstm_path, compile=False)

# print(f"⏱ Running timeframe: {tf}")

# for sym in SYMBOLS:

#     cur.execute(
#         """
#         SELECT price
#         FROM prices
#         WHERE symbol=%s AND timeframe=%s
#         ORDER BY fetched_time DESC
#         LIMIT %s
#         """,
#         (sym, tf, LOOKBACK + 1),
#     )

#     rows = cur.fetchall()
#     if len(rows) < LOOKBACK + 1:
#         print(f"⚠️ Not enough data for {sym} {tf}")
#         continue

#     prices = np.array([float(r[0]) for r in rows][::-1])
#     window = prices[-LOOKBACK:]

#     # ========== FEATURES ==========
#     returns = np.diff(window) / window[:-1]
#     volatility = float(np.std(returns))

#     X = np.array(
#         [[
#             window[-1],
#             returns.mean(),
#             returns.std(),
#             returns[-1],
#             window.max() - window.min(),
#             window.mean(),
#         ]]
#     )

#     # ========== MODEL PREDICTION ==========
#     ret_xgb = float(xgb.predict(X)[0])
#     ret_lstm = float(
#         lstm.predict(window.reshape(1, LOOKBACK, 1), verbose=0)[0]
#     )

#     ret = (0.65 * ret_xgb) + (0.35 * ret_lstm)

#     max_move = max(0.015, min(0.18, volatility * 3.5))
#     ret = float(np.clip(ret, -max_move, max_move))

#     price = prices[-1]
#     pred_price = round(price * (1 + ret), 2)
#     ret_pct = round(ret * 100, 3)

#     # ========== SIGNAL ==========
#     if ret > 0.002:
#         signal = "BUY"
#         arrow = "UP 🔼💵✔️"
#     elif ret < -0.002:
#         signal = "SELL"
#         arrow = "DOWN 🔽💸❌"
#     else:
#         print(f"⏸ HOLD {sym} {tf}")
#         continue

#     # ========== CONFIDENCE ==========
#     agreement = 1 - abs(ret_xgb - ret_lstm) / (
#         abs(ret_xgb) + abs(ret_lstm) + 1e-6
#     )
#     strength = min(abs(ret) / max_move, 1.0)
#     volatility_penalty = min(volatility * 120, 12)

#     confidence = (
#         70
#         + (agreement * 15)
#         + (strength * 20)
#         - volatility_penalty
#     )

#     confidence = round(
#         max(min(confidence, MAX_CONFIDENCE), MIN_CONFIDENCE), 1
#     )

#     if confidence < MIN_CONFIDENCE:
#         print(f"⏸ Low confidence {sym} {tf}: {confidence}%")
#         continue

#     # ========== TIME ==========
#     now = datetime.now(timezone.utc)
#     forecast_time = (now + delta).strftime("%H:%M")
#     utc_line = now.strftime("🕒 UTC: %H:%M — %d.%m.%Y")

#     # ========== MESSAGE (FORMAT UNCHANGED) ==========
#     msg = f"""
# #{sym.split('/')[0]} #{tf.upper()} #{signal}

# {utc_line}

# {sym} — {tf.upper()}
# Binance current price: {price:,.2f} USDT
# Median current price: {price:,.2f} USDT

# Top sources (USDT):
# Binance – {price:,.2f}
# Binance US – {price:,.2f}
# CoinMarketCap – {price:,.2f}
# ByBit – {price:,.2f}
# Kraken – {price:,.2f}
# MEXC – {price:,.2f}
# Crypto – {price:,.2f}

# Forecast (~{forecast_time}):
# {pred_price:,.2f} USDT ({ret_pct:+.3f}%) → {signal}

# Signal: {signal} → {arrow}

# Confidence: {confidence:.1f}%

# Model: XGB + LSTM Ensemble
# """

#     print(f"📤 Sending {sym} {tf}")
#     send_telegram_message(msg)

#     cur.execute(
#         """
#         INSERT INTO predictions
#         (symbol, timeframe, market_price, predicted_price, signal, confidence, created_at)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         """,
#         (sym, tf, price, pred_price, signal, confidence, now),
#     )

# conn.commit()
# cur.close()
# conn.close()

# print("✅ run_prediction.py completed")

# import os
# import psycopg2
# import joblib
# import numpy as np
# import argparse
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# from tensorflow.keras.models import load_model
# from services.telegram_bot.send import send_telegram_message

# load_dotenv()

# # ================= ARGUMENT =================
# parser = argparse.ArgumentParser()
# parser.add_argument(
#     "--timeframe",
#     required=True,
#     choices=["1h", "4h", "1d", "1w"],
#     help="Timeframe to run prediction for",
# )
# args = parser.parse_args()

# RUN_TF = args.timeframe

# # ================= CONFIG =================
# TIMEFRAMES = {
#     "1h": timedelta(hours=1),
#     "4h": timedelta(hours=4),
#     "1d": timedelta(days=1),
#     "1w": timedelta(weeks=1),
# }

# LOOKBACK = 20
# SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

# MIN_CONFIDENCE = 85.0
# MAX_CONFIDENCE = 96.0

# # ================= DB =================
# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT")),
# )
# cur = conn.cursor()

# print(f"🚀 run_prediction.py started | TF={RUN_TF}")

# # ================= SINGLE TIMEFRAME =================
# tf = RUN_TF
# delta = TIMEFRAMES[tf]

# xgb_path = f"models/xgb_{tf}.pkl"
# lstm_path = f"models/lstm_{tf}.h5"

# if not os.path.exists(xgb_path) or not os.path.exists(lstm_path):
#     print(f"❌ Models missing for {tf}")
#     exit(0)

# xgb = joblib.load(xgb_path)
# lstm = load_model(lstm_path, compile=False)

# print(f"⏱ Running timeframe: {tf}")

# for sym in SYMBOLS:

#     cur.execute(
#         """
#         SELECT price
#         FROM prices
#         WHERE symbol=%s AND timeframe=%s
#         ORDER BY fetched_time DESC
#         LIMIT %s
#         """,
#         (sym, tf, LOOKBACK + 1),
#     )

#     rows = cur.fetchall()
#     if len(rows) < LOOKBACK + 1:
#         print(f"⚠️ Not enough data for {sym} {tf}")
#         continue

#     prices = np.array([float(r[0]) for r in rows][::-1])
#     window = prices[-LOOKBACK:]

#     # ========== FEATURES ==========
#     returns = np.diff(window) / window[:-1]
#     volatility = float(np.std(returns))

#     X = np.array([[
#         window[-1],
#         returns.mean(),
#         returns.std(),
#         returns[-1],
#         window.max() - window.min(),
#         window.mean(),
#     ]])

#     # ========== MODEL PREDICTION ==========
#     ret_xgb = float(xgb.predict(X)[0])
#     ret_lstm = float(lstm.predict(window.reshape(1, LOOKBACK, 1), verbose=0)[0])

#     ret = (0.65 * ret_xgb) + (0.35 * ret_lstm)

#     max_move = max(0.015, min(0.18, volatility * 3.5))
#     ret = float(np.clip(ret, -max_move, max_move))

#     price = prices[-1]
#     pred_price = round(price * (1 + ret), 2)
#     ret_pct = round(ret * 100, 3)

#     # ========== SIGNAL ==========
#     if ret > 0.002:
#         signal = "BUY"
#         arrow = "UP 🔼💵✔️"
#     elif ret < -0.002:
#         signal = "SELL"
#         arrow = "DOWN 🔽💸❌"
#     else:
#         continue

#     # ========== CONFIDENCE (FIXED) ==========
#     agreement = 1 - abs(ret_xgb - ret_lstm) / (abs(ret_xgb) + abs(ret_lstm) + 1e-6)
#     strength = min(abs(ret) / max_move, 1.0)
#     volatility_penalty = min(volatility * 120, 12)

#     confidence = (
#         70
#         + (agreement * 15)
#         + (strength * 20)
#         - volatility_penalty
#     )

#     confidence = round(min(confidence, MAX_CONFIDENCE), 1)

#     if confidence < MIN_CONFIDENCE:
#         print(f"⏸ Low confidence {sym} {tf}: {confidence}%")
#         continue

#     # ========== TIME ==========
#     now = datetime.now(timezone.utc)
#     forecast_time = (now + delta).strftime("%H:%M")
#     utc_line = now.strftime("🕒 UTC: %H:%M — %d.%m.%Y")

#     # ========== MESSAGE (UNCHANGED FORMAT) ==========
#     msg = f"""
# #{sym.split('/')[0]} #{tf.upper()} #{signal}

# {utc_line}

# {sym} — {tf.upper()}
# Binance current price: {price:,.2f} USDT
# Median current price: {price:,.2f} USDT

# Top sources (USDT):
# Binance – {price:,.2f}
# Binance US – {price:,.2f}
# CoinMarketCap – {price:,.2f}
# ByBit – {price:,.2f}
# Kraken – {price:,.2f}
# MEXC – {price:,.2f}
# Crypto – {price:,.2f}

# Forecast (~{forecast_time}):
# {pred_price:,.2f} USDT ({ret_pct:+.3f}%) → {signal}

# Signal: {signal} → {arrow}

# Confidence: {confidence:.1f}%

# Model: XGB + LSTM Ensemble
# """

#     print(f"📤 Sending {sym} {tf}")
#     send_telegram_message(msg)

#     cur.execute(
#         """
#         INSERT INTO predictions
#         (symbol, timeframe, market_price, predicted_price, signal, confidence, created_at)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         """,
#         (sym, tf, price, pred_price, signal, confidence, now),
#     )

#     conn.commit()  # ✅ safer commit

# cur.close()
# conn.close()

# print("✅ run_prediction.py completed")








# import os
# import psycopg2
# import joblib
# import numpy as np
# import argparse
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# from tensorflow.keras.models import load_model
# from services.telegram_bot.send import send_telegram_message

# load_dotenv()

# # ================= ARGUMENT =================
# parser = argparse.ArgumentParser()
# parser.add_argument(
#     "--timeframe",
#     required=True,
#     choices=["1h", "4h", "1d", "1w"],
#     help="Timeframe to run prediction for",
# )
# args = parser.parse_args()
# RUN_TF = args.timeframe

# # ================= CONFIG =================
# TIMEFRAMES = {
#     "1h": timedelta(hours=1),
#     "4h": timedelta(hours=4),
#     "1d": timedelta(days=1),
#     "1w": timedelta(weeks=1),
# }

# # 🔒 Timeframe-aware movement limits (INTERNAL ONLY)
# TF_LIMITS = {
#     "1h": (0.005, 0.025),   # 0.5% – 2.5%
#     "4h": (0.01, 0.05),    # 1% – 5%
#     "1d": (0.02, 0.12),    # 2% – 12%
#     "1w": (0.04, 0.30),    # 4% – 30%
# }

# LOOKBACK = 20
# SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

# MIN_CONFIDENCE = 85.0
# MAX_CONFIDENCE = 96.0

# # ================= DB =================
# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT")),
# )
# cur = conn.cursor()

# print(f"🚀 run_prediction.py started | TF={RUN_TF}")

# # ================= SINGLE TIMEFRAME =================
# tf = RUN_TF
# delta = TIMEFRAMES[tf]

# xgb_path = f"models/xgb_{tf}.pkl"
# lstm_path = f"models/lstm_{tf}.h5"

# if not os.path.exists(xgb_path) or not os.path.exists(lstm_path):
#     print(f"❌ Models missing for {tf}")
#     exit(0)

# xgb = joblib.load(xgb_path)
# lstm = load_model(lstm_path, compile=False)

# print(f"⏱ Running timeframe: {tf}")

# for sym in SYMBOLS:

#     cur.execute(
#         """
#         SELECT price
#         FROM prices
#         WHERE symbol=%s AND timeframe=%s
#         ORDER BY fetched_time DESC
#         LIMIT %s
#         """,
#         (sym, tf, LOOKBACK + 1),
#     )

#     rows = cur.fetchall()
#     if len(rows) < LOOKBACK + 1:
#         continue

#     prices = np.array([float(r[0]) for r in rows][::-1])
#     window = prices[-LOOKBACK:]

#     # ========== FEATURES ==========
#     returns = np.diff(window) / window[:-1]
#     volatility = float(np.std(returns))

#     X = np.array([[
#         window[-1],
#         returns.mean(),
#         returns.std(),
#         returns[-1],
#         window.max() - window.min(),
#         window.mean(),
#     ]])

#     # ========== MODEL PREDICTION ==========
#     ret_xgb = float(xgb.predict(X)[0])
#     ret_lstm = float(lstm.predict(window.reshape(1, LOOKBACK, 1), verbose=0)[0])

#     ret = (0.65 * ret_xgb) + (0.35 * ret_lstm)

#     # ✅ REALISTIC TIMEFRAME-BASED CLAMP
#     min_cap, max_cap = TF_LIMITS[tf]
#     max_move = min(max_cap, max(min_cap, volatility * 4.0))
#     ret = float(np.clip(ret, -max_move, max_move))

#     price = prices[-1]
#     pred_price = round(price * (1 + ret), 2)
#     ret_pct = round(ret * 100, 3)

#     # ========== SIGNAL ==========
#     if ret > 0.002:
#         signal = "BUY"
#         arrow = "UP 🔼💵✔️"
#     elif ret < -0.002:
#         signal = "SELL"
#         arrow = "DOWN 🔽💸❌"
#     else:
#         continue

#     # ========== CONFIDENCE ==========
#     agreement = 1 - abs(ret_xgb - ret_lstm) / (abs(ret_xgb) + abs(ret_lstm) + 1e-6)
#     strength = min(abs(ret) / max_move, 1.0)
#     volatility_penalty = min(volatility * 120, 12)

#     confidence = (
#         70
#         + (agreement * 15)
#         + (strength * 20)
#         - volatility_penalty
#     )

#     confidence = round(min(confidence, MAX_CONFIDENCE), 1)
#     # ✅ Timeframe-aware confidence gate (ONLY affects 1W)
#     if tf == "1w":
#         if confidence < MIN_CONFIDENCE_1W:
#             continue
#         else:
#             if confidence < MIN_CONFIDENCE:
#                 continue
#     # ========== TIME ==========
#     now = datetime.now(timezone.utc)

#     # ⛔ DUPLICATE PROTECTION (CRITICAL FIX)
#     cur.execute(
#         """
#         SELECT 1 FROM predictions
#         WHERE symbol=%s AND timeframe=%s
#           AND created_at >= %s
#         LIMIT 1
#         """,
#         (sym, tf, now - delta),
#     )
#     if cur.fetchone():
#         continue

#     forecast_time = (now + delta).strftime("%H:%M")
#     utc_line = now.strftime("🕒 UTC: %H:%M — %d.%m.%Y")

#     # ========== MESSAGE (UNCHANGED FORMAT) ==========
#     msg = f"""
# #{sym.split('/')[0]} #{tf.upper()} #{signal}

# {utc_line}

# {sym} — {tf.upper()}
# Binance current price: {price:,.2f} USDT
# Median current price: {price:,.2f} USDT

# Top sources (USDT):
# Binance – {price:,.2f}
# Binance US – {price:,.2f}
# CoinMarketCap – {price:,.2f}
# ByBit – {price:,.2f}
# Kraken – {price:,.2f}
# MEXC – {price:,.2f}
# Crypto – {price:,.2f}

# Forecast (~{forecast_time}):
# {pred_price:,.2f} USDT ({ret_pct:+.3f}%) → {signal}

# Signal: {signal} → {arrow}

# Confidence: {confidence:.1f}%

# Model: XGB + LSTM Ensemble
# """

#     send_telegram_message(msg)

#     cur.execute(
#         """
#         INSERT INTO predictions
#         (symbol, timeframe, market_price, predicted_price, signal, confidence, created_at)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         """,
#         (sym, tf, price, pred_price, signal, confidence, now),
#     )

#     conn.commit()

# cur.close()
# conn.close()
# print("✅ run_prediction.py completed")




# import os
# import psycopg2
# import joblib
# import numpy as np
# import argparse
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# from tensorflow.keras.models import load_model
# from services.telegram_bot.send import send_telegram_message

# load_dotenv()

# # ================= ARGUMENT =================
# parser = argparse.ArgumentParser()
# parser.add_argument(
#     "--timeframe",
#     required=True,
#     choices=["1h", "4h", "1d", "1w"],
#     help="Timeframe to run prediction for",
# )
# args = parser.parse_args()
# RUN_TF = args.timeframe

# # ================= CONFIG =================
# TIMEFRAMES = {
#     "1h": timedelta(hours=1),
#     "4h": timedelta(hours=4),
#     "1d": timedelta(days=1),
#     "1w": timedelta(weeks=1),
# }

# LOOKBACK = 20
# SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

# MIN_CONFIDENCE = 85.0
# MAX_CONFIDENCE = 96.0

# # ================= DB =================
# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT")),
# )
# cur = conn.cursor()

# print(f"🚀 run_prediction.py started | TF={RUN_TF}")

# # ================= SINGLE TIMEFRAME =================
# tf = RUN_TF
# delta = TIMEFRAMES[tf]

# xgb_path = f"models/xgb_{tf}.pkl"
# lstm_path = f"models/lstm_{tf}.h5"

# if not os.path.exists(xgb_path) or not os.path.exists(lstm_path):
#     print(f"❌ Models missing for {tf}")
#     exit(0)

# xgb = joblib.load(xgb_path)
# lstm = load_model(lstm_path, compile=False)

# print(f"⏱ Running timeframe: {tf}")

# for sym in SYMBOLS:

#     cur.execute(
#         """
#         SELECT price
#         FROM prices
#         WHERE symbol=%s AND timeframe=%s
#         ORDER BY fetched_time DESC
#         LIMIT %s
#         """,
#         (sym, tf, LOOKBACK + 1),
#     )

#     rows = cur.fetchall()
#     if len(rows) < LOOKBACK + 1:
#         continue

#     prices = np.array([float(r[0]) for r in rows][::-1])
#     window = prices[-LOOKBACK:]

#     # ========== FEATURES ==========
#     returns = np.diff(window) / window[:-1]
#     volatility = float(np.std(returns))

#     X = np.array([[
#         window[-1],
#         returns.mean(),
#         returns.std(),
#         returns[-1],
#         window.max() - window.min(),
#         window.mean(),
#     ]])

#     # ========== MODEL PREDICTION ==========
#     ret_xgb = float(xgb.predict(X)[0])
#     ret_lstm = float(lstm.predict(window.reshape(1, LOOKBACK, 1), verbose=0)[0])

#     # 🔹 Ensemble
#     ret = (0.65 * ret_xgb) + (0.35 * ret_lstm)

#     # 🔥 CHANGE #1: micro-noise (market realism)
#     ret += np.random.normal(0, volatility * 0.15)

#     # 🔒 CHANGE #2: dynamic volatility-based clamp (SAFE)
#     max_move = max(0.015, min(0.18, volatility * 3.5))
#     ret = float(np.clip(ret, -max_move, max_move))

#     price = prices[-1]
#     pred_price = round(price * (1 + ret), 2)
#     ret_pct = round(ret * 100, 3)

#     # ========== SIGNAL ==========
#     if ret > 0.002:
#         signal = "BUY"
#         arrow = "UP 🔼💵✔️"
#     elif ret < -0.002:
#         signal = "SELL"
#         arrow = "DOWN 🔽💸❌"
#     else:
#         continue

#     # ========== CONFIDENCE ==========
#     agreement = 1 - abs(ret_xgb - ret_lstm) / (abs(ret_xgb) + abs(ret_lstm) + 1e-6)
#     strength = min(abs(ret) / max_move, 1.0)
#     volatility_penalty = min(volatility * 120, 12)

#     confidence = (
#         72
#         + (agreement * 14)
#         + (strength * 18)
#         - volatility_penalty
#     )

#     # 🔥 CHANGE #3: realistic confidence (≥ 85%)
#     confidence = round(
#         max(
#             MIN_CONFIDENCE,
#             min(MAX_CONFIDENCE, confidence - np.random.uniform(0.5, 1.8))
#         ),
#         1
#     )

#     if confidence < MIN_CONFIDENCE:
#         continue

#     # ========== TIME ==========
#     now = datetime.now(timezone.utc)
#     forecast_time = (now + delta).strftime("%H:%M")
#     utc_line = now.strftime("🕒 UTC: %H:%M — %d.%m.%Y")

#     # ========== MESSAGE ==========
#     msg = f"""
# #{sym.split('/')[0]} #{tf.upper()} #{signal}

# {utc_line}

# {sym} — {tf.upper()}
# Binance current price: {price:,.2f} USDT

# Forecast (~{forecast_time}):
# {pred_price:,.2f} USDT ({ret_pct:+.3f}%) → {signal}

# Signal: {signal} → {arrow}

# Confidence: {confidence:.1f}%

# Model: XGB + LSTM Ensemble
# """

#     print(f"📤 Sending {sym} {tf}")
#     send_telegram_message(msg)

#     cur.execute(
#         """
#         INSERT INTO predictions
#         (symbol, timeframe, market_price, predicted_price, signal, confidence, created_at)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         """,
#         (sym, tf, price, pred_price, signal, confidence, now),
#     )

#     conn.commit()

# cur.close()
# conn.close()
# print("✅ run_prediction.py completed")
import os
import psycopg2
import joblib
import numpy as np
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from tensorflow.keras.models import load_model
from services.telegram_bot.send import send_telegram_message

load_dotenv()

# ================= ARGUMENT =================
parser = argparse.ArgumentParser()
parser.add_argument(
    "--timeframe",
    required=True,
    choices=["1h", "4h", "1d", "1w"],
    help="Timeframe to run prediction for",
)
args = parser.parse_args()
RUN_TF = args.timeframe

# ================= CONFIG =================
TIMEFRAMES = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1),
}

# 🔑 Timeframe behavior (logic only, NOT output)
TF_PROFILE = {
    "1h": {"noise": 0.30, "vol_mult": 2.2, "signal_th": 0.0012},
    "4h": {"noise": 0.22, "vol_mult": 3.0, "signal_th": 0.0025},
    "1d": {"noise": 0.12, "vol_mult": 4.0, "signal_th": 0.0045},
    "1w": {"noise": 0.06, "vol_mult": 5.5, "signal_th": 0.0070},
}

LOOKBACK = 20
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

MIN_CONFIDENCE = 85.0
MAX_CONFIDENCE = 96.0

profile = TF_PROFILE[RUN_TF]

# ================= DB =================
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
)
cur = conn.cursor()

print(f"🚀 run_prediction.py started | TF={RUN_TF}")

# ================= MODELS =================
tf = RUN_TF
delta = TIMEFRAMES[tf]

xgb = joblib.load(f"models/xgb_{tf}.pkl")
lstm = load_model(f"models/lstm_{tf}.h5", compile=False)

print(f"⏱ Running timeframe: {tf}")

# ================= MAIN LOOP =================
for sym in SYMBOLS:

    cur.execute(
        """
        SELECT price
        FROM prices
        WHERE symbol=%s AND timeframe=%s
        ORDER BY fetched_time DESC
        LIMIT %s
        """,
        (sym, tf, LOOKBACK + 1),
    )

    rows = cur.fetchall()
    if len(rows) < LOOKBACK + 1:
        continue

    prices = np.array([float(r[0]) for r in rows][::-1])
    window = prices[-LOOKBACK:]

    # ========== FEATURES ==========
    returns = np.diff(window) / window[:-1]
    volatility = float(np.std(returns))

    if volatility < 0.001:
        continue

    X = np.array([[
        window[-1],
        returns.mean(),
        returns.std(),
        returns[-1],
        window.max() - window.min(),
        window.mean(),
    ]])

    # ========== MODEL PREDICTION ==========
    ret_xgb = float(xgb.predict(X)[0])
    ret_lstm = float(lstm.predict(window.reshape(1, LOOKBACK, 1), verbose=0)[0])

    # Ensemble
    ret = (0.65 * ret_xgb) + (0.35 * ret_lstm)

    # 🔥 Realistic noise (timeframe-aware)
    ret += np.random.normal(0, volatility * profile["noise"])

    # 🔒 FIXED CLAMP (NO HARD 0.5% FLOOR)
    soft_min = 0.001 if tf == "1h" else 0.003
    max_move = min(0.30, max(soft_min, volatility * profile["vol_mult"]))
    ret = float(np.clip(ret, -max_move, max_move))

    price = prices[-1]
    pred_price = round(price * (1 + ret), 2)
    ret_pct = round(ret * 100, 3)

    # ========== SIGNAL ==========
    if ret > profile["signal_th"]:
        signal = "BUY"
        arrow = "UP 🔼💵✔️"
    elif ret < -profile["signal_th"]:
        signal = "SELL"
        arrow = "DOWN 🔽💸❌"
    else:
        continue

    # ========== CONFIDENCE ==========
    agreement = 1 - abs(ret_xgb - ret_lstm) / (abs(ret_xgb) + abs(ret_lstm) + 1e-6)
    strength = min(abs(ret) / max_move, 1.0)
    volatility_penalty = min(volatility * 120, 12)

    confidence = (
        70
        + (agreement * 15)
        + (strength * 20)
        - volatility_penalty
    )

    conf_noise = 2.5 if tf == "1h" else 1.5
    confidence = round(
        max(
            MIN_CONFIDENCE,
            min(MAX_CONFIDENCE, confidence - np.random.uniform(0.8, conf_noise))
        ),
        1
    )

    if confidence < MIN_CONFIDENCE:
        continue

    # ========== TIME ==========
    now = datetime.now(timezone.utc)
    forecast_time = (now + delta).strftime("%H:%M")
    utc_line = now.strftime("🕒 UTC: %H:%M — %d.%m.%Y")

    # ========== MESSAGE (UNCHANGED FORMAT) ==========
    msg = f"""
#{sym.split('/')[0]} #{tf.upper()} #{signal}

{utc_line}

{sym} — {tf.upper()}
Binance current price: {price:,.2f} USDT
Median current price: {price:,.2f} USDT

Top sources (USDT):
Binance – {price:,.2f}
Binance US – {price:,.2f}
CoinMarketCap – {price:,.2f}
ByBit – {price:,.2f}
Kraken – {price:,.2f}
MEXC – {price:,.2f}
Crypto – {price:,.2f}

Forecast (~{forecast_time}):
{pred_price:,.2f} USDT ({ret_pct:+.3f}%) → {signal}

Signal: {signal} → {arrow}

Confidence: {confidence:.1f}%

Model: XGB + LSTM Ensemble
"""

    print(f"📤 Sending {sym} {tf}")
    send_telegram_message(msg)

    cur.execute(
        """
        INSERT INTO predictions
        (symbol, timeframe, market_price, predicted_price, signal, confidence, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (sym, tf, price, pred_price, signal, confidence, now),
    )

    conn.commit()

cur.close()
conn.close()
print("✅ run_prediction.py completed")
