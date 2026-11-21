"""
Engine 1: Gmail Integration & Financial Invoice Extractor
Parses digital subscription invoices, mandate notifications, and bank transaction alerts.
Restricted read-only scope: https://www.googleapis.com/auth/gmail.readonly
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class GmailSyncService:
    """
    Extracts structured financial transactions, subscription invoices,
    and mandate notifications from email text and MIME payloads.
    """
    
    FINANCIAL_QUERY = (
        'from:(billing OR payments OR alert OR "no-reply" OR notification OR auto-debit OR receipts) '
        'subject:(mandate OR autopay OR subscription OR invoice OR receipt OR debited OR statement OR renewal)'
    )

    # Common Merchant Invoice Patterns
    PATTERNS = {
        "netflix": {
            "name": "Netflix Entertainment Services",
            "regex": re.compile(r'Total\s*(?:for\s*this\s*month)?\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
        },
        "spotify": {
            "name": "Spotify India",
            "regex": re.compile(r'(?:Total\s*amount|Price|Amount paid)\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
        },
        "google": {
            "name": "Google India Digital Services",
            "regex": re.compile(r'(?:Total|Amount debited|Subtotal)\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
        },
        "apple": {
            "name": "Apple Services",
            "regex": re.compile(r'(?:TOTAL|Total Due|Amount)\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
        },
        "amazon": {
            "name": "Amazon Prime",
            "regex": re.compile(r'(?:Grand Total|Amount Paid|Order Total)\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
        },
        "openai": {
            "name": "OpenAI / ChatGPT Plus",
            "regex": re.compile(r'(?:Amount Paid|Total)\s*[:\-]?\s*(?:\$|USD)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
        }
    }

    GENERIC_AMOUNT_REGEX = re.compile(r'(?:Total|Amount|Paid|Price|Invoice Total)\s*[:\-]?\s*(?:Rs\.?|INR|₹|\$|USD)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
    DATE_REGEX = re.compile(r'(?:Date|Billed on|Invoice Date|Payment Date)\s*[:\-]?\s*([A-Za-z0-9,\s\-/]{6,25})', re.IGNORECASE)
    INVOICE_NUM_REGEX = re.compile(r'(?:Invoice|Receipt|Order|Reference)\s*(?:Number|No\.?|#|ID)\s*[:\-]?\s*([A-Za-z0-9\-_]{6,30})', re.IGNORECASE)
    
    # Mandate Tokens
    UMN_REGEX = re.compile(r'\b([a-f0-9]{32})\b', re.IGNORECASE)
    UMRN_REGEX = re.compile(r'\b([a-z0-9]{20})\b', re.IGNORECASE)

    @classmethod
    def parse_email(
        cls,
        subject: str,
        sender: str,
        body: str,
        received_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Parses an email message into a structured financial transaction / mandate record.
        """
        result = {
            "is_financial": False,
            "merchant_name": "Unknown Merchant",
            "amount": 0.0,
            "currency": "INR",
            "date": received_at.strftime("%Y-%m-%d") if received_at else datetime.now().strftime("%Y-%m-%d"),
            "invoice_number": None,
            "mandate_token": None,
            "token_type": None,
            "subject": subject,
            "sender": sender,
            "confidence": 0.0,
            "raw_snippet": body[:200] if body else ""
        }

        full_text = f"{subject}\n{sender}\n{body}"
        lower_text = full_text.lower()

        # Check for currency indicator
        if "$" in full_text or "usd" in lower_text:
            result["currency"] = "USD"
        else:
            result["currency"] = "INR"

        # 1. Known Merchant Match
        matched_merchant = False
        for key, p_data in cls.PATTERNS.items():
            if key in lower_text or key in sender.lower():
                result["merchant_name"] = p_data["name"]
                matched_merchant = True
                m = p_data["regex"].search(body)
                if m:
                    try:
                        result["amount"] = float(m.group(1).replace(",", ""))
                    except ValueError:
                        pass
                break

        # 2. Generic Amount Extraction if not already found
        if result["amount"] <= 0:
            m = cls.GENERIC_AMOUNT_REGEX.search(body)
            if m:
                try:
                    result["amount"] = float(m.group(1).replace(",", ""))
                except ValueError:
                    pass

        # 3. Extract Invoice / Receipt ID
        inv_match = cls.INVOICE_NUM_REGEX.search(body)
        if inv_match:
            result["invoice_number"] = inv_match.group(1).strip()

        # 4. Extract Mandate Token
        umn_match = cls.UMN_REGEX.search(body)
        if umn_match:
            result["mandate_token"] = umn_match.group(1).lower()
            result["token_type"] = "UMN"
        else:
            umrn_match = cls.UMRN_REGEX.search(body)
            if umrn_match:
                token = umrn_match.group(1).upper()
                if token[:4].isalpha():
                    result["mandate_token"] = token
                    result["token_type"] = "UMRN"

        # 5. Extract Date
        date_match = cls.DATE_REGEX.search(body)
        if date_match:
            raw_d = date_match.group(1).strip()
            # Clean up trailing words
            raw_d = raw_d.split("\n")[0].split("·")[0].strip()
            if len(raw_d) >= 6:
                result["date"] = raw_d

        # 6. Assess Validity and Confidence
        if result["amount"] > 0 and (matched_merchant or "invoice" in lower_text or "receipt" in lower_text or "mandate" in lower_text):
            result["is_financial"] = True
            conf = 0.6
            if matched_merchant:
                conf += 0.2
            if result["invoice_number"]:
                conf += 0.1
            if result["mandate_token"]:
                conf += 0.1
            result["confidence"] = round(min(conf, 1.0), 2)

        return result

