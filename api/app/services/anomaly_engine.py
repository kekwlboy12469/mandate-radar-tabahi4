"""
Subscription Anomaly Detection Engine
Detects Silent Price Creep, Trial Conversion Traps, Zombie/Dormant Subscriptions,
and Cross-Account Duplicate Subscriptions.
"""
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from app.models.mandate import Mandate

class AnomalyEngine:
    @staticmethod
    def audit_price_creep(
        amounts: List[float],
        cadence_multiplier: float
    ) -> Optional[Dict[str, Any]]:
        """
        Detects silent price increases in recurring payment series.
        Identifies step increases >3% and computes annual financial leakage.
        """
        if len(amounts) < 2:
            return None

        diffs = []
        for i in range(1, len(amounts)):
            prev = amounts[i - 1]
            curr = amounts[i]
            if prev > 0:
                pct = ((curr - prev) / prev) * 100.0
                if pct > 3.0:
                    diffs.append((i, prev, curr, pct))

        if diffs:
            # Pick latest significant hike
            step_idx, old_amt, new_amt, pct_increase = diffs[-1]
            annual_leakage = (new_amt - old_amt) * cadence_multiplier
            return {
                "flag": "PRICE_HIKE",
                "old_amount": old_amt,
                "new_amount": new_amt,
                "pct_increase": round(pct_increase, 1),
                "annual_leakage": round(annual_leakage, 2),
                "reason": f"Silent price increase of +{pct_increase:.1f}% (₹{old_amt:.0f} ➔ ₹{new_amt:.0f}). Stealth extra cost: ₹{annual_leakage:,.0f}/year."
            }
        return None

    @staticmethod
    def audit_trial_conversion(
        initial_amount: float,
        latest_amount: float,
        charge_count: int
    ) -> Optional[Dict[str, Any]]:
        """
        Detects nominal trial verification charges (<= 5) auto-escalating >= 10x into recurring auto-debits.
        """
        if initial_amount <= 5.0 and charge_count >= 2 and latest_amount >= (initial_amount * 10.0):
            ratio = latest_amount / max(initial_amount, 1.0)
            return {
                "flag": "TRIAL_CONVERTED",
                "initial_amount": initial_amount,
                "latest_amount": latest_amount,
                "jump_ratio": round(ratio, 1),
                "reason": f"Trial conversion trap: Nominal initiation charge of ₹{initial_amount:.0f} auto-escalated to recurring ₹{latest_amount:.0f}/cycle ({ratio:.1f}x jump)."
            }
        return None

    @staticmethod
    def audit_zombie_dormancy(
        last_activity_date: Optional[date],
        charges_since_activity: int,
        wasted_amount: float,
        reference_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detects active commitments with 60+ days of zero recorded activity and >= 2 cleared debits since.
        """
        if not last_activity_date:
            return None

        today = reference_date or date.today()
        days_inactive = (today - last_activity_date).days

        if days_inactive >= 60 and charges_since_activity >= 2:
            return {
                "flag": "UNUSED_ZOMBIE",
                "days_inactive": days_inactive,
                "charges_cleared": charges_since_activity,
                "wasted_amount": round(wasted_amount, 2),
                "reason": f"Zombie subscription: Zero account activity for {days_inactive} days. ₹{wasted_amount:,.0f} debited across {charges_since_activity} unutilized cycles."
            }
        return None

    @staticmethod
    def detect_duplicate_subscriptions(
        mandates: List[Mandate]
    ) -> List[Dict[str, Any]]:
        """
        Identifies duplicate active subscriptions paying for the same merchant
        or overlapping services across different payment instruments.
        """
        duplicates = []
        merchant_map: Dict[str, List[Mandate]] = {}

        for m in mandates:
            if m.status != "ACTIVE":
                continue
            key = m.merchant_id or m.merchant_name.lower().strip()
            merchant_map.setdefault(key, []).append(m)

        for key, m_list in merchant_map.items():
            if len(m_list) > 1:
                total_wasted = sum(float(m.annual_committed_cost) for m in m_list[1:])
                duplicates.append({
                    "merchant_name": m_list[0].merchant_name,
                    "merchant_id": key,
                    "duplicate_count": len(m_list),
                    "mandate_ids": [m.id for m in m_list],
                    "total_annual_cost": sum(float(m.annual_committed_cost) for m in m_list),
                    "potential_savings": round(total_wasted, 2),
                    "reason": f"Duplicate active subscriptions found for '{m_list[0].merchant_name}' across {len(m_list)} separate mandates."
                })

        return duplicates

