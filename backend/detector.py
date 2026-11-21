"""
Mandate Radar Deterministic Detection Engine
============================================
Strictly rules-based, non-probabilistic Pandas/Python engine.
Detects recurring cadence, price hikes, trial traps, zombie/unused charges,
tags billing types ('fixed' vs 'usage_based'), calculates expected next charge dates,
and computes idempotent cryptographic charge hashes.
"""

from datetime import datetime
import hashlib
import re
import numpy as np
import pandas as pd
from reference_data import REFERENCE_MERCHANTS, PAYMENT_MECHANISMS, HARD_NEGATIVE_PATTERNS

def clean_descriptor(descriptor: str) -> str:
    """Cleans punctuation, ref IDs, and trailing whitespace for fallback grouping."""
    text = str(descriptor).upper()
    text = re.sub(r"[#*\/\\\-_:]", " ", text)
    text = re.sub(r"\b\d{4,}\b", "", text) # Remove long transaction or reference numbers
    text = re.sub(r"\s+", " ", text).strip()
    return text

def generate_charge_hash(user_id: str, account_label: str, date: str, amount: float, descriptor: str, ref_or_row_idx: str = "") -> str:
    """
    Computes an idempotent cryptographic hash for a transaction line:
    SHA256(user_id + account_label + date + amount + clean_descriptor + ref_or_row_idx)
    Guarantees that re-uploading the same statement creates zero duplicates, while two
    legitimate identical charges on the same day remain distinct.
    """
    raw = f"{user_id}:{account_label}:{date}:{amount:.2f}:{clean_descriptor(descriptor)}:{ref_or_row_idx}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def compute_expected_next_charge_date(last_charged_dt: pd.Timestamp, cadence: str) -> str:
    """Calculates the expected next debit date based on detected interval."""
    if cadence == "MONTHLY":
        next_dt = last_charged_dt + pd.Timedelta(days=30)
    elif cadence == "QUARTERLY":
        next_dt = last_charged_dt + pd.Timedelta(days=91)
    elif cadence == "ANNUAL":
        next_dt = last_charged_dt + pd.Timedelta(days=365)
    else:
        next_dt = last_charged_dt + pd.Timedelta(days=30)
    return next_dt.strftime("%Y-%m-%d")

def resolve_merchant_from_descriptor(descriptor: str):
    """
    Deterministically matches raw descriptor against verified reference graph regexes.
    NEVER guesses or hallucinates. Returns None if unrecognised.
    """
    for m in REFERENCE_MERCHANTS:
        for pattern in m.get("descriptors", []):
            if re.search(pattern, str(descriptor), re.IGNORECASE):
                return m
    return None

def detect_payment_mechanism(descriptor: str, ref_str: str = ""):
    """
    Detects the rail (UPI AutoPay, Card SI, Bank NACH, Play Store, App Store, Direct).
    """
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

def analyze_statement(
    transactions_data: list,
    usage_feed: dict = None,
    user_id: str = "user_primary",
    account_label: str = "Primary Account"
):
    """
    Main detection pipeline running on statement transactions.
    Supports variable-amount recurring charges (usage_based vs fixed contracts),
    multi-statement idempotent hashing, and post-cancellation charge projections.
    """
    if usage_feed is None:
        usage_feed = {}

    df = pd.DataFrame(transactions_data)
    if df.empty or "date" not in df.columns or "amount" not in df.columns:
        return {
            "mandates": [],
            "rejected_transactions": [],
            "annual_committed_total": 0.0,
            "annual_potential_savings": 0.0,
            "fixed_committed_total": 0.0,
            "usage_based_run_rate_total": 0.0,
            "metrics": {
                "total_transactions": 0,
                "mandates_found": 0,
                "price_hikes": 0,
                "trial_conversions": 0,
                "zombie_subscriptions": 0,
                "usage_based_mandates": 0,
                "hard_negatives_filtered": 0
            }
        }

    df["date_dt"] = pd.to_datetime(df["date"])
    df["amount_num"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["raw_descriptor"] = df["descriptor"].fillna("").astype(str)
    df["ref_str"] = df.get("ref", pd.Series([""] * len(df))).fillna("").astype(str)
    df["row_idx"] = df.index.astype(str)

    # Attach idempotent charge hash to each raw transaction
    df["charge_hash"] = df.apply(
        lambda r: generate_charge_hash(
            user_id=user_id,
            account_label=account_label,
            date=str(r["date"]),
            amount=float(r["amount_num"]),
            descriptor=r["raw_descriptor"],
            ref_or_row_idx=str(r["ref_str"]) or str(r["row_idx"])
        ),
        axis=1
    )

    # 1. First Pass: Resolve against reference graph or fallback to cleaned key
    def get_group_key(row):
        resolved = resolve_merchant_from_descriptor(row["raw_descriptor"])
        if resolved:
            return f"REF::{resolved['id']}"
        return f"RAW::{clean_descriptor(row['raw_descriptor'])}"

    df["group_key"] = df.apply(get_group_key, axis=1)

    mandates = []
    rejected = []

    # Reference evaluation date (latest date in statement)
    statement_end_date = df["date_dt"].max()

    for group_key, group in df.groupby("group_key"):
        sorted_group = group.sort_values("date_dt").reset_index(drop=True)
        count = len(sorted_group)

        # Check for hard negative pattern matches first
        sample_desc = sorted_group["raw_descriptor"].iloc[0]
        hard_negative_match = None
        for hn in HARD_NEGATIVE_PATTERNS:
            for p in hn["descriptors"]:
                if re.search(p, sample_desc, re.IGNORECASE):
                    hard_negative_match = hn
                    break
            if hard_negative_match:
                break

        # A recurring mandate requires at least 1 annual or >= 2 monthly/quarterly occurrences
        if count == 1:
            # Check if this single charge matches a known annual subscription in reference
            resolved_ref = resolve_merchant_from_descriptor(sample_desc)
            amount = float(sorted_group["amount_num"].iloc[0])
            is_annual = resolved_ref and "ANNUAL" in resolved_ref.get("supported_cadences", []) and (amount >= 499.0 or resolved_ref.get("supported_cadences") == ["ANNUAL"])
            if is_annual:
                # Annual mandate registered
                annual_committed = amount
                mechanism = detect_payment_mechanism(sample_desc, sorted_group["ref_str"].iloc[0])
                mech_details = PAYMENT_MECHANISMS.get(mechanism, PAYMENT_MECHANISMS["DIRECT_MERCHANT"])
                first_date_dt = sorted_group["date_dt"].iloc[0]
                expected_next = compute_expected_next_charge_date(first_date_dt, "ANNUAL")

                # Prepare charge history with idempotent hashes
                history = []
                for _, row in sorted_group.iterrows():
                    history.append({
                        "id": row["charge_hash"],
                        "date": str(row["date"]),
                        "amount": float(row["amount_num"]),
                        "descriptor": row["raw_descriptor"],
                        "account_label": account_label
                    })

                mandates.append({
                    "id": f"mandate_{resolved_ref['id']}",
                    "merchant_id": resolved_ref["id"],
                    "merchant_name": resolved_ref["name"],
                    "category": resolved_ref["category"],
                    "parent_id": resolved_ref.get("parent_id"),
                    "parent_name": resolved_ref.get("parent"),
                    "descriptor": sample_desc,
                    "is_recognized": True,
                    "cadence": "ANNUAL",
                    "billing_type": "fixed",
                    "latest_amount": amount,
                    "initial_amount": amount,
                    "annual_committed_cost": annual_committed,
                    "charge_count": 1,
                    "first_seen": sorted_group["date"].iloc[0],
                    "last_charged": sorted_group["date"].iloc[0],
                    "expected_next_charge_date": expected_next,
                    "account_label": account_label,
                    "mechanism": mechanism,
                    "mechanism_name": mech_details["name"],
                    "flag": "HEALTHY",
                    "flag_reason": "Verified active annual contract.",
                    "confidence_score": 0.94,
                    "savings_if_cancelled": annual_committed,
                    "pitfall": resolved_ref.get("cancellation_pitfall", ""),
                    "cancellation_steps": mech_details["cancellation_steps"],
                    "history": history
                })
                continue
            else:
                rejected.append({
                    "descriptor": sample_desc,
                    "reason": "Single isolated charge with no recurring schedule detected.",
                    "count": 1,
                    "amounts": [float(sorted_group["amount_num"].iloc[0])]
                })
                continue

        # Multiple transactions: Analyze time gaps and amounts
        date_series = sorted_group["date_dt"]
        gaps_days = (date_series - date_series.shift(1)).dt.days.dropna().tolist()
        amounts = sorted_group["amount_num"].tolist()

        median_gap = float(np.median(gaps_days)) if gaps_days else 0.0

        # Hard negative check: Weekly interval (< 14 days)
        if median_gap < 14:
            rejected.append({
                "descriptor": sample_desc,
                "reason": "Charges occur in rapid non-subscription frequency (<14 days median gap, e.g. weekly orders).",
                "count": count,
                "median_gap_days": median_gap,
                "amounts": amounts[:5]
            })
            continue

        # Infer cadence with tolerance bands
        cadence = None
        if 24 <= median_gap <= 36: # Monthly ±5 days
            cadence = "MONTHLY"
            annual_multiplier = 12.0
        elif 80 <= median_gap <= 100: # Quarterly ±10 days
            cadence = "QUARTERLY"
            annual_multiplier = 4.0
        elif 350 <= median_gap <= 380: # Annual ±15 days
            cadence = "ANNUAL"
            annual_multiplier = 1.0
        else:
            rejected.append({
                "descriptor": sample_desc,
                "reason": f"Irregular interval (median gap: {median_gap:.1f} days) does not align with monthly, quarterly or annual cadence.",
                "count": count,
                "median_gap_days": median_gap,
                "amounts": amounts[:5]
            })
            continue

        latest_amount = float(amounts[-1])
        initial_amount = float(amounts[0])
        last_charged_dt = sorted_group["date_dt"].iloc[-1]
        expected_next = compute_expected_next_charge_date(last_charged_dt, cadence)

        # Analyze amount stability & step changes > 3%
        diffs = []
        for i in range(1, len(amounts)):
            prev = amounts[i-1]
            curr = amounts[i]
            if prev > 0:
                pct = ((curr - prev) / prev) * 100.0
                if abs(pct) > 3.0:
                    diffs.append((i, prev, curr, pct))

        # Check for fluctuating variable bill (hard negative: electricity bill)
        if len(diffs) > 2 and hard_negative_match:
            rejected.append({
                "descriptor": sample_desc,
                "reason": f"Fluctuating utility consumption ({len(diffs)} price swings >3%). Billed for metered consumption, not recurring mandate.",
                "count": count,
                "amounts": amounts[:6]
            })
            continue

        # Billing Type Classification: 'usage_based' vs 'fixed'
        # Compute coefficient of variation across historical amounts
        mean_amt = float(np.mean(amounts))
        std_amt = float(np.std(amounts)) if len(amounts) > 1 else 0.0
        cv = (std_amt / mean_amt) if mean_amt > 0 else 0.0

        # If variance > 10% across cycles (e.g. AWS, Twilio, OpenAI API), tag as usage_based
        is_usage_based = cv > 0.10 and len(diffs) >= 2

        billing_type = "usage_based" if is_usage_based else "fixed"

        # Flag Determination
        flag = "HEALTHY"
        flag_reason = f"Verified stable recurring {cadence.lower()} commitment."
        confidence = 0.98

        # 1. Trial Conversion Check: First charge <= 5 and jump >= 10x
        if initial_amount <= 5.0 and len(amounts) >= 2 and latest_amount >= (initial_amount * 10.0):
            flag = "TRIAL_CONVERTED"
            ratio = latest_amount / max(initial_amount, 1.0)
            flag_reason = f"Trial conversion trap: Nominal initiation charge of ₹{initial_amount:.0f} auto-escalated to recurring ₹{latest_amount:.0f}/cycle ({ratio:.1f}x jump)."
            confidence = 0.99

        # 2. Silent Price Hike Check: Exactly 1 step up > 3% in an otherwise stable fixed series
        elif not is_usage_based and len(diffs) == 1 and diffs[0][3] > 3.0:
            step_idx, old_amt, new_amt, pct_increase = diffs[0]
            annual_leakage = (new_amt - old_amt) * annual_multiplier
            flag = "PRICE_HIKE"
            flag_reason = f"Silent price increase of +{pct_increase:.1f}% (₹{old_amt:.0f} ➔ ₹{new_amt:.0f}). Stealth extra cost: ₹{annual_leakage:,.0f}/year."
            confidence = 0.97

        # 3. Usage-based description note
        elif is_usage_based:
            flag_reason = f"Usage-based {cadence.lower()} billing: Fluctuating metered consumption (trailing run-rate: ₹{latest_amount * annual_multiplier:,.0f}/yr)."
            confidence = 0.92

        # 4. Unused / Zombie Subscription Check
        merchant_info = resolve_merchant_from_descriptor(sample_desc)
        merchant_id = merchant_info["id"] if merchant_info else None

        last_activity_date_str = usage_feed.get(merchant_id) if merchant_id else None
        if last_activity_date_str and flag not in ["PRICE_HIKE", "TRIAL_CONVERTED"]:
            last_activity = pd.to_datetime(last_activity_date_str)
            days_inactive = (statement_end_date - last_activity).days
            charges_since = sum(1 for d in date_series if d > last_activity)

            if days_inactive >= 75 and charges_since >= 2:
                flag = "UNUSED_ZOMBIE"
                wasted = sum(amounts[-charges_since:])
                flag_reason = f"Zombie subscription: Zero account activity for {days_inactive} days. ₹{wasted:,.0f} debited across {charges_since} unutilized cycles."
                confidence = 0.96

        # Annual Committed Exposure
        if is_usage_based:
            annual_committed = round(mean_amt * annual_multiplier, 2)
            # Usage-based mandates are excluded from guaranteed fixed cancellation savings
            savings_if_cancelled = 0.0
        else:
            annual_committed = round(latest_amount * annual_multiplier, 2)
            savings_if_cancelled = annual_committed

        mechanism = detect_payment_mechanism(sample_desc, sorted_group["ref_str"].iloc[-1])
        mech_details = PAYMENT_MECHANISMS.get(mechanism, PAYMENT_MECHANISMS["DIRECT_MERCHANT"])

        is_recognized = merchant_info is not None
        merchant_name = merchant_info["name"] if is_recognized else f"Unrecognised: {clean_descriptor(sample_desc)}"
        category = merchant_info["category"] if is_recognized else "Uncategorized Subscription"
        parent_id = merchant_info.get("parent_id") if is_recognized else None
        parent_name = merchant_info.get("parent") if is_recognized else "Independent / Unmapped"
        pitfall = merchant_info.get("cancellation_pitfall", "") if is_recognized else "Verify merchant cancellation terms."

        # History with idempotent hashes
        history = []
        for _, row in sorted_group.iterrows():
            history.append({
                "id": row["charge_hash"],
                "date": str(row["date"]),
                "amount": float(row["amount_num"]),
                "descriptor": row["raw_descriptor"],
                "account_label": account_label
            })

        mandates.append({
            "id": f"mandate_{merchant_id or clean_descriptor(sample_desc)[:16].replace(' ', '_')}",
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "category": category,
            "parent_id": parent_id,
            "parent_name": parent_name,
            "descriptor": sample_desc,
            "is_recognized": is_recognized,
            "cadence": cadence,
            "billing_type": billing_type,
            "latest_amount": latest_amount,
            "initial_amount": initial_amount,
            "annual_committed_cost": annual_committed,
            "charge_count": count,
            "first_seen": sorted_group["date"].iloc[0],
            "last_charged": sorted_group["date"].iloc[-1],
            "expected_next_charge_date": expected_next,
            "account_label": account_label,
            "mechanism": mechanism,
            "mechanism_name": mech_details["name"],
            "flag": flag,
            "flag_reason": flag_reason,
            "confidence_score": confidence,
            "savings_if_cancelled": savings_if_cancelled,
            "pitfall": pitfall,
            "support_email": merchant_info.get("support_email", "support@merchant.com") if is_recognized else "",
            "grievance_email": merchant_info.get("grievance_email", "grievance@merchant.com") if is_recognized else "",
            "official_website": merchant_info.get("official_website", "") if is_recognized else "",
            "cancellation_steps": mech_details["cancellation_steps"],
            "history": history
        })

    # Sort mandates: flags with highest risk first, then by annual committed spend
    flag_priority = {"UNUSED_ZOMBIE": 1, "PRICE_HIKE": 2, "TRIAL_CONVERTED": 3, "HEALTHY": 4}
    mandates.sort(key=lambda m: (flag_priority.get(m["flag"], 5), -m["annual_committed_cost"]))

    fixed_committed_total = sum(m["annual_committed_cost"] for m in mandates if m.get("billing_type") != "usage_based")
    usage_based_run_rate_total = sum(m["annual_committed_cost"] for m in mandates if m.get("billing_type") == "usage_based")
    annual_committed_total = fixed_committed_total + usage_based_run_rate_total

    # Only fixed flagged mandates produce guaranteed annual potential savings
    potential_savings = sum(m["annual_committed_cost"] for m in mandates if m["flag"] != "HEALTHY" and m.get("billing_type") != "usage_based")

    price_hikes_count = sum(1 for m in mandates if m["flag"] == "PRICE_HIKE")
    trial_conv_count = sum(1 for m in mandates if m["flag"] == "TRIAL_CONVERTED")
    zombies_count = sum(1 for m in mandates if m["flag"] == "UNUSED_ZOMBIE")
    usage_based_count = sum(1 for m in mandates if m.get("billing_type") == "usage_based")

    return {
        "mandates": mandates,
        "rejected_transactions": rejected,
        "annual_committed_total": round(annual_committed_total, 2),
        "fixed_committed_total": round(fixed_committed_total, 2),
        "usage_based_run_rate_total": round(usage_based_run_rate_total, 2),
        "annual_potential_savings": round(potential_savings, 2),
        "metrics": {
            "total_transactions": len(df),
            "mandates_found": len(mandates),
            "price_hikes": price_hikes_count,
            "trial_conversions": trial_conv_count,
            "zombie_subscriptions": zombies_count,
            "usage_based_mandates": usage_based_count,
            "hard_negatives_filtered": len(rejected)
        }
    }
