import os
import psycopg2
from dotenv import load_dotenv

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
    INSERT INTO prices (symbol, exchange, price)
    VALUES ('TEST/USDT', 'manual', 999.99)
""")

conn.commit()
cur.close()
conn.close()

print("✅ Test row inserted into LOCAL PostgreSQL")
