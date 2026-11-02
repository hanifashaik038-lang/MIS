# Testing, QA and Operations

## Test plan
| Level | Scenario | Expected result |
|---|---|---|
| Unit | Sale of 3 from 10 | Ledger sum becomes 7 |
| Unit | Sale exceeds available stock | Validation error; no event |
| Unit | Receipt of 5 | Ledger increases by 5 |
| Unit | Risk band thresholds | Correct Low/Moderate/High/Critical |
| Integration | PO receipt | Positive stock event and PO received quantity update |
| Integration | Prediction page | Risk table renders from DB-derived balances/history |
| Integration | Alert detection twice | Second run does not duplicate unresolved alert |
| Sync | Same event UID twice | Second copy rejected |
| Sync | Same batch UID twice | Duplicate batch acknowledged without replay |
| E2E | PO → receipt → sale → zero → alert → restock → close | Each state transition is recorded |
| Data | Ledger sum vs physical count | Investigate variance; target tolerance agreed |
| Performance | Peak scan workload | Measure p95; target <1 second under normal conditions |
| Security | Store role isolation | Production API must enforce store scope server-side |
| UAT | Employee/manager/regional/HQ tasks | Signed acceptance by role |

## Go-live criteria
Critical tests pass; pilot of 1–2 stores for 1–2 weeks; agreed stock accuracy target (e.g. 98%); backup/restore proven; training complete; rollback documented; no critical security/integrity defects.

## Limitations
No production authentication, independent store servers, real offline networking, camera scanner, live integrations, real notifications, full ASN, complete daily/monthly KPI warehouse, validated business stockout labels or SLA monitoring. Supplier delivery metrics are seeded illustrative estimates. Demo performance score includes illustrative forecast/replenishment inputs.

## Operational hardening
Migrate to PostgreSQL; deploy API service and per-store SQLite/PostgreSQL local node; use encrypted transport and secrets manager; implement OIDC/MFA and RBAC; add event signatures, retry queue, reconciliation and dead-letter queue; add metrics/logging/tracing, backups, disaster recovery, load/security tests and model monitoring.
