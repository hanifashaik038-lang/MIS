# StockSense AI — Requirements and Waterfall Specification

## Abstract and problem
FreshMart is a fictional eight-store FMCG chain. Fragmented stock visibility, delayed replenishment and limited cross-store insight can cause avoidable stockouts. StockSense AI consolidates inventory events, estimates seven-day stockout risk, surfaces replenishment actions and compares store operations. All demo records are synthetic.

## Stakeholders and elicitation
| Stakeholder | Needs |
|---|---|
| Store employee | Fast barcode sales, lookup, receiving, clear validation |
| Store manager | Store stock, risks, alerts, replenishment and KPIs |
| Regional manager | Cross-store comparisons and exceptions |
| Head office | Chain-wide reporting, product/supplier master data, user administration |
| Procurement | PO lifecycle, expected delivery, partial receipt and supplier measures |
| Supplier | PO/ASN exchange contract; external portal is out of demo scope |
| IT administrator | Identity, access, audit, backups, monitoring and synchronization |

### Elicitation questions
- Scale: How many stores, SKUs, scans and daily transactions?
- Scanning: What are entry/exit scans? USB wedge or mobile camera? How are duplicate scans prevented?
- Stockout: Is it zero stock, below reorder point or empty shelf? Are low stock and true stockout separate?
- Suppliers: Are POs internal? Are ASNs available? What are supplier lead times?
- Connectivity: Can stores work offline? How are transactions replayed after reconnect?
- Reports: Which KPIs and management views are required?
- Alerts: Who receives alerts, by which channel, and within what SLA?
- Existing systems: POS/ERP integration and master-data ownership?
- Constraints: Budget, timeline, hosting, security and compliance?

These questions are open elicitation items; the fictional demo assumes 8 stores, 120 SKUs, 180 days, a seven-day prediction horizon and a five-minute alert-generation target.

## Requirements
### Business
Reduce stockouts, improve availability, enable evidence-based replenishment and compare store execution.
### Functional
FR-01 role-aware navigation; FR-02 product/store/supplier master; FR-03 barcode/manual sale; FR-04 append-only stock events; FR-05 goods receipt and partial PO receipt; FR-06 stock balance; FR-07 seven-day risk estimate; FR-08 stockout detection and deduplicated alerts; FR-09 store KPIs/ranking; FR-10 supplier indicators; FR-11 CSV/XLSX/PDF exports; FR-12 idempotent sync ingestion.
### Non-functional
Offline-first target architecture; normal scan response <1s target; alert generation <5 min target; 99.9% central uptime target; role-based access; auditability; integrity; secure transport; recoverability. These are requirements, not demonstrated SLAs.
### User/system requirements
Employees need a keyboard-wedge/manual scanner and stock feedback. Managers need filters and actions. Regional/HQ users need consolidated metrics. System needs a persistent relational store, event ledger, model pipeline, alert service and export layer.
### Acceptance criteria
Sale decreases stock; receipt increases stock; prediction uses history/current stock; alert is generated and deduplicated; managers can compare stores; repeated sync batch/event IDs do not create duplicate events.
### Scope
Included: synthetic FMCG data, inventory, scanning, receiving, PO, baseline risk, training/evaluation pipeline, alerts, KPI and reporting.
Out of scope: customer PII, payments, pricing engine, accounting, live supplier/ERP/POS, production identity, real SMS/email delivery, physical offline deployment.

## Feasibility
Technical: feasible as a Python/Streamlit/SQLite proof of concept. Operational: requires store staff training and validated data capture. Economic: demo uses open-source stack; production costs depend on hosting, devices, integrations and support. Schedule: Waterfall gates require sign-off at each stage.

## Waterfall phases
1. **Requirements** — elicitation, scope, FR/NFR, acceptance and sign-off. Output: approved SRS. Gate: stakeholders approve definitions of stockout, risk, roles and KPIs.
2. **Design** — HLD/MLD/LLD, schema, APIs, event model, UI and security. Output: design baseline. Gate: architecture and data model review.
3. **Implementation** — database, seed data, inventory, PO, risk pipeline, KPI, UI and exports. Output: executable modules. Gate: unit tests pass.
4. **Integration** — connect scan, inventory, receiving, prediction, alerts, dashboards and sync contracts. Output: integrated demo. Gate: end-to-end flow passes.
5. **Testing** — unit, integration, system, sync, data, performance, security and UAT. Output: test report and defect log. Gate: critical tests pass.
6. **Deployment & maintenance** — pilot in 1–2 stores for 1–2 weeks, train users, monitor, backup, rollback and maintain. Output: release candidate and operating plan. Gate: agreed stock tolerance (e.g. 98%) and no critical defects.

Waterfall is sequential: requirements and design are baselined before implementation; change requests are assessed against the baseline.
