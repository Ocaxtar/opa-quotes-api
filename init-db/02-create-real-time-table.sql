-- OPA-423: Crear tabla quotes.real_time según contrato
-- Source: opa-infrastructure-state/contracts/data-models/quotes.md

-- Crear schema si no existe
CREATE SCHEMA IF NOT EXISTS quotes;

-- Crear tabla de cotizaciones en tiempo real
CREATE TABLE IF NOT EXISTS quotes.real_time (
    time TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(5) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    change DOUBLE PRECISION NOT NULL,
    change_percent DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    bid DOUBLE PRECISION,
    ask DOUBLE PRECISION,
    bid_size INTEGER,
    ask_size INTEGER,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    previous_close DOUBLE PRECISION NOT NULL,
    market_cap BIGINT,
    pe_ratio DOUBLE PRECISION,
    avg_volume_10d BIGINT,
    market_status VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL
);

-- Convertir a hypertable de TimescaleDB
SELECT create_hypertable('quotes.real_time', 'time', if_not_exists => TRUE);

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_quotes_real_time_ticker_time ON quotes.real_time (ticker, time DESC);
CREATE INDEX IF NOT EXISTS idx_quotes_real_time_exchange ON quotes.real_time (exchange, time DESC);

-- Otorgar permisos (ajustar usuario según configuración)
GRANT ALL PRIVILEGES ON SCHEMA quotes TO opa_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA quotes TO opa_user;

-- Verificar creación
\d+ quotes.real_time
