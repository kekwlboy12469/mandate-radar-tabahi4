"""
Engine 1: SMS Ingestion & Transaction Extractor
Specialized for Indian Banking & Mandate Telecommunication Alerts
Complies with RBI DLT (Distributed Ledger Technology) Header Guidelines
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

class SMSReceiver:
    """
    Parses, validates, sanitizes, and normalizes financial SMS messages.
    Enforces strict security: immediately drops OTPs and non-financial messages.
    """
    # Standard Indian DLT Telecommunication Sender ID: 2 letters (telecom circle/operator) + hyphen + 6 alphanumeric
    HEADER_REGEX = re.compile(r'^[A-Za-z]{2}-([A-Za-z0-9]{6})$', re.IGNORECASE)
    
    # Well-known bank sender identifiers (last 6 chars)
    KNOWN_BANK_CODES = {
        "HDFCBK", "SBIINB", "ICICIB", "KOTAKB", "AXISBK", "YESBNK", "PNBSMS",
        "BOBTXN", "INDBNK", "CANBNK", "UBISMS", "PAYTM", "GPAYIN", "CREDCL",
        "PHNPAY", "AMEXIN", "CITIBK", "SCISMS", "FEDBNK", "IDFCFB", "RBLBNK"
    }

    # Strict OTP / Security filter - NEVER ingest OTP messages
    OTP_TRIGGER_WORDS = [
        "otp", "one time password", "verification code", "security code",
        "secret code", "never share", "do not share", "valid for", "cvv"
    ]

    AMOUNT_REGEX = re.compile(r'(?:(?:Rs\.?|INR)\s*|debited\s*(?:by|for|with)?\s*(?:Rs\.?|INR)?\s*)([0-9,]+(?:\.[0-9]{1,2})?)', re.IGNORECASE)
    ACCOUNT_REGEX = re.compile(r'(?:A/c|Acct|Account|Card)(?:\s*(?:no\.?|ending))?\s*[:\-]?\s*[*Xx]+([0-9]{4})', re.IGNORECASE)
    
    # Pre-debit and mandate trigger keywords
    PRE_DEBIT_TRIGGERS = [
        "will be debited", "pre-debit", "scheduled for debit", "autopay debit scheduled",
        "mandate debit scheduled", "mandate execution", "standing instruction scheduled"
    ]

    # Mandate tokens
    UMN_REGEX = re.compile(r'\b([a-f0-9]{32})\b', re.IGNORECASE)
    UMRN_REGEX = re.compile(r'\b([a-z0-9]{20})\b', re.IGNORECASE)
    RRN_REGEX = re.compile(r'(?:UPI Ref(?: No)?|Ref(?: No)?|RRN)\s*[:\-]?\s*([0-9]{12})', re.IGNORECASE)

    # Merchant extractors
    MERCHANT_AT_REGEX = re.compile(r'\bat\s+([A-Za-z0-9\*\.\s\-_/]+?)(?:\s+on\s+|\s+ref|\s+avail|\s+avl|\s+bal|\.|\s*$)', re.IGNORECASE)
    MERCHANT_TO_REGEX = re.compile(r'\bto\s+([A-Za-z0-9\*\.\s\-_/]+?)(?:\s+on\s+|\s+ref|\s+avail|\s+avl|\s+bal|\.|\s*$)', re.IGNORECASE)
    MERCHANT_VPA_REGEX = re.compile(r'\bVPA\s+([A-Za-z0-9\.\-_@]+)', re.IGNORECASE)

    @classmethod
    def is_valid_sender(cls, sender: str) -> bool:
        if not sender:
            return False
        clean = sender.strip()
        match = cls.HEADER_REGEX.match(clean)
        if match:
            code = match.group(1).upper()
            return code in cls.KNOWN_BANK_CODES or True  # Allow other banks conforming to DLT
        # Fallback check if sender contains bank code
        upper = clean.upper()
        return any(b in upper for b in cls.KNOWN_BANK_CODES)

    @classmethod
    def is_otp_message(cls, text: str) -> bool:
        lower = text.lower()
        return any(term in lower for term in cls.OTP_TRIGGER_WORDS)

    @classmethod
    def parse_sms(cls, text: str, sender: str = "", timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Parses raw SMS text into a structured financial alert payload.
        """
        result = {
            "is_valid": False,
            "is_transaction": False,
            "is_otp": False,
            "is_pre_debit_alert": False,
            "direction": "UNKNOWN",
            "amount": 0.0,
            "currency": "INR",
            "account_last4": None,
            "merchant_raw": None,
            "reference_number": None,
            "mandate_token": None,
            "token_type": None,
            "scheduled_date": None,
            "confidence": 0.0,
            "sender_id": sender.strip() if sender else "UNKNOWN",
            "reason": None
        }

        # 1. OTP Check
        if cls.is_otp_message(text):
            result["is_otp"] = True
            result["reason"] = "Security alert: OTP discarded per privacy protocol"
            return result

        lower = text.lower()

        # 2. Pre-debit Alert Check
        if any(trigger in lower for trigger in cls.PRE_DEBIT_TRIGGERS):
            result["is_pre_debit_alert"] = True
            result["direction"] = "DEBIT"
        elif "debited" in lower or "spent" in lower or "deducted" in lower or "paid" in lower:
            result["direction"] = "DEBIT"
            result["is_transaction"] = True
        elif "credited" in lower or "received" in lower or "refund" in lower:
            result["direction"] = "CREDIT"
            result["is_transaction"] = True
        else:
            result["reason"] = "Non-transactional / informational text"
            return result

        # 3. Extract Amount
        amt_match = cls.AMOUNT_REGEX.search(text)
        if amt_match:
            amt_str = amt_match.group(1).replace(",", "")
            try:
                result["amount"] = float(amt_str)
            except ValueError:
                pass
        
        if result["amount"] <= 0:
            result["reason"] = "No valid amount parsed"
            return result

        # 4. Extract Account / Card
        acc_match = cls.ACCOUNT_REGEX.search(text)
        if acc_match:
            result["account_last4"] = acc_match.group(1)

        # 5. Extract Mandate Token (UMN or UMRN)
        umn_match = cls.UMN_REGEX.search(text)
        if umn_match:
            result["mandate_token"] = umn_match.group(1).lower()
            result["token_type"] = "UMN"
        else:
            umrn_match = cls.UMRN_REGEX.search(text)
            if umrn_match:
                token = umrn_match.group(1).upper()
                # Must start with alphabetic bank code and not be generic hex
                if token[:4].isalpha():
                    result["mandate_token"] = token
                    result["token_type"] = "UMRN"

        # 6. Extract Reference Number
        rrn_match = cls.RRN_REGEX.search(text)
        if rrn_match:
            result["reference_number"] = rrn_match.group(1)

        # 7. Extract Merchant / Beneficiary
        vpa_match = cls.MERCHANT_VPA_REGEX.search(text)
        if vpa_match:
            result["merchant_raw"] = vpa_match.group(1)
        else:
            at_match = cls.MERCHANT_AT_REGEX.search(text)
            if at_match:
                result["merchant_raw"] = at_match.group(1).strip()
            else:
                to_match = cls.MERCHANT_TO_REGEX.search(text)
                if to_match:
                    result["merchant_raw"] = to_match.group(1).strip()

        # 8. Extract Date (especially for pre-debits)
        date_patterns = [
            r'on\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'on\s+(\d{1,2}-[A-Za-z]{3}-\d{2,4})',
            r'on\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})'
        ]
        for dp in date_patterns:
            dm = re.search(dp, text, re.IGNORECASE)
            if dm:
                raw_d = dm.group(1)
                result["scheduled_date"] = raw_d
                break
        
        if not result["scheduled_date"] and timestamp:
            result["scheduled_date"] = timestamp.isoformat()

        # 9. Confidence Assessment
        confidence = 0.5
        if result["amount"] > 0:
            confidence += 0.2
        if result["merchant_raw"]:
            confidence += 0.15
        if result["mandate_token"] or result["reference_number"]:
            confidence += 0.15
        
        result["confidence"] = round(min(confidence, 1.0), 2)
        result["is_valid"] = True
        return result

