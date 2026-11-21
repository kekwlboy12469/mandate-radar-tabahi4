# Architectural Comparison: Firefly III vs. Mandate Radar

**Date of Analysis:** November 2026  
**Author:** Principal Software Architect & Financial Systems Specialist  
**Reference Applications:**
- **Firefly III:** Open-source personal finance management suite (v6.x+, Laravel 13, PHP 8.5+, Eloquent ORM, MariaDB/PostgreSQL).
- **Mandate Radar:** Fintech commitment & auto-debit intelligence platform (FastAPI, React 19, Neo4j, Python 3.10+).

---

## 1. High-Level Architectural Comparison Matrix

The table below contrasts the architectural approaches between Firefly III and Mandate Radar across all 12 key engineering domains.

| Architectural Domain | Firefly III Implementation (Verified Evidence) | Mandate Radar Current State (Verified Evidence) | Relevance to Mandate Radar | Missing in Mandate Radar | Recommended Adaptation / Independent Design |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Transaction Processing** | Layered Factory/Repository pattern (`TransactionGroupFactory`, `JournalFactory`). Multi-split double-entry transactions. | Procedural script in route handler (`backend/main.py:upload_statement_csv`). Flat dictionary rows. | **High** | Layered domain boundaries; transactional integrity; balance validation. | Adopt domain Factory/Service pattern in Python; maintain ACID transaction boundaries. |
| **2. Transaction Data Models** | Three-tier ledger: `TransactionGroup` $\rightarrow$ `TransactionJournal` $\rightarrow$ twin `Transaction` (debit/credit lines with signed decimals). | Flat dictionary rows: `id`, `date`, `descriptor`, `amount`, `ref`. In-memory only. | **Medium-High** | Double-entry structure; strict decimal precision (`decimal(32,12)`); source/destination accounts. | Implement relational schema: `accounts`, `transactions`, `mandates`. Model bank account debit to merchant credit. |
| **3. Recurring Transaction Engine** | Dual abstraction: Active generator (`Recurrence` creates ledger entries via cron) vs Passive tracker (`Bill` monitors payments & alerts). | Deterministic retrospective analyzer (`detector.py`). Group by descriptor, calculate median interval (monthly, quarterly, annual). | **High** | Distinction between active generator, passive monitor, and legal mandate register; missed payment handling. | Maintain retrospective detection, but split entities: Inferred Recurring Payment vs Verified Legal Mandate (UMN/UMRN). |
| **4. Scheduling Mechanisms** | Cron daemon (`artisan firefly-iii:cron`) executing `CreateRecurringTransactions`. Supports daily, weekly, monthly, N-dom, yearly, weekend shifting. | No cron or background scheduler. Relies on synchronous on-demand HTTP invocation (`/api/analyze`). | **High** | Background scheduler; Celery/APScheduler; upcoming debit calendar; date clamping (leap year / 31st). | Introduce Celery / Redis / APScheduler for recurring background statement ingestion, sync, and pre-debit alerts. |
| **5. Rules Engine** | Complex AST search rule engine (`SearchRuleEngine`). Multi-trigger/action rules with strict/non-strict evaluation and Symfony expressions. | Hardcoded Python regexes in `reference_data.py` and procedural if/elif checks in `detector.py`. | **Medium** | Extensible user-defined rules; dynamic trigger-action execution; rule ordering and short-circuiting. | Implement Two-Tier Hybrid Engine: Tier 1 high-speed regex cache + Tier 2 LLM extraction. Allow user override rules. |
| **6. Transaction Categorization** | Many-to-many pivot tables (`category_transaction_journal`). Managed via user assignment or Rule Engine actions. | Static string lookup from `REFERENCE_MERCHANTS` (e.g. `"Entertainment & Streaming"`). Fallback to `"Uncategorized"`. | **Medium** | Dynamic categorization; user category customization; multi-level category taxonomy. | Adopt hierarchical category taxonomy (`Category` $\rightarrow$ `Subcategory`) with graph projection in Neo4j. |
| **7. Merchant Identification** | No dedicated merchant entity. Merchants are modeled as flat `accounts` of type `Expense account`. Auto-provisions new account names. | Dedicated merchant catalog of 76 verified brands with parent companies, regex patterns, cancellation steps, and pitfalls. | **High** | Scalable dynamic merchant learning; payment gateway unwrapping; alias resolution beyond 76 hardcoded items. | Expand Mandate Radar's knowledge graph in Neo4j. Decouple Gateway/Aggregator (Razorpay) from Beneficiary Brand (Zepto). |
| **8. Database Relationships** | Normalized relational schema (PostgreSQL/MySQL). Foreign keys, soft deletes, composite indexes, polymorphic tags/metadata. | Zero relational database. Entirely in-memory Python dictionaries and lists. Neo4j used for reference graph. | **Critical** | Complete PostgreSQL database; migrations; indexes; relational foreign keys. | Provision PostgreSQL 16+ for ACID ledger and user data; retain Neo4j for merchant knowledge graph. |
| **9. API Architecture** | JSON:API compliant REST API v1 (`/api/v1/...`). OAuth2 Bearer tokens, Fractal transformers, strict FormRequest validation. | Standard FastAPI REST endpoints (`/api/...`). Pydantic v2 schemas. No authentication, CORS wildcard (`*`). | **High** | Authentication; rate limiting; idempotency headers; versioning; pagination. | Harden FastAPI with JWT authentication, API versioning (`/api/v1`), pagination, and `X-Idempotency-Key` headers. |
| **10. Financial Reporting** | Comprehensive retrospective charts (income/expenses, category spend, net worth) using Chart.js. | Forward-looking "Tick-To-Cancel" savings simulator, annual committed cost meter, benchmark metrics. | **High** | Historical spend analytics; month-over-month trends; export capabilities. | Combine Firefly's historical trend reporting with Mandate Radar's forward-looking savings simulator. |
| **11. Security Mechanisms** | 2FA (TOTP), K-anonymity HaveIBeenPwned API check, Argon2id/Bcrypt hashing, multi-tenant user scoping, CSP headers. | No authentication, no user scoping, no encryption at rest, no rate limiting, plaintext memory storage. | **Critical** | Authentication, authorization, token encryption (AES-256-GCM), PII masking, audit logging. | Implement OAuth2/JWT auth, Argon2id passwords, KMS/AES-256 for external tokens, strict DPDP Act compliance. |
| **12. Frontend Architecture** | Server-Side Rendered (Blade) + Hybrid MPA bundle (AdminLTE, Bootstrap 5, Tailwind 4, Alpine.js CSP, Chart.js, FullCalendar). | Single-Page Application (React 19, TypeScript, Vite, Tailwind CSS v4, custom HTML5 Canvas graph visualizer). | **High** | Client-side routing; query caching (React Query); global state management; mobile responsive navigation. | Retain modern React 19 SPA architecture; add TanStack React Query, React Router v7, and accessible UI components. |

---

## 2. Detailed Technical Domain Comparison

### 2.1 Transaction Processing & Data Models

#### Firefly III (Verified Implementation)
- **Source Files:** `app/Factory/TransactionGroupFactory.php`, `app/Factory/TransactionJournalFactory.php`, `app/Models/Transaction.php`.
- **Architecture:** Implements pure double-entry bookkeeping. Every financial movement is represented by a `TransactionGroup` containing one or more `TransactionJournal` entries. Each journal splits into paired `Transaction` ledger lines:
  - Source Account: $-\text{Amount}$ (Debit from Asset/Liability).
  - Destination Account: $+\text{Amount}$ (Credit to Expense/Asset).
- **Precision:** Uses `decimal(32, 12)` and PHP `ext-bcmath` to prevent floating-point rounding errors.
- **Deduplication:** Computes `import_hash_v2 = SHA-256(JSON(row))` stored in `journal_meta`. If a matching hash exists for the user, it rejects the transaction as a duplicate.

#### Mandate Radar (Current Implementation)
- **Source Files:** `backend/main.py:upload_statement_csv()`, `backend/detector.py:analyze_statement()`.
- **Architecture:** Transactions exist as unpersisted dictionary records inside a Pandas DataFrame:
  ```python
  {"id": "CSV_ROW_1", "date": "2026-01-15", "descriptor": "NETFLIX", "amount": 499.0, "type": "DEBIT", "ref": "REF123"}
  ```
- **Precision:** Uses standard 64-bit IEEE-754 floating-point numbers (`float`), introducing subtle rounding risks over large transaction sets.
- **Deduplication:** No deduplication engine is implemented. If the same CSV is uploaded twice or transactions arrive via both SMS and statement, they are processed as duplicate commitments.

#### Analysis & Recommendations
- **Adopt Concept:** Mandate Radar must not abandon double-entry accounting. Tracking recurring debits requires linking a user's `Asset Account` (e.g. HDFC Bank) to a `Merchant Entity` (e.g. Netflix).
- **Independent Design:** Firefly III's exact SHA-256 hash is overly brittle for fintech aggregation. An SMS transaction (`"Debited Rs 499 from HDFC on 15-Jan"`) and a Bank Statement row (`"15/01/2026 NETFLIX MUMBAI - 499.00"`) will have different hashes. Mandate Radar must develop a **Time-Windowed Fuzzy Deduplication Engine** (Amount equality + Normalized Merchant match + $\pm 2$ day window).

---

### 2.2 Recurring Payments, Bills & Scheduling

#### Firefly III (Verified Implementation)
- **Source Files:** `app/Models/Recurrence.php`, `app/Models/Bill.php`, `app/Console/Commands/Tools/Cron.php`, `app/Support/Repositories/Recurring/CalculateRangeOccurrences.php`.
- **Architecture:** 
  1. `Recurrence`: An **active generator**. The user manually defines a schedule (daily, weekly, monthly, N-dom, yearly), and `firefly-iii:cron` generates real future transactions into the ledger.
  2. `Bill`: A **passive expectation monitor**. The user defines an expected range (e.g. min ₹199, max ₹649) and a match pattern. Imported transactions are linked to the bill, and `WarnAboutBills` dispatches alerts if an expected payment is overdue.
  3. Scheduling logic in `CalculateRangeOccurrences.php` handles edge cases such as month-end clamping (running on Feb 28th if scheduled for the 31st) and weekend adjustments (shifting to Friday or Monday).

#### Mandate Radar (Current Implementation)
- **Source Files:** `backend/detector.py:analyze_statement()`.
- **Architecture:** Implements retrospective statistical interval analysis:
  - Groups by descriptor or resolved merchant ID.
  - Computes `median_gap = np.median(gaps_days)`.
  - Maps median gap to cadence: 24–36 days $\rightarrow$ Monthly; 80–100 days $\rightarrow$ Quarterly; 350–380 days $\rightarrow$ Annual.
  - Rejects median gaps $< 14$ days as weekly variable spend (groceries).
  - No background cron, no forward scheduling, and no handling of missed payments.

#### Analysis & Recommendations
- **Adopt Concept:** Firefly III's separation of *generation* from *monitoring* is a critical insight. However, Mandate Radar users will not manually configure bills; they expect the system to discover them automatically.
- **Independent Design:** Mandate Radar must create a three-state recurring model:
  1. `Observed Recurring Pattern`: Statistically inferred from transaction history.
  2. `Active Subscription`: Inferred subscription linked to a verified merchant product.
  3. `Verified Payment Mandate`: Legally binding e-mandate registered with NPCI/Bank with an explicit mandate token (UMN/UMRN).

---

### 2.3 Rules Engine vs. Merchant Intelligence

#### Firefly III (Verified Implementation)
- **Source Files:** `app/TransactionRules/Engine/SearchRuleEngine.php`, `app/TransactionRules/Actions/*`.
- **Architecture:** An enterprise condition-action engine. Users configure `RuleGroups` and `Rules` with multiple triggers (e.g., `description_contains`, `amount_between`, `from_account_is`) and actions (e.g., `SetCategory`, `LinkToBill`, `SetDestinationAccount`). Supports strict (AND) and non-strict (OR) logic, execution ordering, and dynamic evaluation via Symfony Expression Language.
- **Limitations:** Suffers from "rule fatigue." The user must manually author dozens of regexes to catch banking descriptions. Has zero semantic understanding of corporate hierarchies or merchant aliases.

#### Mandate Radar (Current Implementation)
- **Source Files:** `backend/reference_data.py`, `backend/detector.py:resolve_merchant_from_descriptor()`.
- **Architecture:** Employs a curated domain knowledge graph rather than a user-configured rule engine:
  - 76 pre-mapped merchants with verified descriptor regexes, corporate parents (e.g. YouTube $\rightarrow$ Alphabet; Hotstar $\rightarrow$ Disney), payment rails, support contacts, and legal cancellation pitfalls.
  - Unknown descriptors are marked as `Unrecognised: <descriptor>` without guessing.

#### Analysis & Recommendations
- **Do Not Copy Firefly Rule Engine Wholesale:** Forcing fintech users to write manual regex rules is an anti-pattern.
- **Independent Design (Two-Tier Hybrid Architecture):**
  - **Tier 1:** High-speed deterministic regex cache based on Mandate Radar's `reference_data.py`.
  - **Tier 2:** LLM Semantic Extraction fallback (Google Gemini Flash) for uncataloged descriptors. When an unknown descriptor is encountered, the LLM extracts the merchant brand, category, and cadence, and automatically synthesizes a new Tier 1 regex pattern for future instant lookups.

---

### 2.4 Merchant Modeling & Database Architecture

#### Firefly III (Verified Implementation)
- **Source Files:** `database/migrations/2016_06_16_000002_create_main_tables.php`, `app/Models/Account.php`.
- **Architecture:** Merchants are **not** modeled as independent entities. Instead, Firefly III reuses the `accounts` table with an `account_type_id` representing `Expense account`.
- **Limitation:** Inability to represent complex real-world financial topologies:
  - A merchant cannot have multiple payment aggregator aliases (Razorpay, BillDesk, Cashfree).
  - A merchant cannot have corporate parent-subsidiary relationships.
  - A merchant cannot store specific cancellation URLs, grievance officers, or consumer dispute SLAs.

#### Mandate Radar (Current Implementation)
- **Source Files:** `backend/reference_data.py`, `backend/neo4j_service.py`.
- **Architecture:** Models merchants as first-class citizens in a dedicated Neo4j knowledge graph:
  - `(:Descriptor)-[:RESOLVES_TO]->(:Merchant)`
  - `(:Merchant)-[:OWNED_BY]->(:Parent)`
  - `(:Merchant)-[:BILLED_VIA]->(:Mechanism)`
  - `(:Mechanism)-[:CANCELLED_BY]->(:CancellationPath)`
  - `(:CancellationPath)-[:ESCALATES_TO]->(:EscalationStep)`

#### Analysis & Recommendations
- **Mandate Radar's Approach is Architecturally Superior:** Modeling merchants and corporate parents in a graph database solves the alias resolution and aggregator unmasking problem that Firefly III completely ignores.
- **Improvement Required:** Mandate Radar currently lacks the relational counterpart. The system must establish a PostgreSQL schema for transactional records while projecting merchant and mandate topologies into Neo4j.

---

### 2.5 Security, Authentication & Multi-Tenancy

#### Firefly III (Verified Implementation)
- **Source Files:** `config/auth.php`, `app/Services/Password/PwndVerifierV2.php`, `app/Http/Middleware/*`.
- **Architecture:** Enterprise security posture:
  - Stateful session authentication with CSRF tokens for web UI; stateless OAuth2 Bearer tokens via `laravel/passport` for API.
  - Two-Factor Authentication (TOTP / Google Authenticator) via `pragmarx/google2fa`.
  - Breached credential checking via HaveIBeenPwned K-Anonymity SHA-1 API.
  - Strict tenant isolation: Every query is scoped to `user_id`. Route binders throw 404 on cross-user ID access to prevent enumeration.

#### Mandate Radar (Current Implementation)
- **Source Files:** `backend/main.py`.
- **Architecture:** Zero security controls:
  - No authentication, authorization, or user accounts.
  - Hardcoded user identity `"Arun Sharma"` in route payloads.
  - Wildcard CORS (`allow_origins=["*"]`).
  - No encryption at rest or in transit.

#### Analysis & Recommendations
- **Critical Requirement:** Mandate Radar must implement production-grade security before handling any user financial data:
  - FastAPI OAuth2 with JWT access and refresh tokens.
  - Password hashing with Argon2id.
  - Encryption at rest (AES-256-GCM) for sensitive tokens (Gmail OAuth refresh tokens).
  - PII masking on bank account numbers and mandate reference tokens.

---

## 3. Summary of Architectural Takeaways

1. **What to Adopt from Firefly III:**
   - Double-entry accounting concepts in PostgreSQL (Asset Account debit $\rightarrow$ Merchant credit).
   - Domain Factory and Repository patterns to isolate business logic from FastAPI controllers.
   - Month-end date clamping algorithms (handling Feb 28th/29th and 30-day months).
   - Strict multi-tenant data scoping and implicit security route binders.

2. **What to Reject / Avoid from Firefly III:**
   - Flat `Expense account` modeling of merchants.
   - Brittle exact SHA-256 transaction hash deduplication.
   - Manual user rule writing for merchant categorization.
   - Heavy SSR Blade template UI architecture.

3. **What to Develop Independently for Mandate Radar:**
   - Dual-engine ingestion pipeline (Deterministic Regex + LLM Semantic Fallback).
   - Multi-source fuzzy deduplication (SMS vs Statement vs Gmail).
   - NPCI UPI AutoPay (UMN) and NACH (UMRN) mandate tracking engines.
   - Real-world Bank Statement PDF parser with balance validation.
   - Knowledge graph merchant resolution and aggregator unmasking in Neo4j.
   - Forward-looking "Tick-To-Cancel" savings simulator and automated revocation notice generator.

