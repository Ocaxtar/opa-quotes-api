"""SQLAlchemy models for TimescaleDB."""
from sqlalchemy import TIMESTAMP, BigInteger, Column, Double, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RealTimeQuote(Base):
    """Model for quotes.real_time hypertable in TimescaleDB.
    
    Schema based on opa-infrastructure-state/contracts/data-models/quotes.md
    """

    __tablename__ = "real_time"
    __table_args__ = {"schema": "quotes"}

    # Primary key: (ticker, timestamp) según contrato oficial
    ticker = Column(String(5), primary_key=True, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    
    # Price data
    price = Column(Double, nullable=False)
    change = Column(Double, nullable=False)
    change_percent = Column(Double, nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    # Bid/Ask spread
    bid = Column(Double, nullable=True)
    ask = Column(Double, nullable=True)
    bid_size = Column(Integer, nullable=True)
    ask_size = Column(Integer, nullable=True)
    
    # OHLC data
    open = Column(Double, nullable=False)
    high = Column(Double, nullable=False)
    low = Column(Double, nullable=False)
    previous_close = Column(Double, nullable=False)
    
    # Market data
    market_cap = Column(BigInteger, nullable=True)
    pe_ratio = Column(Double, nullable=True)
    avg_volume_10d = Column(BigInteger, nullable=True)
    
    # Metadata
    market_status = Column(String(20), nullable=False)
    exchange = Column(String(10), nullable=False)

    def __repr__(self):
        return f"<RealTimeQuote(ticker='{self.ticker}', timestamp='{self.timestamp}', price={self.price})>"
