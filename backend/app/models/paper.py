from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    id = Column(Integer, primary_key=True, index=True)
    initial_capital = Column(Float, default=100000.0)
    available_cash = Column(Float, default=100000.0)
    used_capital = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    equity = Column(Float, default=100000.0)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    symbol = Column(String, index=True)
    side = Column(String) # BUY / SELL
    order_type = Column(String) # LIMIT
    quantity = Column(Integer)
    requested_price = Column(Float)
    filled_price = Column(Float, nullable=True)
    status = Column(String) # PENDING, FILLED, CANCELLED, REJECTED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    side = Column(String) # LONG / SHORT
    quantity = Column(Integer)
    entry_price = Column(Float)
    current_price = Column(Float)
    stop_loss = Column(Float, nullable=True)
    target = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    status = Column(String) # OPEN, CLOSED, STOPPED_OUT, TARGET_HIT
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String, unique=True, index=True)
    order_id = Column(String, index=True)
    symbol = Column(String, index=True)
    side = Column(String)
    quantity = Column(Integer)
    entry_price = Column(Float)
    exit_price = Column(Float)
    realized_pnl = Column(Float)
    opened_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True), server_default=func.now())
