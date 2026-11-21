"""
Outbox Event Model (Asynchronous Synchronization from PostgreSQL to Neo4j)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Text
from app.core.db import Base

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True) # MANDATE_UPSERTED, TRANSACTION_RECORDED
    aggregate_id = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, PROCESSED, FAILED
    retry_count = Column(String(10), default="0", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

