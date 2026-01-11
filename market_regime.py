import numpy as np

def detect_market_regime(close_prices):
    """
    Detects BTC market regime
    Returns: BULL / BEAR / SIDEWAYS
    """
    closes = np.array(close_prices)

    if len(closes) < 50:
        return "SIDEWAYS"

    returns = np.diff(closes) / closes[:-1]
    volatility = np.std(returns)

    short_ma = closes[-20:].mean()
    long_ma = closes[-50:].mean()

    if short_ma > long_ma and volatility < 0.02:
        return "BULL"

    if short_ma < long_ma and volatility > 0.015:
        return "BEAR"

    return "SIDEWAYS"
