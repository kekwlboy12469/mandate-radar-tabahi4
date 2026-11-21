# Security, Privacy & Compliance Audit: Mandate Radar

**Document Reference:** `security_audit.md`  
**Author:** Principal Software Architect & Financial Cybersecurity Specialist  
**Regulatory Context:** Reserve Bank of India (RBI) e-Mandate Framework, Digital Personal Data Protection (DPDP) Act 2023, NPCI Guidelines  

---

## 1. Executive Security Assessment

The existing Mandate Radar implementation operates as a local hackathon demonstration. It **completely lacks authentication, encryption, access controls, rate limiting, and regulatory privacy compliance**.

Because Mandate Radar is designed to process **sensitive personal financial data (bank statements, SMS debit alerts, Gmail receipts, and mandate authorizations)**, transitioning to production requires establishing an enterprise-grade security posture.

---

## 2. Inviolable Security Tenets (Red Lines)

1. **Zero Credential Retention for Banking Secrets:**
   - Mandate Radar **MUST NEVER** request, ingest, process, or store net-banking passwords, debit/credit card PINs, UPI MPINs, or One-Time Passwords (OTPs).
2. **Ephemeral Statement Processing:**
   - Bank statement PDFs uploaded by users must be processed in ephemeral worker memory. Raw PDF documents must be securely shredded (`shred` / cryptographically unlinked) immediately after transaction extraction, unless the user explicitly opts in to encrypted document retention.
3. **Minimum Necessary Privilege:**
   - External integrations (Gmail, SMS) must request the narrowest possible permission scopes (e.g. `gmail.readonly` with server-side query whitelisting).
4. **Mandatory PII Masking:**
   - Full account numbers, primary account numbers (PAN), and card details must never be stored or displayed in plain text. Only last-4 digit masks (`**4821`) are permissible.

---

## 3. Threat Model and Domain Audit

### 3.1 Authentication & Authorization
- **Current State:** Non-existent. Single hardcoded user `"Arun Sharma"`. Wildcard CORS (`*`).
- **Target Implementation:**
  - **OAuth2 with JWT (JSON Web Tokens):** Short-lived access tokens (15-minute expiration) paired with rotating refresh tokens stored in HTTP-only, `SameSite=Strict`, `Secure` cookies.
  - **Password Security:** Hashes stored using **Argon2id** (memory cost: 65,536 KiB, time cost: 3 iterations, parallelism: 4).
  - **Compromised Password Auditing:** Integrated HaveIBeenPwned K-Anonymity API check during user registration to block breached passwords.
  - **Multi-Factor Authentication (MFA):** Optional Time-Based One-Time Password (TOTP via RFC 6238) for security-conscious users.
  - **Strict Multi-Tenant Scoping:** Every PostgreSQL and Neo4j query must explicitly enforce `WHERE user_id = $authenticated_user_id`.

### 3.2 Encryption at Rest and in Transit
- **In Transit:** Mandatory TLS 1.3 encryption across all client-to-API and internal service-to-service communication. Enforce HTTP Strict Transport Security (`HSTS`: `max-age=63072000; includeSubDomains; preload`).
- **At Rest:**
  - Database volumes encrypted using AES-256 via Cloud KMS.
  - **Column-Level Encryption (PostgreSQL `pgcrypto` / Application-Level AES-256-GCM):** Sensitive external tokens (Gmail OAuth refresh tokens) and mandate identifiers must be encrypted before database write using keys managed in AWS KMS / HashiCorp Vault.

### 3.3 External Integration Security

#### A. Gmail OAuth2 Integration
- **Permission Scope:** Restrict to `https://www.googleapis.com/auth/gmail.readonly`.
- **Query Whitelisting:** The application must never query or index personal correspondence. All API queries are strictly sandboxed to financial receipt patterns:
  ```text
  from:(billing OR payments OR no-reply OR alert) (subject:mandate OR subject:autopay OR subject:invoice OR subject:subscription)
  ```
- **Token Protection:** Google OAuth client secrets and user refresh tokens must never appear in application logs or frontend bundles.

#### B. Android SMS Permissions & Data Ingest
- **Consent Architecture:** Ingestion of transaction SMS requires explicit, unambiguous user consent under India's DPDP Act 2023.
- **Client-Side Filtering:** The mobile application or forwarder must filter messages locally before transmission. Only SMS from verified banking sender IDs (e.g. `^[A-Z]{2}-[A-Z]{6}$` such as `VK-HDFCBK`) are parsed. Non-banking personal SMS messages must never be transmitted to Mandate Radar servers.

### 3.4 API Security & Input Validation
- **Request Whitelisting:** Pydantic v2 schemas reject any undeclared payload fields.
- **Rate Limiting:** Sliding-window rate limiter implemented via Redis:
  - Public / Auth endpoints: Max 5 attempts per minute per IP.
  - File upload endpoints: Max 10 uploads per hour per user.
  - Standard API endpoints: Max 100 requests per minute per user.
- **Injection Defenses:**
  - SQL: Parameterized queries via SQLAlchemy / SQLModel ORM. Zero dynamic string interpolation.
  - Cypher: Parameterized Cypher executions (`session.run(query, {"user_id": uid})`). Sanitized against Cypher injection.

### 3.5 Tamper-Evident Audit Logging
- Dedicated `audit_logs` table in PostgreSQL recording all critical security and financial actions:
  - Account linking and mandate revocations.
  - CSV/PDF file uploads.
  - OAuth authorization grants and revocations.
  - Password and profile changes.
- Audit records are append-only; updates and hard deletes are disallowed via database trigger rules.

---

## 4. Regulatory & Legal Compliance Matrix (India)

| Regulatory Framework | Mandate Radar Compliance Requirement | Architectural Implementation |
| :--- | :--- | :--- |
| **DPDP Act 2023 (Digital Personal Data Protection)** | Purpose limitation; user consent notices; right to erasure ("Right to be Forgotten"). | Clear consent modals on ingest; complete cascade deletion service (`UserDestroyService`) that purges PostgreSQL records and Neo4j nodes upon user request. |
| **RBI e-Mandate Master Circular (2021-22)** | Tracking statutory pre-debit notifications (24-48 hours before debit); statutory right to revoke standing instructions without penalty. | Mandate engine intercepts pre-debit alerts; email generator formats legally binding revocation notices under circular `DPSS.CO.PD.No.S513/02.14.003/2021-22`. |
| **NPCI UPI AutoPay Framework** | Support mandate execution limit checks (AFA required above ₹15,000 for standard mandates; ₹100,000 for mutual funds/credit card bills). | Mandate engine models `max_amount` cap; alerts user if pre-debit notification exceeds registered cap limit. |
| **Consumer Protection (E-Commerce) Rules 2020** | Prevention of dark patterns, forced continuity, and hidden recurring fees. | Mandate Radar automatically flags trial conversion traps ($\ge 10\times$ jumps) and silent price increases ($>3\%$). |

---

## 5. Security Architecture Checklist for Production Readiness

- [ ] Implement OAuth2 / JWT authentication service with Argon2id password hashing.
- [ ] Remove wildcard CORS headers; bind CORS strictly to verified frontend domains.
- [ ] Integrate HaveIBeenPwned API check for breached password detection.
- [ ] Implement column-level encryption (AES-256-GCM) for external OAuth tokens.
- [ ] Provision Redis-backed rate limiting on all API routes.
- [ ] Implement parameterized queries across all PostgreSQL and Neo4j database calls.
- [ ] Enforce automated raw PDF shredding after transaction extraction.
- [ ] Deploy strict Content Security Policy (CSP) and HSTS response headers.
- [ ] Build user data export and account erasure endpoints for DPDP Act compliance.

