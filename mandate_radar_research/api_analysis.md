# Phase 6: Firefly III API Architecture Analysis

**Target Application:** Firefly III  
**Workspace Location:** `e:\firefly-iii-main`  
**Key Sources Analyzed:**
- `routes/api.php`
- `app/Api/V1/Controllers/*`
- `app/Api/V1/Requests/*`
- `app/Transformers/*`
- `app/Api/V1/Controllers/Models/TransactionController.php`, `AccountController.php`, `RecurrenceController.php`, `RuleController.php`

---

## 1. REST API Architecture Overview

Firefly III provides a mature, spec-compliant REST API v1 structured around the **JSON:API standard**.

```mermaid
flowchart LR
    Client[Third-Party Client / Mobile App / CLI] -->|Bearer Token / Personal Access Token| Gateway[Route Layer: routes/api.php]
    Gateway --> Auth[Middleware: auth:api Laravel Passport]
    Auth --> Controller[API Controllers: app/Api/V1/Controllers/Models/*]
    Controller --> RequestVal[FormRequest Validation: app/Api/V1/Requests/Models/*]
    RequestVal --> Repo[Domain Repositories]
    Repo --> Transformer[Fractal Serializer: app/Transformers/*]
    Transformer --> Response[JSON:API Standard Payload]
```

### Key Architectural Characteristics:
- **Stateless OAuth2 Authentication:** Powered by `laravel/passport`, supporting OAuth2 Authorization Code Grants and Personal Access Tokens (PAT).
- **Format Serialization:** Every resource uses `League\Fractal` transformers to format responses into standardized JSON envelopes (`data`, `attributes`, `id`, `type`, `links`).
- **Granular Request Validation:** Every HTTP method (Store, Update, Delete) maps to a dedicated `FormRequest` class in `app/Api/V1/Requests/Models/` providing strict parameter whitelisting and type casting.

---

## 2. Core API Endpoints

### A. Transactions (`/api/v1/transactions`)
- `GET /api/v1/transactions`: Lists transactions with pagination (`?page=1&limit=50`), date filtering (`?start=2026-01-01&end=2026-01-31`), and type filtering (`?type=withdrawal`).
- `POST /api/v1/transactions`: Creates a transaction group. Supports single transactions and multi-split items.
  - **Payload Structure:**
    ```json
    {
      "error_if_duplicate_hash": true,
      "apply_rules": true,
      "fire_webhooks": true,
      "group_title": "Monthly Subscriptions",
      "transactions": [
        {
          "type": "withdrawal",
          "date": "2026-11-20T10:00:00Z",
          "amount": "199.00",
          "description": "Netflix Subscription",
          "source_id": 1,
          "destination_name": "Netflix Entertainment",
          "category_name": "Streaming",
          "bill_name": "Netflix"
        }
      ]
    }
    ```
- `GET /api/v1/transactions/{id}`: Retrieves transaction group details with split arrays.
- `PUT /api/v1/transactions/{id}`: Full update of transaction group.
- `DELETE /api/v1/transactions/{id}`: Soft deletes the transaction group and restores account balances.

### B. Accounts (`/api/v1/accounts`)
- `GET /api/v1/accounts?type=asset`: Lists user bank accounts.
- `GET /api/v1/accounts?type=expense`: Lists merchants and expense entities.
- `POST /api/v1/accounts`: Creates an account (with `opening_balance`, `iban`, `account_number`, `currency_code`).
- `GET /api/v1/autocomplete/accounts`: Ultra-fast typeahead endpoint for transaction inputs.

### C. Recurring Transactions (`/api/v1/recurring`) & Bills (`/api/v1/bills`)
- `GET /api/v1/recurring`: Lists recurrence templates.
- `POST /api/v1/recurring`: Creates a recurrence schedule, specifying `repetition_type` (`daily`, `weekly`, `monthly`, etc.), `repetition_moment`, and transaction splits.
- `GET /api/v1/bills`: Lists bills with paid status in current period.
- `GET /api/v1/bills/{id}/transactions`: Lists all transactions matching this bill.

### D. Rules (`/api/v1/rules` & `/api/v1/rule-groups`)
- `GET /api/v1/rules`: Lists rules with nested triggers and actions.
- `POST /api/v1/rules`: Creates a rule.
- `POST /api/v1/rules/{id}/trigger`: Executes the rule retroactively against existing transactions.
- `POST /api/v1/rules/test`: Dry-runs a set of triggers against existing transactions to preview matches without applying mutations.

### E. Search & Insights
- `GET /api/v1/search/transactions?query={query}`: Exposes the full search query syntax via REST.
- `GET /api/v1/insight/expense/category`: Aggregated spending totals per category.
- `GET /api/v1/insight/expense/bill`: Aggregated payments per subscription/bill.

---

## 3. Webhook Subsystem

Firefly III features an enterprise webhook engine (`app/Api/V1/Controllers/Models/WebhookController.php`):
- **Triggers:** `STORE_TRANSACTION`, `UPDATE_TRANSACTION`, `DESTROY_TRANSACTION`.
- **Delivery Model:** Dispatches `WebhookAttempt` records asynchronously to configured remote endpoints with HMAC signatures.

---

## 4. Useful API Design Patterns for Mandate Radar (FastAPI)

Mandate Radar should adapt several key patterns from Firefly III's API design:

1. **Idempotency & Duplicate Hash Header:**
   - In Firefly III: `"error_if_duplicate_hash": true`.
   - In Mandate Radar: Require an `X-Idempotency-Key` or compute a transaction hash (`SHA-256(amount + merchant + timestamp_window)`). In FastAPI, implement an idempotency middleware backed by Redis or PostgreSQL.
2. **Standardized JSON Schema (Pydantic v2):**
   - Replace Fractal with native Pydantic models for fast response serialization:
     ```python
     class MandateResponse(BaseModel):
         id: UUID
         merchant: MerchantSummary
         account: AccountSummary
         mandate_type: MandateTypeEnum
         cadence: CadenceEnum
         amount_limit: Decimal
         status: MandateStatusEnum
         next_billing_date: date
     ```
3. **Dry-Run / Rule Testing Endpoint:**
   - Firefly III's `/rules/test` is invaluable. Mandate Radar should provide a `/api/v1/intelligence/test-extraction` endpoint allowing users to test SMS or PDF parsing on sample text to verify regex and LLM extractions before saving.
4. **Autocomplete Endpoints:**
   - Specialized lightweight endpoints (`/autocomplete/merchants`, `/autocomplete/accounts`) with sub-20ms latency to deliver responsive frontend search experiences.

