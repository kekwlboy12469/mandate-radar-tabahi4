"""
Mandates & Subscriptions API Router (v1)
Interacts with persistent PostgreSQL models while maintaining high-speed caching.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.db import get_db
from app.models.mandate import Mandate
from app.models.transaction import Transaction
from app.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/mandates", tags=["Mandates"])

@router.get("")
def list_mandates(
    flag: Optional[str] = None,
    status: Optional[str] = "ACTIVE",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves user's mandates from the persistent database."""
    query = db.query(Mandate).filter(Mandate.user_id == user.id)
    if status:
        query = query.filter(Mandate.status == status)
    if flag and flag != "ALL":
        query = query.filter(Mandate.flag == flag)
    
    results = query.order_by(Mandate.annual_committed_cost.desc()).all()
    
    output = []
    for m in results:
        # Fetch charge history
        txs = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.raw_descriptor.ilike(f"%{m.descriptor[:15]}%")
        ).order_by(Transaction.transaction_date.asc()).limit(12).all()
        
        history = [
            {"id": t.id, "date": t.transaction_date.isoformat(), "amount": float(t.amount), "descriptor": t.raw_descriptor}
            for t in txs
        ]
        
        output.append({
            "id": m.id,
            "merchant_id": m.merchant_id,
            "merchant_name": m.merchant_name,
            "category": m.category,
            "parent_name": m.parent_name,
            "descriptor": m.descriptor,
            "is_recognized": m.merchant_id is not None,
            "cadence": m.cadence,
            "latest_amount": float(m.latest_amount),
            "initial_amount": float(m.initial_amount) if m.initial_amount else float(m.latest_amount),
            "annual_committed_cost": float(m.annual_committed_cost),
            "charge_count": int(m.charge_count),
            "first_seen": m.first_seen.isoformat(),
            "last_charged": m.last_charged.isoformat(),
            "mechanism": m.mandate_type,
            "mechanism_name": m.mandate_type.replace("_", " ").title(),
            "flag": m.flag,
            "flag_reason": m.flag_reason,
            "confidence_score": m.confidence_score,
            "status": m.status,
            "savings_if_cancelled": float(m.annual_committed_cost),
            "pitfall": m.pitfall or "",
            "cancellation_steps": m.cancellation_steps or [],
            "support_email": m.support_email or "",
            "grievance_email": m.grievance_email or "",
            "official_website": m.official_website or "",
            "history": history
        })
    return output

@router.get("/summary")
def get_mandate_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculates hero summary metrics directly from the persistent database."""
    mandates = db.query(Mandate).filter(Mandate.user_id == user.id, Mandate.status == "ACTIVE").all()
    annual_committed = sum(float(m.annual_committed_cost) for m in mandates)
    potential_savings = sum(float(m.annual_committed_cost) for m in mandates if m.flag != "HEALTHY")
    
    return {
        "annual_committed_total": round(annual_committed, 2),
        "monthly_equivalent": round(annual_committed / 12.0, 2),
        "potential_savings": round(potential_savings, 2),
        "total_mandates_found": len(mandates),
        "flagged_issues_count": sum(1 for m in mandates if m.flag != "HEALTHY")
    }

@router.post("/{mandate_id}/revoke")
def revoke_mandate(
    mandate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates mandate status to REVOKED in database."""
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id, Mandate.user_id == user.id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    mandate.status = "REVOKED"
    db.commit()
    return {"success": True, "mandate_id": mandate_id, "status": "REVOKED"}

@router.post("/{mandate_id}/pause")
def pause_mandate(
    mandate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pauses an active mandate."""
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id, Mandate.user_id == user.id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    from app.services.mandate_tracker import MandateTracker
    try:
        MandateTracker.transition_status(mandate, "PAUSED", reason="Mandate paused by user.")
        db.commit()
        return {"success": True, "mandate_id": mandate_id, "status": "PAUSED"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{mandate_id}/resume")
def resume_mandate(
    mandate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resumes a paused mandate back to ACTIVE."""
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id, Mandate.user_id == user.id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    from app.services.mandate_tracker import MandateTracker
    try:
        MandateTracker.transition_status(mandate, "ACTIVE", reason="Mandate resumed by user.")
        db.commit()
        return {"success": True, "mandate_id": mandate_id, "status": "ACTIVE"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{mandate_id}/verify")
def verify_mandate_token(
    mandate_id: str,
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attaches a verified UMN / UMRN token to an inferred mandate."""
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id, Mandate.user_id == user.id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    clean_token = token.strip().upper()
    mandate.umn_or_umrn = clean_token
    if "AUTOPAY" in mandate.mandate_type.upper() or len(clean_token) == 32:
        mandate.mandate_type = "VERIFIED_UPI_AUTOPAY"
    else:
        mandate.mandate_type = "VERIFIED_BANK_NACH"
    
    mandate.confidence_score = 0.99
    db.commit()
    return {
        "success": True,
        "mandate_id": mandate_id,
        "mandate_type": mandate.mandate_type,
        "umn_or_umrn": mandate.umn_or_umrn
    }

class PreDebitAlertRequest(BaseModel):
    alert_text: str

@router.post("/pre-debit-alert")
def process_pre_debit_notification(
    req: PreDebitAlertRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingests and audits a 24-48h statutory pre-debit alert against active mandates,
    warning of impending price hikes or charges on dormant services.
    """
    from app.services.pre_debit_matcher import PreDebitMatcher
    user_mandates = db.query(Mandate).filter(Mandate.user_id == user.id, Mandate.status == "ACTIVE").all()
    audit_res = PreDebitMatcher.match_and_audit(req.alert_text, user_mandates)
    return audit_res

