
# def save_prediction(conn, symbol, timeframe, generated_time,
#                     market_price, predicted_price, signal, confidence):
#     with conn.cursor() as cur:
#         cur.execute("""
#             INSERT INTO predictions
#             (symbol, timeframe, generated_time,
#              market_price, predicted_price, signal, confidence)
#             VALUES (%s,%s,%s,%s,%s,%s,%s)
#         """, (
#             symbol, timeframe, generated_time,
#             float(market_price), float(predicted_price),
#             signal, float(confidence)
#         ))
#     conn.commit()
def save_prediction(
    conn,
    symbol,
    timeframe,
    generated_time,
    market_price,
    predicted_price,
    signal,
    confidence
):
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO predictions
        (symbol, timeframe, generated_time, market_price, predicted_price, signal, confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            symbol,
            timeframe,
            generated_time,
            market_price,
            predicted_price,
            signal,
            confidence
        )
    )

    conn.commit()
    cur.close()
