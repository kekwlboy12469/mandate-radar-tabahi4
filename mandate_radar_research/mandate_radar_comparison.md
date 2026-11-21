# Phase 9: Firefly III vs. Mandate Radar Architectural Comparison & Solution Blueprint

**Target Application:** Mandate Radar  
**Reference Analysis:** Firefly III Core Engine  
**Focus:** Indian Fintech Ecosystem (UPI AutoPay, E-NACH, SMS/Statement Ingestion, LLM Intelligence)

---

## 1. High-Level Feature Comparison Matrix

| Capability | Firefly III Implementation | Mandate Radar Requirement | Complexity & Strategy |
| :--- | :--- | :--- | :--- |
| **Transaction Core** | Double-entry ledger (`TransactionGroup` -> `Journal` -> `Transaction`). | Double-entry ledger in PostgreSQL (`Account` -> `Transaction` -> `Merchant`). | **Adopt Concept:** Retain double-entry ledger in PostgreSQL for mathematical consistency. |
| **Recurrence Engine** | Manual user schedule; cron inserts future transactions. | Autonomous discovery engine; tracks external real-world mandates. | **New Algorithm:** Time-series cadence detection over past ledger events. |
| **Rule System** | Deterministic trigger-action search engine (`SearchRuleEngine`). | Hybrid: Deterministic Regex Rules (Tier 1) + LLM Intelligence (Tier 2). | **Hybrid Engine:** Fast local cache rules + LLM extraction fallback. |
| **SMS Ingestion** | **None.** Manual entry or 3rd-party CSV import. | Native parsing of financial SMS notifications (UPI, Bank Debits, AutoPay). | **New Module:** Local NLP parser + Named Entity Recognition (NER). |
| **Statement Parsing** | **None.** Requires manual CSV export/import tool. | Native PDF bank statement parser with OCR fallback for password-protected statements. | **New Module:** Tabular extraction (`pdfplumber` / `PyMuPDF`) + LLM header mapper. |
| **Gmail Integration** | **None.** | Google Workspace OAuth2 + Gmail API fetching digital invoices & mandates. | **External Integration:** Pub/Sub webhooks + MIME parser + LLM receipt extractor. |
| **UPI AutoPay Tracking**| **None.** | Complete lifecycle tracking of UMN (Unique Mandate Number) & execution windows. | **New Module:** NPCI UPI AutoPay specification engine. |
| **E-NACH Tracking** | **None.** Basic SEPA direct debit metadata only. | Tracks NACH/e-Mandate UMRN (Unique Mandate Reference Number) & sponsor banks. | **New Module:** NACH banking rails mandate tracker. |
| **Merchant Intelligence**| Generic `Expense account` name string. | Knowledge Graph in Neo4j resolving merchant aliases, parent companies, & plans. | **Neo4j Graph:** Unifies aggregators (Razorpay/BillDesk) to underlying brands. |
| **Deduplication** | Strict SHA-256 hash (`import_hash_v2`). | Multi-source fuzzy deduplication (SMS vs Statement vs Gmail vs Bank API). | **New Algorithm:** Window-based fuzzy score matcher. |
| **Payment Prediction** | Rigid repetition step calculation (`CalculateRangeOccurrences`). | Probabilistic ARIMA / LSTM / rule-based cadence forecasting. | **AI / Statistics:** Predicts expected debit dates with drift confidence intervals. |
| **Cancellation Help** | Delete local bill / recurrence template. | Actionable cancellation: NPCI revoke guides, direct portal deep-links, auto-emails. | **New Feature:** Automated customer cancellation workflow. |

---

## 2. In-Depth Solution Blueprints for Mandate Radar Core Capabilities

```mermaid
flowchart TD
    subgraph Multi-Channel Ingestion Pipeline
        SMS[1. Android SMS Stream / User Paste] --> Normalizer
        PDF[2. Bank Statement PDF Upload] --> Normalizer
        Gmail[3. Gmail OAuth Auto-Sync] --> Normalizer
        Manual[4. Manual / CSV Ingest] --> Normalizer
    end

    Normalizer[Ingestion Normalizer & Preprocessing] --> Deduplication{Fuzzy Deduplication Engine}
    
    Deduplication -->|Duplicate Found| Merge[Merge Metadata: Cross-channel Evidence]
    Deduplication -->|New Event| EngineSplit[Classification & Mandate Extraction]
    
    EngineSplit --> Tier1[Tier 1: High-Speed Regex Rules Engine]
    Tier1 -->|Match Found| Persist
    Tier1 -->|Unrecognized Pattern| Tier2[Tier 2: LLM Intelligence Engine (Gemini)]
    Tier2 --> Synthesis[Auto-Synthesize New Regex Rule for Tier 1 Cache]
    Synthesis --> Persist[Persistence Pipeline]
    
    Persist --> Postgres[(PostgreSQL: Ledger & ACID Core)]
    Persist --> Neo4j[(Neo4j: Merchant & Mandate Knowledge Graph)]
    
    Postgres & Neo4j --> Radar[Mandate Radar Core Services]
    Radar --> Anomaly[Anomaly & Price Hike Detector]
    Radar --> Predictor[Debit Cadence Predictor]
    Radar --> Cancel[Cancellation Assistant]
```

---

### 1. SMS Financial Transaction Extraction
- **Problem:** Indian bank SMS notifications arrive in hundreds of fragmented formats across banks (HDFC, SBI, ICICI, Axis) and UPI apps (PhonePe, GPay, Paytm).
- **Architecture:**
  1. **Sender Header Whitelisting:** Filter SMS by sender ID regex (`^[A-Z]{2}-[A-Z]{6}$`, e.g., `VK-HDFCBK`, `AD-ICICIB`).
  2. **Pattern Extractors (Regex Engine):** Extract Amount (`(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)`), Account Last 4 (`(?:A/c|card|acct)\s*(?:no\.?)?\s*(?:ending\s*)?(\d{4}|[xX*]+\d{4})`), Merchant string, and Reference number (UTR / UPI Ref).
  3. **AutoPay Specific Triggers:** Recognize keywords: `"mandate"`, `"autopay"`, `"auto-debited"`, `"standing instruction"`, `"scheduled debit"`.
  4. **Fallback:** If confidence < 0.85, route to Gemini Flash with structured JSON output schema.

---

### 2. Bank Statement PDF Parsing
- **Problem:** Statements are locked with passwords (DOB/PAN), contain multi-line descriptions, and span heterogeneous tabular structures.
- **Architecture:**
  1. **Password Decryption:** Try standard password patterns (e.g. User PAN + Date of Birth) supplied securely by the user.
  2. **Table Extraction:** Use `pdfplumber` / `PyMuPDF` to detect column bounding boxes (Date, Description, Chq/Ref No, Withdrawal, Deposit, Balance).
  3. **Transaction Continuation Stitching:** If a transaction description spans multiple visual lines, stitch rows before balance validation.
  4. **Mathematical Balance Proof:** Check `Opening Balance - Sum(Withdrawals) + Sum(Deposits) == Closing Balance`. Only commit to PostgreSQL if the ledger verifies.

---

### 3. Gmail Integration
- **Problem:** Invoices, digital mandate receipts (Google Play, Apple, Netflix, AWS), and pre-debit notices are emailed 24-48 hours before execution.
- **Architecture:**
  1. **OAuth2 Flow:** Use Google Workspace OAuth with restricted scopes (`gmail.readonly`).
  2. **Selective Query Filter:** Avoid reading personal emails by querying exclusively:
     ```text
     from:(billing OR payments OR no-reply OR alert) (subject:mandate OR subject:autopay OR subject:invoice OR subject:subscription)
     ```
  3. **MIME Parser:** Extract HTML/plain text and inline attachments.
  4. **LLM Extraction:** Parse sender, plan name, billing frequency, and mandate tokens.

---

### 4. UPI AutoPay Mandate Detection
- **NPCI Specification Context:** UPI AutoPay operates via a **Unique Mandate Number (UMN)** (e.g. `umn:xxx@bank` or 32-character hex). Debits above ₹15,000 require an additional factor of authentication (AFA), but recurring debits up to ₹100,000 for mutual funds/credit cards are automated.
- **Mandate Radar Implementation:**
  - Track the mandatory **Pre-Debit Notification (SMS/Email sent 24 hours prior to debit)**.
  - Match pre-debit notices to the corresponding mandate record.
  - Alert the user if the debit amount exceeds previous executions (stealth price hike).

---

### 5. NACH Mandate Tracking
- **E-NACH / e-Mandate Context:** Handled via NPCI's National Automated Clearing House using a **Unique Mandate Reference Number (UMRN)**.
- **Mandate Radar Implementation:**
  - Parse UMRN from mandate registration confirmation SMS/emails.
  - Record the `Sponsor Bank`, `Destination Bank`, `Maximum Amount Cap`, and `Frequency`.
  - Alert users when loan EMIs or gym memberships auto-renew unexpectedly.

---

### 6. Merchant Intelligence & Canonical Resolution
- **Problem:** Bank memos obscure real merchants (e.g., `PYTM*NETFLIX`, `BILLDESK*SWIGGY`, `RAZORPAY*ZEPTO`).
- **Architecture:**
  - Maintain a **Merchant Normalization Dictionary** mapping billing payment aggregators (Paytm, BillDesk, Razorpay, Cashfree, PayU) and extracting the underlying beneficiary brand.
  - Link multiple billing entities to a single Canonical Merchant node in Neo4j.

---

### 7. Multi-Source Deduplication
- **Why Firefly III's Hash Fails:** Firefly III's `import_hash_v2` is `SHA-256(JSON(row))`. If the user has both an SMS (`"Rs 199 debited on 2026-11-20"`) and a Bank Statement (`"2026-11-20 NETFLIX REF#123 199.00"`), exact SHA-256 treats them as two separate transactions, doubling the recorded expense!
- **Mandate Radar Fuzzy Window Matcher:**
  ```python
  def is_duplicate(candidate, existing_records):
      for tx in existing_records:
          if tx.account_id == candidate.account_id and abs(tx.amount - candidate.amount) < 0.01:
              date_diff = abs((tx.date - candidate.date).days)
              if date_diff <= 2:
                  similarity = string_similarity(candidate.merchant_normalized, tx.merchant_normalized)
                  if similarity > 0.80 or tx.ref_number == candidate.ref_number:
                      return True, tx
      return False, None
  ```

---

### 8. Recurring Payment Prediction & Anomaly Detection
- **Predictor:** Calculates mean interval $\mu$ and standard deviation $\sigma$ across past payments for a mandate.
- **Expected Debit Date Window:** $[\text{Last Date} + \mu - 2\sigma, \text{Last Date} + \mu + 2\sigma]$.
- **Anomaly Signals:**
  - **Cadence Anomaly:** Debit occurred outside expected window.
  - **Amount Creep:** Billed amount > historical moving average by more than 5%.
  - **Zombie Subscription:** Mandate continues auto-debiting, but zero digital activity detected for 60+ days.

---

### 9. Subscription Cancellation Assistant
- Provide a guided cancellation protocol:
  1. **Direct Link:** Deep-link to merchant's web account settings (`netflix.com/youraccount`).
  2. **UPI App Deep-Link:** Deep-link to mandate management screens in Google Pay, PhonePe, and Paytm.
  3. **Auto-Generated Revocation Email:** Formatted legal revocation under RBI's Framework for Processing of e-Mandates, addressed to merchant support and the user's bank manager.

