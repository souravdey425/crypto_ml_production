import numpy as np

def calculate_atr(prices, period=14):
    prices = np.array(prices, dtype=float)
    return np.mean(np.abs(np.diff(prices))[-period:])
