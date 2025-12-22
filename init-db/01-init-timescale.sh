#!/bin/bash
# Script de inicialización para TimescaleDB

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Crear extensión TimescaleDB
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
    
    -- Crear schema para cotizaciones
    CREATE SCHEMA IF NOT EXISTS quotes;
    
    -- Crear tabla de cotizaciones en tiempo real
    CREATE TABLE IF NOT EXISTS quotes.real_time (
        ticker VARCHAR(10) NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL,
        open NUMERIC(12, 4) NOT NULL,
        high NUMERIC(12, 4) NOT NULL,
        low NUMERIC(12, 4) NOT NULL,
        close NUMERIC(12, 4) NOT NULL,
        volume BIGINT NOT NULL,
        bid NUMERIC(12, 4),
        ask NUMERIC(12, 4),
        CONSTRAINT real_time_ticker_timestamp_key UNIQUE (ticker, timestamp)
    );
    
    -- Convertir a hypertable de TimescaleDB
    SELECT create_hypertable('quotes.real_time', 'timestamp', 
        chunk_time_interval => INTERVAL '1 day',
        if_not_exists => TRUE
    );
    
    -- Crear índices para optimizar consultas
    CREATE INDEX IF NOT EXISTS idx_ticker_timestamp 
        ON quotes.real_time (ticker, timestamp DESC);
    
    CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON quotes.real_time (timestamp DESC);
    
    -- Configurar política de retención (opcional - 90 días)
    -- SELECT add_retention_policy('quotes.real_time', INTERVAL '90 days', if_not_exists => TRUE);
    
    GRANT ALL PRIVILEGES ON SCHEMA quotes TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA quotes TO $POSTGRES_USER;
    
    EOSQL

echo "✓ TimescaleDB initialized successfully"
