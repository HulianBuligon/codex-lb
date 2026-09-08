# Automatic quota failover context

## Purpose

Keep movable requests alive when the selected account returns an explicit
quota rejection before any downstream-visible response, while preserving hard
continuity and keeping retries bounded enough for safe unattended operation.

## Trigger

Only normalized upstream codes `rate_limit_exceeded`, `usage_limit_reached`,
`insufficient_quota`, `usage_not_included`, and `quota_exceeded` qualify. A
generic timeout, transport error, server error, invalid request, authentication
failure, or local capacity rejection does not consume this feature's retry
budget.

## Safety boundaries

- Maximum three additional attempts per request, each delayed five seconds
  after an eligible replacement is selected and before it is dispatched.
- If no eligible replacement exists, the original quota response is surfaced
  without an artificial delay or proxy-generated replacement error.
- Every rejected account is excluded from later selections for that request.
- Any response event or downstream-visible output keeps the request
  fail-closed; accepted or ambiguous work is never replayed as quota failover.
- Previous-response, turn-state, uploaded-file, single-account, and other hard
  ownership remains authoritative.
- Only prompt-cache and sticky-thread affinity is eligible for owner retirement;
  a compare-and-set preserves a concurrently reassigned mapping.
- Disabling the setting surfaces the first explicit quota failure without
  account failover or soft-pin retirement.

## Configuration independence

Replacement selection is delegated to the existing account selector after the
failed account is excluded. Therefore capacity-weighted, relative-availability,
usage-weighted, round-robin, drain, and other routing strategies retain their
own ranking behavior. Earlier-reset preference and HTTP/upstream transport
policy likewise do not enable, disable, or change the quota retry budget.
