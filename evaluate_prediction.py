import os, psycopg2
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from services.telegram_bot.send import send_telegram_message

load_dotenv()

DELAYS = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1)
}

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT"))
)
cur = conn.cursor()

now = datetime.now(timezone.utc)

for tf, delta in DELAYS.items():
    cur.execute("""
        SELECT id,symbol,predicted_price,created_at
        FROM predictions
        WHERE timeframe=%s AND evaluated=false
        AND created_at <= %s
    """, (tf, now-delta))

    for pid, sym, pred, created in cur.fetchall():
        cur.execute("""
            SELECT price FROM prices
            WHERE symbol=%s AND timeframe=%s
            ORDER BY fetched_time DESC LIMIT 1
        """, (sym, tf))

        actual = cur.fetchone()[0]
        correct = "✅" if (actual-pred)*(pred)>0 else "❌"

        send_telegram_message(
            f"📊 RESULT {sym} {tf.upper()}\nPredicted: {pred:,.2f}\nActual: {actual:,.2f}\n{correct}"
        )

        cur.execute("""
            UPDATE predictions
            SET evaluated=true, actual_price=%s
            WHERE id=%s
        """, (actual, pid))

    conn.commit()

cur.close()
conn.close()
