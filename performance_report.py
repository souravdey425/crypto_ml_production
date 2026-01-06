import os, psycopg2
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
    SELECT signal,
    COUNT(*) FILTER (WHERE resolved=true AND result='WIN') AS wins,
    COUNT(*) FILTER (WHERE resolved=true) AS total
    FROM predictions
    GROUP BY signal
""")

text = "📈 PERFORMANCE SUMMARY\n\n"
for s,w,t in cur.fetchall():
    if t>0:
        text += f"{s}: {w}/{t} ({w/t*100:.1f}%)\n"

send_telegram_message(text)
cur.close()
conn.close()
