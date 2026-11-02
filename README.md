# StockSense AI — FreshMart Supermarkets

**DEMO DATA – SIMULATED FRESHMART OPERATIONS**

A modular Streamlit demonstration for multi-store FMCG inventory, seven-day stockout-risk estimation, store performance, procurement, alerts and reporting.

## Run
```bash
cd stocksense_ai
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
SQLite database is created at `stocksense.db` on first run. Data persists between restarts.

## Demo login
The demonstration uses a role selector rather than production password authentication. It is **not** production authentication. Roles: Head Office, Regional Manager, Store Manager, Store Employee. In production, replace this with SSO/OIDC, hashed credentials, MFA and server-side authorization.

## Prediction methodology
On first run, the app generates 180 days of synthetic daily demand and inventory history across 8 stores and 120 SKUs. A Random Forest classifier is trained using a chronological split. The target is whether simulated stock falls to zero in the following seven days. Model metrics are calculated on the held-out later period. All data and model results are illustrative, not actual retail performance or a validated forecast.

## Architecture and limitations
The demo uses one SQLite database and simulates store-specific offline queues. It does not deploy eight physical store databases, a distributed sync service, production alert delivery, camera barcode scanning, POS/ERP integrations, or 99.9% uptime. Interfaces and event schemas are documented for those future production integrations. The immutable stock-event ledger is append-only at application level; stock is derived from events.

## Project structure
- `app.py`: Streamlit UI and navigation
- `database/`: SQLAlchemy schema, initialization and synthetic seeding
- `modules/`: inventory, prediction, procurement, alerts, KPI, sync and reporting logic
- `ml/`: model training/evaluation pipeline
- `utils/`: validation and calculations
- `tests/`: core unit tests
- `docs/`: Waterfall, architecture, data model, API and test documentation

## Notes
This is an academic demonstration foundation. Before production use: threat model, formal authentication/authorization, PostgreSQL migration, per-store databases, signed sync payloads, secrets management, observability, backups, load testing, notification providers, privacy/security review and pilot validation are required.
