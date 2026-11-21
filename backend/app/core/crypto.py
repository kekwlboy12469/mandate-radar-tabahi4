"""
Cryptographic Utilities for Encrypting OAuth Tokens and Secrets at Rest
Enforces AES-256-GCM with Key Derivation from Application SECRET_KEY.
"""
import os
import base64
import hashlib
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from app.core.config import settings

# Deterministic Salt derived from SECRET_KEY for application-level token encryption
_SALT = hashlib.sha256((settings.SECRET_KEY + "_SALT_CREDENTIALS").encode()).digest()[:16]

def _derive_aes_key() -> bytes:
    """Derives a 256-bit AES key using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=100_000,
    )
    return kdf.derive(settings.SECRET_KEY.encode())

_AES_KEY = _derive_aes_key()

def encrypt_secret(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypts sensitive string using AES-256-GCM.
    Returns: Base64-encoded string: nonce (12 bytes) + ciphertext + auth tag.
    """
    if not plaintext:
        return None
    aesgcm = AESGCM(_AES_KEY)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")

def decrypt_secret(encrypted_b64: Optional[str]) -> Optional[str]:
    """
    Decrypts AES-256-GCM encrypted base64 payload.
    """
    if not encrypted_b64:
        return None
    try:
        payload = base64.b64decode(encrypted_b64.encode("utf-8"))
        if len(payload) < 28: # 12 bytes nonce + 16 bytes tag minimum
            return None
        nonce = payload[:12]
        ciphertext = payload[12:]
        aesgcm = AESGCM(_AES_KEY)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception:
        return None

