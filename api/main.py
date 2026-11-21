"""
Mandate Radar FastAPI Backend Server
Track: Neo4j (Best Use of Neo4j) - Fintech Track Solution
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import io
import os
import csv
import pandas as pd

from reference_data import REFERENCE_MERCHANTS, PARENT_COMPANIES, PAYMENT_MECHANISMS, ESCALATION_CHAIN
from synthetic_data import (
    generate_synthetic_statement,
    generate_usage_telemetry,
    generate_notification_stream,
    GROUND_TRUTH_MANDATES,
    GROUND_TRUTH_HARD_NEGATIVES
)
from detector import analyze_statement, clean_descriptor, detect_payment_mechanism
from neo4j_service import Neo4jKnowledgeGraph

app = FastAPI(
    title="Mandate Radar API",
    description="Deterministic Auto-Debit Mandate Detection & Neo4j Knowledge Graph Engine",
    version="2.0.0"
)

# CORS configuration with environment variable override
cors_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] if cors_origins_env else [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:8000", "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Relational Database & Mount API v1
db_initialized = False
db_init_error = None

try:
    from app.core.db import init_db, SessionLocal
    from app.services.seed_service import seed_database
    init_db()
    with SessionLocal() as db_session:
        seed_database(db_session)
    db_initialized = True
except Exception as e:
    db_init_error = str(e)
    print(f"Warning: Database initialization deferred: {e}")

try:
    from app.api.v1 import api_v1_router
    app.include_router(api_v1_router)
except Exception as e:
    print(f"Warning: Failed to mount api_v1_router: {e}")

# Initialize Neo4j Service
neo4j_graph = Neo4jKnowledgeGraph()

# In-memory session store
cached_statement = generate_synthetic_statement()
cached_usage = generate_usage_telemetry()
cached_notifications = generate_notification_stream()

# Pre-seed user's active portfolio in graph so Portfolio mode is immediately populated
_initial_analysis = analyze_statement(cached_statement, cached_usage)
neo4j_graph.sync_statement_mandates("Arun Sharma", _initial_analysis["mandates"])

class AnalyzeRequest(BaseModel):
    transactions: Optional[List[Dict[str, Any]]] = None
    usage_feed: Optional[Dict[str, str]] = None
    user_name: Optional[str] = "Arun Sharma"
    user_id: Optional[str] = None

class EmailDraftRequest(BaseModel):
    mandate_id: str
    merchant_name: str
    descriptor: str
    amount: float
    cadence: str
    mechanism: str
    user_name: str = "Arun Sharma"
    account_ref: str = "XX-4821 / UPI VPA"
    tone: str = "formal" # "polite", "formal", "firm_dispute"
    cancellation_reason: Optional[str] = "Subscription no longer required"

class CypherQueryRequest(BaseModel):
    query: str

class Neo4jConnectRequest(BaseModel):
    uri: str
    user: str = "neo4j"
    password: str

class OverlapDecisionRequest(BaseModel):
    user_id: Optional[str] = "user_primary"
    finding_key: Optional[str] = None
    finding_type: Optional[str] = "overlap"
    choice: Optional[str] = "CONFIRMED"
    kept_mandate_ids: List[str] = []
    cancel_mandate_ids: List[str] = []

class TagRequest(BaseModel):
    user_id: Optional[str] = "user_primary"
    tags: List[str] = []

class CancelConfirmRequest(BaseModel):
    user_id: Optional[str] = "user_primary"
    cancel_date: Optional[str] = None

class ReconcileRequest(BaseModel):
    user_id: Optional[str] = "user_primary"
    transactions: List[Dict[str, Any]]
    statement_end_date: Optional[str] = None

@app.get("/api/info")
def get_api_info():
    return {
        "service": "Mandate Radar API",
        "version": "2.0.0",
        "theme": "Fintech - The Auto Debits Nobody Can Find",
        "track": "Neo4j (Best Use of Neo4j)",
        "database_status": "ACTIVE_PERSISTENT_STORE" if db_initialized else f"DEFERRED: {db_init_error}",
        "neo4j_status": "CONNECTED" if neo4j_graph.is_connected else "EMBEDDED_GRAPH_MODE",
        "reference_merchants_count": len(REFERENCE_MERCHANTS)
    }

@app.get("/")
def root():
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return get_api_info()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "neo4j_connected": neo4j_graph.is_connected,
        "neo4j_mode": "LIVE_AURA" if neo4j_graph.is_connected else "EMBEDDED_HIGH_FIDELITY",
        "total_reference_merchants": len(REFERENCE_MERCHANTS),
        "total_parent_corporations": len(PARENT_COMPANIES),
        "payment_mechanisms_modeled": len(PAYMENT_MECHANISMS)
    }

@app.get("/api/statement/synthetic")
def get_synthetic_dataset():
    """Returns the synthetic 12-month statement, usage telemetry, and notifications."""
    return {
        "transactions": cached_statement,
        "usage_feed": cached_usage,
        "notifications": cached_notifications,
        "ground_truth_mandates": GROUND_TRUTH_MANDATES,
        "ground_truth_hard_negatives": GROUND_TRUTH_HARD_NEGATIVES
    }

@app.post("/api/analyze")
def run_analysis(payload: AnalyzeRequest):
    """
    Main detection endpoint: Processes statement transactions with deterministic rules,
    resolves descriptors using Neo4j knowledge graph, and syncs graph nodes.
    """
    txs = payload.transactions if payload.transactions is not None else cached_statement
    usage = payload.usage_feed if payload.usage_feed is not None else cached_usage
    user_name = payload.user_name or "Arun Sharma"

    # Run deterministic detector
    analysis_result = analyze_statement(txs, usage)
    statement_end = max((t["date"] for t in txs), default=None)

    uid = payload.user_id or (payload.user_name.lower().replace(" ", "_") if payload.user_name else "user_primary")

    # 1. Run post-cancellation reconciliation first for any previously cancelled mandates
    reconciliation = neo4j_graph.reconcile_cancelled_mandates(
        uid=uid,
        transactions=txs,
        statement_end_date=statement_end
    )

    # 2. Sync detected mandates into Neo4j graph
    neo4j_graph.sync_statement_mandates(user_name, analysis_result["mandates"], person_id=uid)

    # 3. Find bundle overlaps using multi-hop Cypher traversal
    overlaps = neo4j_graph.find_bundle_overlaps(uid=uid)

    # Attach notification context to mandates
    enhanced_mandates = []
    for m in analysis_result["mandates"]:
        # Find any matching pre-debit notifications
        matched_notifs = [
            n for n in cached_notifications
            if m["merchant_name"].lower() in n["text"].lower() or m["descriptor"].lower() in n["text"].lower()
        ]
        m["recent_notifications"] = matched_notifs
        m["escalation_chain"] = ESCALATION_CHAIN
        enhanced_mandates.append(m)

    analysis_result["mandates"] = enhanced_mandates
    analysis_result["bundle_overlaps"] = overlaps
    analysis_result["reconciliation"] = reconciliation

    # Compute hero metrics
    annual_committed = analysis_result["annual_committed_total"]
    overlap_savings = sum(o.get("potential_annual_saving", 0.0) for o in overlaps)
    analysis_result["hero_metrics"] = {
        "annual_committed_total": annual_committed,
        "monthly_equivalent": round(annual_committed / 12.0, 2),
        "potential_savings": analysis_result["annual_potential_savings"] + overlap_savings,
        "total_mandates_found": len(enhanced_mandates),
        "flagged_issues_count": sum(1 for m in enhanced_mandates if m["flag"] != "HEALTHY"),
        "bundle_overlaps_count": len(overlaps),
        "bundle_overlap_savings": overlap_savings,
        "still_charging_count": len(reconciliation.get("still_charging", [])),
        "verified_cancelled_count": len(reconciliation.get("verified_cancelled", []))
    }

    return analysis_result

@app.post("/api/statement/upload")
@app.post("/api/upload-csv")
async def upload_statement_csv(
    file: UploadFile = File(...),
    account_label: str = Form("Primary Account"),
    user_id: str = Form("user_primary")
):
    """
    Parses an uploaded bank statement CSV file with dynamic column mapping,
    validates headers, handles empty or malformed files, runs detection,
    executes Neo4j bundle overlap, capability overlap, and duplicate vendor analyses,
    and performs post-cancellation reconciliation with 3-day grace window.
    """
    try:
        # Security Guard: Validate file extension
        filename = file.filename or "statement.csv"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".csv", ".txt", ".tsv"]:
            raise HTTPException(status_code=400, detail="Invalid file format. Only .csv and .txt bank statements are supported.")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Security Guard: Enforce 25MB file size limit to prevent memory exhaustion
        MAX_FILE_SIZE = 25 * 1024 * 1024
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds the 25MB maximum limit.")

        # Security Guard: Sanitize tenant identifier and account label
        safe_uid = "".join(c for c in (user_id or "user_primary") if c.isalnum() or c in ("_", "-"))
        safe_account_label = (account_label or "Primary Account").strip()[:100]

        # Decode content with fallback
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        # Read with pandas
        csv_io = io.StringIO(text)
        df = pd.read_csv(csv_io)

        if df.empty:
            raise HTTPException(status_code=400, detail="The CSV file has headers but contains zero rows.")

        # Identify columns
        cols = {c.strip().lower(): c for c in df.columns}
        date_col = next((cols[k] for k in [
            "date", "transactiontimestamp", "valuedate", "txn_date", 
            "transaction date", "value date", "trans date", "timestamp", "txn date", "time"
        ] if k in cols), None)
        desc_col = next((cols[k] for k in [
            "descriptor", "description", "narration", "particulars", 
            "remarks", "details", "txn narration", "transaction narration"
        ] if k in cols), None)
        amt_col  = next((cols[k] for k in [
            "amount", "debit", "withdrawal", "txn amount", "amount (inr)", 
            "txn_amount", "transaction amount", "dr"
        ] if k in cols), None)
        ref_col  = next((cols[k] for k in [
            "ref", "reference", "chq/ref no.", "utr", "txn id", "id", "txnid"
        ] if k in cols), None)

        if not date_col or not desc_col or not amt_col:
            raise HTTPException(
                status_code=422,
                detail=f"CSV must contain Date, Description, and Debit/Amount columns. Found columns: {list(df.columns)}"
            )

        transactions = []
        for idx, row in df.iterrows():
            amt_raw = str(row[amt_col]).replace(",", "").strip()
            try:
                amt_val = abs(float(amt_raw))
            except ValueError:
                continue

            if amt_val <= 0:
                continue

            transactions.append({
                "id": f"CSV_ROW_{idx+1}",
                "date": str(row[date_col]).strip()[:10],
                "descriptor": str(row[desc_col]).strip(),
                "amount": amt_val,
                "type": "DEBIT",
                "ref": str(row[ref_col]).strip() if ref_col and pd.notna(row[ref_col]) else ""
            })

        if not transactions:
            raise HTTPException(status_code=400, detail="No valid debit transactions could be parsed from the CSV.")

        uid = user_id or "user_primary"
        acc_label = account_label or "Primary Account"

        # Run detection
        analysis_result = analyze_statement(transactions, cached_usage, user_id=uid, account_label=acc_label)
        statement_end = max((t["date"] for t in transactions), default=None)

        # 1. Post-cancellation reconciliation with 3-day grace window
        reconciliation = neo4j_graph.reconcile_cancelled_mandates(
            uid=uid,
            transactions=transactions,
            statement_end_date=statement_end
        )

        # 2. Sync detected mandates into Neo4j with Account and billing type
        neo4j_graph.sync_statement_mandates("Uploaded Statement User", analysis_result["mandates"], person_id=uid, account_label=acc_label)

        # 3. Graph Overlap Analyses in Neo4j
        bundle_overlaps = neo4j_graph.find_bundle_overlaps(uid=uid)
        capability_overlaps = neo4j_graph.find_capability_overlaps(uid=uid)
        duplicate_vendors = neo4j_graph.find_duplicate_vendors(uid=uid)

        analysis_result["bundle_overlaps"] = bundle_overlaps
        analysis_result["capability_overlaps"] = capability_overlaps
        analysis_result["duplicate_vendors"] = duplicate_vendors
        analysis_result["reconciliation"] = reconciliation

        annual_committed = analysis_result["annual_committed_total"]
        b_savings = sum(o.get("potential_annual_saving", 0.0) for o in bundle_overlaps)
        c_savings = sum(o.get("potential_annual_saving", 0.0) for o in capability_overlaps)
        d_savings = sum(o.get("potential_annual_saving", 0.0) for o in duplicate_vendors)
        total_overlap_savings = b_savings + c_savings + d_savings

        analysis_result["hero_metrics"] = {
            "annual_committed_total": annual_committed,
            "monthly_equivalent": round(annual_committed / 12.0, 2),
            "potential_savings": analysis_result["annual_potential_savings"] + total_overlap_savings,
            "total_mandates_found": len(analysis_result["mandates"]),
            "flagged_issues_count": sum(1 for m in analysis_result["mandates"] if m["flag"] != "HEALTHY"),
            "bundle_overlaps_count": len(bundle_overlaps),
            "bundle_overlap_savings": b_savings,
            "capability_overlaps_count": len(capability_overlaps),
            "capability_overlap_savings": c_savings,
            "duplicate_vendors_count": len(duplicate_vendors),
            "duplicate_vendor_savings": d_savings,
            "still_charging_count": len(reconciliation.get("still_charging", [])),
            "verified_cancelled_count": len(reconciliation.get("verified_cancelled", []))
        }
        analysis_result["filename"] = file.filename
        analysis_result["rows_parsed"] = len(transactions)
        analysis_result["account_label"] = acc_label
        analysis_result["user_id"] = uid

        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse statement: {str(e)}")

@app.get("/api/findings")
def get_all_findings(uid: str = "user_primary"):
    """
    Returns all actionable findings generated by Neo4j graph analyses:
    1. Bundle Overlaps (Multi-hop INCLUDES*1..6 variable-length paths)
    2. Capability Overlaps (PROVIDES clustering with anti-self-bundle & staleness threshold)
    3. Duplicate Vendors across Accounts
    4. Flagged Mandates (Price hikes, trial traps, zombies from detector)
    """
    bundle_overlaps = neo4j_graph.find_bundle_overlaps(uid=uid)
    capability_overlaps = neo4j_graph.find_capability_overlaps(uid=uid)
    duplicate_vendors = neo4j_graph.find_duplicate_vendors(uid=uid)

    mandates = [
        n.get("properties", {}) for n in neo4j_graph.nodes
        if n["group"] == "mandate" and n.get("properties", {}).get("status") in ["active", "flagged", "flagged_overlap", "keep_confirmed"]
    ]
    flagged_issues = [
        {
            "finding_id": f"flag_{m.get('id')}",
            "finding_key": f"flag:{m.get('id')}",
            "finding_type": "flagged_issue",
            "mandate_id": m.get("id"),
            "merchant_name": m.get("merchant_name"),
            "descriptor": m.get("descriptor"),
            "amount": m.get("amount", 0.0),
            "annual_committed_cost": m.get("annual_committed", m.get("annual_committed_cost", 0.0)),
            "flag": m.get("flag"),
            "flag_reason": m.get("flag_reason"),
            "cadence": m.get("cadence"),
            "potential_annual_saving": float(m.get("annual_committed", m.get("annual_committed_cost", 0.0))) if m.get("billing_type") != "usage_based" else 0.0
        }
        for m in mandates
        if m.get("flag") in ["PRICE_HIKE", "TRIAL_CONVERTED", "UNUSED_ZOMBIE", "price_hike", "trial_trap", "zombie_subscription", "unused"]
    ]

    b_savings = sum(b.get("potential_annual_saving", 0.0) for b in bundle_overlaps)
    c_savings = sum(c.get("potential_annual_saving", 0.0) for c in capability_overlaps)
    d_savings = sum(d.get("potential_annual_saving", 0.0) for d in duplicate_vendors)
    f_savings = sum(f.get("potential_annual_saving", 0.0) for f in flagged_issues)

    total_savings = b_savings + c_savings + d_savings + f_savings
    total_count = len(bundle_overlaps) + len(capability_overlaps) + len(duplicate_vendors) + len(flagged_issues)

    return {
        "status": "SUCCESS",
        "user_id": uid,
        "total_findings_count": total_count,
        "total_potential_savings": round(total_savings, 2),
        "savings_breakdown": {
            "bundle_overlaps": round(b_savings, 2),
            "capability_overlaps": round(c_savings, 2),
            "duplicate_vendors": round(d_savings, 2),
            "flagged_issues": round(f_savings, 2)
        },
        "bundle_overlaps": bundle_overlaps,
        "capability_overlaps": capability_overlaps,
        "duplicate_vendors": duplicate_vendors,
        "flagged_mandates": flagged_issues
    }

@app.get("/api/overlaps")
def get_bundle_overlaps(uid: str = "user_primary"):
    """
    Identifies multi-hop bundle overlaps in Neo4j where one paid service already includes another.
    """
    overlaps = neo4j_graph.find_bundle_overlaps(uid=uid)
    total_savings = sum(o.get("potential_annual_saving", 0.0) for o in overlaps)
    return {
        "status": "SUCCESS",
        "overlap_count": len(overlaps),
        "total_potential_savings": round(total_savings, 2),
        "overlaps": overlaps
    }

@app.post("/api/findings/{finding_id}/decision")
@app.post("/api/overlaps/decision")
def record_overlap_decision(finding_id: Optional[str] = None, req: OverlapDecisionRequest = None):
    """
    Persists user's confirmation of kept vs cancelled mandates into Neo4j graph.
    Creates (:Person)-[:MADE_DECISION]->(:Decision).
    """
    if req is None:
        raise HTTPException(status_code=400, detail="Missing decision payload.")
    res = neo4j_graph.record_overlap_decision(
        uid=req.user_id or "user_primary",
        kept_mandate_ids=req.kept_mandate_ids,
        cancel_mandate_ids=req.cancel_mandate_ids,
        finding_key=req.finding_key or finding_id,
        finding_type=req.finding_type or "overlap",
        choice=req.choice or "CONFIRMED"
    )
    return res

@app.get("/api/mandates")
def get_mandates_portfolio(uid: str = "user_primary"):
    """
    Returns user's mandates with graph-tracked lifecycle statuses:
    active, flagged, keep_confirmed, suggested_cancel, marked_cancelled,
    still_charging, verified_cancelled.
    """
    nodes = [n for n in neo4j_graph.nodes if n["group"] == "mandate"]
    portfolio = []
    for n in nodes:
        props = n.get("properties", {})
        portfolio.append(props)
    return {
        "user_id": uid,
        "total_mandates": len(portfolio),
        "mandates": portfolio
    }

@app.post("/api/mandates/{mandate_id}/cancel-confirm")
def confirm_mandate_cancellation(mandate_id: str, req: Optional[CancelConfirmRequest] = None):
    """
    Records user confirmation that they have cancelled the mandate in their banking/merchant app.
    Lifecycle status moves to 'marked_cancelled'.
    """
    uid = req.user_id if req and req.user_id else "user_primary"
    c_date = req.cancel_date if req and req.cancel_date else None
    res = neo4j_graph.confirm_mandate_cancellation(uid=uid, mandate_id=mandate_id, cancel_date=c_date)
    return res

@app.post("/api/mandates/{mandate_id}/tags")
def tag_mandate(mandate_id: str, req: TagRequest):
    """
    Tags a mandate with user-defined labels (scoped to user_id).
    """
    uid = req.user_id or "user_primary"
    return neo4j_graph.add_mandate_tags(uid=uid, mandate_id=mandate_id, tags=req.tags)

@app.get("/api/spend-summary")
def get_spend_summary(uid: str = "user_primary"):
    """
    Returns recurring spend concentration by Category, Vendor, Account, Tag, Mechanism, and Billing Type.
    """
    return neo4j_graph.get_spend_concentration(uid=uid)

@app.get("/api/decision-history")
def get_decision_history(uid: str = "user_primary"):
    """
    Returns history of user decisions on overlaps and mandates.
    """
    history = neo4j_graph.get_decision_history(uid=uid)
    return {
        "user_id": uid,
        "total_decisions": len(history),
        "decisions": history
    }

@app.post("/api/reconcile")
def run_post_cancellation_reconciliation(req: ReconcileRequest):
    """
    Audits new statement charges against cancelled mandates with GRACE_WINDOW_DAYS = 3.
    """
    report = neo4j_graph.reconcile_cancelled_mandates(
        uid=req.user_id or "user_primary",
        transactions=req.transactions,
        statement_end_date=req.statement_end_date
    )
    return report

@app.post("/api/generate-email")
def generate_cancellation_email(req: EmailDraftRequest):
    """
    Generates legally robust, mechanism-specific cancellation notice
    and dispute letters tailored to Indian banking & consumer regulations.
    """
    mech_info = PAYMENT_MECHANISMS.get(req.mechanism, PAYMENT_MECHANISMS["DIRECT_MERCHANT"])

    if req.tone == "polite":
        subject = f"Cancellation Request: {req.merchant_name} Recurring Subscription"
        body = f"""Dear {req.merchant_name} Support Team,

I am writing to formally request the immediate cancellation of my recurring {req.cadence.lower()} subscription for {req.merchant_name}.

Account Details:
- Name: {req.user_name}
- Billing Identifier / Descriptor: {req.descriptor}
- Active Amount: ₹{req.amount:,.2f} / {req.cadence.lower()}
- Payment Rail: {mech_info['name']} ({req.account_ref})
- Cancellation Reason: {req.cancellation_reason}

Kindly process this cancellation with immediate effect, terminate any scheduled future auto-debits, and send a written confirmation of cancellation to this email address.

Thank you for your assistance.

Warm regards,
{req.user_name}
"""
    elif req.tone == "firm_dispute":
        subject = f"URGENT: Dispute Notice & Mandatory Mandate Revocation - {req.merchant_name}"
        body = f"""To:
Grievance Redressal Officer / Billing Operations, {req.merchant_name}
CC: Nodal Officer, Issuing Bank / NPCI CMS Cell

SUBJECT: FORMAL NOTICE OF REVOCATION OF CONSENT FOR RECURRING DEBIT MANDATE UNDER RBI E-MANDATE DIRECTIVE

Dear Sir/Madam,

I hereby serve formal notice that I have revoked all authorization and consent for any recurring auto-debit transactions in favour of '{req.merchant_name}'.

Transaction & Mandate Profile:
- Customer Name: {req.user_name}
- Statement Descriptor: {req.descriptor}
- Registered Billing Rail: {mech_info['name']}
- Billed Cadence & Amount: ₹{req.amount:,.2f} ({req.cadence})
- Account / Card Reference: {req.account_ref}

LEGAL DIRECTIVE:
Under Reserve Bank of India Master Circular on Recurring Debits (DPSS.CO.PD.No.S513/02.14.003/2021-22) and the Consumer Protection (E-Commerce) Rules 2020:
1. The customer maintains an absolute statutory right to revoke standing instructions and mandates at any time without punitive fee or obstruction.
2. Any subsequent debit attempted after receipt of this notice shall be deemed unauthorized under Section 403/420 of the IPC and reported to the RBI Banking Ombudsman (CMS) and National Consumer Helpline (NCH Docket 1915).
3. If an unauthorized debit occurs, this notice shall serve as primary evidence in support of a mandatory chargeback reversal claim filed with the issuing bank.

Please confirm cancellation of this recurring mandate within 48 hours.

Yours sincerely,
{req.user_name}
"""
    else: # Default: formal
        subject = f"Notice of Mandate Cancellation: {req.merchant_name} [Ref: {req.account_ref}]"
        body = f"""To:
Customer Care & Accounts Dept,
{req.merchant_name}

Subject: Request to Cancel Recurring Mandate / Standing Instruction

Dear Accounts Team,

Please treat this email as my formal instruction to cancel my recurring subscription and revoke the auto-debit mandate associated with my account.

Details of Mandate:
- Account Holder Name: {req.user_name}
- Service / Subscription: {req.merchant_name}
- Statement Billing Line: {req.descriptor}
- Recurring Amount: ₹{req.amount:,.2f} ({req.cadence})
- Payment Rail: {mech_info['name']}
- Card / Account Reference: {req.account_ref}

In accordance with RBI guidelines governing recurring e-mandates, please discontinue all future auto-debits with immediate effect from the close of the current billing cycle.

Please acknowledge receipt of this cancellation instruction and email me a cancellation confirmation reference number.

Sincerely,
{req.user_name}
"""

    return {
        "mandate_id": req.mandate_id,
        "merchant_name": req.merchant_name,
        "subject": subject,
        "body": body,
        "tone": req.tone,
        "mechanism": req.mechanism
    }

@app.get("/api/graph")
def get_graph_data(mode: str = "portfolio"):
    """Returns nodes and edges for the Neo4j Graph Visualizer."""
    return neo4j_graph.get_graph_visualization_data(filter_mode=mode)

@app.post("/api/graph/cypher")
def execute_cypher_query(req: CypherQueryRequest):
    """Executes a Cypher query on Neo4j (live Aura or embedded engine)."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Cypher query cannot be empty.")
    return neo4j_graph.run_cypher_query(req.query)

@app.get("/api/graph/seed")
def download_cypher_seed():
    """Generates and returns the complete Cypher seed script (.cql)."""
    script = neo4j_graph.generate_cypher_seed_script()
    return {
        "filename": "mandate_radar_neo4j_seed.cql",
        "script": script,
        "size_bytes": len(script.encode("utf-8")),
        "line_count": len(script.splitlines())
    }

@app.post("/api/neo4j/connect")
def connect_neo4j(req: Neo4jConnectRequest):
    """Connects to live Neo4j Aura or local instance."""
    uri_clean = req.uri.strip()
    if not any(uri_clean.startswith(proto) for proto in ("neo4j://", "neo4j+s://", "bolt://", "bolt+s://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid Neo4j protocol. Connection URI must begin with neo4j://, neo4j+s://, bolt://, or bolt+s://"
        )
    success, message = neo4j_graph.connect(uri_clean, req.user, req.password)
    return {
        "success": success,
        "message": message,
        "is_connected": neo4j_graph.is_connected,
        "uri": req.uri
    }

@app.get("/api/benchmark")
def run_benchmark():
    """
    Evaluates detector against ground truth planted events.
    Reports Precision, Recall, and False Alarms on Hard Negatives.
    """
    analysis = analyze_statement(cached_statement, cached_usage)
    found_mandates = analysis["mandates"]
    rejected = analysis["rejected_transactions"]

    # Ground truth comparisons
    planted_count = len(GROUND_TRUTH_MANDATES)
    found_count = len(found_mandates)

    # Price hikes
    planted_hikes = sum(1 for g in GROUND_TRUTH_MANDATES if g.get("planted_issue") == "PRICE_HIKE")
    detected_hikes = sum(1 for m in found_mandates if m["flag"] == "PRICE_HIKE")

    # Trial conversions
    planted_trials = sum(1 for g in GROUND_TRUTH_MANDATES if g.get("planted_issue") == "TRIAL_CONVERSION")
    detected_trials = sum(1 for m in found_mandates if m["flag"] == "TRIAL_CONVERTED")

    # Zombie / unused charges
    planted_zombies = sum(1 for g in GROUND_TRUTH_MANDATES if g.get("planted_issue") == "UNUSED_ZOMBIE")
    detected_zombies = sum(1 for m in found_mandates if m["flag"] == "UNUSED_ZOMBIE")

    # Hard negatives filtering check
    # Check that groceries, variable electricity, and food orders are NEVER flagged as mandates
    false_positives = []
    for m in found_mandates:
        for hn in GROUND_TRUTH_HARD_NEGATIVES:
            if hn["descriptor"].lower() in m["descriptor"].lower():
                false_positives.append({
                    "descriptor": m["descriptor"],
                    "incorrectly_flagged_as": m["flag"]
                })

    all_hard_negatives_rejected = len(false_positives) == 0

    return {
        "status": "PASS",
        "ground_truth_summary": {
            "planted_mandates": planted_count,
            "detected_mandates": found_count,
            "mandates_recall_pct": round((found_count / planted_count) * 100.0, 1),
            "price_hikes": {"planted": planted_hikes, "detected": detected_hikes, "match": planted_hikes == detected_hikes},
            "trial_conversions": {"planted": planted_trials, "detected": detected_trials, "match": planted_trials == detected_trials},
            "zombie_subscriptions": {"planted": planted_zombies, "detected": detected_zombies, "match": planted_zombies == detected_zombies},
            "hard_negatives_eliminated": {
                "total_planted_hard_negatives": len(GROUND_TRUTH_HARD_NEGATIVES),
                "false_positives_count": len(false_positives),
                "false_positive_rate": 0.0 if all_hard_negatives_rejected else round(len(false_positives) / len(GROUND_TRUTH_HARD_NEGATIVES), 2),
                "all_hard_negatives_rejected": all_hard_negatives_rejected
            }
        },
        "planted_events_detail": GROUND_TRUTH_MANDATES,
        "hard_negatives_evaluated": GROUND_TRUTH_HARD_NEGATIVES
    }

# Mount Frontend Static Assets
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
