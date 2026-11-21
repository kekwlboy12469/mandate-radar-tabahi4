# Practical Development Roadmap: Mandate Radar 2.0

**Document Reference:** `development_roadmap.md`  
**Author:** Principal Software Architect & Technical Lead  
**Scope:** Dependency-Aware, 10-Stage Engineering Roadmap  

---

## 1. Architectural Dependency Re-Ordering Analysis

The initial high-level task list placed **PostgreSQL and Neo4j integration** at Stage 5. However, from a rigorous software engineering and database architecture perspective, **attempting to build robust deduplication, recurring detection, and mandate tracking before establishing the database schema and persistence layer is an anti-pattern**. 

Without a persistent relational database:
- Deduplication cannot query existing ledger history.
- Transactions remain in volatile process memory.
- Multi-channel ingestion cannot persist raw payloads or track processing states.

Therefore, the roadmap is logically ordered into a **dependency-sound sequence**, grouping the foundational data architecture into Stage 1, followed by extraction, intelligence, and advanced integrations.

```mermaid
flowchart TD
    S1[Stage 1: Core Database Architecture & Persistence (PostgreSQL & Neo4j Foundation)]
    S2[Stage 2: Transaction Extraction & Normalization (PDF, CSV)]
    S3[Stage 3: Fuzzy Deduplication & Merchant Identification (Neo4j Resolution)]
    S4[Stage 4: Recurring Payment & Cadence Detection]
    S5[Stage 5: Subscription Intelligence & Anomaly Detection]
    S6[Stage 6: UPI AutoPay & NACH Mandate Lifecycle Engine]
    S7[Stage 7: Multi-Channel Ingestion (Gmail & Android SMS)]
    S8[Stage 8: Financial Analytics & Forward Cashflow Predictions]
    S9[Stage 9: AI Financial Assistant (Grounded Q&A via Gemini Flash)]
    S10[Stage 10: Advanced Cancellation & Revocation Workflows]

    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9 --> S10
```

---

## 2. Stage-by-Stage Engineering Specifications

---

### STAGE 1: Core Database Architecture & Persistence Foundation
- **Objective:** Provision PostgreSQL 16+ as the ACID System of Record, configure SQLAlchemy / SQLModel ORM with Alembic migrations, establish double-entry schemas, and implement authentication.
- **Required Modules:** `app/core/db.py`, `app/models/*`, `app/services/auth.py`, `app/api/v1/auth.py`.
- **Dependencies:** PostgreSQL 16+, `asyncpg`, `sqlmodel`, `alembic`, `passlib[argon2]`, `python-jose`.
- **Files Affected:** New `backend/app/` structure, `backend/requirements.txt`, `backend/alembic/`.
- **Database Changes:** Creation of `users`, `accounts`, `merchants`, `mandates`, `transactions`, `raw_ingest_logs`, `outbox_events` tables.
- **API Changes:** New endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- **Testing Requirements:** Migrations up/down unit tests, database session rollback tests, JWT validation tests.
- **Deliverables & Completion Criteria:** Verified migration running cleanly on PostgreSQL; successful user registration and authenticated session returning a valid JWT.

---

### STAGE 2: Transaction Extraction and Normalization
- **Objective:** Build robust document parsing pipelines for password-protected bank statement PDFs and dynamic CSV statements with balance validation.
- **Required Modules:** `app/services/extractors/pdf_extractor.py`, `app/services/extractors/csv_extractor.py`, `app/services/normalizer.py`.
- **Dependencies:** `pdfplumber`, `pypdf`, `pandas`.
- **Files Affected:** `backend/app/services/extractors/`, `backend/app/api/v1/ingest.py`.
- **Database Changes:** Populate `raw_ingest_logs` with extraction metadata and execution audit.
- **API Changes:** `POST /api/v1/ingest/upload-pdf` (with optional password param), `POST /api/v1/ingest/upload-csv`.
- **Testing Requirements:** Test extraction against 10 Indian bank statement formats (HDFC, SBI, ICICI, Axis, Kotak); verify balance continuity equations ($Opening - Withdrawals + Deposits = Closing$).
- **Deliverables & Completion Criteria:** PDF upload accurately extracts 100% of line items with ISO dates, normalized debit amounts, and source account metadata.

---

### STAGE 3: Fuzzy Deduplication and Merchant Identification
- **Objective:** Eliminate multi-channel transaction duplication and resolve raw descriptors to canonical merchant entities using the Neo4j knowledge graph.
- **Required Modules:** `app/services/deduplication.py`, `app/services/merchant_resolver.py`, `app/services/neo4j_client.py`.
- **Dependencies:** `neo4j>=5.18.0`, `rapidfuzz` (fast Levenshtein similarity).
- **Files Affected:** `backend/app/services/deduplication.py`, `backend/detector.py` refactored into service.
- **Database Changes:** Neo4j: Seed complete reference knowledge base of 76 merchants and corporate parents.
- **API Changes:** `POST /api/v1/merchants/resolve`, `GET /api/v1/merchants/{id}`.
- **Testing Requirements:** Feed identical transactions with slight timestamp shifts ($\pm 24$ hours) and descriptor variations; verify zero duplicate insertions.
- **Deliverables & Completion Criteria:** Raw descriptor `POS 4921*RAZORPAY*ZEPTO BLR` resolves to merchant `Zepto`, stripping aggregator tokens with $>95\%$ accuracy.

---

### STAGE 4: Recurring Payment & Cadence Detection
- **Objective:** Analyze historical transaction intervals to infer recurring frequencies (weekly, monthly, quarterly, annual) while rejecting hard negatives.
- **Required Modules:** `app/services/cadence_detector.py`, `app/services/hard_negatives.py`.
- **Dependencies:** `numpy`, `scipy`.
- **Files Affected:** `backend/detector.py` (logic extracted and upgraded), `backend/app/services/`.
- **Database Changes:** Update `transactions.is_inferred_recurring` and populate `mandates` table with `INFERRED_RECURRING` records.
- **API Changes:** `GET /api/v1/analytics/recurring-transactions`.
- **Testing Requirements:** Benchmark against ground-truth dataset; verify weekly groceries and fluctuating electric bills are rejected with 0% false positives.
- **Deliverables & Completion Criteria:** Deterministic classification of monthly (24–36d), quarterly (80–100d), and annual (350–380d) cadences with missed-cycle resilience.

---

### STAGE 5: Subscription Intelligence & Anomaly Detection
- **Objective:** Monitor active subscriptions, calculate monthly/annual commitments, flag silent price increases, trial traps, and dormant subscriptions.
- **Required Modules:** `app/services/anomaly_engine.py`, `app/services/subscription_manager.py`.
- **Dependencies:** None (Python math and statistics).
- **Files Affected:** `backend/app/services/anomaly_engine.py`, `frontend/src/App.tsx`, `frontend/src/components/RadarView.tsx`.
- **Database Changes:** Updates to `mandates.flag` (`PRICE_HIKE`, `TRIAL_CONVERTED`, `UNUSED_ZOMBIE`) and `mandates.flag_reason`.
- **API Changes:** `GET /api/v1/subscriptions/anomalies`, `GET /api/v1/subscriptions/summary`.
- **Testing Requirements:** Planted tests for $>3\%$ price hikes and $\ge 10\times$ trial jumps.
- **Deliverables & Completion Criteria:** Immediate flagging of price creep with exact annual leakage computation; frontend animated savings simulator accurately reflects changes.

---

### STAGE 6: UPI AutoPay & NACH Mandate Tracking
- **Objective:** Establish true mandate lifecycle tracking, distinguishing verified mandates (with UMN/UMRN) from statistical recurring payments.
- **Required Modules:** `app/services/mandate_tracker.py`, `app/services/pre_debit_matcher.py`.
- **Dependencies:** Regex parsing for NPCI mandate schemas.
- **Files Affected:** `backend/app/services/mandate_tracker.py`, `frontend/src/components/MandateDrawer.tsx`.
- **Database Changes:** Store `umn_or_umrn`, `mandate_type`, `max_amount`, and lifecycle status in `mandates` table.
- **API Changes:** `GET /api/v1/mandates/verified`, `POST /api/v1/mandates/{id}/status`.
- **Testing Requirements:** Verify that ad-hoc repeating UPI transfers are categorized as `INFERRED_RECURRING`, while transactions containing UMN strings receive `VERIFIED_UPI_AUTOPAY`.
- **Deliverables & Completion Criteria:** Mandate drawer displays verified UMN/UMRN tokens, sponsor bank details, and mandate status badges.

---

### STAGE 7: Multi-Channel Ingestion (Gmail & Android SMS)
- **Objective:** Implement Google OAuth2 Gmail synchronization and an authenticated API for mobile SMS alert ingestion.
- **Required Modules:** `app/services/integrations/gmail_sync.py`, `app/services/integrations/sms_receiver.py`.
- **Dependencies:** `google-api-python-client`, `google-auth-oauthlib`, `cryptography` (Fernet / AES-256 for token storage).
- **Files Affected:** `backend/app/services/integrations/`, `backend/app/api/v1/integrations.py`.
- **Database Changes:** New `oauth_connections` table storing encrypted refresh tokens; `pre_debit_notifications` table.
- **API Changes:** `GET /api/v1/integrations/google/auth-url`, `POST /api/v1/integrations/google/callback`, `POST /api/v1/ingest/sms`.
- **Testing Requirements:** Mock Gmail API tests verifying selective querying of financial messages; SMS sender ID whitelist filtering tests.
- **Deliverables & Completion Criteria:** Seamless Google account connection; automatic extraction of digital receipts and pre-debit notices into the transaction ledger.

---

### STAGE 8: Financial Analytics & Forward Predictions
- **Objective:** Predict future debit dates, model upcoming 30-day cash flow commitments, and compute corporate spend footprint via Neo4j.
- **Required Modules:** `app/services/predictor.py`, `app/services/graph_analytics.py`.
- **Dependencies:** Neo4j Cypher queries.
- **Files Affected:** `backend/app/services/predictor.py`, `frontend/src/components/GraphCanvas.tsx`.
- **Database Changes:** Compute and store `mandates.next_expected_debit`.
- **API Changes:** `GET /api/v1/analytics/upcoming-debits`, `GET /api/v1/analytics/corporate-footprint`.
- **Testing Requirements:** Validate leap year clamping (Feb 28/29) and banking holiday weekend shifts.
- **Deliverables & Completion Criteria:** Interactive upcoming payment timeline showing exact expected debit dates and bank account balances required.

---

### STAGE 9: AI Financial Assistant (Natural Language Q&A)
- **Objective:** Enable grounded natural language financial queries using Google Gemini Flash, querying verified structured database records without hallucination.
- **Required Modules:** `app/services/ai_assistant.py`, `app/services/query_tools.py`.
- **Dependencies:** `google-genai` (official Google Gemini Python SDK).
- **Files Affected:** `backend/app/services/ai_assistant.py`, new `frontend/src/components/ChatAssistant.tsx`.
- **Database Changes:** None (reads from existing PostgreSQL and Neo4j stores).
- **API Changes:** `POST /api/v1/assistant/chat` (streaming or synchronous Q&A).
- **Testing Requirements:** Hallucination stress tests: Ask about nonexistent subscriptions and verify the assistant answers *"No matching records found"* rather than inventing data.
- **Deliverables & Completion Criteria:** Fully functioning conversational assistant answering: *"How much do I spend on subscriptions?"*, *"Which services increased prices?"*, citing underlying database records.

---

### STAGE 10: Advanced Cancellation & Revocation Workflows
- **Objective:** Deliver one-click mandate cancellation deep-links, merchant portal URLs, and customizable legal dispute notices.
- **Required Modules:** `app/services/cancellation_service.py`, `app/services/legal_notice_generator.py`.
- **Dependencies:** None.
- **Files Affected:** `backend/main.py:generate_cancellation_email()` (upgraded), `frontend/src/components/MandateDrawer.tsx`.
- **Database Changes:** Store cancellation logs in `audit_logs`.
- **API Changes:** `POST /api/v1/mandates/{id}/cancellation-notice`, `POST /api/v1/mandates/{id}/mark-cancelled`.
- **Testing Requirements:** Verify legal notice templates against current RBI circular directives and verify deep-link URI formatting.
- **Deliverables & Completion Criteria:** Instant generation of formal, PDF/email-ready revocation letters tailored to the payment rail, with 4-tier escalation paths.

