"""
Raw Ingestion Logs Model (Audit Trail for PDF, SMS, Gmail, CSV)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, ForeignKey
from app.core.db import Base

class RawIngestLog(Base):
    __tablename__ = "raw_ingest_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    source_type = Column(String(50), nullable=False) # STATEMENT_PDF, STATEMENT_CSV, SMS_STREAM, GMAIL_API
    filename = Column(String(255), nullable=True)
    raw_payload = Column(JSON, nullable=False)
    records_extracted = Column(Integer, default=0, nullable=False)
    processing_status = Column(String(50), default="COMPLETED", nullable=False, index=True) # PENDING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

