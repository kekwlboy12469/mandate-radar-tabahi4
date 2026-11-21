"""
Engine 7: Payment Predictor & Cash Flow Forward Forecasting Engine
Predicts future execution dates, simulates account liquidity runway, and adjusts for banking business days.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import calendar

class PaymentPredictor:
    """
    Computes deterministic forward debit dates, schedules, and cashflow projections.
    """

    # Major Indian National Banking Holidays (Fixed calendar references)
    BANK_HOLIDAYS_FIXED = {
        (1, 26),   # Republic Day
        (8, 15),   # Independence Day
        (10, 2),   # Gandhi Jayanti
        (5, 1),    # May Day
    }

    @classmethod
    def is_banking_business_day(cls, dt: date) -> bool:
        """
        In India, banks are closed on Sundays, and 2nd and 4th Saturdays of every month.
        """
        # 0=Monday, 6=Sunday
        if dt.weekday() == 6:
            return False
        
        # Check 2nd and 4th Saturday
        if dt.weekday() == 5:
            day = dt.day
            # 1-7: 1st Sat, 8-14: 2nd Sat, 15-21: 3rd Sat, 22-28: 4th Sat
            if 8 <= day <= 14 or 22 <= day <= 28:
                return False
        
        # Check fixed public holidays
        if (dt.month, dt.day) in cls.BANK_HOLIDAYS_FIXED:
            return False

        return True

    @classmethod
    def adjust_for_banking_rail(cls, target_date: date, payment_rail: str) -> date:
        """
        UPI AutoPay executes 24x7x365 regardless of banking holidays.
        NACH and Bank Standing Instructions execute only on Banking Business Days.
        """
        rail_upper = (payment_rail or "").upper()
        if "UPI" in rail_upper:
            # UPI operates 24/7/365
            return target_date
        
        # For NACH / ECS / SI, rollover forward to next business day
        curr = target_date
        max_hops = 7
        while not cls.is_banking_business_day(curr) and max_hops > 0:
            curr += timedelta(days=1)
            max_hops -= 1
        return curr

    @classmethod
    def calculate_next_date(cls, last_date: date, cadence: str, payment_rail: str = "UPI") -> date:
        """
        Calculates next expected payment date based on cadence.
        """
        cadence_upper = (cadence or "MONTHLY").upper()

        if cadence_upper == "DAILY":
            raw_next = last_date + timedelta(days=1)
        elif cadence_upper == "WEEKLY":
            raw_next = last_date + timedelta(days=7)
        elif cadence_upper == "BIWEEKLY":
            raw_next = last_date + timedelta(days=14)
        elif cadence_upper == "QUARTERLY":
            # Add 3 months
            month = last_date.month + 3
            year = last_date.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            max_day = calendar.monthrange(year, month)[1]
            day = min(last_date.day, max_day)
            raw_next = date(year, month, day)
        elif cadence_upper == "ANNUAL" or cadence_upper == "YEARLY":
            try:
                raw_next = last_date.replace(year=last_date.year + 1)
            except ValueError:
                # Leap year handling (Feb 29 -> Feb 28)
                raw_next = last_date.replace(year=last_date.year + 1, day=28)
        else: # Default MONTHLY
            month = last_date.month + 1
            year = last_date.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            max_day = calendar.monthrange(year, month)[1]
            day = min(last_date.day, max_day)
            raw_next = date(year, month, day)

        return cls.adjust_for_banking_rail(raw_next, payment_rail)

    @classmethod
    def predict_upcoming_schedule(
        cls,
        mandates: List[Dict[str, Any]],
        days_forward: int = 30,
        from_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates a chronological schedule of predicted debits within the forward horizon.
        """
        ref_date = from_date or date.today()
        end_date = ref_date + timedelta(days=days_forward)

        schedule = []

        for m in mandates:
            status = (m.get("status") or "ACTIVE").upper()
            if status in ("REVOKED", "EXPIRED", "PAUSED"):
                continue

            # Parse last execution date
            last_date_val = m.get("last_execution_date") or m.get("created_at")
            if isinstance(last_date_val, str):
                try:
                    last_date = datetime.strptime(last_date_val[:10], "%Y-%m-%d").date()
                except ValueError:
                    last_date = ref_date
            elif isinstance(last_date_val, datetime):
                last_date = last_date_val.date()
            elif isinstance(last_date_val, date):
                last_date = last_date_val
            else:
                last_date = ref_date

            cadence = m.get("cadence", "MONTHLY")
            rail = m.get("payment_rail", m.get("mechanism", "UPI"))
            amount = float(m.get("latest_amount", m.get("amount", 0.0)))
            merchant = m.get("merchant_name", m.get("descriptor", "Unknown Merchant"))
            mandate_id = m.get("id", "m_unknown")

            # Project forward iteratively
            curr = last_date
            while curr <= end_date:
                next_dt = cls.calculate_next_date(curr, cadence, rail)
                if next_dt > end_date:
                    break
                if next_dt >= ref_date:
                    days_away = (next_dt - ref_date).days
                    urgency = "DUE_TODAY" if days_away == 0 else f"IN_{days_away}_DAYS"
                    if days_away <= 2:
                        urgency = "IMMINENT_48H"

                    schedule.append({
                        "mandate_id": mandate_id,
                        "merchant_name": merchant,
                        "amount": amount,
                        "currency": "INR",
                        "predicted_date": next_dt.isoformat(),
                        "days_until_debit": days_away,
                        "urgency": urgency,
                        "payment_rail": rail,
                        "cadence": cadence,
                        "tier": m.get("mandate_tier", "INFERRED_SUBSCRIPTION")
                    })
                curr = next_dt

        schedule.sort(key=lambda x: x["predicted_date"])
        return schedule

    @classmethod
    def forecast_cashflow(
        cls,
        mandates: List[Dict[str, Any]],
        starting_balance: float = 25000.0,
        days_forward: int = 30
    ) -> Dict[str, Any]:
        """
        Projects running balance and flags potential liquidity shortfalls.
        """
        schedule = cls.predict_upcoming_schedule(mandates, days_forward=days_forward)

        running_balance = starting_balance
        daily_projection = []
        liquidity_warning = None
        total_outflow = 0.0

        for item in schedule:
            debit_amt = item["amount"]
            total_outflow += debit_amt
            running_balance -= debit_amt

            point = {
                "date": item["predicted_date"],
                "merchant": item["merchant_name"],
                "debit_amount": debit_amt,
                "projected_balance": round(running_balance, 2),
                "is_negative": running_balance < 0
            }
            daily_projection.append(point)

            if running_balance < 0 and not liquidity_warning:
                liquidity_warning = {
                    "alert": "POTENTIAL_BOUNCE_RISK",
                    "severity": "CRITICAL",
                    "projected_shortfall": round(abs(running_balance), 2),
                    "breach_date": item["predicted_date"],
                    "failed_merchant": item["merchant_name"],
                    "message": f"Account projected to breach zero balance on {item['predicted_date']} when debiting ₹{debit_amt:.0f} for {item['merchant_name']}."
                }

        return {
            "starting_balance": starting_balance,
            "projected_ending_balance": round(running_balance, 2),
            "total_projected_outflow": round(total_outflow, 2),
            "forecast_days": days_forward,
            "total_events": len(schedule),
            "liquidity_risk": liquidity_warning is not None,
            "liquidity_warning": liquidity_warning,
            "timeline": daily_projection
        }

