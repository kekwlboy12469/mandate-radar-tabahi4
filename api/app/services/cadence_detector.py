"""
Cadence Detection & Recurring Inference Service
Statistical analysis of payment intervals, missed billing cycles, and amount variability.
"""
import numpy as np
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from app.services.hard_negatives import HardNegativeFilter
from app.services.merchant_resolver import MerchantResolver

CADENCE_TOLERANCES = [
    ("MONTHLY", 24, 36, 12.0),
    ("QUARTERLY", 80, 105, 4.0),
    ("ANNUAL", 350, 385, 1.0)
]

class CadenceDetector:
    @classmethod
    def evaluate_series(
        cls,
        dates: List[date],
        amounts: List[float],
        descriptor: str,
        usage_feed: Optional[Dict[str, str]] = None,
        statement_end_date: Optional[date] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Analyzes a chronological series of transaction dates and amounts.
        Returns: (is_recurring, mandate_dict, rejection_dict)
        """
        count = len(dates)
        if count == 0:
            return False, None, {"descriptor": descriptor, "reason": "Empty transaction series."}

        # 1. Resolve against verified merchant catalog
        resolved = MerchantResolver.resolve(descriptor)
        hard_neg = HardNegativeFilter.match(descriptor)

        # 2. Single isolated transaction evaluation
        if count == 1:
            if resolved["is_recognized"] and "ANNUAL" in resolved.get("category", "").upper():
                amount = float(amounts[0])
                return True, {
                    "is_recognized": True,
                    "merchant_id": resolved["merchant_id"],
                    "merchant_name": resolved["merchant_name"],
                    "category": resolved["category"],
                    "parent_name": resolved["parent_name"],
                    "cadence": "ANNUAL",
                    "latest_amount": amount,
                    "initial_amount": amount,
                    "annual_committed_cost": amount,
                    "charge_count": 1,
                    "flag": "HEALTHY",
                    "flag_reason": "Verified active annual commitment.",
                    "confidence_score": 0.94,
                    "mechanism": resolved["payment_rail"],
                    "mechanism_name": resolved["mechanism_name"],
                    "missed_cycles": 0
                }, None
            else:
                return False, None, {
                    "descriptor": descriptor,
                    "reason": "Single isolated charge with no recurring schedule detected.",
                    "count": 1,
                    "amounts": amounts
                }

        # 3. Calculate interval gaps
        gaps_days = [(dates[i] - dates[i-1]).days for i in range(1, count)]
        if not gaps_days:
            return False, None, {"descriptor": descriptor, "reason": "Insufficient dates for gap analysis."}

        median_gap = float(np.median(gaps_days))

        # Check for rapid non-subscription orders (e.g. weekly orders < 14 days)
        if median_gap < 14:
            return False, None, {
                "descriptor": descriptor,
                "reason": f"Charges occur in rapid non-subscription frequency (<14 days median gap: {median_gap:.1f}d).",
                "count": count,
                "median_gap_days": median_gap,
                "amounts": amounts[:5]
            }

        # 4. Missed Cycle Recovery (e.g. 1 skipped monthly cycle causing ~60 day gap)
        normalized_gaps = []
        missed_cycles_count = 0
        for g in gaps_days:
            if 54 <= g <= 68 and 24 <= median_gap <= 36:
                # One missed monthly cycle detected
                normalized_gaps.extend([round(g / 2.0), round(g / 2.0)])
                missed_cycles_count += 1
            else:
                normalized_gaps.append(g)

        effective_median = float(np.median(normalized_gaps))

        # 5. Infer Cadence against Tolerance Bands
        cadence = None
        annual_multiplier = 1.0
        for cad_name, min_gap, max_gap, mult in CADENCE_TOLERANCES:
            if min_gap <= effective_median <= max_gap:
                cadence = cad_name
                annual_multiplier = mult
                break

        if not cadence:
            return False, None, {
                "descriptor": descriptor,
                "reason": f"Irregular interval (median gap: {effective_median:.1f} days) does not align with monthly, quarterly or annual cadence.",
                "count": count,
                "median_gap_days": effective_median,
                "amounts": amounts[:5]
            }

        # 6. Analyze Amount Stability & Variable Bills
        diffs = []
        for i in range(1, count):
            prev = amounts[i-1]
            curr = amounts[i]
            if prev > 0:
                pct = ((curr - prev) / prev) * 100.0
                if abs(pct) > 3.0:
                    diffs.append((i, prev, curr, pct))

        # Reject fluctuating metered utility bills
        if len(diffs) > 2 and hard_neg:
            return False, None, {
                "descriptor": descriptor,
                "reason": f"Variable usage-based charges detected ({len(diffs)} swings >3%). Billed for metered consumption, not fixed commitment.",
                "count": count,
                "amounts": amounts[:6]
            }

        # 7. Anomaly Flag Determination
        latest_amount = float(amounts[-1])
        initial_amount = float(amounts[0])
        annual_committed = latest_amount * annual_multiplier

        flag = "HEALTHY"
        flag_reason = f"Verified stable recurring {cadence.lower()} commitment."
        confidence = min(0.99, 0.75 + (0.04 * count))

        # A. Trial Conversion Trap (first <= 5, jump >= 10x)
        if initial_amount <= 5.0 and count >= 2 and latest_amount >= (initial_amount * 10.0):
            flag = "TRIAL_CONVERTED"
            ratio = latest_amount / max(initial_amount, 1.0)
            flag_reason = f"Trial conversion trap: Nominal initiation charge of ₹{initial_amount:.0f} auto-escalated to recurring ₹{latest_amount:.0f}/cycle ({ratio:.1f}x jump)."
            confidence = 0.99

        # B. Silent Price Hike: Step up > 3% detected in series
        elif any(d[3] > 3.0 for d in diffs):
            hike = next(d for d in diffs if d[3] > 3.0)
            _, old_amt, new_amt, pct_increase = hike
            annual_leakage = (new_amt - old_amt) * annual_multiplier
            flag = "PRICE_HIKE"
            flag_reason = f"Silent price increase of +{pct_increase:.1f}% (₹{old_amt:.0f} ➔ ₹{new_amt:.0f}). Stealth extra cost: ₹{annual_leakage:,.0f}/year."
            confidence = 0.97

        # C. Unused / Zombie Subscription (75+ days inactive, >= 2 charges since)
        if usage_feed and statement_end_date and flag not in ["PRICE_HIKE", "TRIAL_CONVERTED"]:
            m_id = resolved.get("merchant_id")
            last_activity_str = usage_feed.get(m_id) if m_id else None
            if last_activity_str:
                last_act = datetime.strptime(last_activity_str[:10], "%Y-%m-%d").date()
                days_inactive = (statement_end_date - last_act).days
                charges_since = sum(1 for d in dates if d > last_act)

                if days_inactive >= 75 and charges_since >= 2:
                    flag = "UNUSED_ZOMBIE"
                    wasted = sum(amounts[-charges_since:])
                    flag_reason = f"Zombie subscription: Zero account activity for {days_inactive} days. ₹{wasted:,.0f} debited across {charges_since} unutilized cycles."
                    confidence = 0.96

        if missed_cycles_count > 0 and flag == "HEALTHY":
            flag_reason += f" ({missed_cycles_count} skipped billing cycle detected and recovered)."

        return True, {
            "is_recognized": resolved["is_recognized"],
            "merchant_id": resolved.get("merchant_id"),
            "merchant_name": resolved["merchant_name"],
            "category": resolved["category"],
            "parent_name": resolved.get("parent_name", "Independent / Unmapped"),
            "descriptor": descriptor,
            "cadence": cadence,
            "latest_amount": latest_amount,
            "initial_amount": initial_amount,
            "annual_committed_cost": annual_committed,
            "charge_count": count,
            "first_seen": dates[0].isoformat(),
            "last_charged": dates[-1].isoformat(),
            "mechanism": resolved["payment_rail"],
            "mechanism_name": resolved["mechanism_name"],
            "flag": flag,
            "flag_reason": flag_reason,
            "confidence_score": round(confidence, 2),
            "savings_if_cancelled": annual_committed,
            "pitfall": resolved.get("pitfall", ""),
            "support_email": resolved.get("support_email", ""),
            "grievance_email": resolved.get("grievance_email", ""),
            "official_website": resolved.get("official_website", ""),
            "cancellation_steps": resolved.get("cancellation_steps", []),
            "missed_cycles": missed_cycles_count
        }, None
