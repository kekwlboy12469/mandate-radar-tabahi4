"""
Account (Payment Instrument) Data Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey
from app.core.db import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_type = Column(String(50), nullable=False)  # SAVINGS, CURRENT, CREDIT_CARD, UPI_WALLET
    bank_name = Column(String(100), nullable=False)     # e.g., HDFC Bank, ICICI Bank, SBI
    account_mask = Column(String(20), nullable=False)    # e.g., **4821 or user@upi
    currency = Column(String(3), default="INR", nullable=False)
    virtual_balance = Column(Numeric(precision=18, scale=2), default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

