"""
Merchant Knowledge Base Data Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from app.core.db import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(100), primary_key=True) # e.g. "youtube_premium", "netflix_india"
    brand_name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    parent_company = Column(String(255), nullable=True, index=True)
    default_mechanism = Column(String(50), default="CARD_SI", nullable=False)
    support_email = Column(String(255), nullable=True)
    grievance_email = Column(String(255), nullable=True)
    cancellation_pitfall = Column(Text, nullable=True)
    descriptor_regexes = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

