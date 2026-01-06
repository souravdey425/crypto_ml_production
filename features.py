
# import numpy as np

# def build_features(prices, window=10):
#     """
#     prices: list of floats (old → new)
#     """

#     prices = np.array(prices[-window:])

#     returns = np.diff(prices) / prices[:-1]

#     features = [
#         prices[-1],                      # current price
#         prices.mean(),                   # trend
#         prices.std(),                    # volatility
#         prices.max() - prices.min(),     # range
#         returns.mean(),                  # avg return
#         returns.std(),                   # return volatility
#         returns[-1],                     # momentum
#     ]

#     return np.array(features).reshape(1, -1)
import numpy as np
import pandas as pd

def rsi(prices, period=14):
    prices = pd.Series(prices)
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ema(prices, period):
    return pd.Series(prices).ewm(span=period).mean()

def build_features(prices):
    prices = np.array(prices)

    returns = (prices[-1] - prices[-2]) / prices[-2]
    volatility = np.std(np.diff(prices) / prices[:-1])

    rsi_val = rsi(prices).iloc[-1]
    ema_fast = ema(prices, 9).iloc[-1]
    ema_slow = ema(prices, 21).iloc[-1]

    trend = 1 if ema_fast > ema_slow else -1

    return {
        "return": returns,
        "volatility": volatility,
        "rsi": rsi_val,
        "trend": trend
    }
