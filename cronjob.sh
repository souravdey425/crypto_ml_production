#!/bin/sh
set -e

echo "===== CRON RUN $(date -u) ====="
cd /app || exit 1

# ---------- LOAD ENV ----------
if [ -f /app/.env ]; then
  set -a
  . /app/.env
  set +a
  echo "ENV LOADED"
else
  echo "❌ .env not found"
  exit 1
fi

# ---------- LOCK ----------
LOCK="/tmp/cronjob.lock"
if [ -f "$LOCK" ]; then
  echo "⏸ Previous run still active, skipping"
  exit 0
fi
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# ---------- WAIT FOR DB ----------
echo "⏳ Waiting for PostgreSQL..."
until python3 - <<EOF
import psycopg2, os
psycopg2.connect(
  dbname=os.getenv("DB_NAME"),
  user=os.getenv("DB_USER"),
  password=os.getenv("DB_PASSWORD"),
  host=os.getenv("DB_HOST"),
  port=int(os.getenv("DB_PORT"))
)
print("✅ PostgreSQL ready")
EOF
do
  sleep 5
done

# ---------- TIME ----------
HOUR=$(date -u +"%H")
HOUR=$(expr "$HOUR" + 0) 
DOW=$(date -u +"%u")
echo "🕒 UTC HOUR=$HOUR | DOW=$DOW"

# ---------- PRICE FETCH ----------
echo "▶ price_fetcher"
python3 price_fetcher.py || true

# ---------- TRAIN (DAILY) ----------
if [ "$HOUR" -eq 0 ]; then
  echo "🧠 Training models"
  python3 train_models.py || true
fi

# ---------- 1H ----------
echo "▶ 1H prediction"
python3 run_prediction.py --timeframe 1h || true

# ---------- 4H ----------
if [ $((HOUR % 4)) -eq 0 ]; then
  echo "▶ 4H prediction"
  python3 run_prediction.py --timeframe 4h || true
fi

# ---------- 1D ----------
if [ "$HOUR" -ge 19 ]; then
  echo "▶ 1D prediction"
  python3 run_prediction.py --timeframe 1d || true
fi

# ---------- 1W ----------
if [ "$DOW" -ge 5 ]; then
  echo "▶ 1W prediction"
  python3 run_prediction.py --timeframe 1w || true
fi

echo "===== END RUN ====="

# #!/bin/sh
# set -e

# echo "===== CRON RUN $(date -u) ====="

# cd /app || exit 1

# # Load env
# if [ -f /app/.env ]; then
#   export $(grep -v '^#' /app/.env | xargs)
#   echo "ENV LOADED"
# else
#   echo "❌ .env not found"
#   exit 1
# fi

# # Wait for DB
# echo "⏳ Waiting for PostgreSQL..."
# until python3 - <<EOF
# import psycopg2, os
# psycopg2.connect(
#   dbname=os.getenv("DB_NAME"),
#   user=os.getenv("DB_USER"),
#   password=os.getenv("DB_PASSWORD"),
#   host=os.getenv("DB_HOST"),
#   port=int(os.getenv("DB_PORT"))
# )
# print("✅ PostgreSQL ready")
# EOF
# do
#   sleep 5
# done

# # ---------- TIME ----------
# HOUR=$(date -u +"%H")
# HOUR=$(printf "%d" "$HOUR")  # ✅ FIXED
# DOW=$(date -u +"%u") # 1=Mon … 7=Sun

# echo "🕒 UTC HOUR=$HOUR | DOW=$DOW"

# # ---------- PRICE FETCH ----------
# echo "▶ price_fetcher"
# python3 price_fetcher.py || true

# # ---------- TRAIN (once per day) ----------
# if [ "$HOUR" -eq 0 ]; then
#   echo "🧠 Training models"
#   python3 train_models.py || true
# fi

# # ---------- 1H ----------
# echo "▶ 1H prediction"
# python3 run_prediction.py --timeframe 1h || true

# # ---------- 4H ----------
# if [ $((HOUR % 4)) -eq 0 ]; then
#   echo "▶ 4H prediction"
#   python3 run_prediction.py --timeframe 4h || true
# fi

# # ---------- 1D (evening UTC) ----------
# if [ "$HOUR" -ge 19 ]; then
#   echo "▶ 1D prediction"
#   python3 run_prediction.py --timeframe 1d || true
# fi

# # ---------- 1W (Fri–Sun) ----------
# if [ "$DOW" -ge 5 ]; then
#   echo "▶ 1W prediction"
#   python3 run_prediction.py --timeframe 1w || true
# fi

# echo "===== END RUN ====="

# #!/bin/sh
# set -euo pipefail

# TF="${1:-}"

# echo "===== CRON RUN $(date -u) | TF=${TF} ====="

# cd /app || exit 1

# # ---------------- LOAD ENV ----------------
# if [ -f /app/.env ]; then
#   export $(grep -v '^#' /app/.env | xargs)
#   echo "ENV LOADED"
# else
#   echo "❌ .env not found"
#   exit 1
# fi

# # ---------------- WAIT FOR DB ----------------
# echo "⏳ Waiting for PostgreSQL..."
# until python3 - <<EOF
# import psycopg2, os
# psycopg2.connect(
#   dbname=os.getenv("DB_NAME"),
#   user=os.getenv("DB_USER"),
#   password=os.getenv("DB_PASSWORD"),
#   host=os.getenv("DB_HOST"),
#   port=int(os.getenv("DB_PORT"))
# )
# print("✅ PostgreSQL ready")
# EOF
# do
#   sleep 5
# done

# # ---------------- FETCH PRICES ----------------
# echo "▶ price_fetcher"
# python3 price_fetcher.py || echo "⚠️ price_fetcher failed"

# # ---------------- TRAIN (ONLY DAILY/WEEKLY) ----------------
# if [ "$TF" = "1d" ] || [ "$TF" = "1w" ]; then
#   if [ "$(date -u +%H)" = "00" ]; then
#     echo "▶ train_models"
#     python3 train_models.py || echo "⚠️ train_models failed"
#   fi
# fi

# # ---------------- RUN PREDICTION ----------------
# if [ -n "$TF" ]; then
#   echo "▶ run_prediction --timeframe $TF"
#   python3 run_prediction.py --timeframe "$TF" || echo "⚠️ run_prediction failed"
# else
#   echo "⚠️ No timeframe passed — skipping prediction"
# fi

# echo "===== END RUN ====="

# #!/bin/sh
# set -e

# TF="$1"

# echo "===== CRON RUN $(date -u) | TF=${TF} ====="

# cd /app || exit 1

# # Load env
# if [ -f /app/.env ]; then
#   export $(grep -v '^#' /app/.env | xargs)
#   echo "ENV LOADED"
# else
#   echo "❌ .env not found"
#   exit 1
# fi

# # Wait for DB
# echo "⏳ Waiting for PostgreSQL..."
# until python3 - <<EOF
# import psycopg2, os
# psycopg2.connect(
#   dbname=os.getenv("DB_NAME"),
#   user=os.getenv("DB_USER"),
#   password=os.getenv("DB_PASSWORD"),
#   host=os.getenv("DB_HOST"),
#   port=int(os.getenv("DB_PORT"))
# )
# print("✅ PostgreSQL ready")
# EOF
# do
#   sleep 5
# done

# # Fetch prices
# echo "▶ price_fetcher"
# python3 price_fetcher.py

# # Train models once daily
# if [ "$(date -u +%H)" = "00" ]; then
#   echo "▶ train_models"
#   python3 train_models.py || true
# fi

# # Run prediction
# if [ -n "$TF" ]; then
#   echo "▶ run_prediction --timeframe $TF"
#   python3 run_prediction.py --timeframe "$TF"
# else
#   echo "⚠️ No timeframe passed"
# fi

# echo "===== END RUN ====="

# #!/bin/bash
# set -e

# echo "===== CRON RUN $(date -u) ====="

# cd /app || exit 1

# # Load env vars
# if [ -f /app/.env ]; then
#   export $(grep -v '^#' /app/.env | xargs)
# else
#   echo "❌ .env file not found"
#   exit 1
# fi

# echo "DB_HOST=$DB_HOST"
# echo "DB_PORT=$DB_PORT"

# # ✅ WAIT FOR POSTGRES (CRITICAL FIX)
# echo "⏳ Waiting for PostgreSQL to be ready..."
# until python - <<EOF
# import psycopg2, os
# try:
#     psycopg2.connect(
#         dbname=os.getenv("DB_NAME"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         host=os.getenv("DB_HOST"),
#         port=int(os.getenv("DB_PORT"))
#     )
#     print("✅ PostgreSQL is ready")
# except Exception as e:
#     print("⏳ DB not ready:", e)
#     raise
# EOF
# do
#   sleep 5
# done

# # 1️⃣ Fetch prices
# python price_fetcher.py || echo "❌ price_fetcher failed"

# # 2️⃣ Train model
# python train_models.py || echo "⚠️ training skipped"

# # 3️⃣ Run predictions
# python run_prediction.py || echo "⚠️ prediction skipped"

# echo "===== END RUN ====="


# #!/bin/bash
# set -e

# echo "===== CRON RUN $(date -u) ====="

# cd /app || exit 1

# # Load environment variables
# if [ -f /app/.env ]; then
#   export $(grep -v '^#' /app/.env | xargs)
# else
#   echo "❌ .env file not found in /app"
#   exit 1
# fi

# echo "DB_HOST=$DB_HOST"
# echo "DB_PORT=$DB_PORT"

# # 1️⃣ Fetch prices
# python price_fetcher.py

# # 2️⃣ Train model (safe auto-skip inside script)
# python train_models.py || echo "⚠️ Training skipped"

# # 3️⃣ Run predictions
# python run_prediction.py || echo "⚠️ Prediction skipped"

# echo "===== END RUN ====="
