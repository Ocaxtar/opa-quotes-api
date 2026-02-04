#!/bin/bash
# Script de inicialización para TimescaleDB

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Crear extensión TimescaleDB
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
    
    -- Crear schema para cotizaciones
    CREATE SCHEMA IF NOT EXISTS quotes;
    
    -- Crear tabla de cotizaciones en tiempo real
    -- Schema basado en opa-infrastructure-state/contracts/data-models/quotes.md
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
    SELECT create_hypertable('quotes.real_time', 'time', 
        chunk_time_interval => INTERVAL '1 day',
        if_not_exists => TRUE
    );
    
    -- Crear índices para optimizar consultas
    CREATE INDEX IF NOT EXISTS idx_quotes_real_time_ticker_time 
        ON quotes.real_time (ticker, time DESC);
    
    CREATE INDEX IF NOT EXISTS idx_quotes_real_time_exchange 
        ON quotes.real_time (exchange, time DESC);
    
    -- Configurar política de retención (opcional - 90 días)
    -- SELECT add_retention_policy('quotes.real_time', INTERVAL '90 days', if_not_exists => TRUE);
    
    GRANT ALL PRIVILEGES ON SCHEMA quotes TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA quotes TO $POSTGRES_USER;
    
    EOSQL

echo "✓ TimescaleDB initialized successfully"
