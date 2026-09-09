## Why

An upstream account can report a quota limit before producing any response
event while other eligible accounts still have usable quota. Today that
account-local rejection can terminate an otherwise movable request, and its
soft sticky mapping can route a later client retry back to the same exhausted
account.

## What Changes

- Add bounded automatic failover for explicit, pre-visible upstream quota and
  rate-limit responses.
- Exclude each rejected account, wait five seconds, and try another eligible
  account up to three additional times within the request's existing time and
  ownership safety boundaries.
- Retire an exhausted account's soft request affinity without altering hard
  previous-response, turn-state, file, or Codex-session ownership.
- Permit verified account-neutral continuation bodies to leave an exhausted
  owner before acceptance, without forwarding obsolete account-local anchors.
  Stored files, incomplete histories, and durable operation ownership stay
  fail-closed; this is not an unconditional purge of sticky sessions.
- Cover streaming HTTP/WebSocket egress and the HTTP responses bridge without
  depending on routing strategy, reset preference, or transport policy.
- Add a persisted, default-on `quota_failover_enabled` operational kill switch
  and expose it in Settings -> Routing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `responses-api-compat`: explicit pre-visible quota failures can move a safe
  request to another account under a dedicated bounded retry budget.
- `sticky-session-operations`: usage exhaustion retires only soft affinity for
  the rejected owner.
- `frontend-architecture`: Routing settings exposes the automatic quota
  failover control.
- `database-migrations`: the new setting is persisted with a rolling-safe
  default-on column.

## Impact

- Proxy retry and HTTP bridge replay selection.
- Sticky-session cleanup after confirmed usage exhaustion.
- Dashboard settings model, API, cache, UI, and locale bundles.
- One additive Alembic revision; no environment variable, dependency,
  navigation item, setup step, or README section.
