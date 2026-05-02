# Ghostfire Integration Map (Governance-First Scaffold)

## Purpose
This document establishes the Ghostfire integration contract for Kingdom OS as a **documentation-only** scaffold. It defines governance boundaries and integration surfaces without introducing runtime logic.

## Governance Requirements
- **Approval-gated writes:** every state-changing request requires explicit approval before execution.
- **Ledger-first operations:** mutating workflows must record intent and lifecycle events in the ledger.
- **Proof retrieval:** each approved operation must expose retrievable proof artifacts for audit.
- **No destructive actions:** destructive actions are disallowed by default and require separate policy definition.
- **Codex role boundary:** Codex is a review/patch layer and is not an autonomous authority.

## Integration Surfaces
- `services/api/` — API contract boundary.
- `services/operator-console/` — operator workflow and approval UX boundary.
- `integrations/avatar/` — avatar signal/event integration boundary.
- `integrations/sight/` — sight signal/event integration boundary.
- `integrations/voice/` — voice signal/event integration boundary.
- `ledger/` — immutable proof/event recording boundary.
- `registry/` — node and service registry boundary.

## Approval + Ledger Flow (Normative)
1. Intake request through approved API contract.
2. Validate identity, policy scope, and request schema.
3. Record write intent in ledger.
4. Enter explicit approval gate (operator/policy authority).
5. Execute only when approval is present.
6. Record outcome and proof references in ledger.
7. Expose proof retrieval endpoint for audit/review.

## Out of Scope for This Patch
- Runtime handlers, workers, or deployment pipelines.
- Secrets, credentials, or environment provisioning.
- Autonomous or destructive execution paths.
