from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.types import Float
from .database import Base
import enum
from datetime import datetime

class TransactionStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), nullable=False, unique=True, index=True)
    source_account = Column(String(255), nullable=False)
    destination_account = Column(String(255), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PROCESSING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    enqueued_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('transaction_id', name='uq_transaction_transaction_id'),
    )
