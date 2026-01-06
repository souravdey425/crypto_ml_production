import pandas as pd
import numpy as np

def compute_rsi(prices, period=14):
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1])


def compute_ema(prices, period):
    return float(pd.Series(prices).ewm(span=period).mean().iloc[-1])


def build_indicators(prices):
    return {
        "rsi": compute_rsi(prices),
        "ema_fast": compute_ema(prices, 9),
        "ema_slow": compute_ema(prices, 21),
        "volatility": float(np.std(prices[-10:])),
        "momentum": float((prices[-1] - prices[-2]) / prices[-2])
    }