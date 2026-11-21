"""
Financial Normalization Service
Standardizes dates, monetary amounts, and transaction descriptors across heterogeneous Indian banking formats.
"""
import re
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
    "%Y-%m-%d", "%Y/%m/%d",
    "%d-%b-%Y", "%d %b %Y", "%d-%b-%y", "%d %b %y",
    "%d-%B-%Y", "%d %B %Y",
    "%b %d, %Y", "%B %d, %Y"
]

KNOWN_AGGREGATORS = [
    ("RAZORPAY", r"\bRAZORPAY\b|\bRAZ\*[A-Z0-9]+"),
    ("BILLDESK", r"\bBILLDESK\b|\bBD\*[A-Z0-9]+"),
    ("PAYTM", r"\bPAYTM\b|\bPYTM\b"),
    ("CASHFREE", r"\bCASHFREE\b"),
    ("PAYU", r"\bPAYU\b|\bPAY_U\b"),
    ("PHONEPE", r"\bPHONEPE\b"),
    ("CCAVENUE", r"\bCCAVENUE\b"),
    ("STRIPE", r"\bSTRIPE\b")
]

def parse_date(date_str: str) -> Optional[str]:
    """
    Parses a date string from various bank formats into ISO-8601 (YYYY-MM-DD).
    Returns None if unparseable.
    """
    if not date_str:
        return None
    cleaned = date_str.strip()
    # Remove ordinal suffixes like 1st, 2nd, 3rd, 4th
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", cleaned, flags=re.IGNORECASE)
    
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            # Basic sanity check: year between 2000 and 2050
            if 2000 <= dt.year <= 2050:
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def parse_amount(amount_str: Any) -> Tuple[float, str]:
    """
    Parses raw amount string into a float and identifies transaction direction (DEBIT vs CREDIT).
    Handles 'Dr', 'Cr', negative signs, and commas.
    """
    if isinstance(amount_str, (int, float)):
        val = float(amount_str)
        return abs(val), "DEBIT" if val < 0 else "CREDIT"

    s = str(amount_str).strip().upper()
    direction = "DEBIT" # default assumption for mandate debit radar
    
    if "CR" in s or "CREDIT" in s:
        direction = "CREDIT"
    elif "DR" in s or "DEBIT" in s:
        direction = "DEBIT"
        
    # Strip symbols, letters, spaces
    cleaned = re.sub(r"[^\d.-]", "", s.replace(",", ""))
    try:
        val = abs(float(cleaned))
        return val, direction
    except ValueError:
        return 0.0, direction

def clean_descriptor(descriptor: str) -> str:
    """
    Strips noise, punctuation, ATM/terminal IDs, and trailing reference hashes.
    """
    text = descriptor.upper()
    text = re.sub(r"[#*\/\\\-_:]", " ", text)
    text = re.sub(r"\b\d{4,}\b", "", text) # Strip long reference numbers
    text = re.sub(r"\b(UPI|IMPS|NEFT|RTGS|POS|ATM|ECOM)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def detect_aggregator(descriptor: str) -> Optional[str]:
    """Identifies third-party payment aggregators in raw descriptors."""
    for name, pattern in KNOWN_AGGREGATORS:
        if re.search(pattern, descriptor, re.IGNORECASE):
            return name
    return None

def detect_rail(descriptor: str, ref_str: str = "") -> str:
    """Detects the underlying banking rail (UPI AutoPay, NACH, Card SI, Play Store, App Store)."""
    combined = f"{descriptor} {ref_str}".upper()
    if "UPI" in combined or "AUTOPAY" in combined or "VPA" in combined:
        return "UPI_AUTOPAY"
    if "NACH" in combined or "ACH D" in combined or "ECS" in combined:
        return "BANK_NACH"
    if "G.CO/HELPPAY" in combined or "PLAY PASS" in combined or "GOOGLE*PLAY" in combined:
        return "PLAY_STORE"
    if "APPLE.COM/BILL" in combined or "ITUNES" in combined:
        return "APP_STORE"
    if "CARD-SI" in combined or "POS DEBIT" in combined or "MSBILL.INFO" in combined or "STRIPE" in combined:
        return "CARD_SI"
    return "DIRECT_MERCHANT"

