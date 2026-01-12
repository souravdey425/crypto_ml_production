#!/bin/sh
set -e

TF="$1"

echo "===== CRON RUN $(date -u) | TF=$TF ====="
cd /app || exit 1

# Load env
if [ -f /app/.env ]; then
  set -a
  . /app/.env
  set +a
else
  echo ".env not found"
  exit 1
fi

# Lock
LOCK="/tmp/cronjob_$TF.lock"
if [ -f "$LOCK" ]; then
  echo "Previous $TF run active, skipping"
  exit 0
fi
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# Wait for DB
until python3 - <<EOF
import psycopg2, os
psycopg2.connect(
  dbname=os.getenv("DB_NAME"),
  user=os.getenv("DB_USER"),
  password=os.getenv("DB_PASSWORD"),
  host=os.getenv("DB_HOST"),
  port=int(os.getenv("DB_PORT"))
)
EOF
do
  sleep 5
done

# Always fetch price
python3 price_fetcher.py || true

# Train only once daily
if [ "$TF" = "1d" ]; then
  python3 train_models.py || true
fi

# Run prediction
python3 run_prediction.py --timeframe "$TF" || true

echo "===== END $TF ====="
