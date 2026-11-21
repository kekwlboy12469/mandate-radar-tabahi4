# Comprehensive Technical Audit of Existing Mandate Radar Codebase

**Date of Audit:** November 2026  
**Auditor:** Principal Software Architect, Senior Fintech Engineer & Reverse Engineering Specialist  
**Target Repository:** Mandate Radar (`mandate-radar-tabahi4-main`)  
**Scope:** Root Configuration, Backend, API, Frontend, Database, Knowledge Graph, Detection Logic, Security & External Integrations  

---

## Executive Summary

Mandate Radar is currently a functional, single-tier, in-memory proof-of-concept (PoC) / hackathon prototype built using **FastAPI (Python 3.10+)** and **React 19 (TypeScript, Vite, Tailwind CSS v4)**. 

The application demonstrates strong domain modeling in its **hand-curated merchant knowledge base (76 Indian & international merchants)** and a **clean deterministic rule engine** that successfully flags price hikes, trial conversion traps, and dormant (zombie) subscriptions on synthetic datasets. It also includes an embedded graph visualizer that projects relationships between descriptors, merchants, parent companies, payment mechanisms, and cancellation paths.

However, from an enterprise fintech and production architecture standpoint, **the current codebase lacks core persistence, authentication, real-world data ingestion pipelines, and multi-tenant capabilities**:
- **Zero Relational Database (PostgreSQL):** There is no database configured, no ORM (no SQLAlchemy/SQLModel), no migration framework (no Alembic), and no persistent state. All transactions and user portfolios reside in ephemeral in-memory Python structures.
- **Neo4j Integration is Hybrid/Fallback:** While a client exists for connecting to live Neo4j Aura instances, the system primarily operates on an in-memory graph dictionary emulator.
- **Data Ingestion is Restricted to CSV Upload:** There is no bank statement PDF parser, no OCR engine, no Gmail OAuth integration, and no Android SMS listener.
- **Zero Real Mandate Verification:** Mandates are inferred from transaction recurrence; there is no integration with NPCI UPI AutoPay APIs, E-NACH/e-Mandate registers, or banking aggregators to verify Unique Mandate Numbers (UMN) or UMRNs.
- **Zero AI / LLM Implementation:** Despite architectural references to LLMs, no LLM provider SDKs (OpenAI, Anthropic, or Google Gemini) or prompt pipelines are implemented in the code.

Below is the exhaustive audit of every module, component, function, and file in the existing repository.

---

## 1. Project Structure and Dependency Analysis

### 1.1 Directory Layout
```text
mandate-radar-tabahi4-main/
├── .gitignore
├── LICENSE (MIT)
├── README.md (Comprehensive documentation of concept, benchmark, and Neo4j graph)
├── requirements.txt (Root Python dependencies)
├── run.py (Root unified launcher script)
├── vercel.json (Vercel serverless deployment routing)
├── api/
│   ├── detector.py (Duplicate of backend/detector.py for Vercel)
│   ├── index.py (Vercel ASGI serverless handler)
│   ├── main.py (FastAPI app adapted for Vercel runtime)
│   ├── neo4j_service.py (Duplicate of backend/neo4j_service.py)
│   ├── reference_data.py (Duplicate of backend/reference_data.py)
│   ├── requirements.txt (Vercel Python dependencies)
│   └── synthetic_data.py (Duplicate of backend/synthetic_data.py)
├── backend/
│   ├── detector.py (Core deterministic detection and heuristic categorization engine)
│   ├── main.py (Local FastAPI server and static asset host)
│   ├── neo4j_service.py (Neo4j driver and embedded graph emulator)
│   ├── reference_data.py (76 merchants catalog, parent corporations, payment mechanisms)
│   ├── requirements.txt (Backend dependencies)
│   └── synthetic_data.py (Synthetic 12-month statement generator and benchmark dataset)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── dist/ (Pre-built production assets: index-CHP_12x5.js, index-WHHi9dOQ.css)
│   ├── public/ (Favicon, icons)
│   └── src/
│       ├── App.tsx (Main monolithic UI controller, modals, state management)
│       ├── main.tsx (React DOM root mount)
│       ├── style.css (Global styles and CSS custom properties)
│       ├── lib/
│       │   └── format.ts (Currency formatting, issue classification helpers)
│       └── components/
│           ├── GraphCanvas.tsx (HTML5 2D Canvas force-directed graph visualizer)
│           ├── MandateDrawer.tsx (Slide-over drawer with cancellation guidance and email notice generator)
│           └── RadarView.tsx (Tick-to-cancel savings simulator, metrics, and filterable mandate list)
└── mandate_radar_research/ (Architectural research reference reports)
```

### 1.2 Code Duplication Anomaly (`api/` vs `backend/`)
A major architectural anomaly is the exact duplication of Python files between `backend/` and `api/`.
- `api/` was created to support deployment on Vercel's Serverless Python runtime (`vercel.json` routes `/api/(.*)` to `api/index.py`).
- Files `detector.py`, `neo4j_service.py`, `reference_data.py`, and `synthetic_data.py` are bit-for-bit identical between both folders.
- `backend/main.py` (18,180 bytes) and `api/main.py` (15,944 bytes) differ only in how static files are mounted and root paths are handled.
- **Architectural Risk:** Any bug fix or reference data update applied to `backend/` must be manually copied to `api/`, leading to drift and maintenance overhead.

### 1.3 Dependency Audit
- **Backend Dependencies (`backend/requirements.txt`):**
  - `fastapi>=0.110.0`: Modern ASGI web framework.
  - `uvicorn>=0.28.0`: High-performance ASGI server.
  - `pandas>=2.2.0`: Used for tabular grouping, date shifting, and interval statistics.
  - `pydantic>=2.6.0`: Data validation and request schemas.
  - `neo4j>=5.18.0`: Official Neo4j Python Bolt driver.
  - `python-multipart>=0.0.9`: Required for CSV multipart/form-data upload.
  - *Missing from Backend:* SQLAlchemy, Alembic, psycopg2/asyncpg, pdfplumber/PyMuPDF, google-api-python-client, cryptography, redis, celery, pydantic-settings.
- **Frontend Dependencies (`frontend/package.json`):**
  - `react`: `^19.3.1` (React 19)
  - `react-dom`: `^19.3.1`
  - `tailwindcss`: `^4.3.3` (Tailwind CSS v4)
  - `@tailwindcss/vite`: `^4.3.3`
  - `clsx`: `^2.1.1`
  - `lucide-react`: `^1.61.0`
  - *Missing from Frontend:* TanStack React Query (all fetching uses raw `useEffect`/`fetch`), React Router (tabs are managed via local `useState`), Form handling library (Formik/React Hook Form), Charting library (all visual graphs and sparklines are custom raw SVG/Canvas implementations).

---

## 2. Detailed Frontend Audit

### 2.1 Framework & Architecture
- **Framework:** React 19 SPA bundled with Vite 8.
- **Routing:** No router library installed (`react-router` or `@tanstack/react-router` are absent). Routing between screens is managed via an in-memory active tab state (`activeTab: 'radar' | 'graph' | 'benchmark' | 'upload'`) in [App.tsx](file:///e:/mandate-radar-tabahi4-main/frontend/src/App.tsx#L89).
- **State Management:** Fully decentralized and prop-drilled using native React `useState` and `useEffect` hooks in `App.tsx`. There is no global state store (no Zustand, Redux, or Context API).

### 2.2 Component Breakdown and Implementation Details

#### 1. `App.tsx` (Monolithic Controller - 993 lines)
- **Role:** Handles application bootstrapping, initial API fetching, modal state toggling, and layout orchestration.
- **State Variables:**
  - `mandates`: List of `Mandate` objects fetched from `/api/analyze`.
  - `heroMetrics`: Aggregate financial summary (annual committed, potential savings, mandate counts).
  - `cancelledIds`: Set of mandate IDs selected by the user in the savings simulator.
  - `graphData`, `cypherQuery`, `cypherResult`: States for the interactive Neo4j graph tab and Cypher console.
  - `neo4jUri`, `neo4jUser`, `neo4jPass`: Form state for live Neo4j Aura connection.
  - `emailTone`, `emailSubject`, `emailBody`: State for auto-generated cancellation notices.
  - `benchmarkData`: Evaluation results from `/api/benchmark`.
  - `uploadFile`, `uploadLoading`, `uploadError`: State for CSV bank statement upload.
- **API Communication:**
  - Uses raw browser `fetch()` inside `useEffect` and asynchronous callbacks.
  - Does not implement request caching, query retry policies, or optimistic UI updates.

#### 2. `RadarView.tsx` (Savings Simulator & Mandate Explorer - 96 lines)
- **Role:** Presents the financial overview and the "Tick-To-Cancel" savings simulator.
- **Implementation Status:** Fully implemented.
- **Key Functions:**
  - `useTween(target)`: Custom `requestAnimationFrame` tweening hook that smoothly animates financial figures as checkboxes are toggled.
  - Filter chips: Allows filtering by issue type: `All`, `Price creep`, `Trial trap`, `Unused`, `Unrecognised`.
  - Real-time savings calculation: Deducts checked mandates from total annual commitment and updates the visual commitment meter.

#### 3. `MandateDrawer.tsx` (Actionable Resolution & Legal Notice - 96 lines)
- **Role:** Slide-over modal that displays deep metadata for a selected mandate.
- **Implementation Status:** Fully implemented.
- **Key Features:**
  - `Spark({ h })`: Custom inline SVG sparkline rendering the historical charge sequence.
  - `Path({ m })`: Custom SVG diagram displaying the graph resolution path: `Descriptor -> Merchant -> Parent / Mechanism -> Cancellation Path`.
  - Step-by-step cancellation instructions specific to the payment rail.
  - Dynamic legal revocation letter generator with 3 tones (`polite`, `formal`, `firm_dispute`), citing the RBI Master Circular on Recurring Debits (DPSS.CO.PD.No.S513/02.14.003/2021-22) and Consumer Protection E-Commerce Rules 2020.
  - 4-Tier escalation pathway with SLA indicators.

#### 4. `GraphCanvas.tsx` (HTML5 Canvas Graph Visualizer - 534 lines)
- **Role:** Renders an interactive 2D graph of nodes and edges without requiring external heavy graph libraries.
- **Implementation Status:** Fully implemented.
- **Key Features:**
  - Concentric orbital layout: Nodes are positioned in orbital bands around a central `Person` node: Inner Ring = `Mandates`, Middle Ring = `Merchants`, Outer Ring = `Parents` and `Mechanisms`.
  - Custom physics simulation: Implements velocity decay, spring forces on edges, and node repulsion.
  - Interactive controls: Pan, zoom, drag node, hover tooltips, and click-to-select.
  - Filter modes: `Portfolio` (user-specific), `Reference` (full catalog), `Corporations` (parent companies).

### 2.3 Frontend Limitations & Gaps
- **Lack of Pagination / Virtualization:** Renders all mandates and graph nodes in single DOM/Canvas passes; will degrade if processing thousands of transactions.
- **No Responsive Mobile Navigation:** While Tailwind classes provide basic responsiveness, the drawer, canvas, and data tables are desktop-optimized.
- **No User Session Handling:** The user name is hardcoded as `"Arun Sharma"` with no login, logout, or account switching UI.

---

## 3. Detailed Backend Audit

### 3.1 Framework & Architecture
- **Language:** Python 3.10+
- **Framework:** FastAPI (`fastapi>=0.110.0`) running on Uvicorn.
- **Application Entry Point:** `run.py` (which launches `backend/main.py:app` on `127.0.0.1:8000`).
- **Architecture Pattern:** Procedural-to-modular script layout. There is no controller/service/repository separation. All business logic is invoked directly within FastAPI route handler functions in `backend/main.py`.

### 3.2 Endpoint Inventory and Implementation Status

| Method | Route | Handler Function | Status | Implementation Details |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/info` | `get_api_info()` | Fully Implemented | Returns service metadata, track info, Neo4j status, and merchant count. |
| `GET` | `/` | `root()` | Fully Implemented | Serves `frontend/dist/index.html` or API info if dist is missing. |
| `GET` | `/api/health` | `health_check()` | Fully Implemented | Reports connection status, graph mode (`LIVE_AURA` vs `EMBEDDED`), and reference counts. |
| `GET` | `/api/statement/synthetic` | `get_synthetic_dataset()` | Fully Implemented | Returns in-memory 12-month synthetic transactions, usage telemetry, and notifications. |
| `POST` | `/api/analyze` | `run_analysis()` | Fully Implemented | Runs deterministic detection on submitted or cached transactions, syncs Neo4j, attaches notifications and escalation chain. |
| `POST` | `/api/upload-csv` | `upload_statement_csv()` | Fully Implemented | Parses CSV using pandas with flexible column alias matching, validates rows, and runs detection. |
| `POST` | `/api/generate-email` | `generate_cancellation_email()`| Fully Implemented | Returns customized legal cancellation notice text in polite, formal, or dispute tones. |
| `GET` | `/api/graph` | `get_graph_data()` | Fully Implemented | Returns nodes, edges, and graph statistics filtered by mode (`portfolio`, `reference`, `corporate`). |
| `POST` | `/api/graph/cypher` | `execute_cypher_query()` | Partially Implemented | Runs live Cypher if Neo4j is connected; otherwise interprets 3 preset Cypher queries via substring pattern matching. |
| `GET` | `/api/graph/seed` | `download_cypher_seed()` | Fully Implemented | Dynamically generates a complete `.cql` Cypher script of the reference knowledge base. |
| `POST` | `/api/neo4j/connect` | `connect_neo4j()` | Fully Implemented | Establishes connection to remote Neo4j Bolt URI and authenticates user/password. |
| `GET` | `/api/benchmark` | `run_benchmark()` | Fully Implemented | Compares detection output against planted ground-truth issues and hard negatives. |

---

## 4. Detection Engine Audit (`backend/detector.py`)

The detection engine is the analytical core of Mandate Radar. It is strictly deterministic and rules-based, relying on Pandas and standard Python libraries.

### 4.1 Merchant Descriptor Resolution
- **Function:** `resolve_merchant_from_descriptor(descriptor: str)`
- **Mechanism:** Iterates through `REFERENCE_MERCHANTS` in [reference_data.py](file:///e:/mandate-radar-tabahi4-main/backend/reference_data.py#L7) and tests compiled regular expressions against the raw descriptor string.
- **Behavior:** Returns the merchant dictionary if a regex matches; otherwise returns `None`. It does not guess or assign fuzzy names to unknown strings.
- **Limitation:** Inverted linear scan $O(M \times P)$ where $M$ is the number of merchants (76) and $P$ is the number of patterns per merchant (2–8). While fast for 76 merchants, it will not scale to thousands of merchants without an indexed Trie or Aho-Corasick automaton.

### 4.2 Payment Rail Identification
- **Function:** `detect_payment_mechanism(descriptor: str, ref_str: str = "")`
- **Mechanism:** Inspects upper-cased text for keyword signatures:
  - `UPI_AUTOPAY`: Matches `"UPI"`, `"AUTOPAY"`, `"VPA"`.
  - `BANK_NACH`: Matches `"NACH"`, `"ACH D"`, `"ECS"`.
  - `PLAY_STORE`: Matches `"G.CO/HELPPAY"`, `"PLAY PASS"`, `"GOOGLE*PLAY"`.
  - `APP_STORE`: Matches `"APPLE.COM/BILL"`, `"ITUNES"`.
  - `CARD_SI`: Matches `"CARD-SI"`, `"POS DEBIT"`, `"MSBILL.INFO"`, `"STRIPE"`.
  - `DIRECT_MERCHANT`: Fallback if no keywords match.
- **Limitation:** Relies strictly on string heuristics. Does not validate whether a transaction was truly executed under an active mandate or was an ad-hoc one-time UPI payment.

### 4.3 Cadence Inference & Tolerance Bands
- **Logic:** Sorts transaction dates, calculates day differentials using `(date_series - date_series.shift(1)).dt.days`, and computes the median gap:
  - **Weekly Rejection (Hard Negative):** `median_gap < 14` days is rejected as non-subscription grocery/food ordering.
  - **Monthly:** $24 \le \text{median gap} \le 36$ days (multiplier = 12.0).
  - **Quarterly:** $80 \le \text{median gap} \le 100$ days (multiplier = 4.0).
  - **Annual:** $350 \le \text{median gap} \le 380$ days (multiplier = 1.0).
  - **Irregular:** Any interval outside these bands is rejected.
- **Limitation:** Does not support Bi-weekly, Bi-monthly, or Semi-annual cadences. A subscription with a missed payment (e.g. gap of 60 days between monthly charges) will fail the median check or trigger an irregular rejection.

### 4.4 Anomaly Detection Flags
1. **Trial Conversion Trap (`TRIAL_CONVERTED`):**
   - Condition: Initial charge $\le ₹5.00$, at least 2 charges in history, and latest charge $\ge (\text{initial charge} \times 10.0)$.
   - Verified on Spotify: ₹2 trial charge jumping to ₹119/month.
2. **Silent Price Hike (`PRICE_HIKE`):**
   - Condition: Scans consecutive differences. If exactly one step increase occurs where percentage increase $> 3.0\%$, flags as price hike and calculates annual leakage `(new - old) * multiplier`.
   - Verified on YouTube Premium: ₹129 jumping to ₹149 (+15.5%).
3. **Zombie / Dormant Subscription (`UNUSED_ZOMBIE`):**
   - Condition: Evaluates against `usage_feed`. If `days_inactive >= 75` and at least 2 cleared recurring debits occurred after the last activity date, flags as zombie.
   - Verified on Cult.fit (96 days inactive) and Truecaller (84 days inactive).
4. **Hard Negative Filtering:**
   - Evaluates against `HARD_NEGATIVE_PATTERNS`. If a group has fluctuating amounts ($> 2$ swings $> 3\%$) and matches utility patterns, it is rejected as a metered variable bill.

---

## 5. Knowledge Graph & Neo4j Integration Audit (`backend/neo4j_service.py`)

### 5.1 Graph Schema in Existing Implementation
The existing implementation models five primary node labels and five relationship types:

```text
Nodes:
- (:Person {id, name, account_type})
- (:Mandate {id, cadence, amount, annual_committed, flag, flag_reason, descriptor})
- (:Merchant {id, name, category, website, default_amount, pitfall})
- (:Parent {id, name, ...})
- (:Mechanism {id, name, ...})
- (:Descriptor {id, name, pattern})
- (:EscalationStep {id, name, tier, ...})

Relationships:
- (:Person)-[:HAS_MANDATE]->(:Mandate)
- (:Mandate)-[:FOR]->(:Merchant)
- (:Mandate)-[:VIA_MECHANISM]->(:Mechanism)
- (:Merchant)-[:OWNED_BY]->(:Parent)
- (:Merchant)-[:BILLED_VIA]->(:Mechanism)
- (:Descriptor)-[:RESOLVES_TO]->(:Merchant)
```

### 5.2 Embedded Graph Fallback vs. Live Neo4j Aura
- **Embedded Mode:** When no Neo4j URI/credentials are configured, `Neo4jKnowledgeGraph` constructs an in-memory dictionary representation (`self.nodes` and `self.edges`).
  - Graph filtering for the visualizer is performed by iterating Python lists.
  - Cypher query execution is mocked: `run_cypher_query()` inspects query strings for keywords (`"OWNED_BY"`, `"MECHANISM"`, `"FLAG"`) and returns pre-computed Python dictionary projections.
- **Live Aura Mode:** When a valid Bolt URI is supplied, `neo4j.GraphDatabase.driver` is initialized. Cypher queries are executed against the live database via `session.run(cypher)`.
- **Synchronization Method:** `sync_statement_mandates()` in [neo4j_service.py](file:///e:/mandate-radar-tabahi4-main/backend/neo4j_service.py#L168) purges previous Person and Mandate nodes and re-creates them in memory. In live Aura mode, this is not yet backed by transaction-safe parameterized Cypher writes during file upload.

---

## 6. External Integrations Audit

| Integration Channel | Status | Existing Code Evidence | Missing Capabilities |
| :--- | :--- | :--- | :--- |
| **Bank Statement CSV** | Fully Implemented | Handled in `backend/main.py:upload_statement_csv()`. Dynamic column mapping for date, description, amount, ref. | Does not support multi-currency or balance reconciliation. |
| **Bank Statement PDF** | **Not Implemented** | Zero files or references to PDF parsing libraries. | No PDF table extraction, no password decryption, no OCR for scanned statements. |
| **Gmail OAuth / API** | **Not Implemented** | Conceptual mentions in research reports only. | No Google OAuth client, no token storage, no Gmail message fetching or MIME parsing. |
| **Android SMS Ingestion** | **Not Implemented** | Synthetic pre-debit notifications simulated in `synthetic_data.py`. | No SMS permission handling, no Android receiver, no SMS sender whitelisting or parser. |
| **UPI AutoPay APIs** | **Not Implemented** | Pure string keyword heuristics in `detector.py`. | No integration with NPCI Setu / Account Aggregator (AA) APIs to fetch live mandate status. |
| **NACH Clearing System**| **Not Implemented** | Keyword heuristics only. | No integration with NPCI NACH clearing registries or bank statement mandate codes. |
| **AI / LLM Services** | **Not Implemented** | Research documents propose two-tier LLM architecture. | No OpenAI, Anthropic, or Google Gemini API clients, no prompt templates, no LLM fallbacks. |

---

## 7. Feature Classification Matrix

Following Part 3 of the audit instructions, every feature mentioned in the project context is formally classified below:

| Feature | Classification | Source File / Implementation Evidence | Limitations & Missing Functionality |
| :--- | :--- | :--- | :--- |
| **1. Recurring Payment Detection** | **Partially Implemented** | `backend/detector.py:analyze_statement()` | Deterministic interval inference works for synthetic data; fails on missed payments, bi-weekly schedules, or noisy transaction data. |
| **2. Forgotten / Zombie Subscription Detection** | **Prototype** | `backend/detector.py:238-255` | Relies on a hardcoded mock `usage_feed` dictionary. No real-world usage telemetry or API connectors exist. |
| **3. UPI AutoPay Mandate Tracking** | **Prototype** | `backend/detector.py:detect_payment_mechanism()` | Inferred purely from "UPI" or "AUTOPAY" string presence. Does not track UMN, execution limits, or mandate lifecycle. |
| **4. NACH Mandate Tracking** | **Prototype** | `backend/detector.py:detect_payment_mechanism()` | Inferred purely from "NACH" or "ECS" text. Does not extract UMRN or track issuing/sponsor banks. |
| **5. Bank Statement Extraction** | **Partially Implemented** | `backend/main.py:upload_statement_csv()` | CSV parsing is functional. PDF parsing (the standard banking format) is completely missing. |
| **6. Gmail Financial Extraction** | **Not Implemented** | None in codebase. | No OAuth flow, no API integration, no email extraction. |
| **7. Authorized SMS Alert Processing** | **Prototype** | `backend/synthetic_data.py:generate_notification_stream()` | In-memory mock notification stream used for display. No SMS ingestion engine exists. |
| **8. Automatic Merchant Identification** | **Partially Implemented** | `backend/detector.py:resolve_merchant_from_descriptor()` | 76 curated merchants with regexes in `reference_data.py`. Fails on uncataloged merchants (flags them as Unrecognised). |
| **9. Unusual Recurring Charge Detection** | **Fully Implemented** | `backend/detector.py:198-237` (Price Hike & Trial Trap) | Reliably detects step increases >3% and trial jumps $\ge 10\times$ on recurring series. |
| **10. Upcoming Payment Prediction** | **Prototype** | Multiplies latest amount by fixed multiplier (12x, 4x, 1x). | No calendar scheduling, no forecasting of exact future debit dates, no ARIMA/time-series modeling. |
| **11. Subscription Price Increase Detection** | **Fully Implemented** | `backend/detector.py:230-237` | Accurately identifies step increases, percentage jumps, and estimates annual financial leakage. |
| **12. Financial Insights & Savings Simulator** | **Fully Implemented** | `frontend/src/components/RadarView.tsx` | Interactive, animated savings simulator allows users to toggle unwanted commitments and view annual savings. |
| **13. Cancellation & Legal Notice Generator** | **Fully Implemented** | `backend/main.py:generate_cancellation_email()`, `MandateDrawer.tsx` | Generates 3-tone formal revocation notices citing RBI master circulars and provides 4-tier escalation guidance. |
| **14. Knowledge Graph Exploration** | **Fully Implemented** | `backend/neo4j_service.py`, `frontend/src/components/GraphCanvas.tsx` | Interactive 2D canvas visualizer with live Neo4j Aura sync capability and embedded fallback. |
| **15. Persistent Database Storage** | **Not Implemented** | No database configuration or models exist. | Everything is stored in ephemeral memory; reloads reset state. |
| **16. Multi-Tenant User Authentication** | **Not Implemented** | Hardcoded `"Arun Sharma"` string. | No user registration, login, JWT authentication, or password hashing. |
| **17. AI Financial Assistant / Natural Language Q&A**| **Not Implemented** | None in codebase. | No chat interface, no LLM query generator, no embeddings or RAG pipeline. |

---

## 8. Summary of Known Technical Limitations

1. **State Ephemerality:** Any restart of the backend server resets all transactions, uploaded CSVs, and synced graph nodes to the default synthetic dataset.
2. **Fragility of Heuristic Mechanism Classification:** Tagging an item as `UPI_AUTOPAY` based solely on `"UPI"` in the memo causes standard peer-to-peer (P2P) transfers or merchant QR payments to be misclassified if they happen to recur.
3. **No Database Transactions (ACID):** Concurrent file uploads or multi-user access would corrupt the shared in-memory lists `cached_statement` and `cached_usage`.
4. **Vercel Serverless Statelessness:** In Vercel serverless functions, module-level globals do not persist across requests, meaning `/api/analyze` and `/api/graph` operate on cold, un-synced instances.
5. **No Test Suite:** There are no automated unit or integration tests (no `pytest`, `unittest`, or `vitest` configurations). Testing is conducted purely via the `/api/benchmark` endpoint.

