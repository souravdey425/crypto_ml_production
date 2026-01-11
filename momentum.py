import numpy as np

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50

    deltas = np.diff(prices[-(period+1):])
    gains = deltas[deltas > 0].sum() / period
    losses = -deltas[deltas < 0].sum() / period

    if losses == 0:
        return 100

    rs = gains / losses
    return 100 - (100 / (1 + rs))
