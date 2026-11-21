"""
Mandate & Recurring Commitment Data Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Numeric, Float, ForeignKey, Date, JSON
from app.core.db import Base

class Mandate(Base):
    __tablename__ = "mandates"

    id = Column(String(100), primary_key=True, default=lambda: f"mand_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True)
    merchant_id = Column(String(100), ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True, index=True)
    merchant_name = Column(String(255), nullable=False)
    category = Column(String(100), default="Uncategorized Subscription", nullable=False)
    parent_name = Column(String(255), default="Independent / Unmapped", nullable=True)
    descriptor = Column(String(500), nullable=False)
    
    # Mandate Classification: UPI_AUTOPAY, BANK_NACH, CARD_SI, PLAY_STORE, APP_STORE, INFERRED_RECURRING
    mandate_type = Column(String(50), nullable=False, default="INFERRED_RECURRING")
    umn_or_umrn = Column(String(100), nullable=True, index=True) # Unique Mandate Number / UMRN
    cadence = Column(String(50), nullable=False) # MONTHLY, QUARTERLY, ANNUAL
    
    # Monetary values
    latest_amount = Column(Numeric(precision=18, scale=2), nullable=False)
    initial_amount = Column(Numeric(precision=18, scale=2), nullable=True)
    annual_committed_cost = Column(Numeric(precision=18, scale=2), nullable=False)
    charge_count = Column(Float, default=1.0, nullable=False)
    
    # Anomaly Flag: HEALTHY, PRICE_HIKE, TRIAL_CONVERTED, UNUSED_ZOMBIE
    flag = Column(String(50), default="HEALTHY", nullable=False, index=True)
    flag_reason = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.95, nullable=False)
    
    # Lifecycle Status: active, flagged_overlap, keep_confirmed, suggested_cancel, cancel_confirmed_by_user, verified_cancelled, still_charging, PAUSED, REVOKED
    status = Column(String(50), default="active", nullable=False, index=True)
    
    first_seen = Column(Date, nullable=False)
    last_charged = Column(Date, nullable=False)
    next_expected_debit = Column(Date, nullable=True)
    
    # Overlap and Cancellation Lifecycle Tracking
    cancel_confirmed_at = Column(DateTime, nullable=True)
    last_seen_charge_date = Column(Date, nullable=True)
    expected_next_charge_date = Column(Date, nullable=True)
    reminder_count = Column(Numeric(precision=5, scale=0), default=0, nullable=False)
    overlap_decision_at = Column(DateTime, nullable=True)
    
    cancellation_steps = Column(JSON, default=list, nullable=True)
    pitfall = Column(Text, nullable=True)
    support_email = Column(String(255), nullable=True)
    grievance_email = Column(String(255), nullable=True)
    official_website = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
