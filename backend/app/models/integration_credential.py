"""
Integration Credential Model
Stores OAuth credentials, device pairing tokens, and sync history with AES-256-GCM encryption.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON
from app.core.db import Base
from app.core.crypto import encrypt_secret, decrypt_secret

class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    id = Column(String(50), primary_key=True, default=lambda: f"cred_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Provider: GMAIL, ANDROID_SMS
    provider = Column(String(50), nullable=False, index=True)
    
    # Encrypted Tokens (AES-256-GCM)
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scopes = Column(String(255), default="https://www.googleapis.com/auth/gmail.readonly", nullable=False)
    
    # Gmail Metadata
    account_email = Column(String(255), nullable=True)
    last_history_id = Column(String(100), nullable=True)
    
    # Android Device Pairing Metadata
    device_id = Column(String(100), nullable=True, index=True)
    device_name = Column(String(255), nullable=True)
    pairing_token = Column(String(100), nullable=True, index=True)
    pairing_pin = Column(String(10), nullable=True)
    pairing_pin_expires_at = Column(DateTime, nullable=True)
    
    # Status and telemetry
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="CONNECTED", nullable=False) # CONNECTED, EXPIRED, REVOKED, ERROR
    last_error_message = Column(Text, nullable=True)
    
    # Metrics: {"total_scanned": 0, "ingested_txns": 0, "duplicates_filtered": 0, "pre_debit_alerts": 0}
    metrics = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def set_tokens(self, access_token: str, refresh_token: str = None, expiry: datetime = None):
        self.encrypted_access_token = encrypt_secret(access_token)
        if refresh_token:
            self.encrypted_refresh_token = encrypt_secret(refresh_token)
        if expiry:
            self.token_expiry = expiry

    def get_access_token(self) -> str:
        return decrypt_secret(self.encrypted_access_token)

    def get_refresh_token(self) -> str:
        return decrypt_secret(self.encrypted_refresh_token)

