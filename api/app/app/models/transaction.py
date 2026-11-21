"""
Transaction Ledger Data Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, ForeignKey, Date, Text
from app.core.db import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(50), primary_key=True, default=lambda: f"tx_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True)
    merchant_id = Column(String(100), ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True, index=True)
    mandate_id = Column(String(100), ForeignKey("mandates.id", ondelete="SET NULL"), nullable=True, index=True)
    
    transaction_type = Column(String(20), default="DEBIT", nullable=False) # DEBIT, CREDIT
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    transaction_date = Column(Date, index=True, nullable=False)
    
    raw_descriptor = Column(Text, nullable=False)
    cleaned_descriptor = Column(Text, nullable=False)
    ref_number = Column(String(100), nullable=True, index=True)
    payment_rail = Column(String(50), default="DIRECT_MERCHANT", nullable=False)
    
    is_inferred_recurring = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

