import os, psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
from services.telegram_bot.send import send_telegram_message

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT"))
)
cur = conn.cursor()

cur.execute("""
    SELECT id,symbol,timeframe,market_price,signal,created_at
    FROM predictions
    WHERE resolved=false
""")

for pid,sym,tf,price,signal,created in cur.fetchall():
    cur.execute("""
        SELECT price FROM prices
        WHERE symbol=%s AND timeframe=%s
        ORDER BY fetched_time DESC LIMIT 1
    """, (sym,tf))
    now_price = float(cur.fetchone()[0])

    outcome = "WIN ✅" if (
        (signal=="BUY" and now_price>price) or
        (signal=="SELL" and now_price<price)
    ) else "LOSS ❌"

    send_telegram_message(
        f"📊 RESULT {sym} {tf.upper()} → {outcome}\nEntry: {price}\nExit: {now_price}"
    )

    cur.execute("UPDATE predictions SET resolved=true WHERE id=%s",(pid,))

conn.commit()
cur.close()
conn.close()
