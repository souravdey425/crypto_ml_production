# import os
# import psycopg2
# import numpy as np
# import joblib
# from dotenv import load_dotenv
# from xgboost import XGBRegressor

# load_dotenv()

# SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","XRP/USDT"]
# TIMEFRAMES = ["1h","4h","1d","1w"]

# WINDOW = 20
# MIN_SAMPLES = 500

# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT"))
# )
# cur = conn.cursor()

# os.makedirs("models", exist_ok=True)

# for tf in TIMEFRAMES:
#     X, y = [], []

#     for symbol in SYMBOLS:
#         cur.execute("""
#             SELECT price FROM prices
#             WHERE symbol=%s AND timeframe=%s
#             ORDER BY fetched_time
#         """, (symbol, tf))

#         prices = [float(r[0]) for r in cur.fetchall()]
#         if len(prices) < WINDOW + 2:
#             continue

#         for i in range(WINDOW, len(prices)-1):
#             window = prices[i-WINDOW:i]
#             ret = (prices[i+1] - prices[i]) / prices[i]

#             features = [
#                 prices[i],
#                 np.mean(window),
#                 np.std(window),
#                 (prices[i] - prices[i-1]) / prices[i-1],
#                 np.max(window) - np.min(window),
#                 np.std(np.diff(window))
#             ]

#             X.append(features)
#             y.append(ret)

#     if len(X) < MIN_SAMPLES:
#         print(f"❌ Not enough data for {tf}")
#         continue

#     model = XGBRegressor(
#         n_estimators=400,
#         max_depth=5,
#         learning_rate=0.03,
#         subsample=0.9,
#         colsample_bytree=0.9,
#         random_state=42
#     )

#     model.fit(np.array(X), np.array(y))
#     joblib.dump(model, f"models/xgb_{tf}.pkl")

#     print(f"✅ Model trained: {tf}")

# cur.close()
# conn.close()
# import os, psycopg2, joblib, numpy as np
# from dotenv import load_dotenv
# from xgboost import XGBRegressor

# load_dotenv()

# TIMEFRAMES = ["1h","4h","1d","1w"]

# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT"))
# )
# cur = conn.cursor()

# os.makedirs("models", exist_ok=True)

# for tf in TIMEFRAMES:
#     X, y = [], []

#     cur.execute("""
#         SELECT symbol, price FROM prices
#         WHERE timeframe=%s
#         ORDER BY fetched_time
#     """, (tf,))

#     rows = cur.fetchall()
#     prices = [r[1] for r in rows]

#     if len(prices) < 150:
#         print(f"⚠️ Not enough data for {tf}")
#         continue

#     for i in range(20, len(prices)-1):
#         window = prices[i-20:i]
#         features = [
#             prices[i],
#             np.mean(np.diff(window)/window[:-1]),
#             np.std(np.diff(window)/window[:-1]),
#             (prices[i]-prices[i-1])/prices[i-1],
#             np.max(window)-np.min(window),
#             np.mean(window)
#         ]
#         X.append(features)
#         y.append((prices[i+1]-prices[i])/prices[i])

#     model = XGBRegressor(
#         n_estimators=500,
#         max_depth=5,
#         learning_rate=0.03,
#         subsample=0.9,
#         colsample_bytree=0.9
#     )

#     model.fit(np.array(X), np.array(y))
#     joblib.dump(model, f"models/xgb_{tf}.pkl")
#     print(f"✅ Model trained: {tf}")

# cur.close()
# conn.close()
import os, psycopg2, joblib, numpy as np
from dotenv import load_dotenv
from xgboost import XGBRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split

load_dotenv()

TIMEFRAMES = ["1h","4h","1d","1w"]
LOOKBACK = 20

os.makedirs("models", exist_ok=True)

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT"))
)
cur = conn.cursor()

for tf in TIMEFRAMES:
    cur.execute("""
        SELECT price FROM prices
        WHERE timeframe=%s
        ORDER BY fetched_time
    """, (tf,))
    prices = np.array([float(r[0]) for r in cur.fetchall()])

    if len(prices) < 500:
        print(f"⚠️ Not enough data for {tf}")
        continue

    X, y = [], []
    for i in range(LOOKBACK, len(prices)-1):
        window = prices[i-LOOKBACK:i]
        returns = np.diff(window) / window[:-1]
        X.append([
            window[-1],
            returns.mean(),
            returns.std(),
            returns[-1],
            window.max() - window.min(),
            window.mean()
        ])
        y.append((prices[i+1]-prices[i])/prices[i])

    X = np.array(X)
    y = np.array(y)

    # ---------- XGB ----------
    xgb = XGBRegressor(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.9
    )
    xgb.fit(X, y)
    joblib.dump(xgb, f"models/xgb_{tf}.pkl")

    # ---------- LSTM ----------
    X_lstm = []
    for i in range(LOOKBACK, len(prices)-1):
        X_lstm.append(prices[i-LOOKBACK:i])
    X_lstm = np.array(X_lstm).reshape(-1, LOOKBACK, 1)

    y_lstm = y

    lstm = Sequential([
        LSTM(32, input_shape=(LOOKBACK,1)),
        Dense(1)
    ])
    lstm.compile(optimizer="adam", loss="mse")
    lstm.fit(X_lstm, y_lstm, epochs=10, batch_size=32, verbose=0)
    lstm.save(f"models/lstm_{tf}.h5")

    # ---------- BACKTEST CONFIDENCE ----------
    preds = xgb.predict(X)
    wins = np.mean(np.sign(preds) == np.sign(y))
    confidence = round(50 + wins * 40, 2)

    with open(f"models/conf_{tf}.txt","w") as f:
        f.write(str(confidence))

    print(f"✅ {tf} trained | confidence={confidence}%")

cur.close()
conn.close()
