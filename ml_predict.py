# import numpy as np
# import joblib

# model = joblib.load("models/xgb_model.pkl")

# WINDOW = 20

# def predict(prices):
#     if len(prices) < WINDOW + 2:
#         raise ValueError("Not enough prices for prediction")

#     prices = np.array(prices)
#     window = prices[-WINDOW:]
#     returns = np.diff(window) / window[:-1]

#     # ======================
#     # FEATURES (MUST MATCH TRAINING)
#     # ======================
#     X = np.array([[
#         prices[-1],                          # price
#         np.mean(returns),                    # mean return
#         np.std(returns),                     # volatility
#         (prices[-1] - prices[-2]) / prices[-2],  # momentum
#         np.max(window) / prices[-1] - 1,     # high ratio
#         prices[-1] / np.min(window) - 1      # low ratio
#     ]])

#     predicted_return = float(model.predict(X)[0])

#     # ======================
#     # SIGNAL LOGIC
#     # ======================
#     if predicted_return > 0.002:
#         signal = "BUY"
#     elif predicted_return < -0.002:
#         signal = "SELL"
#     else:
#         signal = "HOLD"

#     # ======================
#     # REAL CONFIDENCE (NOT FAKE)
#     # ======================
#     strength = min(abs(predicted_return) * 12000, 30)
#     volatility_penalty = np.std(returns) * 800

#     confidence = 55 + strength - volatility_penalty
#     confidence = max(55, min(confidence, 88))

#     return predicted_return, confidence, signal
import numpy as np
import joblib

WINDOW = 20

def predict(prices, model, timeframe):
    prices = np.array(prices)

    # ---------- Base features (same as training) ----------
    returns = np.diff(prices) / prices[:-1]
    features = np.array([[
        prices[-1],
        returns.mean(),
        returns.std(),
        returns[-1],
        ema(prices, 14),
        rsi(prices, 14)
    ]])

    predicted_return = float(model.predict(features)[0])

    # ---------- SIGNAL ----------
    if predicted_return > 0.002:
        signal = "BUY"
    elif predicted_return < -0.002:
        signal = "SELL"
    else:
        signal = "HOLD"

    # ---------- CONFIDENCE SCALING ----------
    confidence = 50  # base

    # 1️⃣ Model conviction (bigger move → more confidence)
    confidence += min(abs(predicted_return) * 4000, 15)

    # 2️⃣ Trend alignment (EMA)
    price_vs_ema = (prices[-1] - ema(prices)) / prices[-1]
    if signal == "BUY" and price_vs_ema > 0:
        confidence += 10
    if signal == "SELL" and price_vs_ema < 0:
        confidence += 10

    # 3️⃣ RSI confirmation
    r = rsi(prices)
    if signal == "BUY" and r < 70:
        confidence += 10
    if signal == "SELL" and r > 30:
        confidence += 10

    # 4️⃣ Volatility penalty (choppy market)
    if returns.std() > 0.01:
        confidence -= 10

    # 5️⃣ Timeframe weight (higher TF = more trust)
    tf_weight = {
        "1h": 0,
        "4h": 5,
        "1d": 10,
        "1w": 15
    }
    confidence += tf_weight.get(timeframe, 0)

    # Clamp
    confidence = max(45, min(confidence, 92))

    return predicted_return, confidence, signal


def ema(prices, period=14):
    prices = np.array(prices)
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    return np.convolve(prices, weights, mode='valid')[-1]

def rsi(prices, period=14):
    prices = np.array(prices)
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.abs(np.minimum(deltas, 0))

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:]) + 1e-9

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
