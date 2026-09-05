# RecoverAI — Agentic Revenue Recovery Engine

> **Tagline:** Turn revenue leakage into recovered cash.

RecoverAI is an autonomous, agentic revenue recovery system that continuously detects revenue at risk, diagnoses why the revenue failed, evaluates candidate interventions using economic optimization (Expected Recovery Value), validates actions against deterministic policy guardrails, executes bounded interventions, observes real outcomes, and re-evaluates until resolution or hard stop.

---

## 1. Architectural Source-of-Truth Guarantee

**RecoverAI adheres to a strict non-negotiable architectural invariant: The database is the sole source of truth.**
- Zero hardcoded numbers, customer records, case statuses, or recovery percentages in React.
- All numbers, KPIs, charts, agent decisions, policy evaluations, and audit logs are dynamically queried from the FastAPI backend and computed from persistent database records.
- When an action recovers revenue in the backend, the database updates, the API recalculates metrics, and the UI reflects real recovered cash.

```
Database / Simulation Engine (SQLite / PostgreSQL)
                   ↓
         Backend Business Logic
                   ↓
         FastAPI REST Endpoints
                   ↓
           Frontend API Client
                   ↓
          React State & Views
```

---

## 2. The Core Agentic Loop

```
DETECT
  ↓
DIAGNOSE (Mistral AI / Structured Deterministic Fallback)
  ↓
EVALUATE INTERVENTIONS (Expected Recovery Value & Incremental Recovery)
  ↓
SELECT BEST ACTION (Highest ERV among allowed policies)
  ↓
POLICY CHECK (Deterministic Guardrails & Bounded Autonomy)
  ↓
EXECUTE (Razorpay Provider / Simulation Provider)
  ↓
OBSERVE RESULT
  ↓
RECOVER / RE-EVALUATE / ESCALATE / STOP
```

RecoverAI supports three specialized loss workflows within one shared intelligence engine:
1. **Payment Failures:** Insufficient funds, temporary issuer decline, expired card, mandate failures, UPI declines, gateway timeouts.
2. **Checkout Abandonment:** Cart abandonment, payment page drop-off, session timeouts, price friction, payment method mismatch.
3. **Overdue B2B Receivables:** First-time delays, chronic late payers, dispute-flagged accounts, cash-flow issues, Promise-to-Pay commitments.

---

## 3. Economic Decision Model: Expected Recovery Value (ERV)

RecoverAI does not blindly pick the intervention with the highest recovery probability. It optimizes net economic recovery:

$$\text{Expected Recovery Value (ERV)} = \text{Probability of Recovery} \times \text{Amount at Risk} - \text{Intervention Cost}$$

### Estimated Incremental Recovery (Uplift)
$$\text{Estimated Incremental Recovery} = P(\text{recovery} \mid \text{action}) - P(\text{recovery} \mid \text{baseline})$$

- **Intervention Costs:** Smart Retry (₹10), Payment Link (₹15), Alternate Payment Method (₹20), Contextual Reminder (₹5), Hinglish Message (₹8), Promise-to-Pay (₹5), Payment Plan (₹25), Human Escalation (₹200).
- Probabilities are dynamically calculated from customer lifetime value (LTV), transaction history, failure code, days overdue, and prior attempt counts.

---

## 4. Deterministic Policy Guardrails & Bounded Autonomy

While Mistral provides structured diagnostic reasoning, **the deterministic policy engine holds authoritative execution veto power**.

### Configurable Dynamic Policies (Stored in DB, Editable via UI):
- `MAX_PAYMENT_RETRIES`: Maximum automated retries per case (default: 3).
- `RETRY_COOLDOWN_HOURS`: Minimum cooldown window between retries (default: 4 hours).
- `MAX_CONTACTS_PER_DAY`: Maximum communications per customer per day (default: 3).
- `HIGH_VALUE_THRESHOLD`: Exposure threshold requiring human approval (default: ₹50,000).
- `MAX_DUNNING_DAYS`: Maximum dunning window for overdue invoices (default: 90 days).
- `MIN_EXPECTED_VALUE`: Negative ERV threshold blocking unprofitable actions (default: ₹0).

### Invariant Hard Stops:
- Customer Opt-Out: Immediately terminates all outreach.
- Active Dispute / Chargeback: Hard blocks retries and communications.
- Financial Hardship: Requires human operator review.
- Maximum Attempts Reached: Halts automated execution and escalates.

---

## 5. Technology Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React, React Router.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy (asyncio), aiosqlite (zero-credential local SQLite fallback, PostgreSQL compatible).
- **AI Engine:** Mistral API for structured reasoning, diagnosis, and Hinglish recovery copy, paired with deterministic rule-based fallbacks so the app never crashes without credentials.
- **Payment Layer:** Abstract `PaymentProvider` with `SimulationProvider` (probabilistic dynamic outcomes) and `RazorpayProvider` (live test mode).

---

## 6. Setup & Local Development Instructions

### Prerequisites
- Python 3.12+ (or `uv` package manager)
- Node.js 18+ and npm

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Contents:
```ini
MISTRAL_API_KEY=your_mistral_api_key_here
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
DATABASE_URL=sqlite+aiosqlite:///./recoverai.db
```
*(Note: If `MISTRAL_API_KEY` is not provided, RecoverAI seamlessly runs in full deterministic mode with 100% functionality.)*

### 2. Run Backend
```bash
cd backend
# With uv (recommended):
uv venv --python 3.12 .venv
uv pip install -r requirements.txt --python .venv/Scripts/python.exe
.venv/Scripts/uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The backend automatically initializes tables and seeds 100 realistic cases on first launch.

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 7. Automated Test Suite

Run backend unit and integration tests:
```bash
cd backend
.venv/Scripts/python -m pytest tests/ -v
```
Tests cover:
- Policy Engine guardrails (opt-out, disputes, hardship, cooldowns)
- Value Calculator economic equations (ERV, incremental uplift)
- Deterministic and structured Root Cause diagnostics
- Core FastAPI endpoints (Dashboard, Revenue Risk, Policies, Permissions)

---

## 8. 5-Minute Demo Script for Judges (§58)

1. **Minute 0–1: Command Center**
   - Open Command Center dashboard.
   - Point out live dynamic metrics (e.g. Total Revenue at Risk, Revenue Recovered, Recovery Yield).
   - Emphasize: *All metrics are computed live from database rows; zero hardcoding.*
2. **Minute 1–2: Single Case Walkthrough**
   - Navigate to **Revenue Risk**. Select a payment failure case.
   - View root cause diagnosis with confidence percentage and factual evidence points.
   - Inspect the **Expected Recovery Value (ERV) Table** comparing Smart Retry, Payment Link, and Reminders.
   - Click **"Run Recovery Agent"**.
   - Show the policy check passing, simulated provider execution, dynamic success or failure outcome, and automatic transition.
3. **Minute 2–3: Real-Time Dashboard & Ledger Reflection**
   - Click **Recovery Ledger** to view the newly minted audit trail record with timestamp and ERV.
   - Return to **Command Center**. Show that Revenue Recovered and Recovery Rate updated immediately because the database changed.
4. **Minute 3–4: Dynamic Policy Modification**
   - Navigate to **Policies**.
   - Change `MAX_PAYMENT_RETRIES` from 3 to 5 (or change High Value Threshold).
   - Save. Show that the next agent execution immediately honors the updated database configuration.
5. **Minute 4–5: Batch Simulator & Baseline Benchmark**
   - Navigate to **Data Simulator**.
   - Select 500 events and click **"Run Batch Recovery"**.
   - Watch live concurrent processing of cases.
   - Open **Analytics** to view the side-by-side **Baseline vs. RecoverAI** chart demonstrating measurable incremental recovery.

---

## 9. Future Architecture Roadmap (§52)

- **Temporal Graph Intelligence (T-GNN):** Continuous temporal graph modeling linking multi-account merchants, recurring mandates, and behavioral velocity.
- **Causal Machine Learning & Heterogeneous Treatment Effects:** Moving from estimated incremental recovery to uplift modeling (Causal Forests / Double Machine Learning).
- **Cross-Merchant Pattern Learning:** Shared risk signals across merchant ecosystems without leaking proprietary transaction records.
- **Autonomous Voice Recovery:** Conversational AI phone agents with real-time Hinglish speech synthesis for high-value B2B receivables collections.
