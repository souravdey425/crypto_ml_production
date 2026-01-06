FROM python:3.10-slim

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 👇 THIS LINE COPIES .env TOO
COPY . .

RUN touch /var/log/cron.log

COPY cronjob.sh /usr/local/bin/cronjob.sh
COPY crontab /etc/cron.d/crypto-cron

RUN chmod +x /usr/local/bin/cronjob.sh \
    && chmod 0644 /etc/cron.d/crypto-cron \
    && crontab /etc/cron.d/crypto-cron

CMD ["cron", "-f"]
