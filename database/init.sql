CREATE TABLE IF NOT EXISTS prices (
 id SERIAL PRIMARY KEY,
 symbol TEXT NOT NULL,
 exchange TEXT NOT NULL,
 price NUMERIC NOT NULL,
 fetched_time TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
 id SERIAL PRIMARY KEY,
 symbol TEXT NOT NULL,
 timeframe TEXT NOT NULL,
 generated_time TIMESTAMPTZ NOT NULL,
 predicted_time TIMESTAMPTZ,
 market_price NUMERIC NOT NULL,
 predicted_price NUMERIC NOT NULL,
 price_delta NUMERIC,
 price_delta_pct NUMERIC,
 direction INT CHECK (direction IN (-1, 0, 1)),
 signal TEXT NOT NULL,
 confidence FLOAT NOT NULL,
 model_version TEXT
);

CREATE INDEX IF NOT EXISTS idx_prices_symbol_time
ON prices (symbol, fetched_time);

CREATE INDEX IF NOT EXISTS idx_predictions_symbol_timeframe
ON predictions (symbol, timeframe, generated_time);
