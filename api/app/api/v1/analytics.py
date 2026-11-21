"""
Analytics & Cadence API Router (v1)
Provides recurring payment detection, cadence reporting, and anomaly discovery.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.db import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.mandate import Mandate
from app.api.v1.auth import get_current_user
from app.services.cadence_detector import CadenceDetector
from app.services.normalizer import clean_descriptor
from app.services.predictor import PaymentPredictor
from app.services.graph_analytics import GraphAnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/recurring")
def analyze_user_recurring_payments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates all transactions in the user's ledger, executes statistical cadence detection,
    and returns detected mandates alongside rejected non-recurring groups.
    """
    txs = db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.transaction_date.asc()).all()
    if not txs:
        return {"mandates": [], "rejected_transactions": [], "metrics": {"total_transactions": 0}}

    # Group transactions by canonical merchant if recognized, otherwise cleaned descriptor
    from app.services.merchant_resolver import MerchantResolver

    groups: Dict[str, List[Transaction]] = {}
    for t in txs:
        res = MerchantResolver.resolve(t.raw_descriptor, t.ref_number or "")
        if res["is_recognized"]:
            key = f"REF::{res['merchant_id']}"
        else:
            key = f"RAW::{clean_descriptor(t.raw_descriptor)}"
        if key not in groups:
            groups[key] = []
        groups[key].append(t)

    statement_end_date = max(t.transaction_date for t in txs)
    mandates = []
    rejected = []

    for key, group_txs in groups.items():
        sample_desc = group_txs[0].raw_descriptor
        dates = [t.transaction_date for t in group_txs]
        amounts = [float(t.amount) for t in group_txs]

        is_rec, m_data, rej_data = CadenceDetector.evaluate_series(
            dates=dates,
            amounts=amounts,
            descriptor=sample_desc,
            statement_end_date=statement_end_date
        )

        if is_rec and m_data:
            m_data["id"] = f"mand_{key[:16].replace(' ', '_').lower()}"
            m_data["history"] = [
                {"id": t.id, "date": t.transaction_date.isoformat(), "amount": float(t.amount), "descriptor": t.raw_descriptor}
                for t in group_txs
            ]
            mandates.append(m_data)
        elif rej_data:
            rejected.append(rej_data)

    annual_committed = sum(m["annual_committed_cost"] for m in mandates)
    potential_savings = sum(m["annual_committed_cost"] for m in mandates if m["flag"] != "HEALTHY")

    return {
        "mandates": mandates,
        "rejected_transactions": rejected,
        "metrics": {
            "total_transactions": len(txs),
            "mandates_found": len(mandates),
            "price_hikes": sum(1 for m in mandates if m["flag"] == "PRICE_HIKE"),
            "trial_conversions": sum(1 for m in mandates if m["flag"] == "TRIAL_CONVERTED"),
            "zombie_subscriptions": sum(1 for m in mandates if m["flag"] == "UNUSED_ZOMBIE"),
            "non_recurring_rejected": len(rejected)
        },
        "financial_summary": {
            "annual_committed_total": round(annual_committed, 2),
            "monthly_equivalent": round(annual_committed / 12.0, 2),
            "annual_potential_savings": round(potential_savings, 2)
        }
    }

@router.get("/anomalies")
def get_flagged_anomalies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all active commitments flagged with price creep, trial traps, or dormancy."""
    analysis = analyze_user_recurring_payments(user=user, db=db)
    flagged = [m for m in analysis["mandates"] if m["flag"] != "HEALTHY"]
    return {
        "count": len(flagged),
        "potential_annual_savings": sum(m["annual_committed_cost"] for m in flagged),
        "anomalies": flagged
    }

@router.get("/upcoming-debits")
def get_upcoming_debits(
    days: int = Query(30, ge=1, le=180, description="Forward forecast window in days"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a calendar of predicted upcoming auto-debits within the specified window.
    Adjusts for Indian banking business days and statutory pre-debit lead times.
    """
    mandates = db.query(Mandate).filter(
        Mandate.user_id == user.id,
        Mandate.status.in_(["ACTIVE", "PENDING_VERIFICATION"])
    ).all()

    mandates_data = [
        {
            "id": m.id,
            "merchant_name": m.merchant_name,
            "descriptor": m.descriptor,
            "latest_amount": float(m.latest_amount),
            "cadence": m.cadence,
            "payment_rail": m.mandate_type,
            "status": m.status,
            "last_execution_date": m.last_charged.isoformat() if m.last_charged else (m.created_at.isoformat() if m.created_at else None),
            "mandate_tier": m.mandate_type
        }
        for m in mandates
    ]

    schedule = PaymentPredictor.predict_upcoming_schedule(mandates_data, days_forward=days)
    total_due = sum(item["amount"] for item in schedule)

    return {
        "forward_window_days": days,
        "total_scheduled_events": len(schedule),
        "total_projected_outflow": round(total_due, 2),
        "schedule": schedule
    }

@router.get("/cashflow-forecast")
def get_cashflow_forecast(
    days: int = Query(30, ge=7, le=90),
    balance: float = Query(25000.0, description="Current available liquid balance"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Projects daily running account balance and alerts on potential overdraft/bounce risks.
    """
    mandates = db.query(Mandate).filter(
        Mandate.user_id == user.id,
        Mandate.status.in_(["ACTIVE", "PENDING_VERIFICATION"])
    ).all()

    mandates_data = [
        {
            "id": m.id,
            "merchant_name": m.merchant_name,
            "latest_amount": float(m.latest_amount),
            "cadence": m.cadence,
            "payment_rail": m.mandate_type,
            "status": m.status,
            "last_execution_date": m.last_charged.isoformat() if m.last_charged else (m.created_at.isoformat() if m.created_at else None)
        }
        for m in mandates
    ]

    forecast = PaymentPredictor.forecast_cashflow(
        mandates=mandates_data,
        starting_balance=balance,
        days_forward=days
    )
    return forecast

@router.get("/corporate-footprint")
def get_corporate_footprint(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Groups subscriptions by parent company conglomerates (e.g. Alphabet, Amazon, Apple, Times Internet)
    and surfaces bundle/consolidation recommendations.
    """
    mandates = db.query(Mandate).filter(
        Mandate.user_id == user.id,
        Mandate.status != "REVOKED"
    ).all()

    mandates_data = [
        {
            "id": m.id,
            "merchant_name": m.merchant_name,
            "latest_amount": float(m.latest_amount),
            "cadence": m.cadence,
            "payment_rail": m.mandate_type,
            "status": m.status,
            "mandate_tier": m.mandate_type
        }
        for m in mandates
    ]

    return {
        "footprint": GraphAnalyticsService.analyze_corporate_footprint(mandates_data),
        "functional_redundancies": GraphAnalyticsService.detect_functional_redundancies(mandates_data),
        "vulnerability_audit": GraphAnalyticsService.calculate_vulnerability_index(mandates_data)
    }
