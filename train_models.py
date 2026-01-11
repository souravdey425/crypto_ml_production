# import os
# import psycopg2
# import joblib
# import numpy as np
# from dotenv import load_dotenv
# from xgboost import XGBRegressor
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import LSTM, Dense
# from tensorflow.keras.callbacks import EarlyStopping
# from sklearn.model_selection import train_test_split

# load_dotenv()

# TIMEFRAMES = ["1h", "4h", "1d", "1w"]
# LOOKBACK = 20

# os.makedirs("models", exist_ok=True)

# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT")),
# )
# cur = conn.cursor()

# for tf in TIMEFRAMES:
#     print(f"🧠 Training {tf}")

#     cur.execute("""
#         SELECT price FROM prices
#         WHERE timeframe=%s
#         ORDER BY fetched_time
#     """, (tf,))
#     prices = np.array([float(r[0]) for r in cur.fetchall()])

#     if len(prices) < 600:
#         print(f"⚠️ Not enough data for {tf}")
#         continue

#     X, y = [], []
#     for i in range(LOOKBACK, len(prices) - 1):
#         window = prices[i - LOOKBACK:i]
#         returns = np.diff(window) / window[:-1]

#         X.append([
#             window[-1],
#             returns.mean(),
#             returns.std(),
#             returns[-1],
#             window.max() - window.min(),
#             window.mean(),
#         ])
#         y.append((prices[i + 1] - prices[i]) / prices[i])

#     X = np.array(X)
#     y = np.array(y)

#     X_train, X_val, y_train, y_val = train_test_split(
#         X, y, test_size=0.2, shuffle=False
#     )

#     # ---------- XGB ----------
#     xgb = XGBRegressor(
#         n_estimators=250,
#         max_depth=4,
#         learning_rate=0.05,
#         subsample=0.85,
#         colsample_bytree=0.85,
#         n_jobs=2,
#         tree_method="hist",
#     )
#     xgb.fit(X_train, y_train)
#     joblib.dump(xgb, f"models/xgb_{tf}.pkl")

#     # ---------- LSTM ----------
#     X_lstm = []
#     for i in range(LOOKBACK, len(prices) - 1):
#         X_lstm.append(prices[i - LOOKBACK:i])

#     X_lstm = np.array(X_lstm).reshape(-1, LOOKBACK, 1)
#     y_lstm = y

#     split = int(len(X_lstm) * 0.8)
#     Xl_train, Xl_val = X_lstm[:split], X_lstm[split:]
#     yl_train, yl_val = y_lstm[:split], y_lstm[split:]

#     lstm = Sequential([
#         LSTM(32, input_shape=(LOOKBACK, 1)),
#         Dense(1),
#     ])
#     lstm.compile(optimizer="adam", loss="mse")

#     lstm.fit(
#         Xl_train,
#         yl_train,
#         validation_data=(Xl_val, yl_val),
#         epochs=6,
#         batch_size=64,
#         callbacks=[EarlyStopping(patience=2, restore_best_weights=True)],
#         verbose=0,
#     )

#     lstm.save(f"models/lstm_{tf}.h5")

#     preds = xgb.predict(X_val)
#     win_rate = np.mean(np.sign(preds) == np.sign(y_val))
#     confidence = round(50 + win_rate * 40, 2)

#     with open(f"models/conf_{tf}.txt", "w") as f:
#         f.write(str(confidence))

#     print(f"✅ {tf} trained | confidence={confidence}%")

# cur.close()
# conn.close()
# print("🎯 Training complete")
# import os, psycopg2, joblib, numpy as np
# from dotenv import load_dotenv
# from xgboost import XGBRegressor
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import LSTM, Dense
# from sklearn.preprocessing import StandardScaler

# load_dotenv()

# TIMEFRAMES = ["1h","4h","1d","1w"]
# LOOKBACK = 20

# os.makedirs("models", exist_ok=True)

# conn = psycopg2.connect(
#     dbname=os.getenv("DB_NAME"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     host=os.getenv("DB_HOST"),
#     port=int(os.getenv("DB_PORT"))
# )
# cur = conn.cursor()

# for tf in TIMEFRAMES:

#     cur.execute("""
#         SELECT price FROM prices
#         WHERE timeframe=%s
#         ORDER BY fetched_time
#     """, (tf,))
#     prices = np.array([float(r[0]) for r in cur.fetchall()])

#     if len(prices) < 1000:
#         print(f"⚠️ Not enough data for {tf}")
#         continue

#     X, y = [], []

#     for i in range(LOOKBACK, len(prices)-LOOKBACK):
#         window = prices[i-LOOKBACK:i]
#         future = prices[i+LOOKBACK]

#         # normalized future return
#         ret = (future - prices[i]) / prices[i]

#         # suppress noise
#         if abs(ret) < 0.0008:
#             ret = 0.0

#         returns = np.diff(window) / window[:-1]

#         X.append([
#             window[-1],
#             returns.mean(),
#             returns.std(),
#             returns[-1],
#             window.max() - window.min(),
#             window.mean(),
#         ])
#         y.append(ret)

#     X = np.array(X)
#     y = np.array(y)

#     # ---------- SCALE FEATURES ----------
#     scaler = StandardScaler()
#     X_scaled = scaler.fit_transform(X)

#     joblib.dump(scaler, f"models/scaler_{tf}.pkl")

#     # ---------- XGB ----------
#     xgb = XGBRegressor(
#         n_estimators=300,
#         max_depth=4,
#         learning_rate=0.04,
#         subsample=0.8,
#         colsample_bytree=0.8,
#         reg_lambda=2.0,
#         random_state=42
#     )
#     xgb.fit(X_scaled, y)
#     joblib.dump(xgb, f"models/xgb_{tf}.pkl")

#     # ---------- LSTM ----------
#     X_lstm = []
#     for i in range(LOOKBACK, len(prices)-LOOKBACK):
#         X_lstm.append(
#             (prices[i-LOOKBACK:i] - prices[i-LOOKBACK:i].mean()) /
#             (prices[i-LOOKBACK:i].std() + 1e-6)
#         )

#     X_lstm = np.array(X_lstm).reshape(-1, LOOKBACK, 1)
#     y_lstm = y

#     lstm = Sequential([
#         LSTM(32, input_shape=(LOOKBACK,1)),
#         Dense(1)
#     ])
#     lstm.compile(optimizer="adam", loss="mse")
#     lstm.fit(X_lstm, y_lstm, epochs=6, batch_size=64, verbose=0)
#     lstm.save(f"models/lstm_{tf}.h5")

#     print(f"✅ {tf} trained")

# cur.close()
# conn.close()
import os
import psycopg2
import joblib
import numpy as np
from dotenv import load_dotenv
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

load_dotenv()

TIMEFRAMES = ["1h", "4h", "1d", "1w"]
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
    print(f"🧠 Training {tf}")

    cur.execute("""
        SELECT price FROM prices
        WHERE timeframe=%s
        ORDER BY fetched_time
    """, (tf,))
    prices = np.array([float(r[0]) for r in cur.fetchall()])

    if len(prices) < 800:
        print(f"⚠️ Not enough data for {tf}")
        continue

    X, y = [], []

    for i in range(LOOKBACK, len(prices) - 1):
        window = prices[i - LOOKBACK:i]
        returns = np.diff(window) / window[:-1]

        X.append([
            window[-1],
            returns.mean(),
            returns.std(),
            returns[-1],
            window.max() - window.min(),
            window.mean()
        ])

        y.append((prices[i + 1] - prices[i]) / prices[i])

    X = np.array(X)
    y = np.clip(np.array(y), -0.05, 0.05)  # 🔒 prevent explosion

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, f"models/scaler_{tf}.pkl")

    # ---------- XGBOOST ----------
    xgb = XGBRegressor(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="reg:squarederror",
        random_state=42
    )
    xgb.fit(X_scaled, y)
    joblib.dump(xgb, f"models/xgb_{tf}.pkl")

    # ---------- LSTM ----------
    X_lstm = []
    for i in range(LOOKBACK, len(prices) - 1):
        X_lstm.append(prices[i - LOOKBACK:i])

    X_lstm = np.array(X_lstm).reshape(-1, LOOKBACK, 1)

    lstm = Sequential([
        LSTM(32, input_shape=(LOOKBACK, 1)),
        Dense(1)
    ])
    lstm.compile(optimizer="adam", loss="mse")

    lstm.fit(
        X_lstm,
        y,
        epochs=8,
        batch_size=32,
        callbacks=[EarlyStopping(patience=2, restore_best_weights=True)],
        verbose=0
    )

    lstm.save(f"models/lstm_{tf}.h5")

    print(f"✅ {tf} trained")

cur.close()
conn.close()
print("🎯 TRAINING COMPLETE")
