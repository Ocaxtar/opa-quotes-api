"""SQLAlchemy models for TimescaleDB."""
from sqlalchemy import TIMESTAMP, BigInteger, Column, Numeric, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RealTimeQuote(Base):
    """Model for quotes.real_time hypertable in TimescaleDB."""

    __tablename__ = "real_time"
    __table_args__ = {"schema": "quotes"}

    ticker = Column(String(10), primary_key=True, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    open = Column(Numeric(precision=10, scale=2), nullable=False)
    high = Column(Numeric(precision=10, scale=2), nullable=False)
    low = Column(Numeric(precision=10, scale=2), nullable=False)
    close = Column(Numeric(precision=10, scale=2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    bid = Column(Numeric(precision=10, scale=2), nullable=True)
    ask = Column(Numeric(precision=10, scale=2), nullable=True)

    def __repr__(self):
        return f"<RealTimeQuote(ticker='{self.ticker}', timestamp='{self.timestamp}', close={self.close})>"
