"""
Pre-Debit Notification Matching Service
Under RBI Master Circular on Recurring Debits, banks must dispatch alerts 24-48 hours before execution.
Matches pre-debit alerts against registered mandates to prevent unauthorized debits and price surprises.
"""
import re
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from app.models.mandate import Mandate
from app.services.normalizer import parse_amount, parse_date
from app.services.mandate_tracker import MandateTracker

class PreDebitMatcher:
    @classmethod
    def parse_pre_debit_alert(cls, alert_text: str) -> Dict[str, Any]:
        """
        Extracts expected amount, scheduled execution date, merchant keyword,
        and mandate tokens from pre-debit alert messages.
        """
        tokens = MandateTracker.extract_mandate_tokens(alert_text)
        
        # Extract scheduled date
        date_match = re.search(r"\b(?:on|scheduled for|due on)\s+(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})\b", alert_text, re.IGNORECASE)
        scheduled_date = parse_date(date_match.group(1)) if date_match else None

        # Extract amount
        amt_match = re.search(r"(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d{0,2})", alert_text, re.IGNORECASE)
        amount = 0.0
        if amt_match:
            amount, _ = parse_amount(amt_match.group(1))

        # Check for merchant keywords
        return {
            "raw_text": alert_text,
            "expected_amount": amount,
            "scheduled_date": scheduled_date or date.today().isoformat(),
            "tokens": tokens
        }

    @classmethod
    def match_and_audit(
        cls,
        alert_text: str,
        user_mandates: List[Mandate]
    ) -> Dict[str, Any]:
        """
        Matches a pre-debit alert to an active mandate and checks for limit breaches,
        price hikes, or impending zombie charges.
        """
        parsed = cls.parse_pre_debit_alert(alert_text)
        expected_amt = parsed["expected_amount"]
        tokens = parsed["tokens"]

        matched_mandate: Optional[Mandate] = None

        # 1. Match by UMN / UMRN Token
        if tokens.get("umn") or tokens.get("umrn"):
            target_token = tokens.get("umn") or tokens.get("umrn")
            for m in user_mandates:
                if m.umn_or_umrn and m.umn_or_umrn.upper() == target_token.upper():
                    matched_mandate = m
                    break

        # 2. Match by Merchant Name in alert text
        if not matched_mandate:
            for m in user_mandates:
                if m.merchant_name.lower() in alert_text.lower() or m.descriptor.lower() in alert_text.lower():
                    matched_mandate = m
                    break

        if not matched_mandate:
            return {
                "matched": False,
                "alert": parsed,
                "warning": "No matching active mandate found for this pre-debit alert."
            }

        # Audit against matched mandate
        alerts = []
        is_safe = True

        # Check Cap Limit (if latest_amount or registered cap is exceeded)
        latest_amt = float(matched_mandate.latest_amount)
        if expected_amt > (latest_amt * 1.05):
            is_safe = False
            pct = ((expected_amt - latest_amt) / latest_amt) * 100.0
            alerts.append({
                "type": "IMPENDING_PRICE_HIKE",
                "severity": "HIGH",
                "message": f"Pre-debit alert of ₹{expected_amt:.0f} is +{pct:.1f}% higher than previous cycle (₹{latest_amt:.0f})."
            })

        # Check Zombie Alert
        if matched_mandate.flag == "UNUSED_ZOMBIE":
            is_safe = False
            alerts.append({
                "type": "DORMANT_SUBSCRIPTION_DEBIT",
                "severity": "CRITICAL",
                "message": f"Impending auto-debit of ₹{expected_amt:.0f} for dormant subscription '{matched_mandate.merchant_name}'. Revoke mandate now before execution."
            })

        return {
            "matched": True,
            "mandate_id": matched_mandate.id,
            "merchant_name": matched_mandate.merchant_name,
            "expected_amount": expected_amt,
            "scheduled_date": parsed["scheduled_date"],
            "is_safe_to_execute": is_safe,
            "risk_alerts": alerts,
            "cancellation_steps": matched_mandate.cancellation_steps
        }
