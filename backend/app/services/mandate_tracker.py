"""
Mandate Lifecycle & Token Verification Service
Enforces strict distinction between Inferred Recurring Payments and Verified Legal Mandates (UPI AutoPay UMN & NACH UMRN).
"""
import re
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from app.models.mandate import Mandate

# UMN (Unique Mandate Number) for UPI AutoPay:
# Usually a 32-character hex string or UMN: <identifier>@<bank>
UMN_PATTERNS = [
    r"\bUMN[:\s#]+([A-Za-z0-9@\.\-_]{16,40})\b",
    r"\b([a-f0-9]{32})\b",
    r"\bAUTOPAY/([A-Za-z0-9]{12,32})\b"
]

# UMRN (Unique Mandate Reference Number) for NACH / eNACH:
# Formatted as 4-letter bank code + 16 alphanumeric characters (20 chars total)
UMRN_PATTERNS = [
    r"\bUMRN[:\s#]+([A-Za-z0-9]{16,25})\b",
    r"\b([A-Z]{4}\d{16})\b",
    r"\bNACH/([A-Za-z0-9]{16,25})\b"
]

class MandateTracker:
    @staticmethod
    def extract_mandate_tokens(text: str) -> Dict[str, Optional[str]]:
        """
        Scans transaction descriptions or notification texts for official NPCI UMN/UMRN tokens.
        """
        clean_text = text.strip()
        umn_token = None
        umrn_token = None

        # Check UMN
        for pat in UMN_PATTERNS:
            match = re.search(pat, clean_text, re.IGNORECASE)
            if match:
                umn_token = match.group(1).upper()
                break

        # Check UMRN
        for pat in UMRN_PATTERNS:
            match = re.search(pat, clean_text, re.IGNORECASE)
            if match:
                umrn_token = match.group(1).upper()
                break

        return {
            "umn": umn_token,
            "umrn": umrn_token
        }

    @classmethod
    def classify_mandate_tier(
        cls,
        descriptor: str,
        ref_str: str,
        is_recognized_merchant: bool,
        extracted_tokens: Optional[Dict[str, Optional[str]]] = None
    ) -> Tuple[str, float, Optional[str]]:
        """
        Classifies transaction into its appropriate ontological mandate tier:
        - VERIFIED_UPI_AUTOPAY (Confidence 0.98): Valid UMN token or verified UPI AutoPay rail.
        - VERIFIED_BANK_NACH (Confidence 0.98): Valid UMRN token or verified NACH rail.
        - INFERRED_SUBSCRIPTION (Confidence 0.85): Repetitive debits to known digital service.
        - INFERRED_RECURRING (Confidence 0.65): Statistical repetition without verified mandate proof.
        """
        combined = f"{descriptor} {ref_str}"
        tokens = extracted_tokens or cls.extract_mandate_tokens(combined)

        if tokens.get("umn"):
            return "VERIFIED_UPI_AUTOPAY", 0.98, tokens["umn"]

        if tokens.get("umrn"):
            return "VERIFIED_BANK_NACH", 0.98, tokens["umrn"]

        combined_upper = combined.upper()
        if "AUTOPAY" in combined_upper and "UPI" in combined_upper:
            # High-confidence UPI AutoPay indicator
            return "VERIFIED_UPI_AUTOPAY", 0.92, None

        if "NACH" in combined_upper or "ACH D" in combined_upper:
            # High-confidence NACH indicator
            return "VERIFIED_BANK_NACH", 0.92, None

        if is_recognized_merchant:
            return "INFERRED_SUBSCRIPTION", 0.85, None

        return "INFERRED_RECURRING", 0.65, None

    @staticmethod
    def transition_status(
        mandate: Mandate,
        target_status: str,
        reason: Optional[str] = None
    ) -> Mandate:
        """
        Transitions mandate through its formal lifecycle:
        PENDING_VERIFICATION -> ACTIVE -> PAUSED -> REVOKED -> EXPIRED
        """
        valid_transitions = {
            "PENDING_VERIFICATION": ["ACTIVE", "REVOKED"],
            "ACTIVE": ["PAUSED", "REVOKED", "EXPIRED"],
            "PAUSED": ["ACTIVE", "REVOKED", "EXPIRED"],
            "REVOKED": ["ACTIVE"], # Reactivation if re-authorized
            "EXPIRED": ["ACTIVE"]
        }

        current = mandate.status or "ACTIVE"
        if target_status not in valid_transitions.get(current, []):
            raise ValueError(f"Invalid mandate status transition: Cannot move from {current} to {target_status}")

        mandate.status = target_status
        if reason:
            mandate.flag_reason = reason
        return mandate

