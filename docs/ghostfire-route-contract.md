# Ghostfire Route Contract (Draft v0)

## Scope
Documentation-only API contract draft for Ghostfire integration. This file defines intended interfaces and governance controls; it does not implement runtime behavior.

## Global Contract Rules
- All **write** routes are approval-gated.
- All **mutating** workflows are ledger-first.
- Every approved workflow must support proof retrieval.
- Destructive operations are excluded from v0.
- Codex acts as a review/patch executor, never autonomous authority.

## Read Routes
| Route | Purpose | Governance Notes |
|---|---|---|
| `GET /health` | Service liveness check | Read-only |
| `GET /version` | Service + contract version metadata | Read-only |
| `GET /ghostfire/proof/:id` | Retrieve proof bundle | Audit surface |
| `GET /ghostfire/ledger/:id` | Retrieve ledger event/segment | Audit surface |
| `GET /ghostfire/nodes` | List registered nodes | Read-only |
| `GET /ghostfire/operators` | Operator queue/status summary | Read-only |

## Write Routes (Approval-Gated)
| Route | Purpose | Required Control |
|---|---|---|
| `POST /ghostfire/handoff` | Codex handoff intake | Approval + ledger intent |
| `POST /ghostfire/ledger/append` | Append approved ledger event | Approval provenance |
| `POST /ghostfire/nodes/register` | Register/update node metadata | Approval + registry policy |
| `POST /ghostfire/avatar/event` | Ingest avatar event | Approval policy + ledger trail |
| `POST /ghostfire/sight/event` | Ingest sight event | Approval policy + ledger trail |
| `POST /ghostfire/voice/event` | Ingest voice event | Approval policy + ledger trail |

## Missing/Deferred Routes (Intentional)
- No delete/purge endpoints in v0.
- No force-update or bypass-approval endpoints.
- No direct “execute-now” autonomous control route.

## Implementation Follow-Ups
- Define request/response schemas and error model.
- Define authn/authz matrix per route.
- Define idempotency and replay protection for write routes.
- Define proof bundle format and retention policy.
