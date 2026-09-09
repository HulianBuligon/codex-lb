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
- A previous-response/turn-state body may be replaced by an existing verified,
  account-neutral full-history projection after a pre-created quota rejection.
  Uploaded-file, single-account, durable operation, incomplete-history, and
  other non-reconstructible ownership remains authoritative.
- Only prompt-cache and sticky-thread affinity is eligible for owner retirement;
  a compare-and-set preserves a concurrently reassigned mapping.
- Disabling the setting surfaces the first explicit quota failure without
  account failover or soft-pin retirement.

## Verified continuation example and limitations

A client resends a proven full history, and the proxy trims it with an anchor
owned by A. If A rejects the new turn for quota before acceptance, recovery can
send the retained full history to B without A's response id or turn-state
header. The old durable ownership is not reassigned to make a partial history
appear portable. HTTP bridge sessions use the existing replacement lifecycle;
an already-registered durable operation is not moved by this extension.

This does not establish that every observed desktop usage-limit incident has
this cause. Clearing sticky mappings and seeing a subsequent request succeed
is recovery evidence, not a request-id-correlated root-cause diagnosis. Tests
exercise the verified replay path; production validation remains separate.

## Configuration independence

Replacement selection is delegated to the existing account selector after the
failed account is excluded. Therefore capacity-weighted, relative-availability,
usage-weighted, round-robin, drain, and other routing strategies retain their
own ranking behavior. Earlier-reset preference and HTTP/upstream transport
policy likewise do not enable, disable, or change the quota retry budget.
