import numpy as np

def trend_direction(prices, short=10, long=30):
    if len(prices) < long:
        return 0

    short_ema = np.mean(prices[-short:])
    long_ema = np.mean(prices[-long:])

    if short_ema > long_ema * 1.002:
        return 1     # uptrend
    elif short_ema < long_ema * 0.998:
        return -1    # downtrend
    else:
        return 0     # sideways
